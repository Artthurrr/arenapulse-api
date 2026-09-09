from fastapi import APIRouter

from app.api.routes import auth, challenges, games, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(games.router)
api_router.include_router(challenges.router)
api_router.include_router(users.router)

