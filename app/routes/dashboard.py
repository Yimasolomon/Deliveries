from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_login
from app.models import User
from app.services.dashboard_service import DashboardService


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)


@router.get("/dashboard")
async def dashboard(
    request: Request,
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)

    dashboard_data = service.get_dashboard_data()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "page_title": "Dashboard",
            "user": current_user,
            **dashboard_data,
        },
    )