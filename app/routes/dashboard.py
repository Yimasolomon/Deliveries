from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Delivery

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count(Delivery.id))
    ) or 0

    pending = db.scalar(
        select(func.count(Delivery.id))
        .where(Delivery.status == "pending")
    ) or 0

    in_transit = db.scalar(
        select(func.count(Delivery.id))
        .where(Delivery.status == "in_transit")
    ) or 0

    out_for_delivery = db.scalar(
        select(func.count(Delivery.id))
        .where(Delivery.status == "out_for_delivery")
    ) or 0

    delivered = db.scalar(
        select(func.count(Delivery.id))
        .where(Delivery.status == "delivered")
    ) or 0

    failed = db.scalar(
        select(func.count(Delivery.id))
        .where(Delivery.status == "failed")
    ) or 0

    delayed = db.scalar(
        select(func.count(Delivery.id))
        .where(
            Delivery.scheduled_at < datetime.utcnow(),
            Delivery.status.notin_(
                ["delivered", "failed", "cancelled"]
            ),
        )
    ) or 0

    recent_deliveries = list(
        db.scalars(
            select(Delivery)
            .options(
                joinedload(Delivery.customer),
                joinedload(Delivery.driver),
            )
            .order_by(Delivery.created_at.desc())
            .limit(10)
        ).unique()
    )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page_title": "Dashboard",
            "total": total,
            "pending": pending,
            "in_transit": in_transit,
            "out_for_delivery": out_for_delivery,
            "delivered": delivered,
            "failed": failed,
            "delayed": delayed,
            "recent_deliveries": recent_deliveries,
        },
    )