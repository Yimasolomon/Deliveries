Delivery Dashboard
A web-based delivery management system for managing customers, drivers, deliveries, tracking delivery status, and viewing reports.

Features
Dashboard with delivery statistics

Customer management

Driver management

Delivery management

Delivery status tracking

Status history

Search and filtering

Delivery reports

Responsive and consistent UI

SQLite database

Automated testing

Tech Stack
Python

FastAPI

SQLAlchemy

Jinja2

SQLite

HTML / CSS / JavaScript

Pytest

Project Structure
Deliveries/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── repositories.py
│   ├── schemas.py
│   ├── routes/
│   └── services/
│
├── static/
├── templates/
├── conftest.py
├── requirements.txt
├── seed.py
└── README.md
Setup
Clone the repository:

git clone https://github.com/Yimasolomon/Deliveries.git
cd Deliveries
Create and activate a virtual environment:

python3 -m venv .venv
source .venv/bin/activate
Install dependencies:

pip install -r requirements.txt
Run the Application
Start the FastAPI server:

uvicorn app.main:app --reload
Open the application at:

http://127.0.0.1:8000
Testing
Run the complete test suite:

pytest -q
Current test result:

89 passed
Main Sections
Dashboard — Overview of deliveries, customers, and drivers

Deliveries — Create, view, update, and track deliveries

Customers — Manage customer information

Drivers — Manage drivers and availability

Reports — View delivery and people summaries

Status
Completed and merged. ✅

The project has been fully implemented, tested, and integrated successfully.