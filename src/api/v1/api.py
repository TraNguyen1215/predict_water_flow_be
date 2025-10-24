from fastapi import APIRouter
from .endpoints import nguoi_dung, auth, loai_cam_bien, cam_bien, may_bom, nhat_ky_may_bom, du_lieu_cam_bien, du_lieu_du_bao

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

api_v1_router.include_router(
    cam_bien.router,
    prefix="/cam-bien",
    tags=["cam-bien"]
)

api_v1_router.include_router(
    may_bom.router,
    prefix="/may-bom",
    tags=["may-bom"]
)

api_v1_router.include_router(
    nhat_ky_may_bom.router,
    prefix="/nhat-ky-may-bom",
    tags=["nhat-ky-may-bom"]
)

api_v1_router.include_router(
    du_lieu_cam_bien.router,
    prefix="/du-lieu-cam-bien",
    tags=["du-lieu-cam-bien"]
)


api_v1_router.include_router(
    du_lieu_du_bao.router,
    prefix="/du-lieu-du-bao",
    tags=["du-lieu-du-bao"]
)
