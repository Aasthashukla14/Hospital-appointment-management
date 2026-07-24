# Database Relationships

## Overview

The Hospital Appointment Management System uses a relational database to maintain data integrity and establish relationships between departments, doctors, patients, and appointments.

---

## Entity Relationships

### 1. Department → Doctor (One-to-Many)

One department can have multiple doctors, but each doctor belongs to only one department.

**Relationship:**

Department (1) → Doctor (Many)

**Foreign Key:**

- `doctors.department_id` references `departments.id`

---

### 2. Doctor → Appointment (One-to-Many)

A doctor can have many appointments, but each appointment is assigned to only one doctor.

**Relationship:**

Doctor (1) → Appointment (Many)

**Foreign Key:**

- `appointments.doctor_id` references `doctors.id`

---

### 3. Patient → Appointment (One-to-Many)

A patient can book multiple appointments over time, but each appointment belongs to one patient.

**Relationship:**

Patient (1) → Appointment (Many)

**Foreign Key:**

- `appointments.patient_id` references `patients.id`

---

### 4. Department → Appointment (One-to-Many)

Each appointment is associated with one department through the selected doctor.

**Relationship:**

Department (1) → Appointment (Many)

**Foreign Key:**

- `appointments.department_id` references `departments.id`

---

## Constraints

The database uses constraints to maintain data integrity.

- Primary Keys uniquely identify each record.
- Foreign Keys ensure valid relationships between tables.
- Unique constraints prevent duplicate UHIDs, Employee IDs, and Appointment Numbers.
- NOT NULL constraints ensure required information is always provided.

---

## Indexes

Indexes improve query performance by speeding up searches on frequently used columns.

Recommended indexes:

- `patient_id`
- `doctor_id`
- `department_id`
- `appointment_date`
- `appointment_number`

---

## Cascading Rules

To maintain referential integrity:

- A department should not be deleted if doctors are assigned to it.
- A doctor should not be deleted if appointments exist.
- A patient should not be deleted if appointment history must be preserved.
- Updates to referenced records should maintain valid relationships.

---

## ER Diagram

The Entity Relationship Diagram (ERD) in the `diagrams` folder visually represents these relationships.
