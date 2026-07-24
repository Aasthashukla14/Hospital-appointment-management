# Database Design

## Objective

The Appointment Management Module uses a relational database to store and manage information related to patients, doctors, departments, and appointments.

The database is designed using PostgreSQL and follows normalization principles to reduce redundancy, maintain data integrity, and improve query performance.

## Main Entities

The system contains four main entities:

1. Department
2. Doctor
3. Patient
4. Appointment

Each entity represents an important part of the appointment booking process and is connected through relationships using primary and foreign keys.


## Department Entity

The Department entity stores information about hospital departments such as Cardiology, Neurology, and Orthopedics.

### Attributes

- id (Primary Key)
- department_name
- description
- status

A department can have multiple doctors.

---

## Doctor Entity

The Doctor entity stores information about doctors working in different departments.

### Attributes

- id (Primary Key)
- employee_id
- full_name
- department_id (Foreign Key)
- specialization
- consultation_fee
- phone
- email
- status

Each doctor belongs to one department.

---

## Patient Entity

The Patient entity stores personal and contact information of registered patients. Each patient is identified by a unique UHID (Unique Hospital ID), which is used throughout the hospital system.

### Attributes

- id (Primary Key)
- uhid (Unique)
- first_name
- last_name
- gender
- date_of_birth
- phone
- email
- address
- status

A patient can book multiple appointments with different doctors.

---

## Appointment Entity

The Appointment entity records every appointment booked in the hospital system. It connects patients, doctors, and departments through foreign keys.

### Attributes

- id (Primary Key)
- appointment_number (Unique)
- patient_id (Foreign Key)
- doctor_id (Foreign Key)
- department_id (Foreign Key)
- appointment_date
- appointment_time
- duration_minutes
- appointment_type
- priority
- reason
- status
- created_at

Each appointment belongs to one patient, one doctor, and one department.