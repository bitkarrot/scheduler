from fastapi import APIRouter, Depends, Request
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer
from starlette.responses import HTMLResponse

scheduler_generic_router = APIRouter()


def scheduler_renderer():
    return template_renderer(["scheduler/templates"])


@scheduler_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return scheduler_renderer().TemplateResponse(
        "scheduler/index.html", {"request": request, "user": user.json()}
    )
