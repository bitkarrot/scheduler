from fastapi import APIRouter

from lnbits.db import Database
from lnbits.helpers import template_renderer

db = Database("ext_scheduler")

scheduler_ext: APIRouter = APIRouter(prefix="/scheduler", tags=["scheduler"])

scheduler_static_files = [
    {
        "path": "/scheduler/static",
        "name": "scheduler_static",
    }
]


def scheduler_renderer():
    return template_renderer(["scheduler/templates"])


from .views import *  # noqa
from .views_api import *  # noqa
from .cron_handler import *  # noqa
