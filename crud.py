import json
from typing import Optional
from uuid import uuid4

from lnbits.db import Database, Filters, Page

from .logger import logger
from .models import CreateJobData, HeaderItems, Job, JobFilters, LogEntry
from .scheduler_handler import add_job, remove_job, validate_cron_string

db = Database("ext_scheduler")


async def create_scheduler_jobs(admin_id: str, data: CreateJobData) -> Job:
    try:
        # Generate unique ID
        job_id = uuid4().hex

        # Validate cron schedule
        is_valid = await validate_cron_string(data.schedule)
        if not is_valid:
            raise ValueError(f"Invalid cron schedule format: {data.schedule}")

        # Prepare database data
        headers_json = (
            json.dumps([h.dict() for h in data.headers]) if data.headers else "[]"
        )
        extra_json = json.dumps(data.extra) if data.extra else "{}"

        # Create database entry
        job = Job(
            id=job_id,
            name=data.name or f"Job-{job_id}",
            admin=admin_id,
            status=data.status,  # Use the status from the input
            schedule=data.schedule,
            selectedverb=data.selectedverb,
            url=data.url,
            headers=[HeaderItems(**h) for h in json.loads(headers_json)]
            if headers_json != "[]"
            else None,
            body=data.body or "{}",
            extra=json.loads(extra_json) if extra_json != "{}" else None,
        )

        await db.execute(
            """
            INSERT INTO scheduler.jobs (
                id, name, admin, status, schedule, selectedverb, url, headers, body, extra
            ) VALUES (
                :id, :name, :admin, :status, :schedule, :selectedverb,
                :url, :headers, :body, :extra
            )
            """,
            {
                "id": job.id,
                "name": job.name,
                "admin": job.admin,
                "status": job.status,
                "schedule": job.schedule,
                "selectedverb": job.selectedverb,
                "url": job.url,
                "headers": headers_json,
                "body": job.body,
                "extra": extra_json,
            },
        )

        # Add to APScheduler if status is running (True)
        if job.status:
            from .job_runner import execute_job

            await add_job(
                job_id=job.id,
                cron_expr=job.schedule,
                func=execute_job,
                args=[job.id],
            )

        logger.info("Scheduler job created: %s", job)
        return job

    except Exception as e:
        logger.error("Failed to create scheduler job: %s", str(e))
        raise ValueError(f"Failed to create scheduler job: {e!s}")


async def get_scheduler_job(job_id: str) -> Optional[Job]:
    row = await db.fetchone(
        "SELECT * FROM scheduler.jobs WHERE id = :id",
        {"id": job_id},
    )
    if not row:
        return None

    # Parse JSON strings back to Python objects
    headers = [HeaderItems(**h) for h in json.loads(row.headers)] if row.headers else []
    extra = json.loads(row.extra) if row.extra else {}

    return Job(
        id=row.id,
        name=row.name,
        admin=row.admin,
        status=row.status,
        schedule=row.schedule,
        selectedverb=row.selectedverb,
        url=row.url,
        headers=headers,
        body=row.body,
        extra=extra,
    )


async def get_scheduler_jobs(admin: str, filters: Filters[JobFilters]) -> Page[Job]:
    rows = await db.fetch_page(
        "SELECT * FROM scheduler.jobs",
        ["admin = :admin"],
        {"admin": admin},
        filters,
    )

    jobs = []
    for row in rows.data:
        # Parse JSON strings back to Python objects
        headers = (
            [HeaderItems(**h) for h in json.loads(row.headers)] if row.headers else []
        )
        extra = json.loads(row.extra) if row.extra else {}

        jobs.append(
            Job(
                id=row.id,
                name=row.name,
                admin=row.admin,
                status=row.status,
                schedule=row.schedule,
                selectedverb=row.selectedverb,
                url=row.url,
                headers=headers,
                body=row.body,
                extra=extra,
            )
        )

    return Page(data=jobs, total=rows.total)


async def delete_scheduler_jobs(job_id: str) -> None:
    try:
        # Remove from APScheduler
        await remove_job(job_id)

        # Then remove from database
        await db.execute("DELETE FROM scheduler.jobs WHERE id = :id", {"id": job_id})

        # Also clean up any log entries
        await delete_log_entries(job_id)

        logger.info(f"Deleted scheduler job and associated logs: {job_id}")
    except Exception as e:
        logger.error(f"Error deleting scheduler job {job_id}: {e!s}")
        raise ValueError(f"Failed to delete scheduler job: {e!s}")


async def update_scheduler_job(job: Job) -> Job:
    try:
        # Convert headers and extra to JSON strings
        headers_json = (
            json.dumps([h.dict() if hasattr(h, "dict") else h for h in job.headers])
            if job.headers
            else "[]"
        )
        extra_json = json.dumps(job.extra) if job.extra else "{}"

        # Update database
        await db.execute(
            """
            UPDATE scheduler.jobs SET
                name = :name,
                status = :status,
                schedule = :schedule,
                selectedverb = :selectedverb,
                url = :url,
                headers = :headers,
                body = :body,
                extra = :extra
            WHERE id = :id
            """,
            {
                "id": job.id,
                "name": job.name,
                "status": job.status,
                "schedule": job.schedule,
                "selectedverb": job.selectedverb,
                "url": job.url,
                "headers": headers_json,
                "body": job.body,
                "extra": extra_json,
            },
        )

        # Update APScheduler
        from .job_runner import execute_job

        if job.status:
            # Job should be running - add or update it
            await add_job(
                job_id=job.id,
                cron_expr=job.schedule,
                func=execute_job,
                args=[job.id],
            )
        else:
            # Job should be stopped - remove it from scheduler
            await remove_job(job.id)

        logger.info("Updated scheduler job: %s", job.id)
        return await get_scheduler_job(job.id)

    except Exception as e:
        logger.error("Failed to update scheduler job: %s", str(e))
        raise ValueError(f"Failed to update job: {e!s}")


async def pause_scheduler(job_id: str, active: Optional[bool] = None) -> Optional[Job]:
    """Update a job status and keep APScheduler runtime in sync with DB."""
    try:
        job = await get_scheduler_job(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return None

        new_status = active if active is not None else not job.status

        # Keep runtime scheduler state aligned with desired status.
        if new_status:
            from .job_runner import execute_job

            await add_job(
                job_id=job.id,
                cron_expr=job.schedule,
                func=execute_job,
                args=[job.id],
            )
        else:
            await remove_job(job.id)

        # DB is source of truth
        await db.execute(
            "UPDATE scheduler.jobs SET status = :status WHERE id = :id",
            {"id": job_id, "status": new_status},
        )

        return await get_scheduler_job(job_id)

    except Exception as e:
        logger.error(f"Exception in pause_scheduler: {type(e).__name__}: {e!s}")
        return None


async def create_log_entry(data: LogEntry) -> LogEntry:
    """
    create log entry in database
    """
    entry = LogEntry(
        id=uuid4().hex,
        job_id=data.job_id,
        status=data.status,
        response=data.response,
    )
    await db.insert("scheduler.logs", entry)
    return entry


async def get_log_entry(log_id: str) -> LogEntry:
    """
    get a single log entry based on primary key Unique ID
    """
    return await db.fetchone(
        "SELECT * FROM scheduler.logs WHERE id = :id",
        {"id": log_id},
        LogEntry,
    )


async def get_log_entries(job_id: str) -> str:
    """
    get all log entries from data base for particular job
    """
    log_entries = await db.fetchall(
        "SELECT * FROM scheduler.logs WHERE job_id = :id",
        {"id": job_id},
        LogEntry,
    )
    all_entries = ""
    for entry in log_entries:
        all_entries += (
            f"[{entry.timestamp}]: JobID: {entry.job_id} "
            f"Status: {entry.status} Response: {entry.response}\n\n"
        )
    return all_entries


async def delete_log_entries(job_id: str) -> None:
    """
    delete all log entries from data base for particular job
    """
    await db.execute("DELETE FROM scheduler.logs WHERE job_id = :id", {"id": job_id})


async def get_all_active_scheduler_jobs() -> list[Job]:
    """
    Get all jobs with status=True (running) for scheduler initialization.
    """
    rows = await db.fetchall(
        "SELECT * FROM scheduler.jobs WHERE status = :status",
        {"status": True},
    )

    jobs = []
    for row in rows:
        # Parse JSON strings back to Python objects
        headers = (
            [HeaderItems(**h) for h in json.loads(row.headers)] if row.headers else []
        )
        extra = json.loads(row.extra) if row.extra else {}

        jobs.append(
            Job(
                id=row.id,
                name=row.name,
                admin=row.admin,
                status=row.status,
                schedule=row.schedule,
                selectedverb=row.selectedverb,
                url=row.url,
                headers=headers,
                body=row.body,
                extra=extra,
            )
        )

    return jobs
