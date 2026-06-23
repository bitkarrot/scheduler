import pytest

from scheduler_handler import add_job, get_job_status, remove_job, start_scheduler, stop_scheduler


async def _noop(job_id: str) -> None:
    return None


@pytest.mark.asyncio
async def test_scheduler_handler_add_get_remove_job():
    await start_scheduler()

    job_id = "test_scheduler_handler_add_get_remove_job"
    await add_job(job_id=job_id, cron_expr="*/5 * * * *", func=_noop, args=[job_id])

    assert await get_job_status(job_id) is True

    result = await remove_job(job_id)
    assert result == "job removed"

    assert await get_job_status(job_id) is False

    await stop_scheduler()
