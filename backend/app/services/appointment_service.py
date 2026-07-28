"""
Appointment service — business logic and workflow rules for the core
Appointment module.

Business rules implemented (per assignment spec):
    1. A doctor cannot have overlapping appointments.
    2. A patient cannot have multiple appointments at the same time.
    3. Appointment date cannot be in the past.
    4. Appointment duration is configurable (default from settings, 30 min).
    5. Inactive doctors cannot receive appointments.
    6. Cancelled (and no-show) slots become available again — enforced by
       excluding RELEASED_STATUSES from all overlap queries.
    7. Follow-up appointments must reference a previous appointment for the
       same patient.
    8. Emergency appointments may bypass the *doctor's* overlap restriction
       (a doctor can be double-booked to accommodate an emergency) but never
       bypass the *patient's* own double-booking restriction — a patient
       cannot physically be in two appointments at once regardless of
       urgency. Emergency bookings are logged distinctly for audit purposes.

RBAC (Part 4 addition):
    A caller with role DOCTOR is scoped to their own appointments only —
    they cannot list, read, book on behalf of, update, cancel, or
    reschedule another doctor's appointments, and patient-history lookups
    are filtered down to visits with that doctor only. All other roles
    (RECEPTIONIST, HOSPITAL_ADMIN, SUPER_ADMIN) are unscoped, matching the
    pre-existing router-level RoleChecker permissions. Scoping is applied
    in the service layer (not just the router) so it can never be bypassed
    by calling the service directly.
"""
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InactiveResourceException,
    NotFoundException,
    SlotUnavailableException,
)
from app.core.logging import get_logger
from app.models.appointment import (
    ALLOWED_STATUS_TRANSITIONS,
    Appointment,
    AppointmentPriority,
    AppointmentStatus,
    AppointmentType,
)
from app.models.audit_log import AuditAction
from app.models.doctor import DoctorStatus
from app.models.patient import PatientStatus
from app.models.user import User, UserRole
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.appointment import (
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentResponse,
    AppointmentSearchParams,
    AppointmentUpdateRequest,
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.audit_log_service import AuditLogService

logger = get_logger(__name__)

# Statuses beyond which an appointment may no longer be rescheduled.
NON_RESCHEDULABLE_STATUSES = {
    AppointmentStatus.CHECKED_IN,
    AppointmentStatus.IN_CONSULTATION,
    AppointmentStatus.COMPLETED,
    AppointmentStatus.CANCELLED,
    AppointmentStatus.NO_SHOW,
}

# Statuses beyond which an appointment may no longer be cancelled.
NON_CANCELLABLE_STATUSES = {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED}


def _slot_range(appointment_date: date, appointment_time, duration: int) -> tuple[datetime, datetime]:
    start = datetime.combine(appointment_date, appointment_time)
    end = start + timedelta(minutes=duration)
    return start, end


def _ranges_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and end_a > start_b


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AppointmentRepository(db)
        self.patient_repo = PatientRepository(db)
        self.doctor_repo = DoctorRepository(db)
        self.department_repo = DepartmentRepository(db)
        self.audit = AuditLogService(db)

    # ------------------------------------------------------------------
    # RBAC scoping helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _doctor_scope(current_user: User | None) -> uuid.UUID | None:
        """Returns the doctor_id a DOCTOR-role caller is restricted to, or
        None if the caller is unscoped (not a DOCTOR, or no user context
        was supplied — e.g. internal/background callers)."""
        if current_user is None or current_user.role != UserRole.DOCTOR:
            return None
        if current_user.doctor_id is None:
            raise ForbiddenException(
                "Your account has the DOCTOR role but is not linked to a doctor "
                "profile. Contact an administrator to link your account."
            )
        return current_user.doctor_id

    @staticmethod
    def _enforce_ownership(appointment: Appointment, doctor_scope: uuid.UUID | None) -> None:
        if doctor_scope is not None and appointment.doctor_id != doctor_scope:
            raise ForbiddenException("You may only access your own appointments")

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _validate_not_past(self, appointment_date: date) -> None:
        if appointment_date < date.today():
            raise BadRequestException("Appointment date cannot be in the past")

    def _validate_patient(self, patient_id: uuid.UUID):
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException("Patient", str(patient_id))
        if patient.status != PatientStatus.ACTIVE:
            raise InactiveResourceException(f"Patient '{patient.full_name}' is inactive")
        return patient

    def _validate_doctor(self, doctor_id: uuid.UUID):
        doctor = self.doctor_repo.get_by_id(doctor_id)
        if not doctor:
            raise NotFoundException("Doctor", str(doctor_id))
        if doctor.status != DoctorStatus.ACTIVE:
            raise InactiveResourceException(
                f"Dr. {doctor.full_name} is inactive and cannot receive new appointments"
            )
        return doctor

    def _validate_department(self, department_id: uuid.UUID, doctor):
        department = self.department_repo.get_by_id(department_id)
        if not department:
            raise NotFoundException("Department", str(department_id))
        if doctor.department_id != department.id:
            raise BadRequestException(
                f"Dr. {doctor.full_name} does not belong to the selected department"
            )
        return department

    def _validate_parent_appointment(self, parent_id: uuid.UUID, patient_id: uuid.UUID) -> Appointment:
        parent = self.repo.get_by_id(parent_id)
        if not parent:
            raise NotFoundException("Parent appointment", str(parent_id))
        if parent.patient_id != patient_id:
            raise BadRequestException(
                "The referenced parent appointment does not belong to the same patient"
            )
        return parent

    def _check_doctor_overlap(
        self,
        doctor_id: uuid.UUID,
        appointment_date: date,
        appointment_time,
        duration: int,
        priority: AppointmentPriority,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        if priority == AppointmentPriority.EMERGENCY:
            logger.warning(
                "Emergency appointment bypassing doctor overlap check: doctor_id=%s date=%s time=%s",
                doctor_id,
                appointment_date,
                appointment_time,
            )
            return

        new_start, new_end = _slot_range(appointment_date, appointment_time, duration)
        existing = self.repo.get_active_for_doctor_on_date(doctor_id, appointment_date, exclude_id)
        for appt in existing:
            existing_start, existing_end = _slot_range(
                appt.appointment_date, appt.appointment_time, appt.duration
            )
            if _ranges_overlap(new_start, new_end, existing_start, existing_end):
                raise SlotUnavailableException(
                    f"Doctor already has an overlapping appointment "
                    f"({appt.appointment_number}) at this time"
                )

    def _check_patient_overlap(
        self,
        patient_id: uuid.UUID,
        appointment_date: date,
        appointment_time,
        duration: int,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        # Never bypassed, even for emergency priority — a patient cannot be
        # in two appointments simultaneously.
        new_start, new_end = _slot_range(appointment_date, appointment_time, duration)
        existing = self.repo.get_active_for_patient_on_date(patient_id, appointment_date, exclude_id)
        for appt in existing:
            existing_start, existing_end = _slot_range(
                appt.appointment_date, appt.appointment_time, appt.duration
            )
            if _ranges_overlap(new_start, new_end, existing_start, existing_end):
                raise ConflictException(
                    f"Patient already has an appointment ({appt.appointment_number}) at this time"
                )

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------
    def book_appointment(
        self,
        payload: AppointmentCreateRequest,
        created_by: uuid.UUID,
        current_user: User | None = None,
    ) -> Appointment:
        doctor_scope = self._doctor_scope(current_user)
        if doctor_scope is not None and payload.doctor_id != doctor_scope:
            raise ForbiddenException("Doctors may only book appointments under their own name")

        self._validate_not_past(payload.appointment_date)
        self._validate_patient(payload.patient_id)
        doctor = self._validate_doctor(payload.doctor_id)
        self._validate_department(payload.department_id, doctor)

        if payload.appointment_type == AppointmentType.FOLLOW_UP:
            self._validate_parent_appointment(payload.parent_appointment_id, payload.patient_id)

        self._check_doctor_overlap(
            payload.doctor_id,
            payload.appointment_date,
            payload.appointment_time,
            payload.duration,
            payload.priority,
        )
        self._check_patient_overlap(
            payload.patient_id, payload.appointment_date, payload.appointment_time, payload.duration
        )

        data = payload.model_dump()
        data["appointment_number"] = self.repo.generate_next_appointment_number()
        data["created_by"] = created_by
        data["status"] = AppointmentStatus.SCHEDULED

        appointment = self.repo.create(data)
        self.audit.record(
            action=AuditAction.APPOINTMENT_BOOKED,
            actor_user_id=created_by,
            actor_username=current_user.username if current_user else None,
            resource_type="Appointment",
            resource_id=str(appointment.id),
            details={
                "appointment_number": appointment.appointment_number,
                "doctor_id": str(appointment.doctor_id),
                "patient_id": str(appointment.patient_id),
                "priority": appointment.priority.value,
            },
        )
        self.repo.commit()
        logger.info(
            "Appointment booked: number=%s patient=%s doctor=%s date=%s time=%s priority=%s",
            appointment.appointment_number,
            appointment.patient_id,
            appointment.doctor_id,
            appointment.appointment_date,
            appointment.appointment_time,
            appointment.priority,
        )
        return appointment

    def get_appointment(
        self, appointment_id: uuid.UUID, current_user: User | None = None
    ) -> Appointment:
        appointment = self.repo.get_by_id(appointment_id)
        if not appointment:
            raise NotFoundException("Appointment", str(appointment_id))
        self._enforce_ownership(appointment, self._doctor_scope(current_user))
        return appointment

    def update_appointment(
        self,
        appointment_id: uuid.UUID,
        payload: AppointmentUpdateRequest,
        current_user: User | None = None,
    ) -> Appointment:
        appointment = self.get_appointment(appointment_id, current_user)
        update_data = payload.model_dump(exclude_unset=True)
        previous_status = appointment.status

        if "status" in update_data:
            new_status = update_data["status"]
            allowed = ALLOWED_STATUS_TRANSITIONS.get(appointment.status, set())
            if new_status != appointment.status and new_status not in allowed:
                raise BadRequestException(
                    f"Cannot transition appointment from '{appointment.status.value}' "
                    f"to '{new_status.value}'"
                )

        appointment = self.repo.update(appointment, update_data)

        if "status" in update_data and update_data["status"] != previous_status:
            self.audit.record(
                action=AuditAction.APPOINTMENT_STATUS_CHANGED,
                actor_user_id=current_user.id if current_user else None,
                actor_username=current_user.username if current_user else None,
                resource_type="Appointment",
                resource_id=str(appointment.id),
                details={
                    "appointment_number": appointment.appointment_number,
                    "from_status": previous_status.value,
                    "to_status": appointment.status.value,
                },
            )

        self.repo.commit()
        logger.info("Appointment updated: id=%s", appointment.id)
        return appointment

    def cancel_appointment(
        self, appointment_id: uuid.UUID, reason: str, current_user: User | None = None
    ) -> Appointment:
        appointment = self.get_appointment(appointment_id, current_user)
        if appointment.status in NON_CANCELLABLE_STATUSES:
            raise BadRequestException(
                f"Appointment in status '{appointment.status.value}' cannot be cancelled"
            )

        note = f"[CANCELLED] {reason}"
        combined_notes = f"{appointment.notes}\n{note}" if appointment.notes else note
        appointment = self.repo.update(
            appointment, {"status": AppointmentStatus.CANCELLED, "notes": combined_notes}
        )
        self.audit.record(
            action=AuditAction.APPOINTMENT_CANCELLED,
            actor_user_id=current_user.id if current_user else None,
            actor_username=current_user.username if current_user else None,
            resource_type="Appointment",
            resource_id=str(appointment.id),
            details={"appointment_number": appointment.appointment_number, "reason": reason},
        )
        self.repo.commit()
        logger.info("Appointment cancelled: id=%s reason=%s", appointment.id, reason)
        return appointment

    def reschedule_appointment(
        self,
        appointment_id: uuid.UUID,
        payload: AppointmentRescheduleRequest,
        current_user: User | None = None,
    ) -> Appointment:
        appointment = self.get_appointment(appointment_id, current_user)
        if appointment.status in NON_RESCHEDULABLE_STATUSES:
            raise BadRequestException(
                f"Appointment in status '{appointment.status.value}' cannot be rescheduled"
            )

        self._validate_not_past(payload.appointment_date)
        duration = payload.duration or appointment.duration

        self._check_doctor_overlap(
            appointment.doctor_id,
            payload.appointment_date,
            payload.appointment_time,
            duration,
            appointment.priority,
            exclude_id=appointment.id,
        )
        self._check_patient_overlap(
            appointment.patient_id,
            payload.appointment_date,
            payload.appointment_time,
            duration,
            exclude_id=appointment.id,
        )

        old_slot = f"{appointment.appointment_date} {appointment.appointment_time}"
        note = f"[RESCHEDULED from {old_slot}] {payload.reason}"
        combined_notes = f"{appointment.notes}\n{note}" if appointment.notes else note

        appointment = self.repo.update(
            appointment,
            {
                "appointment_date": payload.appointment_date,
                "appointment_time": payload.appointment_time,
                "duration": duration,
                "status": AppointmentStatus.SCHEDULED,
                "notes": combined_notes,
            },
        )
        self.audit.record(
            action=AuditAction.APPOINTMENT_RESCHEDULED,
            actor_user_id=current_user.id if current_user else None,
            actor_username=current_user.username if current_user else None,
            resource_type="Appointment",
            resource_id=str(appointment.id),
            details={
                "appointment_number": appointment.appointment_number,
                "old_slot": old_slot,
                "new_date": str(payload.appointment_date),
                "new_time": str(payload.appointment_time),
            },
        )
        self.repo.commit()
        logger.info(
            "Appointment rescheduled: id=%s -> %s %s",
            appointment.id,
            payload.appointment_date,
            payload.appointment_time,
        )
        return appointment

    def get_patient_history(
        self, patient_id: uuid.UUID, current_user: User | None = None
    ) -> list[Appointment]:
        self._validate_patient(patient_id)
        history = self.repo.get_history_for_patient(patient_id)
        doctor_scope = self._doctor_scope(current_user)
        if doctor_scope is not None:
            history = [appt for appt in history if appt.doctor_id == doctor_scope]
        return history

    def search_appointments(
        self,
        search: AppointmentSearchParams,
        pagination: PaginationParams,
        current_user: User | None = None,
    ) -> PaginatedResponse[AppointmentResponse]:
        doctor_scope = self._doctor_scope(current_user)
        # A DOCTOR caller is always forced to their own doctor_id, even if a
        # different doctor_id was supplied in the query string — the filter
        # is not merely a default, it is a hard override, so scoping cannot
        # be bypassed by simply passing someone else's doctor_id.
        effective_doctor_id = doctor_scope if doctor_scope is not None else search.doctor_id

        items, total = self.repo.search(
            patient_id=search.patient_id,
            doctor_id=effective_doctor_id,
            department_id=search.department_id,
            status=search.status,
            appointment_type=search.appointment_type,
            priority=search.priority,
            date_from=search.date_from,
            date_to=search.date_to,
            uhid=search.uhid,
            skip=pagination.offset,
            limit=pagination.page_size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
        )
        response_items = [AppointmentResponse.model_validate(a) for a in items]
        return PaginatedResponse.create(response_items, total, pagination.page, pagination.page_size)
