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