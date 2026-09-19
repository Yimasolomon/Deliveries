# Delivery Dashboard

A web-based delivery management system for managing customers, drivers, deliveries, delivery status, and reports.

## Features

* Dashboard with delivery statistics
* Customer management
* Driver management
* Delivery management
* Delivery status tracking
* Status history
* Search and filtering
* Delivery reports
* Responsive UI
* SQLite for local development
* PostgreSQL support for production
* Automated database migrations with Alembic
* Automated testing
* Docker deployment support
* Health and readiness checks
* Security headers and request logging

## Tech Stack

* Python
* FastAPI
* SQLAlchemy
* Alembic
* Jinja2
* SQLite
* PostgreSQL
* HTML / CSS / JavaScript
* Pytest
* Docker

## Project Structure

```text
Deliveries/
├── alembic/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── database_init.py
│   ├── models.py
│   ├── repositories.py
│   ├── schemas.py
│   ├── routes/
│   └── services/
├── static/
├── templates/
├── data/
├── conftest.py
├── Dockerfile
├── .dockerignore
├── .env.example
├── alembic.ini
├── requirements.txt
├── seed.py
└── README.md
```

## Local Setup

Clone the repository:

```bash
git clone https://github.com/Yimasolomon/Deliveries.git
cd Deliveries
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

## Database

SQLite is used automatically for local development.

Initialize or migrate the database:

```bash
alembic upgrade head
```

Optional development seed data:

```bash
python seed.py
```

## Run the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Health Checks

Application health:

```text
GET /health
```

Database readiness:

```text
GET /ready
```

`/health` confirms that the application is running.

`/ready` verifies that the application can communicate with the database.

## Testing

Run the complete test suite:

```bash
pytest -q
```

Latest verified result:

```text
99 passed
```

## Production Configuration

Production should use PostgreSQL rather than the local SQLite database.

Set the following environment variables:

```env
APP_ENV=production
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
PORT=8080
```

Do not commit `.env` or production credentials to Git.

## Production Database Migration

Production databases are managed with Alembic.

Before starting the application for the first time:

```bash
alembic upgrade head
```

Check the current migration:

```bash
alembic current
```

The application does not automatically create database tables when `APP_ENV=production`.

## Docker

Build the production image:

```bash
docker build -t delivery-dashboard .
```

Run the container:

```bash
docker run --env-file .env -p 8080:8080 delivery-dashboard
```

The application will be available at:

```text
http://127.0.0.1:8080
```

For production deployments, configure the hosting platform with the required environment variables and run the Alembic migration before starting the application.

## Production Server

The production container runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The application listens on port `8080`.

## Security and Observability

The application includes:

* Security response headers
* Request logging
* Exception logging
* Database readiness checks
* Environment-based configuration
* Production database migrations

Sensitive values such as database credentials must be supplied through environment variables.

## Status

Production hardening completed and merged.

Current project status:

* Core application: completed
* Database migrations: completed
* Production configuration: completed
* Security hardening: completed
* Request logging: completed
* Health/readiness checks: completed
* Docker deployment configuration: completed
* Final production verification: pending
