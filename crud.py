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
    # Wallet,
)


async def create_crontabs_user(admin_id: str, data: CreateUserData) -> UserDetailed:
    link_id = urlsafe_short_hash()[:6]

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
    rows = await db.fetchall(
        f"""
        SELECT * FROM crontabs.jobs
        {filters.where(["admin = ?"])}
        {filters.pagination()}
        """,
        filters.values([admin])
    )
    return [User(**row) for row in rows]


async def delete_crontabs_user(user_id: str, delete_core: bool = True) -> None:
    await db.execute("DELETE FROM crontabs.jobs WHERE id = ?", (user_id,))

# this only works for UpdateUserData, adjust UpdateUserData to be the full set (e.g. command, schedule, etc)
async def update_crontabs_user(user_id: str, admin_id: str, data: UpdateUserData) -> UserDetailed:
    cols = []
    values = []
    if data.user_name:
        cols.append("name = ?")
        values.append(data.user_name)
    if data.extra:
        if db.type == POSTGRES:
            cols.append("extra = extra::jsonb || ?")
        else:
            cols.append("extra = json_patch(extra, ?)")
        values.append(json.dumps(data.extra))
    values.append(user_id)
    values.append(admin_id)

    await db.execute(
        f"""
        UPDATE crontabs.jobs SET {", ".join(cols)} WHERE id = ? AND admin = ?
        """,
        values
    )
    return await get_crontabs_user(user_id)
