from fastapi import APIRouter
from .endpoints import nguoi_dung, auth

api_v1_router = APIRouter()

# Include authentication routes

api_v1_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_v1_router.include_router(
    nguoi_dung.router,
    prefix="/nguoi-dung",
    tags=["nguoi-dung"]
)
