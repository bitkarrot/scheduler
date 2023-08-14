from fastapi import Depends, Request
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists

from . import crontabs_ext, crontabs_renderer


@crontabs_ext.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return crontabs_renderer().TemplateResponse(
        "crontabs/index.html", {"request": request, "user": user.dict()}
    )
