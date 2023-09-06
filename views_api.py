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

from . import crontabs_ext
from .crud import (
    create_crontabs_user,
    delete_crontabs_user,
    get_crontabs_user,
    get_crontabs_users,
    update_crontabs_user,
)
from .models import (
    CreateUserData,
    UpdateUserData,
    User,
    UserDetailed,
    UserFilters,
    # CreateUserWallet,
    # Wallet,
)


@crontabs_ext.get(
    "/api/v1/users",
    status_code=HTTPStatus.OK,
    name="User List",
    summary="get list of users",
    response_description="list of users",
    response_model=List[User],
    openapi_extra=generate_filter_params_openapi(UserFilters),
)
async def api_crontabs_users(
    wallet: WalletTypeInfo = Depends(require_admin_key),
    filters: Filters[UserFilters] = Depends(parse_filters(UserFilters))
) -> List[User]:
    """
    Retrieves all users, supporting flexible filtering (LHS Brackets).

    ### Syntax
    `field[op]=value`

    ### Example Query Strings
    ```
    email[eq]=test@mail.com
    name[ex]=dont-want&name[ex]=dont-want-too
    extra.role[ne]=role-id
    ```
    ### Operators
    - eq, ne
    - gt, lt
    - in (include)
    - ex (exclude)

    Fitlers are AND-combined
    """
    admin_id = wallet.wallet.user
    return await get_crontabs_users(admin_id, filters)


@crontabs_ext.get(
    "/api/v1/users/{user_id}",
    name="User Get",
    summary="Get a specific user",
    description="get user",
    response_description="user if user exists",
    dependencies=[Depends(get_key_type)],
    response_model=UserDetailed
)
async def api_crontabs_user(user_id: str) -> UserDetailed:
    user = await get_crontabs_user(user_id)
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='User not found')
    return user


@crontabs_ext.post(
    "/api/v1/users",
    name="User Create",
    summary="Create a new user",
    description="Create a new user",
    response_description="New User",
    #response_model=UserDetailed,
    response_model=User,
)
async def api_crontabs_users_create(
    data: CreateUserData,
    info: WalletTypeInfo = Depends(require_admin_key)
) -> User:
    return await create_crontabs_user(info.wallet.user, data)


@crontabs_ext.put(
    "/api/v1/users/{user_id}",
    name="User Update",
    summary="Update a user",
    description="Update a user",
    response_description="Updated user",
    response_model=UserDetailed,
)
async def api_crontabs_users_create(
    user_id: str,
    data: UpdateUserData,
    info: WalletTypeInfo = Depends(require_admin_key)
) -> UserDetailed:
    return await update_crontabs_user(user_id, info.wallet.user, data)


@crontabs_ext.delete(
    "/api/v1/users/{user_id}",
    name="User Delete",
    summary="Delete a user",
    description="Delete a user",
    dependencies=[Depends(require_admin_key)],
    responses={404: {"description": "User does not exist."}},
    status_code=HTTPStatus.OK,
)
async def api_crontabs_users_delete(
    user_id,
    delete_core: bool = Query(True),
) -> None:
    user = await get_crontabs_user(user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User does not exist."
        )
    await delete_crontabs_user(user_id, delete_core)


# Activate Extension
@crontabs_ext.post(
    "/api/v1/extensions",
    name="Extension Toggle",
    summary="Extension Toggle",
    description="Extension Toggle",
    response_model=dict[str, str],
    responses={404: {"description": "User does not exist."}},
)
async def api_crontabs_activate_extension(
    extension: str = Query(...), userid: str = Query(...), active: bool = Query(...)
) -> dict:
    user = await get_user(userid)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User does not exist."
        )
    await update_user_extension(user_id=userid, extension=extension, active=active)
    return {"extension": "updated"}

