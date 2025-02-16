import json
import os
import sys

from lnbits.settings import settings

from .cron_handler import CronHandler
from .models import Job

# TODO: use `settings.lnbits_extensions_path`

# python path
py_path = sys.executable
dir_path = os.path.dirname(os.path.realpath(__name__))
command = py_path + f" {dir_path}/lnbits/extensions/scheduler/run_cron_job.py"

# .log path
log_path = f"{dir_path}/lnbits/extensions/scheduler/scheduler.log"


async def convert_headers(headers: list) -> str:
    # print(f'header list length: "{len(headers)}')
    allitems_as_dicts = [item.to_dict() for item in headers]
    headers_string = json.dumps(allitems_as_dicts)
    # print(f'headers as json string: {headers_string}')
    return headers_string


async def create_scheduler_jobs(link_id: str, admin_id: str, schedule: str):
    base_url = f"http://{settings.host}:{settings.port}"
    env_vars = {"ID": link_id, "adminkey": admin_id, "BASE_URL": base_url}

    ch = CronHandler()
    is_valid = await ch.validate_cron_string(schedule)
    if not is_valid:
        assert is_valid, "Invalid cron schedule, please check the format."
        return f"Error in cron string syntax {schedule}"
    response = await create_cron(link_id, command, schedule, env_vars)

    if response.startswith("Error"):
        assert response.startswith("Error"), "Error creating Cron job"
        return f"Error creating cron job: {response}"


# crontab-specific methods, direct to system cron
async def create_cron(comment: str, command: str, schedule: str, env_vars: dict):
    try:
        ch = CronHandler()
        response = await ch.new_job(command, schedule, comment=comment, env=env_vars)
        # make sure job is not running on creation by default
        status = await ch.enable_job_by_comment(comment=comment, active=False)
        # print(f'create_cron: {response}, {status}')
        if status is False:
            return response
        else:  # error setting job to 'Not Running' and creating job
            raise ValueError(
                f"Error setting job to 'Not Running' and creating job: {response}"
            )
    except Exception as exc:
        return f"Error creating cron job: {exc!s}"


async def update_cron(job: Job):
    # check to make sure DB was updated
    # write update to cron tab
    ch = CronHandler()
    await ch.enable_job_by_comment(comment=job.id, active=job.status)
    await ch.edit_job(command, job.schedule, comment=job.id)


async def delete_cron(link_id: str):
    # the comment in actual crontab is the job ID in LNBits
    try:
        ch = CronHandler()
        response = await ch.remove_by_comment(link_id)
        return response
    except Exception as e:
        return f"Error deleting job: {e}"


async def pause_scheduler(job_id: str):
    # print(f'Pausing job in pause_scheduler: {job_id}, State: {state}')
    ch = CronHandler()
    await ch.enable_job_by_comment(comment=job_id, active=False)


# log helpers
async def read_last_n_lines(file_path, n):
    with open(file_path) as file:
        lines = file.readlines()[-n:]
    return lines


async def get_complete_log() -> str:
    """
    return entire text log from disk, including other errors
    for now, only fetch the last 1000 lines,
    so that response does not get too large
    """
    if os.path.exists(log_path):
        content = ""
        last_1000_lines = await read_last_n_lines(log_path, 1000)
        for line in last_1000_lines:
            content += line
        return content
    else:
        return f"log file does not exist at location: {log_path}"


async def delete_complete_log() -> bool:
    """
    clear the contents of the text log on disk
    """
    # Check if the file exists before trying to delete it
    if os.path.exists(log_path):
        os.remove(log_path)
        return True
    else:
        return False
