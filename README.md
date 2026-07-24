# Hospital Appointment Management System

A backend system design project for managing hospital appointments using **FastAPI** and **PostgreSQL** concepts. This repository focuses on the analysis, design, and documentation of an appointment management module, including workflow, database design, REST API planning, authentication, and project architecture.

---

## Project Overview

The Hospital Appointment Management System is designed to streamline the process of booking and managing patient appointments. It covers the complete appointment lifecycle, database schema, business rules, API design, authentication, search functionality, and backend project organization.

The project serves as a blueprint for developing a scalable hospital appointment management application.

---

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- JWT Authentication
- Draw.io
- dbdiagram.io
- Git & GitHub

---

## Project Features

- Patient Registration
- Doctor & Department Management
- Appointment Booking
- Appointment Confirmation
- Appointment Cancellation
- Appointment Rescheduling
- Appointment Workflow Design
- Database Schema Design
- Entity Relationship Diagram
- Business Rules
- REST API Design
- Authentication & Authorization
- Search & Filtering
- Error Handling
- Performance & Scalability Planning

---

# Appointment Workflow

The workflow below illustrates the complete appointment lifecycle from patient registration to appointment completion.

<p align="center">
  <img src="diagrams/appointment-workflow.png" alt="Appointment Workflow" width="900">
</p>

---

# Entity Relationship Diagram

The ER diagram represents the relationships between Departments, Doctors, Patients, and Appointments.

<p align="center">
  <img src="diagrams/er-diagram.png" alt="ER Diagram" width="900">
</p>

---

## Project Structure

```text
Hospital-appointment-management/
│
├── README.md
│
├── api/
│   └── endpoints.md
│
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── database/
│   ├── schema.sql
│   └── relationships.md
│
├── diagrams/
│   ├── appointment-workflow.png
│   └── er-diagram.png
│
└── docs/
    ├── appointment-workflow.md
    ├── authentication.md
    ├── business-rules.md
    ├── database-design.md
    ├── error-handling.md
    ├── performance.md
    ├── project-structure.md
    └── search-filtering.md
```

---

## Documentation

The repository includes documentation for:

- Appointment Workflow
- Database Design
- Database Relationships
- Business Rules
- REST API Design
- Authentication & Authorization
- Search & Filtering
- Error Handling
- FastAPI Project Structure
- Performance & Scalability

---

## Database

The database design consists of the following entities:

- Departments
- Doctors
- Patients
- Appointments

The SQL schema and relationships are documented in the `database` folder.

---

## REST API

The API documentation includes endpoints for:

- Departments
- Doctors
- Patients
- Appointments

Each endpoint includes:

- HTTP Method
- Request Body
- Response Body
- Validation Rules
- Error Responses
- Status Codes

---

## Backend Structure

The backend follows a modular FastAPI architecture with separate folders for:

- Routers
- Models
- Schemas
- Services
- Repositories
- Authentication
- Middleware
- Exception Handling
- Utilities

This structure improves maintainability and scalability for future development.


---

## Author

**Aastha Shukla**

---

## Academic Note

This project was prepared as part of an academic assignment to understand the design and architecture of a Hospital Appointment Management System. It focuses on system analysis, database design, API planning, and backend project organization using FastAPI and PostgreSQL concepts.