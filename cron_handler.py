from typing import Union
import logging
from crontab import CronSlices, CronTab

logger = logging.getLogger("scheduler")

"""
CronHandler class contains methods for handling cron jobs, create, edit, delete

see originaldocs for python-crontab package
https://pypi.org/project/python-crontab/
"""


class CronHandler:
    def __init__(self, user: Union[str, bool] = None):
        # Default to current user if none specified
        self._user = user if user is not None else True
        try:
            self._cron = CronTab(user=self._user)
            logger.info(f"CronHandler initialized with user: {self._user}")
        except Exception as e:
            logger.error(f"Failed to initialize CronTab: {str(e)}")
            raise

    def get_cron(self):
        return self._cron

    def set_cron(self, cron):
        self._cron = cron

    def get_user(self):
        return self._user

    def set_user(self, user):
        self._user = user

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
        logger.info(f"Creating new cron job: command={command}, frequency={frequency}, comment={comment}, env={env}")
        job = self._cron.new(command=command, comment=comment)
        if len(env) > 0:
            for key in env:
                job.env[key] = env[key]
        job.setall(frequency)
        if job.is_valid():
            logger.info("Job is valid, writing to crontab")
            try:
                self._cron.write_to_user(user=self._user)
                jobs = await self.list_jobs()
                logger.info(f"Current crontab jobs after write: {jobs}")
                return f"job created: {command}, {self._user}, {frequency}"
            except Exception as e:
                logger.error(f"Failed to write to crontab: {str(e)}")
                return f"Error writing to crontab: {str(e)}"
        else:
            logger.error(f"Invalid job: command={command}, frequency={frequency}")
            return f"Error creating job: {command}, {self._user}, {frequency}"

    # TODO: add means to edit env variables in the job
    async def edit_job(self, command: str, frequency: str, comment: str):
        logger.info(f"Editing existing cron job: command={command}, frequency={frequency}, comment={comment}")
        jobs = self._cron.find_comment(comment)
        for job in jobs:
            ## assume job comment ID is unique
            job.command = command
            job.setall(frequency)
            if job.is_valid():
                logger.info("Job is valid, writing to crontab")
                try:
                    self._cron.write_to_user(user=self._user)
                    jobs = await self.list_jobs()
                    logger.info(f"Current crontab jobs after write: {jobs}")
                    return f"job edited: {command}, {self._user}, {frequency}"
                except Exception as e:
                    logger.error(f"Failed to write to crontab: {str(e)}")
                    return f"Error writing to crontab: {str(e)}"
            else:
                logger.error(f"Invalid job: command={command}, frequency={frequency}")
                return f"Error editing job: {command}, {self._user}, {frequency}"

    async def enable_job_by_comment(self, comment: str, active: bool):
        logger.info(f"Enabling/disabling cron job by comment: comment={comment}, active={active}")
        jobs = self._cron.find_comment(comment)
        ## assume iter is only 1 long as using unique comment ID
        for job in jobs:
            job.enable(active)
            self._cron.write_to_user(user=self._user)
            return job.is_enabled()

    async def get_job_status(self, job_id: str) -> bool:
        logger.info(f"Getting cron job status by ID: job_id={job_id}")
        jobs = self._cron.find_comment(job_id)
        for job in jobs:
            return job.is_enabled()
        return False

    async def remove_job(self, command: str):
        logger.info(f"Removing cron job by command: command={command}")
        self._cron.remove_all(command=command)
        self._cron.write_to_user(user=self._user)

    async def clear_all_jobs(self):
        logger.info("Clearing all cron jobs")
        self._cron.remove_all()
        self._cron.write_to_user(user=self._user)

    async def remove_by_comment(self, comment):
        logger.info(f"Removing cron job by comment: comment={comment}")
        self._cron.remove_all(comment=comment)
        self._cron.write_to_user(user=self._user)

    async def remove_by_time(self, time):
        logger.info(f"Removing cron job by time: time={time}")
        self._cron.remove_all(time=time)
        self._cron.write_to_user(user=self._user)

    async def set_global_env_vars(self, env: dict):
        logger.info(f"Setting global environment variables: env={env}")
        if self._cron.env:
            for name, value in env.items():
                self._cron.env[name] = value
        self._cron.write_to_user(user=self._user)

    async def get_global_env_vars(self):
        logger.info("Getting global environment variables")
        output = ""
        if self._cron.env:
            for name, value in self._cron.env.items():
                output += f"name: {name}, value: {value}\n"
        return output

    async def clear_global_env_vars(self):
        logger.info("Clearing global environment variables")
        if self._cron.env:
            self._cron.env.clear()
        self._cron.write_to_user(user=self._user)

    async def validate_cron_string(self, timestring: str):
        logger.info(f"Validating cron string: timestring={timestring}")
        is_valid = CronSlices.is_valid(timestring)
        return is_valid
