from fastapi import Depends, Request
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists

from . import scheduler_ext, scheduler_renderer


@scheduler_ext.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return scheduler_renderer().TemplateResponse(
        "scheduler/index.html", {"request": request, "user": user.dict()}
    )
