from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)


@router.get(
    "/login",
    response_class=HTMLResponse,
)
async def login_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
        },
    )


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    user = service.authenticate(
        email=email,
        password=password,
    )

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Invalid email or password",
            },
            status_code=401,
        )

    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    request.session["user_role"] = user.role

    return RedirectResponse(
        url="/dashboard",
        status_code=303,
    )


@router.post("/logout")
async def logout(
    request: Request,
):
    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=303,
    )
