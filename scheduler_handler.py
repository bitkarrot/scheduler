import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional

logger = logging.getLogger("scheduler")

# APScheduler is preferred, but not always available in host LNbits venv.
# Keep extension importable by falling back to an internal async scheduler.
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    HAS_APSCHEDULER = True
except Exception:  # pragma: no cover - depends on host runtime
    AsyncIOScheduler = None  # type: ignore[assignment]
    CronTrigger = None  # type: ignore[assignment]
    HAS_APSCHEDULER = False

if TYPE_CHECKING:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler


_scheduler: Optional[Any] = None
_fallback_runner: Optional[asyncio.Task] = None
_fallback_jobs: dict[str, dict] = {}


def _parse_int_set(token: str, low: int, high: int) -> set[int]:
    vals: set[int] = set()
    for part in token.split(","):
        part = part.strip()
        if not part:
            raise ValueError("Empty cron token")

        step = 1
        if "/" in part:
            base, step_s = part.split("/", 1)
            step = int(step_s)
            if step <= 0:
                raise ValueError("Cron step must be > 0")
        else:
            base = part

        if base == "*":
            start, end = low, high
        elif "-" in base:
            s, e = base.split("-", 1)
            start, end = int(s), int(e)
        else:
            v = int(base)
            start = end = v

        if start < low or end > high or start > end:
            raise ValueError("Cron value out of range")

        vals.update(range(start, end + 1, step))

    return vals


def _parse_cron(expr: str) -> dict[str, set[int]]:
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError("Cron must have exactly 5 fields")

    minute, hour, dom, month, dow = parts
    return {
        "minute": _parse_int_set(minute, 0, 59),
        "hour": _parse_int_set(hour, 0, 23),
        "dom": _parse_int_set(dom, 1, 31),
        "month": _parse_int_set(month, 1, 12),
        "dow": _parse_int_set(dow, 0, 6),  # sunday=0
    }


def _cron_matches(now: datetime, spec: dict[str, set[int]]) -> bool:
    dow = (now.weekday() + 1) % 7  # convert monday=0 -> monday=1, sunday=0
    return (
        now.minute in spec["minute"]
        and now.hour in spec["hour"]
        and now.day in spec["dom"]
        and now.month in spec["month"]
        and dow in spec["dow"]
    )


async def _fallback_loop() -> None:
    logger.warning("APScheduler unavailable; running fallback scheduler loop")
    while True:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

        for job_id, job in list(_fallback_jobs.items()):
            if not job.get("active", True):
                continue
            if not _cron_matches(now, job["spec"]):
                continue
            if job.get("last_run") == now:
                continue
            job["last_run"] = now
            try:
                task = asyncio.create_task(job["func"](*job.get("args", [])))
                job["task"] = task
            except Exception as exc:
                logger.error(f"Fallback scheduler failed to schedule {job_id}: {exc}")

        # sleep to just after next minute
        nxt = now + timedelta(minutes=1)
        delay = max(0.1, (nxt - datetime.now(timezone.utc)).total_seconds() + 0.1)
        await asyncio.sleep(delay)


def get_scheduler() -> Any:
    if not HAS_APSCHEDULER:
        raise RuntimeError("APScheduler not available")
    assert AsyncIOScheduler is not None
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def start_scheduler() -> None:
    global _fallback_runner
    if HAS_APSCHEDULER:
        scheduler = get_scheduler()
        if not scheduler.running:
            scheduler.start()
            logger.info("APScheduler started")
        return

    if _fallback_runner is None or _fallback_runner.done():
        _fallback_runner = asyncio.create_task(_fallback_loop())
        logger.info("Fallback scheduler started")


async def stop_scheduler() -> None:
    global _scheduler, _fallback_runner
    if HAS_APSCHEDULER:
        scheduler = get_scheduler()
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("APScheduler stopped")
        _scheduler = None
        return

    if _fallback_runner and not _fallback_runner.done():
        _fallback_runner.cancel()
        try:
            await _fallback_runner
        except asyncio.CancelledError:
            pass
    _fallback_runner = None
    logger.info("Fallback scheduler stopped")


async def add_job(
    job_id: str,
    cron_expr: str,
    func: Callable[..., Awaitable[None]],
    args: list | None = None,
) -> str:
    # Ensure runtime scheduler is alive even if startup hook did not run
    # (can happen on some hot-install/activation flows).
    await start_scheduler()

    if HAS_APSCHEDULER:
        scheduler = get_scheduler()
        trigger = CronTrigger.from_crontab(cron_expr)  # type: ignore[union-attr]
        scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            args=args or [],
            replace_existing=True,
            misfire_grace_time=60,
        )
        logger.info(f"Job added: {job_id} @ {cron_expr}")
        return f"job created: {job_id}, {cron_expr}"

    spec = _parse_cron(cron_expr)
    _fallback_jobs[job_id] = {
        "spec": spec,
        "func": func,
        "args": args or [],
        "active": True,
        "last_run": None,
    }
    logger.info(f"Fallback job added: {job_id} @ {cron_expr}")
    return f"job created: {job_id}, {cron_expr}"


async def remove_job(job_id: str) -> str:
    if HAS_APSCHEDULER:
        scheduler = get_scheduler()
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Job removed: {job_id}")
            return "job removed"
        except Exception:
            logger.warning(f"Job not found for removal: {job_id}")
            return "job not found"

    if _fallback_jobs.pop(job_id, None) is not None:
        logger.info(f"Fallback job removed: {job_id}")
        return "job removed"
    logger.warning(f"Fallback job not found for removal: {job_id}")
    return "job not found"


async def enable_job(job_id: str, active: bool) -> bool:
    if HAS_APSCHEDULER:
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

    job = _fallback_jobs.get(job_id)
    if not job:
        logger.error(f"Fallback job not found: {job_id}")
        return False
    job["active"] = active
    logger.info(f"Fallback job {job_id} {'resumed' if active else 'paused'}")
    return True


async def get_job_status(job_id: str) -> bool:
    if HAS_APSCHEDULER:
        scheduler = get_scheduler()
        job = scheduler.get_job(job_id)
        if job is None:
            return False
        return job.next_run_time is not None

    job = _fallback_jobs.get(job_id)
    return bool(job and job.get("active"))


async def list_jobs() -> list[str]:
    if HAS_APSCHEDULER:
        scheduler = get_scheduler()
        return [str(job) for job in scheduler.get_jobs()]

    return [f"{k}:active={v.get('active')}" for k, v in _fallback_jobs.items()]


async def validate_cron_string(expr: str) -> bool:
    try:
        if HAS_APSCHEDULER:
            assert CronTrigger is not None
            CronTrigger.from_crontab(expr)
        else:
            _parse_cron(expr)
        return True
    except Exception:
        return False
