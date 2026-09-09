from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UserRole(str, enum.Enum):
    PLAYER = "player"
    MANAGER = "manager"
    ADMIN = "admin"


class GameCategory(str, enum.Enum):
    FOOTBALL = "football"
    FPS = "fps"


class ChallengeStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    FINISHED = "finished"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.PLAYER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    challenges: Mapped[list[Challenge]] = relationship(back_populates="creator")
    participations: Mapped[list[Participation]] = relationship(back_populates="user")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[GameCategory] = mapped_column(Enum(GameCategory))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    challenges: Mapped[list[Challenge]] = relationship(back_populates="game")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text)
    reward: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[ChallengeStatus] = mapped_column(
        Enum(ChallengeStatus), default=ChallengeStatus.PUBLISHED, index=True
    )
    points_win: Mapped[int] = mapped_column(Integer, default=3)
    points_draw: Mapped[int] = mapped_column(Integer, default=1)
    points_loss: Mapped[int] = mapped_column(Integer, default=0)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), index=True)

    creator: Mapped[User] = relationship(back_populates="challenges")
    game: Mapped[Game] = relationship(back_populates="challenges")
    participations: Mapped[list[Participation]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


class Participation(Base):
    __tablename__ = "participations"
    __table_args__ = (UniqueConstraint("user_id", "challenge_id", name="uq_user_challenge"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), index=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    matches_played: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="participations")
    challenge: Mapped[Challenge] = relationship(back_populates="participations")
    results: Mapped[list[MatchResult]] = relationship(
        back_populates="participation", cascade="all, delete-orphan"
    )


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    participation_id: Mapped[int] = mapped_column(ForeignKey("participations.id"), index=True)
    score_for: Mapped[int] = mapped_column(Integer)
    score_against: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(8))
    points_awarded: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(280), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    participation: Mapped[Participation] = relationship(back_populates="results")

