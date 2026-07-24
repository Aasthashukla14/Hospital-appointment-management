# REST API Design

## Overview

The Hospital Appointment Management System exposes RESTful APIs to manage patients, doctors, departments, and appointments.

---

## Department APIs

### Get All Departments

- **Method:** GET
- **Endpoint:** `/departments`

### Get Department by ID

- **Method:** GET
- **Endpoint:** `/departments/{id}`

---

## Doctor APIs

### Get All Doctors

- **Method:** GET
- **Endpoint:** `/doctors`

### Get Doctor by ID

- **Method:** GET
- **Endpoint:** `/doctors/{id}`

### Get Doctors by Department

- **Method:** GET
- **Endpoint:** `/departments/{id}/doctors`

---

## Patient APIs

### Register Patient

- **Method:** POST
- **Endpoint:** `/patients`

### Get Patient Details

- **Method:** GET
- **Endpoint:** `/patients/{id}`

### Update Patient

- **Method:** PUT
- **Endpoint:** `/patients/{id}`

---

## Appointment APIs

### Book Appointment

- **Method:** POST
- **Endpoint:** `/appointments`

### Get Appointment

- **Method:** GET
- **Endpoint:** `/appointments/{id}`

### Get All Appointments

- **Method:** GET
- **Endpoint:** `/appointments`

### Update Appointment

- **Method:** PUT
- **Endpoint:** `/appointments/{id}`

### Cancel Appointment

- **Method:** DELETE
- **Endpoint:** `/appointments/{id}`

### Reschedule Appointment

- **Method:** PATCH
- **Endpoint:** `/appointments/{id}/reschedule`