from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.dependencies import require_login
from app.models import User

from app.database import get_db
from app.models import Customer, Delivery, Driver
from app.services.delivery_service import (
    DeliveryService,
    DeliveryServiceError,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

router = APIRouter()

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

@router.get("/deliveries")
async def deliveries(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    service = DeliveryService(db)

    page_size = 10

    if page < 1:
        page = 1

    deliveries, total_deliveries = service.get_deliveries(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
    )

    total_pages = max(
        1,
        (total_deliveries + page_size - 1)
        // page_size,
    )

    if page > total_pages and total_deliveries > 0:
        page = total_pages

        deliveries, total_deliveries = service.get_deliveries(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
        )

    delayed_delivery_ids = {
        delivery.id
        for delivery in deliveries
        if service.is_delayed(delivery)
    }

    statuses = [
        "pending",
        "in_transit",
        "out_for_delivery",
        "delivered",
        "failed",
        "cancelled",
    ]

    return templates.TemplateResponse(
        request=request,
        name="deliveries.html",
        context={
            "request": request,
            "page_title": "Deliveries",
            "deliveries": deliveries,
            "search": search or "",
            "selected_status": status or "",
            "statuses": statuses,
            "delayed_delivery_ids": delayed_delivery_ids,
            "page": page,
            "page_size": page_size,
            "total_deliveries": total_deliveries,
            "total_pages": total_pages,
        },
    )


@router.get(
    "/deliveries/new",
    response_class=HTMLResponse,
)
async def new_delivery_form(
    request: Request,
    db: Session = Depends(get_db),
):
    customers = (
        db.query(Customer)
        .order_by(Customer.name)
        .all()
    )

    drivers = (
        db.query(Driver)
        .filter(Driver.status == "available")
        .order_by(Driver.name)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="delivery_form.html",
        context={
            "request": request,
            "page_title": "New Delivery",
            "customers": customers,
            "drivers": drivers,
            "error": None,
            "form_data": {},
        },
    )


@router.post("/deliveries")
async def create_delivery(
    request: Request,
    customer_id: int = Form(...),
    driver_id: int | None = Form(None),
    pickup_address: str = Form(...),
    delivery_address: str = Form(...),
    scheduled_at: str | None = Form(None),
    db: Session = Depends(get_db),
):
    scheduled_datetime = None

    if scheduled_at:
        try:
            scheduled_datetime = datetime.fromisoformat(
                scheduled_at
            )
        except ValueError:
            customers = (
                db.query(Customer)
                .order_by(Customer.name)
                .all()
            )

            drivers = (
                db.query(Driver)
                .filter(Driver.status == "available")
                .order_by(Driver.name)
                .all()
            )

            return templates.TemplateResponse(
                request=request,
                name="delivery_form.html",
                context={
                    "request": request,
                    "page_title": "New Delivery",
                    "customers": customers,
                    "drivers": drivers,
                    "error": "Invalid scheduled date and time.",
                    "form_data": {
                        "customer_id": customer_id,
                        "driver_id": driver_id,
                        "pickup_address": pickup_address,
                        "delivery_address": delivery_address,
                        "scheduled_at": scheduled_at,
                    },
                },
                status_code=400,
            )

    service = DeliveryService(db)

    try:
        delivery = service.create_delivery(
            customer_id=customer_id,
            driver_id=driver_id,
            pickup_address=pickup_address,
            delivery_address=delivery_address,
            scheduled_at=scheduled_datetime,
        )

        return RedirectResponse(
            url=f"/deliveries/{delivery.id}",
            status_code=303,
        )

    except DeliveryServiceError as exc:
        customers = (
            db.query(Customer)
            .order_by(Customer.name)
            .all()
        )

        drivers = (
            db.query(Driver)
            .filter(Driver.status == "available")
            .order_by(Driver.name)
            .all()
        )

        return templates.TemplateResponse(
            request=request,
            name="delivery_form.html",
            context={
                "request": request,
                "page_title": "New Delivery",
                "customers": customers,
                "drivers": drivers,
                "error": str(exc),
                "form_data": {
                    "customer_id": customer_id,
                    "driver_id": driver_id,
                    "pickup_address": pickup_address,
                    "delivery_address": delivery_address,
                    "scheduled_at": scheduled_at,
                },
            },
            status_code=400,
        )


@router.get(
    "/deliveries/{delivery_id}",
    response_class=HTMLResponse,
)
async def delivery_detail(
    request: Request,
    delivery_id: int,
    db: Session = Depends(get_db),
):
    delivery = (
        db.query(Delivery)
        .options(
            joinedload(Delivery.customer),
            joinedload(Delivery.driver),
        )
        .filter(Delivery.id == delivery_id)
        .first()
    )

    if delivery is None:
        return HTMLResponse(
            content="Delivery not found",
            status_code=404,
        )

    service = DeliveryService(db)
    history = service.get_status_history(delivery_id)
    allowed_statuses = service.ALLOWED_TRANSITIONS.get(
        delivery.status,
        set(),
    )

    return templates.TemplateResponse(
        request=request,
        name="delivery_detail.html",
        context={
            "request": request,
            "page_title": f"Delivery {delivery.tracking_number}",
            "delivery": delivery,
            "history": history,
            "allowed_statuses": allowed_statuses,
        },
    )


@router.get(
    "/deliveries/{delivery_id}/edit",
    response_class=HTMLResponse,
)
async def edit_delivery_form(
    request: Request,
    delivery_id: int,
    db: Session = Depends(get_db),
):
    service = DeliveryService(db)

    try:
        delivery = service.get_delivery(delivery_id)

    except DeliveryServiceError:
        return HTMLResponse(
            content="Delivery not found",
            status_code=404,
        )

    customers = (
        db.query(Customer)
        .order_by(Customer.name)
        .all()
    )

    drivers = (
        db.query(Driver)
        .filter(
            (Driver.status == "available")
            | (Driver.id == delivery.driver_id)
        )
        .order_by(Driver.name)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="delivery_edit.html",
        context={
            "request": request,
            "page_title": f"Edit {delivery.tracking_number}",
            "delivery": delivery,
            "customers": customers,
            "drivers": drivers,
            "error": None,
        },
    )


@router.post("/deliveries/{delivery_id}/edit")
async def edit_delivery(
    request: Request,
    delivery_id: int,
    customer_id: int = Form(...),
    driver_id: int | None = Form(None),
    pickup_address: str = Form(...),
    delivery_address: str = Form(...),
    scheduled_at: str | None = Form(None),
    db: Session = Depends(get_db),
):
    service = DeliveryService(db)

    parsed_scheduled_at = None

    if scheduled_at:
        try:
            parsed_scheduled_at = datetime.fromisoformat(
                scheduled_at
            )
        except ValueError:
            parsed_scheduled_at = None

    try:
        service.update_delivery(
            delivery_id=delivery_id,
            customer_id=customer_id,
            driver_id=driver_id,
            pickup_address=pickup_address,
            delivery_address=delivery_address,
            scheduled_at=parsed_scheduled_at,
        )

        return RedirectResponse(
            url=f"/deliveries/{delivery_id}",
            status_code=303,
        )

    except DeliveryServiceError as exc:
        delivery = service.get_delivery(delivery_id)

        customers = (
            db.query(Customer)
            .order_by(Customer.name)
            .all()
        )

        drivers = (
            db.query(Driver)
            .order_by(Driver.name)
            .all()
        )

        return templates.TemplateResponse(
            request=request,
            name="delivery_edit.html",
            context={
                "request": request,
                "page_title": f"Edit {delivery.tracking_number}",
                "delivery": delivery,
                "customers": customers,
                "drivers": drivers,
                "error": str(exc),
            },
            status_code=400,
        )


@router.post("/deliveries/{delivery_id}/status")
async def update_delivery_status(
    request: Request,
    delivery_id: int,
    status: str = Form(...),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
):
    service = DeliveryService(db)

    try:
        service.update_status(
            delivery_id=delivery_id,
            new_status=status,
            note=note,
        )

        return RedirectResponse(
            url=f"/deliveries/{delivery_id}",
            status_code=303,
        )

    except DeliveryServiceError as exc:
        delivery = (
            db.query(Delivery)
            .options(
                joinedload(Delivery.customer),
                joinedload(Delivery.driver),
            )
            .filter(Delivery.id == delivery_id)
            .first()
        )

        if delivery is None:
            return HTMLResponse(
                content="Delivery not found",
                status_code=404,
            )

        history = service.get_status_history(delivery_id)
        allowed_statuses = service.ALLOWED_TRANSITIONS.get(
            delivery.status,
            set(),
        )

        return templates.TemplateResponse(
            request=request,
            name="delivery_detail.html",
            context={
                "request": request,
                "page_title": f"Delivery {delivery.tracking_number}",
                "delivery": delivery,
                "history": history,
                "allowed_statuses": allowed_statuses,
                "error": str(exc),
            },
            status_code=400,
        )


@router.post("/deliveries/{delivery_id}/delete")
async def delete_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
):
    service = DeliveryService(db)

    try:
        service.cancel_delivery(
            delivery_id=delivery_id,
            note="Delivery cancelled by user.",
        )

        return RedirectResponse(
            url="/deliveries",
            status_code=303,
        )

    except DeliveryServiceError as exc:
        return HTMLResponse(
            content=str(exc),
            status_code=400,
        )
