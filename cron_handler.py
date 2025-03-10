import getpass
import logging
from typing import Union

from crontab import CronSlices, CronTab

logger = logging.getLogger("scheduler")

"""
CronHandler class contains methods for handling cron jobs, create, edit, delete

see originaldocs for python-crontab package
https://pypi.org/project/python-crontab/
"""


class CronHandler:
    def __init__(self, user: Union[str, bool] = None):
        """Initialize CronHandler"""
        try:
            self._username = getpass.getuser()
            # Initialize crontab with current user
            self._cron = CronTab(user=self._username)
            logger.info(f"CronHandler initialized for user: {self._username}")
        except Exception as e:
            logger.error(f"Failed to initialize CronTab: {e!s}")
            raise

    def get_cron(self):
        return self._cron

    def set_cron(self, cron):
        self._cron = cron

    def get_user(self):
        return self._username

    def set_user(self, user):
        self._username = user

    async def list_jobs(self) -> list:
        jobs = []
        for job in self._cron:
            jobs.append(str(job))
        return jobs

    async def pretty_print_jobs(self) -> None:
        print("==== Cron Jobs List: ====")
        jobs = await self.list_jobs()
        for i in jobs:
            print(i)

    async def new_job(self, command: str, frequency: str, comment: str, env: dict):
        logger.info("Creating new cron job:")
        logger.info(f"Command: {command!r}")
        logger.info(f"Frequency: {frequency!r}")
        logger.info(f"Comment: {comment!r}")
        logger.info(f"Environment: {env}")

        try:
            # Create the job with command and comment
            job = self._cron.new(command=command, comment=comment)

            # Set environment variables
            if env:
                for key, value in env.items():
                    if " " in str(value):
                        value = f'"{value}"'
                    job.env[key] = value

            # Set the schedule
            job.setall(frequency)

            # Validate and log the job details
            logger.info(f"Job valid: {job.is_valid()}")
            logger.info(f"Job slices: {job.slices}")
            logger.info(f"Job render: {job.render()}")

            if not job.is_valid():
                logger.error(f"Invalid job: frequency={frequency!r}")
                return f"Error creating job: Invalid frequency {frequency}"

            # Write to crontab
            try:
                # Log the full crontab content before writing
                logger.info("Current crontab content:")
                for existing_job in self._cron:
                    logger.info(f"Existing job: {existing_job}")
                logger.info("Environment variables:")
                for key, value in self._cron.env.items():
                    logger.info(f"{key}={value}")

                self._cron.write()

                # Log the crontab content after writing
                logger.info("Crontab content after write:")
                logger.info(self._cron.render())
                return f"job created: {command}, {self._username}, {frequency}"
            except Exception as e:
                logger.error(f"Failed to write to crontab: {e!s}")
                return f"Error writing to crontab: {e!s}"
        except Exception as e:
            logger.error(f"Error in new_job: {e!s}")
            return f"Error creating job: {e!s}"

    async def edit_job(
        self, command: str, frequency: str, comment: str, env: dict = None
    ):
        try:
            job = await self.find_comment(comment)
            if job is not None:
                job.clear()  # Clear existing schedule
                job.setall(frequency)  # Set new schedule
                job.set_command(command)  # Update command

                # Update environment variables
                if env:
                    for key, value in env.items():
                        if " " in str(value):
                            value = f'"{value}"'
                        job.env[key] = value

                self._cron.write()
                return f"job edited: {command}, {self._username}, {frequency}"
            return "job not found"
        except Exception as e:
            logger.error(f"Failed to edit job: {e!s}")
            return f"Error editing job: {e!s}"

    async def enable_job_by_comment(self, comment: str, active: bool):
        """
        Enable or disable a job by its comment.

        Args:
            comment: The comment of the job to enable/disable
            active: True to enable, False to disable

        Returns:
            True if the job was found and enabled/disabled successfully, False otherwise
        """
        try:
            logger.info(
                f"Enabling/disabling cron job by comment: comment={comment}, active={active}"
            )

            # Find the job by comment
            jobs = list(self._cron.find_comment(comment))
            job_count = len(jobs)
            logger.info(f"Found {job_count} jobs with comment {comment}")

            if job_count == 0:
                logger.error(f"No jobs found with comment: {comment}")
                return False

            # Get the first job (should only be one since comments are unique)
            job = jobs[0]
            current_status = job.is_enabled()
            logger.info(
                f"Job found, current enabled status: {current_status}, changing to: {active}"
            )

            # Only update if the status is different
            if current_status == active:
                logger.info("Job already in the requested state, no change needed")
                return active

            # Update job status
            job.enable(active)

            # Write changes to crontab
            try:
                self._cron.write()
                logger.info("Crontab updated successfully")
            except Exception as write_error:
                logger.error(f"Failed to write to crontab: {write_error!s}")
                return False

            # Verify the status was updated
            new_status = job.is_enabled()
            logger.info(f"Job status after update: {new_status}")

            if new_status != active:
                logger.error(
                    f"Job status was not updated correctly. Expected: {active}, Got: {new_status}"
                )
                return False

            return new_status

        except Exception as e:
            logger.error(
                f"Exception in enable_job_by_comment: {type(e).__name__}: {e!s}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def get_job_status(self, job_id: str) -> bool:
        logger.info(f"Getting cron job status by ID: job_id={job_id}")
        jobs = self._cron.find_comment(job_id)
        for job in jobs:
            return job.is_enabled()
        return False

    async def find_comment(self, comment: str):
        """Find a job by its comment"""
        jobs = self._cron.find_comment(comment)
        for job in jobs:  # Should only be one since comments are unique
            return job
        return None

    async def remove_job(self, comment: str):
        """Remove a job by its comment"""
        logger.info(f"Removing cron job by comment: comment={comment}")
        job = await self.find_comment(comment)
        if job is not None:
            self._cron.remove(job)
            self._cron.write()
            return "job removed"
        return "job not found"

    async def clear_all_jobs(self):
        logger.info("Clearing all cron jobs")
        self._cron.remove_all()
        self._cron.write()

    async def remove_by_comment(self, comment):
        logger.info(f"Removing cron job by comment: comment={comment}")
        self._cron.remove_all(comment=comment)
        self._cron.write()

    async def remove_by_time(self, time):
        logger.info(f"Removing cron job by time: time={time}")
        self._cron.remove_all(time=time)
        self._cron.write()

    async def validate_cron_string(self, timestring: str) -> bool:
        """Validate cron string format"""
        logger.info(f"Validating cron string: {timestring!r}")
        try:
            is_valid = CronSlices.is_valid(timestring)
            logger.info(f"CronSlices validation result: {is_valid}")
            return is_valid
        except Exception as e:
            logger.error(f"Invalid cron string: {timestring!r}, error: {e!s}")
            return False

    async def normalize_cron_string(self, timestring: str) -> str:
        """Convert cron string to standard format"""
        try:
            entry = CronTab(timestring)
            return str(entry)
        except Exception:
            return timestring
