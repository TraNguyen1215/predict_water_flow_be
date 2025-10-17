from fastapi import APIRouter
from .endpoints import auth_router

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
