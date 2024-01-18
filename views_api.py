from http import HTTPStatus
from typing import List

from fastapi import Depends, Query
from starlette.exceptions import HTTPException

from lnbits.core import update_user_extension
from lnbits.core.crud import get_user
from lnbits.db import Filters
from lnbits.decorators import (
    WalletTypeInfo,
    get_key_type,
    parse_filters,
    require_admin_key,
)
from lnbits.helpers import generate_filter_params_openapi

from . import scheduler_ext
from .crud import (
    create_scheduler_jobs,
    delete_scheduler_jobs,
    get_scheduler_job,
    get_scheduler_jobs,
    update_scheduler_job,
    pause_scheduler,
    create_log_entry,
    get_log_entries,
    delete_log_entries,
    get_complete_log,
    delete_complete_log
)
from .models import (
    CreateJobData,
    UpdateJobData,
    Job,
    JobDetailed,
    JobFilters,
    LogEntry
)

from .test_run_job import test_job

@scheduler_ext.get(
    "/api/v1/test_log/{job_id}",
    name="testlog",
    summary="his log saves the testlogs",
    description="testlog",
    response_description="testlog",
    dependencies=[Depends(require_admin_key)],
    response_model=str,
)
async def api_get_testlog(
    job_id: str,
    info: WalletTypeInfo = Depends(require_admin_key)
) -> JobDetailed:
    print(f'inside api_get_test_log, job_id: {job_id}')
    print(f'inside api_get_test_log, adminkey : {info.wallet.adminkey}')
    return await test_job(job_id, info.wallet.adminkey)

#await update_scheduler_job(job_id, info.wallet.adminkey, data)

@scheduler_ext.get(
    "/api/v1/logentry/{log_id}",
    status_code=HTTPStatus.OK,
    name="Log entries for a specific job id from DB",
    summary="get log entires for job from DB",
    response_description="log entries for a job from DB",
    dependencies=[Depends(require_admin_key)],
    response_model=str,
)
async def api_get_log_entries(log_id: str) -> str:
    info: WalletTypeInfo = Depends(require_admin_key)
    return await get_log_entries(log_id)


@scheduler_ext.post(
    "/api/v1/deletelog",
    name="Job Log Delete",
    summary="Delete a Job's Log from DB",
    description="Delete Job Log from DB",
    dependencies=[Depends(require_admin_key)],
    response_model=bool,
)
async def api_job_log_delete(
    id: str,
    info: WalletTypeInfo = Depends(require_admin_key)
) -> None:
    # print(f'inside api_job_log_delete: {id}')
    await delete_log_entries(id)

@scheduler_ext.post(
    "/api/v1/logentry",
    name="Log Entry Create",
    summary="Create a new log entry in DB",
    description="Create a new log entry in DB",
    response_description="New Log Entry",
    response_model=LogEntry,
    dependencies=[Depends(require_admin_key)],
)
async def api_job_entry_create(
    data: LogEntry,
    info: WalletTypeInfo = Depends(require_admin_key)
) -> bool:
    return await create_log_entry(data)


@scheduler_ext.get(
    "/api/v1/complete_log",
    status_code=HTTPStatus.OK,
    name="Complete Log",
    summary="get log of all the jobs plus extra logs",
    response_description="complete log from scheduler.log",
    dependencies=[Depends(require_admin_key)],
    response_model=str,
)
async def api_get_complete_log() -> str:
    info: WalletTypeInfo = Depends(require_admin_key)
    return await get_complete_log()


@scheduler_ext.post(
    "/api/v1/delete_log",
    status_code=HTTPStatus.OK,
    name="delete Log",
    summary="clear all log messages",
    response_description="delete complete log from scheduler.log",
    dependencies=[Depends(require_admin_key)],
    response_model=bool,
)
async def api_delete_complete_log() -> bool:
    info: WalletTypeInfo = Depends(require_admin_key)    
    return await delete_complete_log()


@scheduler_ext.get(
    "/api/v1/jobs",
    status_code=HTTPStatus.OK,
    name="Jobs List",
    summary="get list of jobs",
    response_description="list of jobs",
    response_model=List[Job],
    dependencies=[Depends(require_admin_key)],
    openapi_extra=generate_filter_params_openapi(JobFilters),
)
async def api_scheduler_jobs(
    # trunk-ignore(ruff/B008)
    wallet: WalletTypeInfo = Depends(require_admin_key),
    filters: Filters[JobFilters] = Depends(parse_filters(JobFilters))
) -> List[Job]:
    """
    Retrieves all jobs, supporting flexible filtering (LHS Brackets).

    ### Syntax
    `field[op]=value`

    ### Operators
    - eq, ne
    - gt, lt
    - in (include)
    - ex (exclude)

    Filters are AND-combined
    """
    return await get_scheduler_jobs(wallet.wallet.adminkey, filters)

@scheduler_ext.get(
    "/api/v1/jobs/{job_id}",
    name="Jobs Get",
    summary="Get a specific jobs",
    description="get jobs",
    response_description="job if job exists",
    dependencies=[Depends(get_key_type)],
    response_model=JobDetailed
)
async def api_scheduler_user(job_id: str) -> JobDetailed:
    Job = await get_scheduler_job(job_id)
    if not Job:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Jobs not found')
    return Job


@scheduler_ext.post(
    "/api/v1/jobs",
    name="Job Create",
    summary="Create a new job",
    description="Create a new job",
    response_description="New Job",
    dependencies=[Depends(require_admin_key)],
    response_model=Job,
)
async def api_scheduler_jobs_create(
    data: CreateJobData,
    info: WalletTypeInfo = Depends(require_admin_key)  
) -> Job:
     return await create_scheduler_jobs(info.wallet.adminkey, data)


@scheduler_ext.put(
    "/api/v1/jobs/{job_id}",
    name="Jobs Update",
    summary="Update a jobs",
    description="Update a jobs",
    response_description="Updated jobs",
    dependencies=[Depends(require_admin_key)],
    response_model=JobDetailed,
)
async def api_scheduler_jobs_update(
    job_id: str,
    data: UpdateJobData,
    info: WalletTypeInfo = Depends(require_admin_key)
) -> JobDetailed:
    return await update_scheduler_job(job_id, info.wallet.adminkey, data)


@scheduler_ext.delete(
    "/api/v1/jobs/{jobs_id}",
    name="Jobs Delete",
    summary="Delete a jobs",
    description="Delete a jobs",
    dependencies=[Depends(require_admin_key)],
    responses={404: {"description": "Jobs does not exist."}},
    status_code=HTTPStatus.OK,
)
async def api_scheduler_jobs_delete(
    jobs_id
) -> None:
    jobs = await get_scheduler_job(jobs_id)
    if not jobs:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Jobs does not exist."
        )
    # delete both the job and the log entries
    await delete_scheduler_jobs(jobs_id)
    await delete_log_entries(jobs_id)


@scheduler_ext.post(
    "/api/v1/pause/{job_id}/{status}",
    name="Pause Jobs",
    summary="Start or Stop Cron jobs",
    description="Stop or Start Cron jobs",
    response_description="Pause jobs",
    dependencies=[Depends(require_admin_key)],
    responses={404: {"description": "Job does not exist."}},
    status_code=HTTPStatus.OK,
)
async def api_scheduler_pause(
    job_id, status
) -> JobDetailed:
    return await pause_scheduler(job_id, status)


# Activate Extension
@scheduler_ext.post(
    "/api/v1/extensions",
    name="Extension Toggle",
    summary="Extension Toggle",
    description="Extension Toggle",
    response_model=dict[str, str],
    responses={404: {"description": "Jobs does not exist."}},
)
async def api_scheduler_activate_extension(
    extension: str = Query(...), jobsid: str = Query(...), active: bool = Query(...)
) -> dict:
    job = await get_user(jobsid)
    if not job:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Job does not exist."
        )
    await update_user_extension(job_id=jobsid, extension=extension, active=active)
    return {"extension": "updated"}

