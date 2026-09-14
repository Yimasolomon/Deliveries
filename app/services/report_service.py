from sqlalchemy.orm import Session

from app.repositories import (
    CustomerRepository,
    DeliveryRepository,
    DriverRepository,
)
from app.services.delivery_service import DeliveryService


class ReportService:
    def __init__(self, db: Session):
        self.delivery_repository = DeliveryRepository(db)
        self.customer_repository = CustomerRepository(db)
        self.driver_repository = DriverRepository(db)
        self.delivery_service = DeliveryService(db)

    def get_delivery_summary(self) -> dict[str, int]:
        deliveries = self.delivery_repository.get_all()

        summary = {
            "total": len(deliveries),
            "pending": 0,
            "in_transit": 0,
            "out_for_delivery": 0,
            "delivered": 0,
            "failed": 0,
            "cancelled": 0,
            "delayed": 0,
        }

        for delivery in deliveries:
            status = delivery.status

            if status in summary:
                summary[status] += 1

            if self.delivery_service.is_delayed(delivery):
                summary["delayed"] += 1

        return summary

    def get_people_summary(self) -> dict[str, int]:
        return {
            "total_customers": len(self.customer_repository.get_all()),
            "total_drivers": len(self.driver_repository.get_all()),
        }