"""
Appointment endpoints.

RBAC summary:
    - Book / Update / Cancel / Reschedule: RECEPTIONIST, DOCTOR, HOSPITAL_ADMIN, SUPER_ADMIN
    - Read / Search / History: any authenticated user

    A caller with role DOCTOR is additionally scoped, at the service layer,
    to their own appointments only — see app.services.appointment_service
    for details. This cannot be bypassed by query parameters.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, Pagination, RoleChecker
from app.models.appointment import AppointmentPriority, AppointmentStatus, AppointmentType
from app.models.user import UserRole
from app.schemas.appointment import (
    AppointmentCancelRequest,
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentResponse,
    AppointmentSearchParams,
    AppointmentUpdateRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])

can_manage_appointments = RoleChecker(
    [UserRole.RECEPTIONIST, UserRole.DOCTOR, UserRole.HOSPITAL_ADMIN, UserRole.SUPER_ADMIN]
)


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new appointment",
    dependencies=[Depends(can_manage_appointments)],
)
def book_appointment(payload: AppointmentCreateRequest, db: DbSession, current_user: CurrentUser):
    return AppointmentService(db).book_appointment(
        payload, created_by=current_user.id, current_user=current_user
    )


@router.get(
    "/",
    response_model=PaginatedResponse[AppointmentResponse],
    summary="List / search appointments with filtering, sorting, and pagination",
)
def search_appointments(
    db: DbSession,
    current_user: CurrentUser,
    pagination: Pagination,
    patient_id: uuid.UUID | None = None,
    doctor_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    status_: AppointmentStatus | None = None,
    appointment_type: AppointmentType | None = None,
    priority: AppointmentPriority | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    uhid: str | None = None,
):
    search_params = AppointmentSearchParams(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department_id,
        status=status_,
        appointment_type=appointment_type,
        priority=priority,
        date_from=date_from,
        date_to=date_to,
        uhid=uhid,
    )
    return AppointmentService(db).search_appointments(search_params, pagination, current_user=current_user)


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get an appointment by ID",
)
def get_appointment(appointment_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return AppointmentService(db).get_appointment(appointment_id, current_user=current_user)


@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Update appointment status/metadata (confirm, check-in, start, complete, etc.)",
    dependencies=[Depends(can_manage_appointments)],
)
def update_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    return AppointmentService(db).update_appointment(
        appointment_id, payload, current_user=current_user
    )


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    summary="Cancel an appointment",
    dependencies=[Depends(can_manage_appointments)],
)
def cancel_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentCancelRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    return AppointmentService(db).cancel_appointment(
        appointment_id, payload.reason, current_user=current_user
    )


@router.post(
    "/{appointment_id}/reschedule",
    response_model=AppointmentResponse,
    summary="Reschedule an appointment to a new date/time",
    dependencies=[Depends(can_manage_appointments)],
)
def reschedule_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentRescheduleRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    return AppointmentService(db).reschedule_appointment(
        appointment_id, payload, current_user=current_user
    )


@router.get(
    "/patient/{patient_id}/history",
    response_model=list[AppointmentResponse],
    summary="Get a patient's full appointment history",
)
def get_patient_history(patient_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return AppointmentService(db).get_patient_history(patient_id, current_user=current_user)
