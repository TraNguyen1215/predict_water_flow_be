from fastapi import APIRouter
from .endpoints import nguoi_dung

api_v1_router = APIRouter()

# Include authentication routes

api_v1_router.include_router(
    nguoi_dung.router,
    prefix="/nguoi-dung",
    tags=["nguoi-dung"]
)
