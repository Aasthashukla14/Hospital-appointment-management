# Authentication and Authorization

## Objective

Authentication verifies the identity of users, while authorization controls what actions they are allowed to perform within the Hospital Appointment Management System.

---

## Authentication

The system uses **JWT (JSON Web Token)** based authentication.

### Login Process

1. User enters username and password.
2. The system validates the credentials.
3. If the credentials are valid, a JWT access token is generated.
4. The token is sent to the client.
5. The client includes the token in the Authorization header for future API requests.

Example:

Authorization: Bearer <JWT_TOKEN>

---

## Authorization

The system supports role-based access control (RBAC).

### Admin

- Manage departments
- Manage doctors
- View all appointments
- Manage users

### Receptionist

- Register patients
- Book appointments
- Cancel appointments
- Reschedule appointments
- View appointment schedules

### Doctor

- View assigned appointments
- Access patient details
- Mark appointments as completed

### Patient

- View personal appointments
- Book appointments
- Cancel appointments
- Reschedule appointments

---

## Security Features

- Passwords should be securely hashed.
- JWT tokens have an expiration time.
- Unauthorized users cannot access protected APIs.
- Role-based permissions restrict system access.