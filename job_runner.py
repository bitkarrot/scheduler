import json
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

                body_data = json.loads(job.body)
            except json.JSONDecodeError:
                logger.warning(f"Job {job_id}: body is not valid JSON, sending as raw")
                body_data = job.body

        method = (job.selectedverb or "GET").upper()
        if not job.url:
            raise ValueError("Job URL is missing")
        request_kwargs = {
            "method": method,
            "url": job.url,
            "headers": headers_dict,
        }

        # Keep compatibility with legacy behavior:
        # - GET/DELETE: body treated as query params when JSON object
        # - POST/PUT/PATCH: body treated as JSON if parseable, raw content otherwise
        if method in {"GET", "DELETE"}:
            if isinstance(body_data, dict):
                request_kwargs["params"] = body_data
        else:
            if isinstance(body_data, (dict, list)):
                request_kwargs["json"] = body_data
            elif isinstance(body_data, str) and body_data.strip():
                request_kwargs["content"] = body_data

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(**request_kwargs)

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
