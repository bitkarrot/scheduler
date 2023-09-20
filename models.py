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


class CreateJobData(BaseModel):
    #user_name: str = Query(..., description="Name of the Job")
    #command: str = Query("")
    job_name: Optional[str] = Query(default=None, description="Name of the Job")
    status: bool  # true is active, false if paused
    httpverb: Optional[str] = Query(default=None)
    url: Optional[str] = Query(default=None)
    headers: Optional[dict[str, str]] = Query(default=None)
    body: Optional[dict[str, str]] = Query(default=None)
    schedule: str = Query("")
    extra: Optional[dict[str, str]] = Query(default=None)


class UpdateJobData(BaseModel):
#    command: Optional[str] = Query(default=None, description='Command to run')
    job_name: Optional[str] = Query(default=None, description="Name of the Job")
    status: bool  # true is active, false if paused
    httpverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    body: Optional[dict[str, str]] = None
    schedule: Optional[str] = Query(default=None, description='Schedule to run')
    extra: Optional[dict[str, str]] = Query(default=None, description='Partial update for extra field')


class Job(BaseModel):
    id: str
    name: str
    admin: str
    status: bool  # true is active, false if paused
    schedule: Optional[str] = None
    # command: Optional[str] = None
    httpverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    body: Optional[dict[str, str]] = None
    extra: Optional[dict[str, str]]


class JobFilters(FilterModel):
    id: str
    name: str
    # command: Optional[str] = None
    schedule: Optional[str] = None
    httpverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    body: Optional[dict[str, str]] = None
    extra: Optional[dict[str, str]]


class JobDetailed(Job):
    pass
    #wallets: list[Wallet]
