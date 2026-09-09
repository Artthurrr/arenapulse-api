from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import (
    Challenge,
    ChallengeStatus,
    Game,
    MatchResult,
    Participation,
    User,
)
from app.schemas.domain import (
    ChallengeCreate,
    ChallengeRead,
    LeaderboardEntry,
    ParticipationRead,
    ResultCreate,
    ResultRead,
)

router = APIRouter(prefix="/challenges", tags=["Desafios"])


def is_after_now(value: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return datetime.now(UTC) > value


def get_challenge_or_404(db: Session, challenge_id: int) -> Challenge:
    challenge = db.scalar(
        select(Challenge).options(joinedload(Challenge.game)).where(Challenge.id == challenge_id)
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="Desafio não encontrado")
    return challenge


@router.post("", response_model=ChallengeRead, status_code=status.HTTP_201_CREATED)
def create_challenge(
    payload: ChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Challenge:
    game = db.get(Game, payload.game_id)
    if not game or not game.is_active:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    challenge = Challenge(**payload.model_dump(), creator_id=current_user.id)
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return get_challenge_or_404(db, challenge.id)


@router.get("", response_model=list[ChallengeRead])
def list_challenges(
    game_slug: str | None = None,
    challenge_status: ChallengeStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Challenge]:
    query = select(Challenge).options(joinedload(Challenge.game)).join(Challenge.game)
    if game_slug:
        query = query.where(Game.slug == game_slug)
    if challenge_status:
        query = query.where(Challenge.status == challenge_status)
    query = query.order_by(Challenge.starts_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(query))


@router.get("/{challenge_id}", response_model=ChallengeRead)
def get_challenge(challenge_id: int, db: Session = Depends(get_db)) -> Challenge:
    return get_challenge_or_404(db, challenge_id)


@router.post(
    "/{challenge_id}/join", response_model=ParticipationRead, status_code=status.HTTP_201_CREATED
)
def join_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Participation:
    challenge = get_challenge_or_404(db, challenge_id)
    if challenge.status != ChallengeStatus.PUBLISHED:
        raise HTTPException(status_code=409, detail="Este desafio não aceita inscrições")
    if is_after_now(challenge.ends_at):
        raise HTTPException(status_code=409, detail="Este desafio já terminou")

    existing = db.scalar(
        select(Participation).where(
            Participation.user_id == current_user.id,
            Participation.challenge_id == challenge_id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Você já participa deste desafio")

    participation = Participation(user_id=current_user.id, challenge_id=challenge_id)
    db.add(participation)
    db.commit()
    db.refresh(participation)
    return participation


@router.post("/{challenge_id}/results", response_model=ResultRead, status_code=201)
def submit_result(
    challenge_id: int,
    payload: ResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MatchResult:
    challenge = get_challenge_or_404(db, challenge_id)
    participation = db.scalar(
        select(Participation).where(
            Participation.user_id == current_user.id,
            Participation.challenge_id == challenge_id,
        )
    )
    if not participation:
        raise HTTPException(status_code=403, detail="Entre no desafio antes de enviar resultados")
    if challenge.status != ChallengeStatus.PUBLISHED or is_after_now(challenge.ends_at):
        raise HTTPException(status_code=409, detail="O desafio não está recebendo resultados")

    if payload.score_for > payload.score_against:
        outcome, points = "win", challenge.points_win
        participation.wins += 1
    elif payload.score_for == payload.score_against:
        outcome, points = "draw", challenge.points_draw
        participation.draws += 1
    else:
        outcome, points = "loss", challenge.points_loss
        participation.losses += 1

    participation.matches_played += 1
    participation.points += points
    result = MatchResult(
        participation_id=participation.id,
        outcome=outcome,
        points_awarded=points,
        **payload.model_dump(),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.get("/{challenge_id}/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(
    challenge_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[LeaderboardEntry]:
    get_challenge_or_404(db, challenge_id)
    rows = db.execute(
        select(Participation, User.username)
        .join(Participation.user)
        .where(Participation.challenge_id == challenge_id)
        .order_by(
            Participation.points.desc(),
            Participation.wins.desc(),
            Participation.joined_at.asc(),
        )
        .limit(limit)
    ).all()
    return [
        LeaderboardEntry(
            position=position,
            username=username,
            points=participation.points,
            matches_played=participation.matches_played,
            wins=participation.wins,
            draws=participation.draws,
            losses=participation.losses,
        )
        for position, (participation, username) in enumerate(rows, start=1)
    ]
