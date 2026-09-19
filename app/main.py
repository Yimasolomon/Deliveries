from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.database_init import init_db
from app.models import Customer, Delivery, Driver
from app.routes.dashboard import router as dashboard_router
from app.routes.reports import router as reports_router
from app.services.customer_service import (
    CustomerNotFoundError,
    CustomerService,
    CustomerServiceError,
)
from app.services.delivery_service import (
    DeliveryService,
    DeliveryServiceError,
)

from app.services.driver_service import (
    DriverNotFoundError,
    DriverService,
    DriverServiceError,
    DuplicateDriverError,
    InvalidDriverDataError,
    InvalidDriverStatusError,
)

BASE_DIR = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Delivery Tracking Dashboard",
    description="Delivery management system",
    version="0.1.0",
    lifespan=lifespan,
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
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    service = DeliveryService(db)

    page_size = 10

    if page < 1:
        page = 1

    deliveries, total_deliveries = (
        service.get_deliveries(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
        )
    )

    total_pages = max(
        1,
        (total_deliveries + page_size - 1)
        // page_size,
    )

    # If a user requests a page beyond the final page,
    # show the final valid page.
    if page > total_pages and total_deliveries > 0:
        page = total_pages

        deliveries, total_deliveries = (
            service.get_deliveries(
                page=page,
                page_size=page_size,
                search=search,
                status=status,
            )
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

            # Pagination
            "page": page,
            "page_size": page_size,
            "total_deliveries": total_deliveries,
            "total_pages": total_pages,
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

@app.get(
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
            "page_title": (
                f"Edit {delivery.tracking_number}"
            ),
            "delivery": delivery,
            "customers": customers,
            "drivers": drivers,
            "error": None,
        },
    )

@app.post("/deliveries/{delivery_id}/edit")
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
                "page_title": (
                    f"Edit {delivery.tracking_number}"
                ),
                "delivery": delivery,
                "customers": customers,
                "drivers": drivers,
                "error": str(exc),
            },
            status_code=400,
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
        allowed_statuses = service.ALLOWED_TRANSITIONS.get(
            delivery.status,
            set(),
        )

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
                "allowed_statuses": allowed_statuses,
                "error": str(exc),
            },
            status_code=400,
        )

app.include_router(
    dashboard_router
)
app.include_router(
    reports_router
)

@app.post("/deliveries/{delivery_id}/delete")
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

@app.get("/customers", response_class=HTMLResponse)
async def customers_page(
    request: Request,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    customers = service.get_customers(search)

    return templates.TemplateResponse(
        request=request,
        name="customers.html",
        context={
            "request": request,
            "page_title": "Customers",
            "customers": customers,
            "search": search or "",
        },
    )

@app.get(
    "/customers/new",
    response_class=HTMLResponse,
)
async def new_customer_form(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="customer_form.html",
        context={
            "request": request,
            "page_title": "New Customer",
            "customer": None,
            "error": None,
        },
    )

@app.post("/customers")
async def create_customer(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    email: str | None = Form(None),
    address: str = Form(...),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    try:
        customer = service.create_customer(
            name=name,
            phone=phone,
            email=email,
            address=address,
        )

        return RedirectResponse(
            url=f"/customers/{customer.id}",
            status_code=303,
        )

    except CustomerServiceError as exc:
        return templates.TemplateResponse(
            request=request,
            name="customer_form.html",
            context={
                "request": request,
                "page_title": "New Customer",
                "customer": None,
                "error": str(exc),
                "form_data": {
                    "name": name,
                    "phone": phone,
                    "email": email or "",
                    "address": address,
                },
            },
            status_code=400,
        )


@app.get("/customers/{customer_id}", response_class=HTMLResponse)
def customer_detail(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    try:
        customer = service.get_customer(customer_id)
        deliveries = service.get_customer_deliveries(customer_id)
        stats = service.get_customer_stats(customer_id)
    except CustomerNotFoundError:
        return HTMLResponse(
            content="Customer not found.",
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="customer_detail.html",
        context={
            "request": request,
            "page_title": customer.name,
            "customer": customer,
            "deliveries": deliveries,
            "stats": stats,
        },
    )

@app.get(
    "/customers/{customer_id}/edit",
    response_class=HTMLResponse,
)
async def edit_customer_form(
    request: Request,
    customer_id: int,
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    try:
        customer = service.get_customer(customer_id)

    except CustomerNotFoundError:
        return HTMLResponse(
            content="Customer not found",
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="customer_edit.html",
        context={
            "request": request,
            "page_title": f"Edit {customer.name}",
            "customer": customer,
            "error": None,
        },
    )

@app.post("/customers/{customer_id}/edit")
async def edit_customer(
    request: Request,
    customer_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    email: str | None = Form(None),
    address: str = Form(...),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    try:
        service.update_customer(
            customer_id=customer_id,
            name=name,
            phone=phone,
            email=email,
            address=address,
        )

        return RedirectResponse(
            url=f"/customers/{customer_id}",
            status_code=303,
        )

    except CustomerServiceError as exc:
        try:
            customer = service.get_customer(customer_id)
        except CustomerNotFoundError:
            return HTMLResponse(
                content="Customer not found",
                status_code=404,
            )

        return templates.TemplateResponse(
            request=request,
            name="customer_edit.html",
            context={
                "request": request,
                "page_title": f"Edit {customer.name}",
                "customer": customer,
                "error": str(exc),
            },
            status_code=400,
        )

@app.get("/drivers", response_class=HTMLResponse)
def drivers_page(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    service = DriverService(db)

    drivers = service.get_drivers(
        search=search,
        status=status,
    )

    return templates.TemplateResponse(
        request=request,
        name="drivers.html",
        context={
            "request": request,
            "drivers": drivers,
            "search": search or "",
            "status": status or "",
        },
    )

@app.get("/drivers/new", response_class=HTMLResponse)
def new_driver_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="driver_form.html",
        context={
            "request": request,
        },
    )

@app.post("/drivers", response_class=HTMLResponse)
def create_driver(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    vehicle_type: str = Form(...),
    vehicle_number: str = Form(...),
    status: str = Form("available"),
    db: Session = Depends(get_db),
):
    service = DriverService(db)

    try:
        driver = service.create_driver(
            name=name,
            phone=phone,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            status=status,
        )

        return RedirectResponse(
            url=f"/drivers/{driver.id}",
            status_code=303,
        )

    except (
        DuplicateDriverError,
        InvalidDriverDataError,
        InvalidDriverStatusError,
        DriverServiceError,
    ) as exc:
        return templates.TemplateResponse(
            request=request,
            name="driver_form.html",
            context={
                "request": request,
                "driver": {
                    "name": name,
                    "phone": phone,
                    "vehicle_type": vehicle_type,
                    "vehicle_number": vehicle_number,
                    "status": status,
                },
                "error": str(exc),
            },
            status_code=400,
        )

@app.get("/drivers/{driver_id}", response_class=HTMLResponse)
def driver_detail(
    driver_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    service = DriverService(db)

    try:
        driver = service.get_driver(driver_id)
        deliveries = service.get_driver_deliveries(driver_id)
        stats = service.get_driver_stats(driver_id)

    except DriverNotFoundError:
        return HTMLResponse(
            content="Driver not found.",
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="driver_detail.html",
        context={
            "request": request,
            "driver": driver,
            "deliveries": deliveries,
            "stats": stats,
        },
    )

@app.get("/drivers/{driver_id}/edit", response_class=HTMLResponse)
def edit_driver_page(
    driver_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    service = DriverService(db)

    try:
        driver = service.get_driver(driver_id)

    except DriverNotFoundError:
        return HTMLResponse(
            content="Driver not found.",
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="driver_edit.html",
        context={
            "request": request,
            "driver": driver,
        },
    )

@app.post("/drivers/{driver_id}/edit", response_class=HTMLResponse)
def edit_driver(
    driver_id: int,
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    vehicle_type: str = Form(...),
    vehicle_number: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    service = DriverService(db)

    try:
        driver = service.update_driver(
            driver_id=driver_id,
            name=name,
            phone=phone,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            status=status,
        )

        return RedirectResponse(
            url=f"/drivers/{driver.id}",
            status_code=303,
        )

    except DriverNotFoundError:
        return HTMLResponse(
            content="Driver not found.",
            status_code=404,
        )

    except (
        DuplicateDriverError,
        InvalidDriverDataError,
        InvalidDriverStatusError,
        DriverServiceError,
    ) as exc:
        try:
            driver = service.get_driver(driver_id)
        except DriverNotFoundError:
            return HTMLResponse(
                content="Driver not found.",
                status_code=404,
            )

        return templates.TemplateResponse(
            "driver_edit.html",
            {
                "request": request,
                "driver": driver,
                "error": str(exc),
            },
            status_code=400,
        )

@app.post("/drivers/{driver_id}/status")
def update_driver_status(
    driver_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    service = DriverService(db)

    try:
        service.update_status(
            driver_id=driver_id,
            status=status,
        )

        return RedirectResponse(
            url=f"/drivers/{driver_id}",
            status_code=303,
        )

    except DriverNotFoundError:
        return HTMLResponse(
            content="Driver not found.",
            status_code=404,
        )

    except InvalidDriverStatusError as exc:
        return HTMLResponse(
            content=str(exc),
            status_code=400,
        )