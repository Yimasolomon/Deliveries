from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.models import Delivery
from app.repositories import DashboardRepository
from app.services.delivery_service import DeliveryService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.dashboard = DashboardRepository(db)
        self.delivery_service = DeliveryService(db)

    def get_dashboard_data(self) -> dict[str, object]:
        deliveries = self.dashboard.get_all_deliveries()

        delayed_deliveries = [
            delivery
            for delivery in deliveries
            if self.delivery_service.is_delayed(delivery)
        ]

        recent_deliveries = self.dashboard.get_recent_deliveries(10)

        return {
            # Delivery statistics
            "total": self.dashboard.count_deliveries(),
            "pending": self.dashboard.count_deliveries_by_status(
                "pending"
            ),
            "in_transit": self.dashboard.count_deliveries_by_status(
                "in_transit"
            ),
            "out_for_delivery": self.dashboard.count_deliveries_by_status(
                "out_for_delivery"
            ),
            "delivered": self.dashboard.count_deliveries_by_status(
                "delivered"
            ),
            "failed": self.dashboard.count_deliveries_by_status(
                "failed"
            ),
            "cancelled": self.dashboard.count_deliveries_by_status(
                "cancelled"
            ),

            # Delayed deliveries are calculated dynamically.
            "delayed": len(delayed_deliveries),
            "delayed_deliveries": delayed_deliveries,

            # Recent activity
            "recent_deliveries": recent_deliveries,

            # Customer statistics
            "total_customers": self.dashboard.count_customers(),

            # Driver statistics
            "total_drivers": self.dashboard.count_drivers(),
            "available_drivers": self.dashboard.count_drivers_by_status(
                "available"
            ),
            "busy_drivers": self.dashboard.count_drivers_by_status(
                "busy"
            ),
            "unavailable_drivers": self.dashboard.count_drivers_by_status(
                "unavailable"
            ),
        }