from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import Participation, User
from app.schemas.domain import Dashboard, UserRead

router = APIRouter(prefix="/me", tags=["Meu perfil"])


@router.get("", response_model=UserRead)
def read_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.get("/dashboard", response_model=Dashboard)
def dashboard(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Dashboard:
    values = db.execute(
        select(
            func.count(Participation.id),
            func.coalesce(func.sum(Participation.points), 0),
            func.coalesce(func.sum(Participation.matches_played), 0),
            func.coalesce(func.sum(Participation.wins), 0),
        ).where(Participation.user_id == current_user.id)
    ).one()
    return Dashboard(
        username=current_user.username,
        challenges_joined=values[0],
        total_points=values[1],
        total_matches=values[2],
        total_wins=values[3],
    )
