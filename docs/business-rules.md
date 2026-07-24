# Business Rules

## Objective

Business rules define the conditions and constraints that the Hospital Appointment Management System must follow to ensure accurate appointment scheduling and efficient hospital operations.

## Business Rules

### 1. Patient Registration

- A patient must be registered before booking an appointment.
- Each patient is assigned a unique UHID (Unique Hospital ID).

### 2. Doctor Availability

- A patient can book appointments only with active doctors.
- Doctors are assigned to a specific department.

### 3. Appointment Booking

- An appointment can be booked only for available time slots.
- The system generates a unique appointment number for every booking.
- Appointment date and time cannot be in the past.

### 4. Double Booking Prevention

- A doctor cannot have two appointments at the same date and time.
- A patient cannot book multiple appointments for the same time slot.

### 5. Appointment Status

An appointment can have one of the following statuses:

- Scheduled
- Completed
- Cancelled
- Rescheduled

### 6. Cancellation

- Patients can cancel appointments before the consultation begins.
- A cancelled appointment frees the time slot for another patient.

### 7. Rescheduling

- Patients can reschedule appointments based on doctor availability.
- A new confirmation is generated after rescheduling.

### 8. Data Integrity

- Every appointment must be linked to a valid patient.
- Every appointment must be linked to a valid doctor.
- Every doctor must belong to a valid department.

### 9. Security

- Only authorized users can modify appointment details.
- Patients can view only their own appointments.
- Hospital staff can manage appointments based on their role.