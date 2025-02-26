import json
from typing import Optional
from uuid import uuid4
import sys
import os
from datetime import datetime
from lnbits.settings import settings
from lnbits.db import Database, Filters, Page
from .logger import logger
from .models import CreateJobData, HeaderItems, Job, JobFilters, LogEntry
from .cron_handler import CronHandler

db = Database("ext_scheduler")

# Get the absolute paths
dir_path = os.path.dirname(os.path.realpath(__file__))
root_path = os.path.dirname(os.path.dirname(dir_path))
poetry_env = os.path.join(root_path, ".venv")
python_path = os.path.join(poetry_env, "bin", "python") if os.path.exists(poetry_env) else sys.executable
command = f"{python_path} {os.path.join(dir_path, 'run_cron_job.py')}"

logger.info(f"Using Python interpreter: {python_path}")
logger.info(f"Using command: {command}")


def get_safe_path():
    """Get PATH from virtualenv or fall back to standard path"""
    standard_path = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    if poetry_env and os.path.exists(poetry_env):
        bin_dir = os.path.join(poetry_env, "bin")
        if os.path.exists(bin_dir):
            return f"{bin_dir}:{standard_path}"
    return standard_path


async def create_scheduler_jobs(admin_id: str, data: CreateJobData) -> Job:
    try:
        # Generate unique ID
        job_id = uuid4().hex

        # Validate cron schedule
        ch = CronHandler()
        is_valid = await ch.validate_cron_string(data.schedule)
        if not is_valid:
            raise ValueError(f"Invalid cron schedule format: {data.schedule}")

        # Set up environment variables for the cron job
        base_url = f"http://{settings.host}:{settings.port}"
        env_vars = {
            "ID": job_id,
            "adminkey": admin_id,
            "BASE_URL": base_url,
            "PYTHONPATH": root_path,  # Ensure Python can find the LNbits package
            "PATH": get_safe_path(),
            "VIRTUAL_ENV": poetry_env if os.path.exists(poetry_env) else "",
        }

        logger.info(f"Creating cron job with command: {command}")
        logger.info(f"Environment variables: {env_vars}")

        # Create the cron job first
        response = await ch.new_job(command=command, frequency=data.schedule, comment=job_id, env=env_vars)
        if isinstance(response, str) and response.startswith("Error"):
            raise ValueError(f"Failed to create cron job: {response}")

        # Set initial state (disabled by default)
        await ch.enable_job_by_comment(comment=job_id, active=False)

        # Prepare database data
        headers_json = json.dumps([h.dict() for h in data.headers]) if data.headers else "[]"
        extra_json = json.dumps(data.extra) if data.extra else "{}"

        # Create database entry
        job = Job(
            id=job_id,
            name=data.name or f"Job-{job_id}",
            admin=admin_id,
            status=False,  # Start disabled
            schedule=data.schedule,
            selectedverb=data.selectedverb,
            url=data.url,
            headers=[HeaderItems(**h) for h in json.loads(headers_json)] if headers_json != "[]" else None,
            body=data.body or "{}",
            extra=json.loads(extra_json) if extra_json != "{}" else None
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
                "extra": extra_json
            }
        )

        logger.info('Scheduler job created: %s', job)
        return job

    except Exception as e:
        # If anything fails, clean up any partially created resources
        try:
            await ch.remove_by_comment(job_id)
        except:
            pass
        logger.error('Failed to create scheduler job: %s', str(e))
        raise ValueError(f"Failed to create scheduler job: {str(e)}")


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

    # Verify actual crontab status
    ch = CronHandler()
    actual_status = await ch.get_job_status(job_id)

    # If database and crontab status don't match, update database
    if actual_status != row.status:
        logger.warning(f"Job {job_id} status mismatch: db={row.status}, crontab={actual_status}. Fixing...")
        await db.execute(
            """
            UPDATE scheduler.jobs SET status = :status WHERE id = :id
            """,
            {
                "id": job_id,
                "status": actual_status
            }
        )

    return Job(
        id=row.id,
        name=row.name,
        admin=row.admin,
        status=actual_status,  # Use actual status from crontab
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
        # Remove from crontab first
        ch = CronHandler()
        await ch.remove_job(job_id)

        # Then remove from database
        await db.execute("DELETE FROM scheduler.jobs WHERE id = :id", {"id": job_id})

        # Also clean up any log entries
        await delete_log_entries(job_id)

        logger.info(f"Deleted scheduler job and associated logs: {job_id}")
    except Exception as e:
        logger.error(f"Error deleting scheduler job {job_id}: {str(e)}")
        raise ValueError(f"Failed to delete scheduler job: {str(e)}")


async def update_scheduler_job(job: Job) -> Job:
    try:
        # Convert headers and extra to JSON strings
        headers_json = (
            json.dumps([h.dict() if hasattr(h, "dict") else h for h in job.headers])
            if job.headers
            else "[]"
        )
        extra_json = json.dumps(job.extra) if job.extra else "{}"

        # Update crontab first
        ch = CronHandler()

        # Update the command and schedule
        base_url = f"http://{settings.host}:{settings.port}"
        env_vars = {
            "ID": job.id,
            "adminkey": job.admin,
            "BASE_URL": base_url,
            "PYTHONPATH": root_path,  # Ensure Python can find the LNbits package
            "PATH": get_safe_path(),
            "VIRTUAL_ENV": poetry_env if os.path.exists(poetry_env) else "",
        }

        # Update the job in crontab
        await ch.edit_job(command=command, frequency=job.schedule, comment=job.id, env=env_vars)

        # Update the job's enabled state
        await ch.enable_job_by_comment(comment=job.id, active=job.status)

        # Then update database
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
            }
        )

        logger.info('Updated scheduler job: %s', job.id)
        return await get_scheduler_job(job.id)

    except Exception as e:
        logger.error('Failed to update scheduler job: %s', str(e))
        raise ValueError(f"Failed to update job: {str(e)}")


async def pause_scheduler(job_id: str, active: bool = None) -> Job:
    """
    Update the status of a job.
    
    Args:
        job_id: ID of the job to update
        active: If True, activate the job; if False, deactivate it; if None, toggle the current state
        
    Returns:
        The updated job object or None if the job was not found or an error occurred
    """
    try:
        # Get current job state
        job = await get_scheduler_job(job_id)
        logger.info(f"Pausing job {job_id}, current status: {getattr(job, 'status', 'N/A')}, setting to: {active}")
        
        if not job:
            logger.error(f"Job not found: {job_id}")
            return None

        # Use provided active state or toggle current state if not provided
        new_status = active if active is not None else not job.status
        logger.info(f"New status will be: {new_status}")

        # Try crontab update but don't rely on it for database update
        try:
            ch = CronHandler()
            crontab_job = await ch.find_comment(job_id)
            if crontab_job:
                logger.info(f"Found job in crontab, updating status to {new_status}")
                await ch.enable_job_by_comment(comment=job_id, active=new_status)
            else:
                logger.warning(f"Job {job_id} not found in crontab, only updating database")
        except Exception as e:
            logger.error(f"Error updating crontab: {str(e)}")
            logger.info("Will continue with database update only")

        # Update database directly with the new status
        logger.info(f"Setting database status for job {job_id} to {new_status}")
        await db.execute(
            """
            UPDATE scheduler.jobs SET status = :status WHERE id = :id
            """,
            {
                "id": job_id,
                "status": new_status
            }
        )

        # Get and return updated job
        updated_job = await get_scheduler_job(job_id)
        if updated_job:
            logger.info(f"Job {job_id} status successfully changed to: {updated_job.status}")
            return updated_job
        else:
            logger.error(f"Failed to retrieve updated job after status change: {job_id}")
            return None

    except Exception as e:
        logger.error(f"Exception in pause_scheduler: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return None instead of raising an exception to let the caller handle it
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
