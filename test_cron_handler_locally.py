#!/usr/bin/env python3
import asyncio
import logging
from cron_handler import CronHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cron_handler():
    try:
        # Initialize CronHandler
        ch = CronHandler()
        logger.info("CronHandler initialized")

        # Test creating a job
        env = {"LNBITS_PATH": "/path/to/lnbits"}
        result = await ch.new_job(
            command="echo 'test job'",
            frequency="*/5 * * * *",  # Every 5 minutes
            comment="test_job_1",
            env=env
        )
        logger.info(f"Create job result: {result}")

        # List all jobs
        jobs = await ch.list_jobs()
        logger.info("Current jobs:")
        for job in jobs:
            logger.info(job)

        # Test editing the job
        edit_result = await ch.edit_job(
            command="echo 'edited test job'",
            frequency="*/10 * * * *",  # Every 10 minutes
            comment="test_job_1"
        )
        logger.info(f"Edit job result: {edit_result}")

        # List jobs after edit
        jobs = await ch.list_jobs()
        logger.info("Jobs after edit:")
        for job in jobs:
            logger.info(job)

        # Test enabling/disabling job
        enable_result = await ch.enable_job_by_comment("test_job_1", False)
        logger.info(f"Disable job result: {enable_result}")

        # Check job status
        status = await ch.get_job_status("test_job_1")
        logger.info(f"Job status after disable: {status}")

        # Re-enable job
        enable_result = await ch.enable_job_by_comment("test_job_1", True)
        logger.info(f"Re-enable job result: {enable_result}")

        # Test removing the job
        remove_result = await ch.remove_job("test_job_1")
        logger.info(f"Remove job result: {remove_result}")

        # Final job list
        jobs = await ch.list_jobs()
        logger.info("Final job list:")
        for job in jobs:
            logger.info(job)

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_cron_handler())
