from fastapi import APIRouter
from .endpoints import (
    auth,
    cam_bien,
    cau_hinh_thiet_bi,
    du_lieu_cam_bien,
    du_lieu_du_bao,
    loai_cam_bien,
    may_bom,
    mo_hinh_du_bao,
    nguoi_dung,
    nhat_ky_may_bom,
    thong_bao,
    admin_alerts,
)

api_v1_router = APIRouter()

# Include all endpoint routers
api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(nguoi_dung.router, prefix="/nguoi-dung", tags=["nguoi-dung"])
api_v1_router.include_router(may_bom.router, prefix="/may-bom", tags=["may-bom"])
api_v1_router.include_router(cam_bien.router, prefix="/cam-bien", tags=["cam-bien"])
api_v1_router.include_router(cau_hinh_thiet_bi.router, prefix="/cau-hinh-thiet-bi", tags=["cau-hinh-thiet-bi"])
api_v1_router.include_router(loai_cam_bien.router, prefix="/loai-cam-bien", tags=["loai-cam-bien"])
api_v1_router.include_router(du_lieu_cam_bien.router, prefix="/du-lieu-cam-bien", tags=["du-lieu-cam-bien"])
api_v1_router.include_router(du_lieu_du_bao.router, prefix="/du-lieu-du-bao", tags=["du-lieu-du-bao"])
api_v1_router.include_router(mo_hinh_du_bao.router, prefix="/mo-hinh-du-bao", tags=["mo-hinh-du-bao"])
api_v1_router.include_router(nhat_ky_may_bom.router, prefix="/nhat-ky-may-bom", tags=["nhat-ky-may-bom"])
api_v1_router.include_router(thong_bao.router, prefix="/thong-bao", tags=["thong-bao"])
api_v1_router.include_router(admin_alerts.router, prefix="/admin-alerts", tags=["admin-alerts"])
