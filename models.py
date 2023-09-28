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
    name: Optional[str] = Query(default=None, description="Name of the Job")
    status: bool = Query(False) # true is active, false if paused
    selectedverb: Optional[str] = Query(default=None)
    url: Optional[str] = Query(default=None)
    headers: Optional[str] = Query(default=None)
    body: Optional[str] = Query(default=None)
    schedule: str = Query(default=None)
    extra: Optional[dict[str, str]] = Query(default=None)


class UpdateJobData(BaseModel):
    name: Optional[str] = Query(default=None, description="Name of the Job")
    status: bool  # true is active, false if paused
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[str] = None
    body: Optional[str] = None
    schedule: str = Query(default=None, description='Schedule to run')
    extra: Optional[dict[str, str]] = Query(default=None, description='Partial update for extra field')


class Job(BaseModel):
    id: str
    name: str
    admin: str
    status: bool  # true is active, false if paused
    schedule: str
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[str] = None
    body: Optional[str] = None
    extra: Optional[dict[str, str]]


class JobFilters(FilterModel):
    id: str
    name: str
    schedule: Optional[str] = None
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[str] = None
    body: Optional[str] = None
    extra: Optional[dict[str, str]]


class JobDetailed(Job):
    pass
    #wallets: list[Wallet]


class LogEntry(BaseModel):
    id: str
    status: str
    response: str
    timestamp: str