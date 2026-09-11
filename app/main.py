from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.database_init import init_db
from app.models import Delivery
from app.routes.dashboard import router as dashboard_router

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.models import Customer, Delivery, Driver
from app.services.delivery_service import (
    DeliveryService,
    DeliveryServiceError,
)


BASE_DIR = Path(__file__).resolve().parent.parent


app = FastAPI(
    title="Delivery Tracking Dashboard",
    description="Delivery management system",
    version="0.1.0",
)


templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


app.mount(
    "/static",
    StaticFiles(
        directory=str(BASE_DIR / "static")
    ),
    name="static",
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
async def root():
    return RedirectResponse(
        url="/dashboard",
        status_code=307,
    )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
    }


@app.get(
    "/deliveries",
    response_class=HTMLResponse,
)
async def deliveries(
    request: Request,
    db: Session = Depends(get_db),
):
    deliveries = (
        db.query(Delivery)
        .options(
            joinedload(Delivery.customer),
            joinedload(Delivery.driver),
        )
        .order_by(Delivery.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="deliveries.html",
        context={
            "request": request,
            "page_title": "Deliveries",
            "deliveries": deliveries,
        },
    )

@app.get("/deliveries/new", response_class=HTMLResponse)
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


@app.post("/deliveries")
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
            from datetime import datetime

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


@app.get("/deliveries/{delivery_id}", response_class=HTMLResponse)
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

    return templates.TemplateResponse(
        request=request,
        name="delivery_detail.html",
        context={
            "request": request,
            "page_title": f"Delivery {delivery.tracking_number}",
            "delivery": delivery,
            "history": history,
        },
    )

@app.post("/deliveries/{delivery_id}/status")
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

        return templates.TemplateResponse(
            request=request,
            name="delivery_detail.html",
            context={
                "request": request,
                "page_title": (
                    f"Delivery {delivery.tracking_number}"
                ),
                "delivery": delivery,
                "history": history,
                "error": str(exc),
            },
            status_code=400,
        )

app.include_router(
    dashboard_router
)
