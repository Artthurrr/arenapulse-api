from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models.domain import (
    Challenge,
    Game,
    GameCategory,
    Participation,
    User,
    UserRole,
)


def seed_demo_data() -> None:
    with SessionLocal() as db:
        game_specs = [
            ("EA Sports FC", "ea-sports-fc", GameCategory.FOOTBALL),
            ("Counter-Strike 2", "counter-strike-2", GameCategory.FPS),
            ("Valorant", "valorant", GameCategory.FPS),
        ]
        games: dict[str, Game] = {}
        for name, slug, category in game_specs:
            game = db.scalar(select(Game).where(Game.slug == slug))
            if not game:
                game = Game(name=name, slug=slug, category=category)
                db.add(game)
                db.flush()
            games[slug] = game

        host = db.scalar(select(User).where(User.username == "arena_host"))
        if not host:
            host = User(
                email="host@arenapulse.local",
                username="arena_host",
                password_hash="system-account-disabled",
                role=UserRole.MANAGER,
                is_active=False,
            )
            db.add(host)
            db.flush()

        first_challenge = db.scalar(select(Challenge).order_by(Challenge.id).limit(1))
        if not first_challenge:
            now = datetime.now(UTC)
            challenges = [
                Challenge(
                    title="Fim de semana sem perder",
                    description="Some pontos em partidas de EA Sports FC durante sete dias.",
                    reward="Badge Invicto",
                    starts_at=now - timedelta(days=1),
                    ends_at=now + timedelta(days=7),
                    creator_id=host.id,
                    game_id=games["ea-sports-fc"].id,
                ),
                Challenge(
                    title="Esquadrão preciso",
                    description="Vitórias ranqueadas de Counter-Strike 2 contam para a tabela.",
                    reward="Badge Tático",
                    starts_at=now - timedelta(hours=12),
                    ends_at=now + timedelta(days=5),
                    creator_id=host.id,
                    game_id=games["counter-strike-2"].id,
                ),
                Challenge(
                    title="Rota da mira",
                    description="Registre placares no Valorant e avance no ranking da temporada.",
                    reward="Badge Clutch",
                    starts_at=now - timedelta(hours=6),
                    ends_at=now + timedelta(days=10),
                    creator_id=host.id,
                    game_id=games["valorant"].id,
                ),
            ]
            db.add_all(challenges)
            db.flush()
            first_challenge = challenges[0]

        if not db.scalar(
            select(Participation.id)
            .join(Participation.user)
            .where(User.username.like("demo_%"))
            .limit(1)
        ):
            player_specs = [
                ("demo_tatica10", 14, 6, 4, 2, 0),
                ("demo_viperbr", 11, 5, 3, 2, 0),
                ("demo_noscope", 9, 4, 3, 0, 1),
                ("demo_meia9", 8, 6, 2, 2, 2),
            ]
            for index, (username, points, matches, wins, draws, losses) in enumerate(
                player_specs, start=1
            ):
                player = User(
                    email=f"demo{index}@arenapulse.local",
                    username=username,
                    password_hash="demo-account-disabled",
                    is_active=False,
                )
                db.add(player)
                db.flush()
                db.add(
                    Participation(
                        user_id=player.id,
                        challenge_id=first_challenge.id,
                        points=points,
                        matches_played=matches,
                        wins=wins,
                        draws=draws,
                        losses=losses,
                    )
                )
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    yield


app = FastAPI(
    title=settings.app_name,
    description="API de desafios, resultados e rankings para comunidades gamer.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/", tags=["Infraestrutura"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "message": "ArenaPulse está online",
        "docs": "/docs",
    }


@app.get("/health", tags=["Infraestrutura"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
