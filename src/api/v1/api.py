from fastapi import APIRouter
from .endpoints import nguoi_dung, auth, loai_cam_bien

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

api_v1_router.include_router(
    loai_cam_bien.router,
    prefix="/loai-cam-bien",
    tags=["loai-cam-bien"]
)
