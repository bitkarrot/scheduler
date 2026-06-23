import logging
from datetime import datetime

import httpx

from .crud import create_log_entry, get_scheduler_job
from .models import LogEntry

logger = logging.getLogger("scheduler")


async def execute_job(job_id: str) -> None:
    """Called directly by APScheduler — no subprocess, no cold start."""
    job = await get_scheduler_job(job_id)
    if not job:
        logger.error(f"Job not found at execution time: {job_id}")
        return

    try:
        # Prepare headers
        headers_dict = {}
        if job.headers:
            for h in job.headers:
                headers_dict[h.key] = h.value

        # Prepare body
        body_data = None
        if job.body:
            try:
                import json
                body_data = json.loads(job.body) if job.body else None
            except json.JSONDecodeError:
                logger.warning(f"Job {job_id}: body is not valid JSON, sending as-is")
                body_data = job.body

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=job.selectedverb,
                url=job.url,
                headers=headers_dict,
                json=body_data if body_data else None,
            )
        
        log_entry = LogEntry(
            id="",  # Will be generated in create_log_entry
            job_id=job_id,
            status=str(response.status_code),
            response=response.text[:4000],
            timestamp=datetime.utcnow(),
        )
        await create_log_entry(log_entry)
        logger.info(f"Job {job_id} executed: HTTP {response.status_code}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e!s}")
        log_entry = LogEntry(
            id="",  # Will be generated in create_log_entry
            job_id=job_id,
            status="0",
            response=str(e)[:4000],
            timestamp=datetime.utcnow(),
        )
        await create_log_entry(log_entry)
