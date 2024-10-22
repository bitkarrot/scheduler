from datetime import datetime, timezone
from typing import Optional

from fastapi import Query
from lnbits.db import FilterModel
from pydantic import BaseModel


class HeaderItems(BaseModel):
    key: str
    value: str

    def to_dict(self):
        return {"key": self.key, "value": self.value}


class CreateJobData(BaseModel):
    name: Optional[str] = Query(default=None, description="Name of the Job")
    status: bool = Query(False)  # true is active, false if paused
    selectedverb: Optional[str] = Query(default=None)
    url: Optional[str] = Query(default=None)
    headers: Optional[list[HeaderItems]]
    body: Optional[str] = Query(default=None)
    schedule: str = Query(default=None)
    extra: Optional[dict[str, str]] = Query(default=None)


class UpdateJobData(BaseModel):
    id: str
    name: Optional[str] = Query(default=None, description="Name of the Job")
    status: bool
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[list[HeaderItems]]
    body: Optional[str] = None
    schedule: str = Query(default=None, description="Schedule to run")
    extra: Optional[dict[str, str]] = Query(
        default=None, description="Partial update for extra field"
    )


class Job(BaseModel):
    id: str
    name: str
    admin: str
    status: bool
    schedule: str
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[list[HeaderItems]]
    body: Optional[str] = None
    extra: Optional[dict[str, str]]


class JobFilters(FilterModel):
    id: str
    name: str
    schedule: Optional[str] = None
    selectedverb: Optional[str] = None
    url: Optional[str] = None
    body: Optional[str] = None
    extra: Optional[dict[str, str]]


class LogEntry(BaseModel):
    id: str
    job_id: str
    status: Optional[str] = None
    response: Optional[str] = None
    timestamp: datetime = datetime.now(timezone.utc)
