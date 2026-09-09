from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain import Game
from app.schemas.domain import GameRead

router = APIRouter(prefix="/games", tags=["Jogos"])


@router.get("", response_model=list[GameRead])
def list_games(db: Session = Depends(get_db)) -> list[Game]:
    return list(db.scalars(select(Game).where(Game.is_active.is_(True)).order_by(Game.name)))

