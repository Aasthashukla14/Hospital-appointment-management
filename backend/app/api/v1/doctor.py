"""
Doctor endpoints.

RBAC summary:
    - Create/Update/Delete: HOSPITAL_ADMIN, SUPER_ADMIN
    - Read/Search: any authenticated user
"""
import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, Pagination, RoleChecker
from app.models.doctor import DoctorStatus
from app.models.user import UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.doctor import (
    DoctorCreateRequest,
    DoctorResponse,
    DoctorSearchParams,
    DoctorUpdateRequest,
)
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["Doctors"])

can_manage_doctors = RoleChecker([UserRole.HOSPITAL_ADMIN, UserRole.SUPER_ADMIN])


@router.post(
    "/",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new doctor",
    dependencies=[Depends(can_manage_doctors)],
)
def create_doctor(payload: DoctorCreateRequest, db: DbSession):
    return DoctorService(db).create_doctor(payload)


@router.get(
    "/",
    response_model=PaginatedResponse[DoctorResponse],
    summary="Search doctors by name, department, specialization, or status",
)
def search_doctors(
    db: DbSession,
    current_user: CurrentUser,
    pagination: Pagination,
    name: str | None = None,
    department_id: uuid.UUID | None = None,
    specialization: str | None = None,
    status_: DoctorStatus | None = None,
):
    search_params = DoctorSearchParams(
        name=name, department_id=department_id, specialization=specialization, status=status_
    )
    return DoctorService(db).search_doctors(search_params, pagination)


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Get a doctor by ID",
)
def get_doctor(doctor_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return DoctorService(db).get_doctor(doctor_id)


@router.put(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Update a doctor's details",
    dependencies=[Depends(can_manage_doctors)],
)
def update_doctor(doctor_id: uuid.UUID, payload: DoctorUpdateRequest, db: DbSession):
    return DoctorService(db).update_doctor(doctor_id, payload)


@router.delete(
    "/{doctor_id}",
    response_model=MessageResponse,
    summary="Deactivate (soft-delete) a doctor",
    dependencies=[Depends(can_manage_doctors)],
)
def delete_doctor(doctor_id: uuid.UUID, db: DbSession):
    DoctorService(db).deactivate_doctor(doctor_id)
    return MessageResponse(message="Doctor deactivated successfully")
