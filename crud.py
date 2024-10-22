from typing import Optional
from uuid import uuid4

from lnbits.db import Database, Filters, Page

from .logger import logger
from .models import CreateJobData, Job, JobFilters, LogEntry

db = Database("ext_scheduler")


async def create_scheduler_jobs(admin_id: str, data: CreateJobData) -> Job:

    job = Job(
        id=uuid4().hex,
        name=data.name or f"Job-{uuid4().hex}",
        admin=admin_id,
        status=data.status,
        schedule=data.schedule,
        selectedverb=data.selectedverb,
        url=data.url,
        headers=data.headers,
        body=data.body,
        extra=data.extra,
    )
    await db.update("scheduler.jobs", job)
    logger.info(f"Scheduler job created: {job.id}")
    return job


async def get_scheduler_job(job_id: str) -> Optional[Job]:
    return await db.fetchone(
        "SELECT * FROM scheduler.jobs WHERE id = :id",
        {"id": job_id},
        Job,
    )


async def get_scheduler_jobs(admin: str, filters: Filters[JobFilters]) -> Page[Job]:
    # check that job id match crontab list
    return await db.fetch_page(
        "SELECT * FROM scheduler.jobs",
        ["admin = :admin"],
        {"admin": admin},
        filters,
        Job,
    )


async def delete_scheduler_jobs(job_id: str) -> None:
    await db.execute("DELETE FROM scheduler.jobs WHERE id = :id", {"id": job_id})
    logger.info(f"Deleted scheduler job: {job_id}")


async def update_scheduler_job(job: Job) -> Job:
    await db.update("scheduler.jobs", job)
    # TODO UPDATE CRON
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
