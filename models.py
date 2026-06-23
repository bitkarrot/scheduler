from datetime import datetime, timezone

from crontab import CronSlices
from fastapi import Query
from lnbits.db import FilterModel
from pydantic import BaseModel, Field, validator


class HeaderItems(BaseModel):
    key: str
    value: str

    def to_dict(self):
        return {"key": self.key, "value": self.value}


class CreateJobData(BaseModel):
    name: str | None = Query(default=None, description="Name of the Job")
    status: bool = Query(False)  # true is active, false if paused
    selectedverb: str | None = Query(default=None)
    url: str | None = Query(default=None)
    headers: list[HeaderItems] | None
    body: str | None = Query(default=None)
    schedule: str = Field(
        ...,
        description="Cron schedule expression (e.g. '*/5 * * * *' for every 5 minutes)",
    )
    extra: dict[str, str] | None = Query(default=None)

    @validator("schedule")
    def validate_schedule(cls, v):
        if not CronSlices.is_valid(v):
            raise ValueError(
                f"Invalid cron schedule format: {v}."
                + 'Example format: "*/5 * * * *" for every 5 minutes'
            )
        return v


class UpdateJobData(BaseModel):
    id: str
    name: str | None = Query(default=None, description="Name of the Job")
    status: bool
    selectedverb: str | None = None
    url: str | None = None
    headers: list[HeaderItems] | None
    body: str | None = None
    schedule: str = Query(default=None, description="Schedule to run")
    extra: dict[str, str] | None = Query(
        default=None, description="Partial update for extra field"
    )


class Job(BaseModel):
    id: str
    name: str
    admin: str
    status: bool
    schedule: str
    selectedverb: str | None = None
    url: str | None = None
    headers: list[HeaderItems] | None
    body: str | None = None
    extra: dict[str, str] | None


class JobFilters(FilterModel):
    id: str
    name: str
    schedule: str | None = None
    selectedverb: str | None = None
    url: str | None = None
    body: str | None = None
    extra: dict[str, str] | None


class LogEntry(BaseModel):
    id: str
    job_id: str
    status: str | None = None
    response: str | None = None
    timestamp: datetime = datetime.now(timezone.utc)
