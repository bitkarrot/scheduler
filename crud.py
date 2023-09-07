import json
from typing import List, Optional
from lnbits.helpers import urlsafe_short_hash
from lnbits.db import POSTGRES, Filters

from . import db
from .models import (
    CreateUserData,
    UpdateUserData,
    User,
    UserDetailed,
    UserFilters,
)

from .cron_handler import CronHandler
import os 

# TODO - do we manage this in admin panel somewhere or in environment variable?
# set username to match that of user account that is running lnbits server
# username = 'bitcarrot'
username = os.environ.get('CRON_USERNAME')

# crontab-specific methods, direct to system cron
async def create_cron(comment:str, command:str, schedule:str, env_vars:dict):    
    try:
        ch = CronHandler(username)
        response = await ch.new_job_with_env(command, schedule, comment=comment, env=env_vars)
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
async def create_crontabs_user(admin_id: str, data: CreateUserData) -> UserDetailed:
    link_id = urlsafe_short_hash()[:6]

    # temporary blank env_vars held here, left here for future customization
    env_vars = {}
    
    ch = CronHandler(username)
    is_valid = await ch.validate_cron_string(data.schedule)
    if not is_valid:
        assert is_valid, "Invalid cron string, please check the format."
        return f"Error in cron string syntax {data.schedule}"

    response = await create_cron(link_id, data.command, data.schedule, env_vars)
    print(response)
    if response.startswith("Error"):
        assert response.startswith("Error"), "Error creating Cron job"
        return f"Error creating cron job: {response}"
    
    await db.execute(
        """
        INSERT INTO crontabs.jobs (id, name, admin, command, schedule, extra)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (link_id, data.user_name, admin_id, data.command, data.schedule,
         json.dumps(data.extra) if data.extra else None),
    )

    user_created = await get_crontabs_user(link_id)
    assert user_created, "Newly created user couldn't be retrieved"
    return user_created


async def get_crontabs_user(user_id: str) -> Optional[UserDetailed]:
    row = await db.fetchone("SELECT * FROM crontabs.jobs WHERE id = ?", (user_id,))
    if row:
        return User(**row)
        # return UserDetailed(**row, wallets=wallets)


async def get_crontabs_users(admin: str, filters: Filters[UserFilters]) -> list[User]:
    # check that job id match crontab list
    rows = await db.fetchall(
        f"""
        SELECT * FROM crontabs.jobs
        {filters.where(["admin = ?"])}
        {filters.pagination()}
        """,
        filters.values([admin])
    )
    return [User(**row) for row in rows]


async def pause_crontabs(job_id: str, state: str) -> bool:
    try: 
        print(f'Pausing job: {job_id}, State: {state}') 
        ch = CronHandler(username)
        b = True
        if state.lower() == "false":
            b = False
        status = await ch.enable_job_by_comment(comment=job_id, bool=b)
        print(f'Status: {status}')
        return status
    except Exception as e: 
        return f"Error pausing job: {e}"


async def delete_crontabs_user(user_id: str, delete_core: bool = True) -> None:
    #TODO: get rid of delete_core
    deleted = await delete_cron(user_id)
    print(f'Deletion status for {user_id} : {deleted}')
    await db.execute("DELETE FROM crontabs.jobs WHERE id = ?", (user_id,))


async def update_crontabs_user(user_id: str, admin_id: str, data: UpdateUserData) -> UserDetailed:
    cols = []
    values = []
    if data.job_name:
        cols.append("name = ?")
        values.append(data.job_name)
    if data.extra:
        if db.type == POSTGRES:
            cols.append("extra = extra::jsonb || ?")
        else:
            cols.append("extra = json_patch(extra, ?)")
        values.append(json.dumps(data.extra))
    if data.command:
        cols.append("command = ?")
        values.append(data.command)
    if data.schedule:
        cols.append("schedule = ?")
        values.append(data.schedule)
    values.append(user_id)
    values.append(admin_id)

    # validate cron job before here
    # write update to cron tab
    ch = CronHandler(username)
    await ch.edit_job(data.command, data.schedule, comment=user_id)


    await db.execute(
        f"""
        UPDATE crontabs.jobs SET {", ".join(cols)} WHERE id = ? AND admin = ?
        """,
        values
    )
    return await get_crontabs_user(user_id)
