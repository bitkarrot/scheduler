import json
from typing import List, Optional

from lnbits.core.crud import (
    create_account,
    create_wallet,
    delete_wallet,
    get_payments,
    get_user,
)
from lnbits.core.models import Payment
from lnbits.db import POSTGRES, Filters

from . import db
from .models import (
    CreateUserData,
    UpdateUserData,
    User,
    UserDetailed,
    UserFilters,
    Wallet,
)


async def create_crontabs_user(admin_id: str, data: CreateUserData) -> UserDetailed:
    account = await create_account()
    user = await get_user(account.id)
    assert user, "Newly created user couldn't be retrieved"

    wallet = await create_wallet(user_id=user.id, wallet_name=data.wallet_name)

    await db.execute(
        """
        INSERT INTO crontabs.users (id, name, admin, email, password, extra)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user.id, data.user_name, admin_id, data.email, data.password,
         json.dumps(data.extra) if data.extra else None),
    )

    await db.execute(
        """
        INSERT INTO crontabs.wallets (id, admin, name, "user", adminkey, inkey)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            wallet.id,
            admin_id,
            data.wallet_name,
            user.id,
            wallet.adminkey,
            wallet.inkey,
        ),
    )

    user_created = await get_crontabs_user(user.id)
    assert user_created, "Newly created user couldn't be retrieved"
    return user_created


async def get_crontabs_user(user_id: str) -> Optional[UserDetailed]:
    row = await db.fetchone("SELECT * FROM crontabs.users WHERE id = ?", (user_id,))
    if row:
        wallets = await get_crontabs_users_wallets(user_id)
        return UserDetailed(**row, wallets=wallets)


async def get_crontabs_users(admin: str, filters: Filters[UserFilters]) -> list[User]:
    rows = await db.fetchall(
        f"""
        SELECT * FROM crontabs.users
        {filters.where(["admin = ?"])}
        {filters.pagination()}
        """,
        filters.values([admin])
    )
    return [User(**row) for row in rows]


async def delete_crontabs_user(user_id: str, delete_core: bool = True) -> None:
    if delete_core:
        wallets = await get_crontabs_wallets(user_id)
        for wallet in wallets:
            await delete_wallet(user_id=user_id, wallet_id=wallet.id)

    await db.execute("DELETE FROM crontabs.users WHERE id = ?", (user_id,))
    await db.execute("""DELETE FROM crontabs.wallets WHERE "user" = ?""", (user_id,))


async def create_crontabs_wallet(
    user_id: str, wallet_name: str, admin_id: str
) -> Wallet:
    wallet = await create_wallet(user_id=user_id, wallet_name=wallet_name)
    await db.execute(
        """
        INSERT INTO crontabs.wallets (id, admin, name, "user", adminkey, inkey)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (wallet.id, admin_id, wallet_name, user_id, wallet.adminkey, wallet.inkey),
    )
    wallet_created = await get_crontabs_wallet(wallet.id)
    assert wallet_created, "Newly created wallet couldn't be retrieved"
    return wallet_created


async def get_crontabs_wallet(wallet_id: str) -> Optional[Wallet]:
    row = await db.fetchone(
        "SELECT * FROM crontabs.wallets WHERE id = ?", (wallet_id,)
    )
    return Wallet(**row) if row else None


async def get_crontabs_wallets(admin_id: str) -> List[Wallet]:
    rows = await db.fetchall(
        "SELECT * FROM crontabs.wallets WHERE admin = ?", (admin_id,)
    )
    return [Wallet(**row) for row in rows]


async def get_crontabs_users_wallets(user_id: str) -> List[Wallet]:
    rows = await db.fetchall(
        """SELECT * FROM crontabs.wallets WHERE "user" = ?""", (user_id,)
    )
    return [Wallet(**row) for row in rows]


async def get_crontabs_wallet_transactions(wallet_id: str) -> List[Payment]:
    return await get_payments(
        wallet_id=wallet_id, complete=True, pending=False, outgoing=True, incoming=True
    )


async def delete_crontabs_wallet(wallet_id: str, user_id: str) -> None:
    await delete_wallet(user_id=user_id, wallet_id=wallet_id)
    await db.execute("DELETE FROM crontabs.wallets WHERE id = ?", (wallet_id,))


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
        UPDATE crontabs.users
        SET {", ".join(cols)}
        WHERE id = ? AND admin = ?
        """,
        values
    )
    return await get_crontabs_user(user_id)
