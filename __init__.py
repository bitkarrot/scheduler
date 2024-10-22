from fastapi import APIRouter

from .crud import db
from .views import scheduler_generic_router
from .views_api import scheduler_api_router

scheduler_ext: APIRouter = APIRouter(prefix="/scheduler", tags=["scheduler"])
scheduler_ext.include_router(scheduler_generic_router)
scheduler_ext.include_router(scheduler_api_router)

scheduler_static_files = [
    {
        "path": "/scheduler/static",
        "name": "scheduler_static",
    }
]

__all__ = ["db", "scheduler_ext", "scheduler_static_files"]
