from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from lnbits.db import Database
from lnbits.helpers import template_renderer

db = Database("ext_crontabs")

crontabs_ext: APIRouter = APIRouter(prefix="/crontabs", tags=["crontabs"])

crontabs_static_files = [
    {
        "path": "/crontabs/static",
        "app": StaticFiles(directory="lnbits/extensions/crontabs/static"),
        "name": "crontabs_static",
    }
]


def crontabs_renderer():
    return template_renderer(["lnbits/extensions/crontabs/templates"])


from .views import *  # noqa
from .views_api import *  # noqa
