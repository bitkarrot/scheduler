from http import HTTPStatus
from typing import List

from fastapi import Depends, Query
from starlette.exceptions import HTTPException

from lnbits.core import update_user_extension
from lnbits.core.crud import get_user
# from lnbits.core.models import Payment
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
)
from .models import (
    CreateUserData,
    UpdateUserData,
    User,
    UserDetailed,
    UserFilters,
)

@scheduler_ext.get(
    "/api/v1/jobs",
    status_code=HTTPStatus.OK,
    name="Jobs List",
    summary="get list of jobs",
    response_description="list of jobs",
    response_model=List[User],
    openapi_extra=generate_filter_params_openapi(UserFilters),
)
async def api_scheduler_jobs(
    wallet: WalletTypeInfo = Depends(require_admin_key),
    filters: Filters[UserFilters] = Depends(parse_filters(UserFilters))
) -> List[User]:
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
    admin_id = wallet.wallet.user
    return await get_scheduler_jobs(admin_id, filters)


@scheduler_ext.get(
    "/api/v1/jobs/{job_id}",
    name="Jobs Get",
    summary="Get a specific jobs",
    description="get jobs",
    response_description="job if job exists",
    dependencies=[Depends(get_key_type)],
    response_model=UserDetailed
)
async def api_scheduler_user(job_id: str) -> UserDetailed:
    user = await get_scheduler_job(job_id)
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Jobs not found')
    return user


@scheduler_ext.post(
    "/api/v1/jobs",
    name="Job Create",
    summary="Create a new job",
    description="Create a new job",
    response_description="New Job",
    #response_model=UserDetailed,
    response_model=User,
)
async def api_scheduler_jobs_create(
    data: CreateUserData,
    info: WalletTypeInfo = Depends(require_admin_key)
) -> User:
    return await create_scheduler_jobs(info.wallet.user, data)


@scheduler_ext.put(
    "/api/v1/jobs/{job_id}",
    name="Jobs Update",
    summary="Update a jobs",
    description="Update a jobs",
    response_description="Updated jobs",
    response_model=UserDetailed,
)
async def api_scheduler_jobs_create(
    job_id: str,
    data: UpdateUserData,
    info: WalletTypeInfo = Depends(require_admin_key)
) -> UserDetailed:
    return await update_scheduler_job(job_id, info.wallet.user, data)


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
    jobs_id,
    delete_core: bool = Query(True),
) -> None:
    jobs = await get_scheduler_job(jobs_id)
    if not jobs:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Jobs does not exist."
        )
    await delete_scheduler_jobs(jobs_id, delete_core)


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
) -> bool:
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

