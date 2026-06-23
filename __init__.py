import logging

from fastapi import APIRouter

from .crud import db
from .views import scheduler_generic_router
from .views_api import scheduler_api_router

logger = logging.getLogger("scheduler")

scheduler_ext: APIRouter = APIRouter(prefix="/scheduler", tags=["scheduler"])
scheduler_ext.include_router(scheduler_generic_router)
scheduler_ext.include_router(scheduler_api_router)

scheduler_static_files = [
    {
        "path": "/scheduler/static",
        "name": "scheduler_static",
    }
]


@scheduler_ext.on_event("startup")
async def on_startup() -> None:
    """Initialize APScheduler and reload active jobs from DB on startup."""
    from .crud import get_all_active_scheduler_jobs
    from .job_runner import execute_job
    from .scheduler_handler import add_job, start_scheduler

    await start_scheduler()
    # Re-hydrate scheduler from DB on every restart
    active_jobs = await get_all_active_scheduler_jobs()
    for job in active_jobs:
        await add_job(
            job_id=job.id,
            cron_expr=job.schedule,
            func=execute_job,
            args=[job.id],
        )
    logger.info(f"Loaded {len(active_jobs)} active jobs from DB into scheduler")


@scheduler_ext.on_event("shutdown")
async def on_shutdown() -> None:
    """Shutdown APScheduler gracefully."""
    from .scheduler_handler import stop_scheduler

    await stop_scheduler()


__all__ = ["db", "scheduler_ext", "scheduler_static_files"]
