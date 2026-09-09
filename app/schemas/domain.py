from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.domain import ChallengeStatus, GameCategory, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    role: UserRole
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    category: GameCategory


class ChallengeCreate(BaseModel):
    title: str = Field(min_length=4, max_length=120)
    description: str = Field(min_length=10, max_length=2000)
    reward: str | None = Field(default=None, max_length=160)
    game_id: int
    starts_at: datetime
    ends_at: datetime
    points_win: int = Field(default=3, ge=0, le=100)
    points_draw: int = Field(default=1, ge=0, le=100)
    points_loss: int = Field(default=0, ge=0, le=100)

    @model_validator(mode="after")
    def validate_period(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at deve ser posterior a starts_at")
        return self


class ChallengeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    reward: str | None
    status: ChallengeStatus
    points_win: int
    points_draw: int
    points_loss: int
    starts_at: datetime
    ends_at: datetime
    creator_id: int
    game: GameRead


class ParticipationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    challenge_id: int
    points: int
    matches_played: int
    wins: int
    draws: int
    losses: int
    joined_at: datetime


class ResultCreate(BaseModel):
    score_for: int = Field(ge=0, le=999)
    score_against: int = Field(ge=0, le=999)
    notes: str | None = Field(default=None, max_length=280)


class ResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    participation_id: int
    score_for: int
    score_against: int
    outcome: str
    points_awarded: int
    notes: str | None
    submitted_at: datetime


class LeaderboardEntry(BaseModel):
    position: int
    username: str
    points: int
    matches_played: int
    wins: int
    draws: int
    losses: int


class Dashboard(BaseModel):
    username: str
    challenges_joined: int
    total_points: int
    total_matches: int
    total_wins: int

