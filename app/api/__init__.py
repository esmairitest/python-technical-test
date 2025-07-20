from api.groups import group_router
from api.sites import site_router
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")
api_router.include_router(group_router)
api_router.include_router(site_router)

__all__ = ["api_router"]
