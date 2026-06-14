# Real-Time Production Monitoring System using FastAPI, PostgreSQL and Docker

## Overview

Production Monitoring System is a web-based application developed to monitor and manage production lines in real-time.

The system was designed to replace a Microsoft Access based solution and provide a modern, scalable, and centralized platform for production tracking.

The application supports multiple production lines, serial number registration, production monitoring, factory dashboard visualization, order code management, and AIO-equivalent production calculations.

---

## Features

### User Authentication

* Login page
* User role management
* Operator accounts per production line
* Supervisor and Manager accounts

### Production Registration

* Order Number scanning
* Serial Number scanning
* Duplicate serial validation
* Automatic product type detection

### Order Code Management

* Register new Order Codes
* Assign product types:

  * AIO
  * MNT
  * CASE
  * NB

### Production Monitoring

* Real-time production statistics
* Actual Production Count
* Expected Production Count
* Difference Calculation
* Line Stop Minutes
* Model Switch Count

### Factory Dashboard

* Real-time monitoring of all production lines
* Production comparison between lines
* Color-based status indicators
* Live updates

### AIO Equivalent Calculation

The system converts all product types into a unified AIO equivalent value.

Formula:

AIO = AIO

AIO = (MNT × 135) ÷ 225

AIO = (CASE × 180) ÷ 225

AIO = NB

Equivalent Factors:

* AIO = 1.00
* MNT = 0.60
* CASE = 0.80
* NB = 1.00

### Additional Features

* Live refresh
* Production counters
* Dashboard visualization
* Audio feedback after successful serial registration
* Date and Time display

---

## Technology Stack

Backend:

* Python
* FastAPI
* SQLAlchemy

Database:

* PostgreSQL

Frontend:

* HTML
* CSS
* JavaScript

Deployment:

* Docker

---

## Production Lines

The system currently supports 6 production lines.

Line 1

Line 2

Line 3

Line 4

Line 5

Line 6

---

## Future Improvements

* Excel Reporting
* PDF Reports
* Password Hashing
* Session Authentication
* Role Based Access Control
* KPI Dashboard
* Production Trend Charts
* Mobile Responsive Dashboard

---

## Getting Started

1. Create Virtual Environment
python -m venv venv

Activate virtual environment:

Windows:

venv\Scripts\activate

Linux / macOS:

source venv/bin/activate
2. Install Required Packages
pip install -r requirements.txt
3. Start PostgreSQL Database

Using Docker:

docker run -d \
--name production-db \
-e POSTGRES_PASSWORD=123456 \
-e POSTGRES_DB=production \
-p 5432:5432 \
postgres
4. Configure Database Connection

Open:

database.py

Update database connection string if needed.

Example:

DATABASE_URL = "postgresql://postgres:123456@localhost:5432/production"
5. Start Application
uvicorn app:app --reload
6. Open Application

Login Page:

http://127.0.0.1:8000

Swagger Documentation:

http://127.0.0.1:8000/docs

Factory Dashboard:

http://127.0.0.1:8000/dashboard

Order Code Management:

http://127.0.0.1:8000/ordercode

Production Monitor:

http://127.0.0.1:8000/monitor/1

## Initial Setup
Before using the system:

1. Start PostgreSQL database.
2. Start FastAPI application.
3. Open Order Code Management page.
4. Register Order Codes and Product Types.
5. Create user accounts.
6. Open production line page.
7. Start serial registration.

Important:

Order Codes must be registered before serial scanning. Otherwise the system will return:

Order Code Not Found

## V1.1 Release
Features:
- Role Based Authentication
- Admin Panel
- User Management
- Supervisor Panel
- Production Dashboard
- Order Code Management
- Stop & Switch Tracking
- Excel Export
- Daily Backup


## Author

BlackRoot
