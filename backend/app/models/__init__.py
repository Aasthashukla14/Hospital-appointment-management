"""
Import every ORM model here so that `Base.metadata` is fully populated
before Alembic autogenerate or `Base.metadata.create_all()` runs.
"""
from app.models.user import User, UserRole  # noqa: F401
from app.models.patient import Patient, Gender, PatientStatus  # noqa: F401
from app.models.department import Department, DepartmentStatus  # noqa: F401
from app.models.doctor import Doctor, DoctorStatus  # noqa: F401
from app.models.appointment import (  # noqa: F401
    Appointment,
    AppointmentType,
    AppointmentPriority,
    AppointmentStatus,
)
from app.models.audit_log import AuditLog, AuditAction  # noqa: F401
