import json
from typing import Optional
from uuid import uuid4
import sys

from lnbits.db import POSTGRES, Filters

from . import db
from .models import (
    CreateJobData,
    UpdateJobData,
    Job,
    JobDetailed,
    JobFilters,
)

from .cron_handler import CronHandler
from .utils import get_env_data_as_dict
import os

# exception throw might need to be handled higher up in the stack 
cwd = os.getcwd()
vars = get_env_data_as_dict(cwd + '/lnbits/extensions/scheduler/.env')
username = vars['SCHEDULER_USER']

# python path 
py_path = sys.executable
dir_path = os.path.dirname(os.path.realpath(__name__))
command = py_path + f" {dir_path}/cron-job.py"


# crontab-specific methods, direct to system cron
async def create_cron(comment:str, command:str, schedule:str, env_vars:dict):    
    try:
        ch = CronHandler(username)
        response = await ch.new_job(command, schedule, comment=comment, env=env_vars)
        return response
    except Exception as e: 
        return f"Error creating job: {e}"
    

async def delete_cron(link_id: str):
    # the comment in actual crontab is the job ID in LNBits
    try:
        ch = CronHandler(username)
        response = await ch.remove_by_comment(link_id)
        return response
    except Exception as e: 
        return f"Error deleting job: {e}"


## database + crontab handling methods
async def create_scheduler_jobs(admin_id: str, data: CreateJobData) -> JobDetailed:
    link_id = uuid4().hex 

    # temporary blank env_vars held here, left here for future customization
    env_vars = {"ID": link_id}
    
    ch = CronHandler(username)
    is_valid = await ch.validate_cron_string(data.schedule)
    if not is_valid:
        assert is_valid, "Invalid cron string, please check the format."
        return f"Error in cron string syntax {data.schedule}"
    response = await create_cron(link_id, command, data.schedule, env_vars)

    print(command)
    print(response)

    if response.startswith("Error"):
        assert response.startswith("Error"), "Error creating Cron job"
        return f"Error creating cron job: {response}"
    
    await db.execute(
        """
        INSERT INTO scheduler.jobs (id, name, admin, status, schedule, httpverb, url, headers, body, extra)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (link_id, data.job_name, admin_id, data.status, data.schedule, data.httpverb, data.url,
         json.dumps(data.headers), json.dumps(data.body),
         json.dumps(data.extra) if data.extra else None),
    )

    job_created = await get_scheduler_job(link_id)
    assert job_created, "Newly created Job couldn't be retrieved"
    return job_created


async def get_scheduler_job(job_id: str) -> Optional[JobDetailed]:
    row = await db.fetchone("SELECT * FROM scheduler.jobs WHERE id = ?", (job_id,))
    if row:
        return Job(**row)


async def get_scheduler_jobs(admin: str, filters: Filters[JobFilters]) -> list[Job]:
    # check that job id match crontab list
    rows = await db.fetchall(
        f"""
        SELECT * FROM scheduler.jobs
        {filters.where(["admin = ?"])}
        {filters.pagination()}
        """,
        filters.values([admin])
    )
    return [Job(**row) for row in rows]


async def pause_scheduler(job_id: str, state: str) -> bool:
    try: 
        print(f'Pausing job: {job_id}, State: {state}') 
        ch = CronHandler(username)
        b = True
        if state.lower() == "false":
            b = False
        status = await ch.enable_job_by_comment(comment=job_id, bool=b)
        print(f'Status: {status}')
        ## update database
        return status
    except Exception as e: 
        return f"Error pausing job: {e}"


async def delete_scheduler_jobs(job_id: str, delete_core: bool = True) -> None:
    # TODO: get rid of delete_core
    deleted = await delete_cron(job_id)
    print(f'Deletion status for {job_id} : {deleted}')
    await db.execute("DELETE FROM scheduler.jobs WHERE id = ?", (job_id,))


async def update_scheduler_job(job_id: str, admin_id: str, data: UpdateJobData) -> JobDetailed:
    cols = []
    values = []
    if data.job_name:
        cols.append("name = ?")
        values.append(data.job_name)
    if data.status:
        cols.append("status = ?")
        values.append(data.status)
    if data.schedule:
        cols.append("schedule = ?")
        values.append(data.schedule)
    if data.httpverb:
        cols.append("httpverb = ?")
        values.append(data.httpverb)
    if data.url:
        cols.append("url = ?")
        values.append(data.url)

    values.append(job_id)
    values.append(admin_id)
    if data.extra:
        if db.type == POSTGRES:
            cols.append("extra = extra::jsonb || ?")
        else:
            cols.append("extra = json_patch(extra, ?)")
        values.append(json.dumps(data.extra))
    if data.headers:
        if db.type == POSTGRES:
            cols.append("headers = headers::jsonb || ?")
        else:
            cols.append("headers = json_patch(headers, ?)")
        values.append(json.dumps(data.headers))
    if data.data:
        if db.type == POSTGRES:
            cols.append("data = data::jsonb || ?")
        else:
            cols.append("data = json_patch(data, ?)")
        values.append(json.dumps(data.data))
    
    # validate cron job before here
    # write update to cron tab
    ch = CronHandler(username)
    # TODO update Job status w/ data.status
    # await ch.enable_job_by_comment(comment=job_id, bool=data.status)
    # await ch.edit_job(command, data.schedule, comment=job_id)


    await db.execute(
        f"""
        UPDATE scheduler.jobs SET {", ".join(cols)} WHERE id = ? AND admin = ?
        """,
        values
    )
    return await get_scheduler_job(job_id)
