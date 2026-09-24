import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.session import add_session_middleware

from app.database import get_db
from app.database_init import init_db
from app.models import Customer, Driver
from app.routes.dashboard import router as dashboard_router
from app.routes.deliveries import router as deliveries_router
from app.routes.reports import router as reports_router
from app.services.customer_service import (
    CustomerNotFoundError,
    CustomerService,
    CustomerServiceError,
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Delivery Tracking Dashboard",
    version="0.1.0",
    lifespan=lifespan,
)
add_session_middleware(app)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - start_time

        logger.exception(
            "Request failed: %s %s (%.3fs)",
            request.method,
            request.url.path,
            duration,
        )

        raise

    duration = time.perf_counter() - start_time

    logger.info(
        "Request: %s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response


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


@app.get("/ready")
async def readiness_check(
    db: Session = Depends(get_db),
):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ready",
        }

    except Exception:
        logger.exception("Readiness check failed")

        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
            },
        )


# Register application routers.
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(deliveries_router)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


@app.get(
    "/customers",
    response_class=HTMLResponse,
)
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


@app.get(
    "/customers/{customer_id}",
    response_class=HTMLResponse,
)
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


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------


@app.get(
    "/drivers",
    response_class=HTMLResponse,
)
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


@app.get(
    "/drivers/new",
    response_class=HTMLResponse,
)
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


@app.post(
    "/drivers",
    response_class=HTMLResponse,
)
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


@app.get(
    "/drivers/{driver_id}",
    response_class=HTMLResponse,
)
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


@app.get(
    "/drivers/{driver_id}/edit",
    response_class=HTMLResponse,
)
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


@app.post(
    "/drivers/{driver_id}/edit",
    response_class=HTMLResponse,
)
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
            request=request,
            name="driver_edit.html",
            context={
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