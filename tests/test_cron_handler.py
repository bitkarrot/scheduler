import asyncio
import datetime as dt
import sys

sys.path.insert(0, "..")

import os

from ..cron_handler import CronHandler
from ..utils import get_env_data_as_dict

## TODO make this a legit pytest


async def main():
    _vars = get_env_data_as_dict("../.env")
    print(_vars)
    username = True  # vars['SCHEDULER_USER']
    print(f"Scheduler Username: {username}")

    print("testing CronHandler")
    env_vars = {"SHELL": "/usr/bin/bash", "API_URL": "http://localhost:8000"}
    id_vars = {"ID": "23487923847298347928987"}
    id_vars_2 = {"ID": "adf098werlkj987"}

    # unique job id number to be placed in comment
    comment = "cron python script"
    # echo_comment = "cron now echo"

    now = dt.datetime.now()
    print(f"current datetime: {now}")

    ch = CronHandler(user=username)

    # regular cron job with comment
    response = await ch.new_job("ls", "15 * * * *", comment=comment, env={})
    print(response)

    # regular cron job with log handler
    py_path = sys.executable
    dir_path = os.path.dirname(os.path.realpath(__name__))
    command = py_path + f" {dir_path}/cron-job.py"

    response = await ch.new_job(
        command, "* * * * *", comment=id_vars["ID"], env=id_vars
    )
    print(response)

    # cron job with env vars with errors redirected to text file
    pypath = "/Users/bitcarrot/.pyenv/shims/python3"
    response = await ch.new_job(
        f"{pypath} {dir_path}/../log_handler.py >> /tmp/output.txt 2>&1",
        "* * * * *",
        comment=id_vars_2["ID"],
        env=id_vars_2,
    )
    print(response)

    # enable job
    print("Enable Job by Comment")
    enable_status = await ch.enable_job_by_comment(comment=comment, active=True)
    print(f"enabled status: {enable_status}")

    # disable job
    print("Disable Job by Comment")
    disable_status = await ch.enable_job_by_comment(comment=comment, active=False)
    print(f"enabled status: {disable_status}")

    # job status
    jobid = id_vars["ID"]
    status = await ch.get_job_status(jobid)
    print(f"ID: {jobid}, Job Status: {status}")

    # pretty print jobs
    print("\npretty print jobs")
    await ch.pretty_print_jobs()

    # edit job - make this a method
    await ch.edit_job("ls", "*/8 * * * *", comment=comment)

    # validate cron string is valid
    cron_string = "10 * * * *"
    is_valid = await ch.validate_cron_string(cron_string)
    print(f"cron string {cron_string} is valid: {is_valid}")

    # validate cron string is valid
    cron_string = "hourly"
    is_valid = await ch.validate_cron_string(cron_string)
    print(f"cron string {cron_string} is valid: {is_valid}")

    # validate cron string is valid
    cron_string = "@reboot"
    is_valid = await ch.validate_cron_string(cron_string)
    print(f"cron string {cron_string} is valid: {is_valid}")

    # set global env vars
    print("set global env vars")
    await ch.set_global_env_vars(env_vars)

    # print environment variables
    print("get env vars")
    output = await ch.get_global_env_vars()
    print(output)

    print("clear global env vars")
    output = await ch.clear_global_env_vars()
    print(output)

    # remove all jobs
    await ch.clear_all_jobs()


if __name__ == "__main__":
    asyncio.run(main())
