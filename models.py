from enum import Enum
from sqlite3 import Row
from typing import Optional, List

from fastapi.param_functions import Query
from pydantic import BaseModel

from lnbits.db import FilterModel
import json

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


class HeaderItems(BaseModel):
    key: str
    value: str
    def to_dict(self):
        return {
        'key': self.key,
        'value': self.value
    }


class CreateJobData(BaseModel):
    name: Optional[str] = Query(default=None, description="Name of the Job")
    status: bool = Query(False) # true is active, false if paused
    selectedverb: Optional[str] = Query(default=None)
    url: Optional[str] = Query(default=None)
    headers: Optional[List[HeaderItems]]
    body: Optional[str] = Query(default=None)
    schedule: str = Query(default=None)
    extra: Optional[dict[str, str]] = Query(default=None)


class UpdateJobData(BaseModel):
    id: str
    name: Optional[str] = Query(default=None, description="Name of the Job")
    status: bool
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[List[HeaderItems]]
    body: Optional[str] = None
    schedule: str = Query(default=None, description='Schedule to run')
    extra: Optional[dict[str, str]] = Query(default=None, description='Partial update for extra field')


class Job(BaseModel):
    id: str
    name: str
    admin: str
    status: bool
    schedule: str
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[List[HeaderItems]]
    body: Optional[str] = None
    extra: Optional[dict[str, str]]

    @classmethod
    def from_db_row(cls, row):
        # Convert the 'headers' column from a string to a list of dictionaries
        if row['headers']:
            headers = json.loads(row['headers'])
            headers = [HeaderItems(**header) for header in headers]
        else:
            headers = []

        return cls(
            id=row['id'],
            name=row['name'],
            admin=row['admin'],
            status=row['status'],
            schedule=row['schedule'],
            selectedverb=row['selectedverb'],
            url=row['url'],
            headers=headers,
            body=row['body'],
            extra=row['extra']
        )


class JobFilters(FilterModel):
    id: str
    name: str
    schedule: Optional[str] = None
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    body: Optional[str] = None
    extra: Optional[dict[str, str]]
    # headers: Optional[List[HeaderItems]] = None

class JobDetailed(Job):
    pass

class LogEntry(BaseModel):
    job_id: str
    status: Optional[str] = None
    response: Optional[str] = None
    timestamp: Optional[str] = None