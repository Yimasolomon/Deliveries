from datetime import datetime

from pydantic import BaseModel, ConfigDict


# =========================
# Customer Schemas
# =========================

class CustomerBase(BaseModel):
    name: str
    phone: str
    email: str | None = None
    address: str


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================
# Driver Schemas
# =========================

class DriverBase(BaseModel):
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str
    status: str = "available"


class DriverCreate(DriverBase):
    pass


class DriverResponse(DriverBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================
# Delivery Schemas
# =========================

class DeliveryBase(BaseModel):
    pickup_address: str
    delivery_address: str
    status: str = "pending"
    scheduled_at: datetime | None = None


class DeliveryCreate(DeliveryBase):
    tracking_number: str
    customer_id: int
    driver_id: int | None = None


class DeliveryResponse(DeliveryBase):
    id: int
    tracking_number: str
    customer_id: int
    driver_id: int | None
    delivered_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

