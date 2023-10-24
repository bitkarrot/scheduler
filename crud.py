import json
from typing import Optional
from uuid import uuid4
from datetime import datetime
import sys
import datetime as dt

from lnbits.db import POSTGRES, Filters

from . import db
from .models import (
    CreateJobData,
    UpdateJobData,
    Job,
    JobDetailed,
    JobFilters,
    LogEntry
)

from .cron_handler import CronHandler
from .utils import get_env_data_as_dict
import os

# exception throw might need to be handled higher up in the stack 
cwd = os.getcwd()
vars = get_env_data_as_dict(cwd + '/lnbits/extensions/scheduler/.env')
username = True

# python path 
py_path = sys.executable
dir_path = os.path.dirname(os.path.realpath(__name__))
command = py_path + f" {dir_path}/lnbits/extensions/scheduler/run_cron_job.py"

# .log path 
log_path = f"{dir_path}/lnbits/extensions/scheduler/scheduler.log"

# crontab-specific methods, direct to system cron
async def create_cron(comment:str, command:str, schedule:str, env_vars:dict):    
    try:
        ch = CronHandler(user=username)
        response = await ch.new_job(command, schedule, comment=comment, env=env_vars)
        # make sure job is not running on creation by default
        status = await ch.enable_job_by_comment(comment=comment, bool=False)
        # print(f'create_cron: {response}, {status}')
        if status == False:
            return response
        else: # error setting job to 'Not Running' and creating job
            raise e
    except Exception as e: 
        return f"Error creating cron job: {e}"
    

async def delete_cron(link_id: str):
    # the comment in actual crontab is the job ID in LNBits
    try:
        ch = CronHandler(user=username)
        response = await ch.remove_by_comment(link_id)
        return response
    except Exception as e: 
        return f"Error deleting job: {e}"


async def convert_headers(headers: list):
    # print(f'header list length: "{len(headers)}')
    allitems_as_dicts = [item.to_dict() for item in headers]
    headers_string = json.dumps(allitems_as_dicts)
    # print(f'headers as json string: {headers_string}')
    return headers_string


async def create_scheduler_jobs(admin_id: str, data: CreateJobData) -> JobDetailed:
    link_id = uuid4().hex 
    env_vars = {"ID": link_id, "adminkey": admin_id}
    # print(f'env_vars: {env_vars}')
    headers_string = await convert_headers(data.headers)

    ch = CronHandler(user=username)
    is_valid = await ch.validate_cron_string(data.schedule)
    if not is_valid:
        assert is_valid, "Invalid cron schedule, please check the format."
        return f"Error in cron string syntax {data.schedule}"
    response = await create_cron(link_id, command, data.schedule, env_vars)

    if response.startswith("Error"):
        assert response.startswith("Error"), "Error creating Cron job"
        return f"Error creating cron job: {response}"
    
    await db.execute(
        """
        INSERT INTO scheduler.jobs (id, name, admin, status, schedule, selectedverb, url, headers, body, extra)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (link_id, data.name, admin_id, data.status, 
         data.schedule, data.selectedverb, data.url,
         headers_string, data.body,
         json.dumps(data.extra) if data.extra else None),
    )

    job_created = await get_scheduler_job(link_id)
    assert job_created, "Newly created Job couldn't be retrieved"
    return job_created


async def get_scheduler_job(job_id: str) -> Optional[JobDetailed]:
    row = await db.fetchone("SELECT * FROM scheduler.jobs WHERE id = ?", (job_id,))
    if row:
        return Job.from_db_row(row)


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
    jobs = [Job.from_db_row(row) for row in rows]
    return jobs


async def pause_scheduler(job_id: str, state: str) -> bool:
    try: 
        print(f'Pausing job in pause_scheduler: {job_id}, State: {state}') 
        ch = CronHandler(user=username)
        b = True
        if state.lower() == "false":
            b = False
        status = await ch.enable_job_by_comment(comment=job_id, bool=b)
        now =  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f' Time: {now}, Is Running?: {status}')
        await db.execute(
            f"""
            UPDATE scheduler.jobs SET status = ? WHERE id = ?
            """,
            (status, job_id)
        )
        # print("Updated database with current status ")
        return await get_scheduler_job(job_id)

    except Exception as e: 
        return f"Error pausing job: {e}"


async def delete_scheduler_jobs(job_id: str) -> None:
    try:
        deleted = await delete_cron(job_id)
        # print(f'Deletion status for {job_id} : {deleted}')
        await db.execute("DELETE FROM scheduler.jobs WHERE id = ?", (job_id,))
    except Exception as e:
        raise e

async def update_scheduler_job(job_id: str, admin_id: str, data: UpdateJobData) -> JobDetailed:
    cols = []
    values = []
    if data.name:
        cols.append("name = ?")
        values.append(data.name)
    if data.status:
        cols.append("status = ?")  ## check if this works
        values.append(data.status)
    if data.schedule:
        cols.append("schedule = ?")
        values.append(data.schedule)
    if data.selectedverb:
        cols.append("selectedverb = ?")
        values.append(data.selectedverb)
    if data.url:
        cols.append("url = ?")
        values.append(data.url)
    if data.headers:
        cols.append("headers = ?")
        headers_string = await convert_headers(data.headers)
        values.append(headers_string)
    if data.body:
        cols.append("body = ?")
        values.append(data.body)
    
    values.append(job_id)
    values.append(admin_id)
    
    if data.extra:
        if db.type == POSTGRES:
            cols.append("extra = extra::jsonb || ?")
        else:
            cols.append("extra = json_patch(extra, ?)")
        values.append(json.dumps(data.extra))
    
    await db.execute(
        f"""
        UPDATE scheduler.jobs SET {", ".join(cols)} WHERE id = ? AND admin = ?
        """,
        values
    )
    # check to make sure DB was updated
    # write update to cron tab
    ch = CronHandler(user=username)
    await ch.enable_job_by_comment(comment=job_id, bool=data.status)
    await ch.edit_job(command, data.schedule, comment=job_id)

    return await get_scheduler_job(job_id)


async def create_log_entry(data: LogEntry) -> LogEntry:
    '''
        create log entry in database
    '''
    job_id = data.job_id
    status = data.status
    response = data.response
    timestamp =  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    id = uuid4().hex

    await db.execute(
        """
        INSERT INTO scheduler.logs (id, job_id, status, response, timestamp) VALUES (?, ?, ?, ?, ?)
        """,
        (id, job_id, status, response, timestamp)
    )
    # print(f'Creating Log Entry in DB: {job_id}, {status}, {response}, {timestamp}')
    log_created = await get_log_entry(id)
    assert log_created, "Newly created Log Entry couldn't be retrieved"
    return log_created

async def get_log_entry(id: str) -> LogEntry:
    '''
        get a single log entry based on primary key Unique ID        
    '''
    row = await db.fetchone("SELECT * FROM scheduler.logs WHERE id = ?", (id,))
    return LogEntry(**row)

async def get_log_entries(job_id: str) -> str:
    '''
        get all log entries from data base for particular job
    '''
    # print(f'inside get_log_entries with job_id: {job_id}')
    rows = await db.fetchall("SELECT * FROM scheduler.logs WHERE job_id = ?", (job_id,))
    all_entries = ""
    for row in rows: 
        all_entries = (all_entries + "[" + LogEntry(**row).timestamp + "]: JobID:" +
                        LogEntry(**row).job_id + " Status: "+  LogEntry(**row).status +
                        " Response: " + LogEntry(**row).response + "\n\n")
    return all_entries


async def delete_log_entries(job_id: str) -> None:
    '''
        delete all log entries from data base for particular job
    '''
    try:
        await db.execute("DELETE FROM scheduler.logs WHERE job_id = ?", (job_id,))
    except Exception as e:
        raise e


async def read_last_n_lines(file_path, n):
    with open(file_path, 'r') as file:
        lines = file.readlines()[-n:]
    return lines


async def get_complete_log() -> str:
    '''
        return entire text log from disk, including other errors
        for now, only fetch the last 1000 lines, 
        so that response does not get too large
    '''
    if os.path.exists(log_path):  
        content = ''
        last_1000_lines = await read_last_n_lines(log_path, 1000)
        for line in last_1000_lines:
            content += line
        return content
    else: 
        return f'log file does not exist at location: {log_path}'

async def delete_complete_log() -> bool: 
    '''
        clear the contents of the text log on disk
    '''
    # Check if the file exists before trying to delete it
    if os.path.exists(log_path):
        os.remove(log_path)
        return True
    else:
        return False

