from app.services.report_service import ReportService


def test_delivery_summary(db):
    service = ReportService(db)

    summary = service.get_delivery_summary()

    assert summary["total"] == 0
    assert summary["pending"] == 0
    assert summary["delivered"] == 0
    assert summary["delayed"] == 0


def test_people_summary(db):
    service = ReportService(db)

    summary = service.get_people_summary()

    assert summary["total_customers"] == 0
    assert summary["total_drivers"] == 0


def test_reports_page(route_client):
    client, _ = route_client

    response = client.get("/reports")

    assert response.status_code == 200
    assert "Reports" in response.text