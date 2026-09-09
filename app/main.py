from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models.domain import Game, GameCategory


def seed_games() -> None:
    with SessionLocal() as db:
        if db.scalar(select(Game.id).limit(1)):
            return
        db.add_all(
            [
                Game(name="EA Sports FC", slug="ea-sports-fc", category=GameCategory.FOOTBALL),
                Game(name="Counter-Strike 2", slug="counter-strike-2", category=GameCategory.FPS),
                Game(name="Valorant", slug="valorant", category=GameCategory.FPS),
            ]
        )
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_games()
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
