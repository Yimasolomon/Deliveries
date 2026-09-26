from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.dependencies import require_login
from app.models import User
from app.services.report_service import ReportService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/reports")
async def reports(
    request: Request,
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    service = ReportService(db)

    delivery_summary = service.get_delivery_summary()
    people_summary = service.get_people_summary()

    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={
            "request": request,
            "page_title": "Reports",
            "user": current_user,
            **delivery_summary,
            **people_summary,
        },
    )