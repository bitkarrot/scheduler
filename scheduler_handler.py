import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("scheduler")

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")


async def stop_scheduler() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


async def add_job(job_id: str, cron_expr: str, func, args: list | None = None) -> str:
    """Add or replace a scheduled job by cron expression (e.g. '*/5 * * * *')."""
    scheduler = get_scheduler()
    trigger = CronTrigger.from_crontab(cron_expr)
    scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        args=args or [],
        replace_existing=True,
        misfire_grace_time=60,  # tolerate up to 60s of scheduler lag
    )
    logger.info(f"Job added: {job_id} @ {cron_expr}")
    return f"job created: {job_id}, {cron_expr}"


async def remove_job(job_id: str) -> str:
    scheduler = get_scheduler()
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Job removed: {job_id}")
        return "job removed"
    except Exception:
        logger.warning(f"Job not found for removal: {job_id}")
        return "job not found"


async def enable_job(job_id: str, active: bool) -> bool:
    """Pause or resume a job without removing it from the scheduler."""
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)
    if job is None:
        logger.error(f"Job not found: {job_id}")
        return False
    if active:
        scheduler.resume_job(job_id)
    else:
        scheduler.pause_job(job_id)
    logger.info(f"Job {job_id} {'resumed' if active else 'paused'}")
    return True


async def get_job_status(job_id: str) -> bool:
    """Returns True if the job exists and is not paused."""
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)
    if job is None:
        return False
    return job.next_run_time is not None  # None means paused


async def list_jobs() -> list[str]:
    scheduler = get_scheduler()
    return [str(job) for job in scheduler.get_jobs()]


async def validate_cron_string(expr: str) -> bool:
    try:
        CronTrigger.from_crontab(expr)
        return True
    except Exception:
        return False
