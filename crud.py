import json
from typing import Optional
from uuid import uuid4

from lnbits.db import Database, Filters, Page

from .logger import logger
from .models import CreateJobData, Job, JobFilters, LogEntry

db = Database("ext_scheduler")


async def create_scheduler_jobs(admin_id: str, data: CreateJobData) -> Job:
    # Convert headers to JSON string if present
    headers_json = (
        json.dumps([h.dict() for h in data.headers]) if data.headers else "[]"
    )
    # Convert extra to JSON string if present
    extra_json = json.dumps(data.extra) if data.extra else "{}"

    job = Job(
        id=uuid4().hex,
        name=data.name or f"Job-{uuid4().hex}",
        admin=admin_id,
        status=data.status,
        schedule=data.schedule,
        selectedverb=data.selectedverb,
        url=data.url,
        headers=headers_json,  # Store as JSON string
        body=data.body or "{}",
        extra=extra_json,  # Store as JSON string
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

    logger.info(f"Scheduler job created: {job.id}")
    return job


async def get_scheduler_job(job_id: str) -> Optional[Job]:
    row = await db.fetchone(
        "SELECT * FROM scheduler.jobs WHERE id = :id",
        {"id": job_id},
    )
    if not row:
        return None

    # Parse JSON strings back to Python objects
    headers = json.loads(row.headers) if row.headers else []
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
        headers = json.loads(row.headers) if row.headers else []
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
    await db.execute("DELETE FROM scheduler.jobs WHERE id = :id", {"id": job_id})
    logger.info(f"Deleted scheduler job: {job_id}")


async def update_scheduler_job(job: Job) -> Job:
    # Convert headers and extra to JSON strings
    headers_json = json.dumps([h.dict() for h in job.headers]) if job.headers else "[]"
    extra_json = json.dumps(job.extra) if job.extra else "{}"

    await db.execute(
        """
        UPDATE scheduler.jobs
        SET name = :name,
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
            "body": job.body or "{}",
            "extra": extra_json,
        },
    )
    return job


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
