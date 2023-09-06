from enum import Enum
from sqlite3 import Row
from typing import Optional

from fastapi.param_functions import Query
from pydantic import BaseModel

from lnbits.db import FilterModel


class Operator(Enum):
    GT = "gt"
    LT = "lt"
    EQ = "eq"
    NE = "ne"
    INCLUDE = "in"
    EXCLUDE = "ex"

    @property
    def as_sql(self):
        if self == Operator.EQ:
            return "="
        elif self == Operator.NE:
            return "!="
        elif self == Operator.INCLUDE:
            return "IN"
        elif self == Operator.EXCLUDE:
            return "NOT IN"
        elif self == Operator.GT:
            return ">"
        elif self == Operator.LT:
            return "<"
        else:
            raise ValueError('Unknown')


class CreateUserData(BaseModel):
    user_name: str = Query(..., description="Name of the user")
    command: str = Query("")
    schedule: str = Query("")
    extra: Optional[dict[str, str]] = Query(default=None)


class UpdateUserData(BaseModel):
    user_name: Optional[str] = Query(default=None, description="Name of the user")
    extra: Optional[dict[str, str]] = Query(default=None, description='Partial update for extra field')


class User(BaseModel):
    id: str
    name: str
    admin: str
    command: Optional[str] = None
    schedule: Optional[str] = None
    extra: Optional[dict[str, str]]


class UserFilters(FilterModel):
    id: str
    name: str
    command: Optional[str] = None
    extra: Optional[dict[str, str]]


class UserDetailed(User):
    pass
    #wallets: list[Wallet]
