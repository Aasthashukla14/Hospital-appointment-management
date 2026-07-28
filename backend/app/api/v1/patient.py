"""
Patient endpoints.

RBAC summary:
    - Create/Update/Deactivate: RECEPTIONIST, HOSPITAL_ADMIN, SUPER_ADMIN
    - Read/Search: any authenticated user (including DOCTOR)
"""
import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, Pagination, RoleChecker
from app.models.patient import PatientStatus
from app.models.user import UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.patient import (
    PatientCreateRequest,
    PatientResponse,
    PatientSearchParams,
    PatientUpdateRequest,
)
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])

can_manage_patients = RoleChecker(
    [UserRole.RECEPTIONIST, UserRole.HOSPITAL_ADMIN, UserRole.SUPER_ADMIN]
)


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
    dependencies=[Depends(can_manage_patients)],
)
def create_patient(payload: PatientCreateRequest, db: DbSession):
    return PatientService(db).create_patient(payload)


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get a patient by ID",
)
def get_patient(patient_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return PatientService(db).get_patient(patient_id)


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update a patient's details",
    dependencies=[Depends(can_manage_patients)],
)
def update_patient(patient_id: uuid.UUID, payload: PatientUpdateRequest, db: DbSession):
    return PatientService(db).update_patient(patient_id, payload)


@router.delete(
    "/{patient_id}",
    response_model=MessageResponse,
    summary="Deactivate (soft-delete) a patient",
    dependencies=[Depends(can_manage_patients)],
)
def deactivate_patient(patient_id: uuid.UUID, db: DbSession):
    PatientService(db).deactivate_patient(patient_id)
    return MessageResponse(message="Patient deactivated successfully")


@router.get(
    "/",
    response_model=PaginatedResponse[PatientResponse],
    summary="Search / list patients with filtering, sorting, and pagination",
)
def search_patients(
    db: DbSession,
    current_user: CurrentUser,
    pagination: Pagination,
    name: str | None = None,
    uhid: str | None = None,
    mobile_number: str | None = None,
    status_: PatientStatus | None = None,
):
    search_params = PatientSearchParams(
        name=name, uhid=uhid, mobile_number=mobile_number, status=status_
    )
    return PatientService(db).search_patients(search_params, pagination)
