"""
Department endpoints.

RBAC summary:
    - Create/Update/Delete: HOSPITAL_ADMIN, SUPER_ADMIN
    - Read/List: any authenticated user
"""
import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, Pagination, RoleChecker
from app.models.department import DepartmentStatus
from app.models.user import UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.department import (
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentSearchParams,
    DepartmentUpdateRequest,
)
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"])

can_manage_departments = RoleChecker([UserRole.HOSPITAL_ADMIN, UserRole.SUPER_ADMIN])


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department",
    dependencies=[Depends(can_manage_departments)],
)
def create_department(payload: DepartmentCreateRequest, db: DbSession):
    return DepartmentService(db).create_department(payload)


@router.get(
    "/",
    response_model=PaginatedResponse[DepartmentResponse],
    summary="List / search departments with filtering, sorting, and pagination",
)
def search_departments(
    db: DbSession,
    current_user: CurrentUser,
    pagination: Pagination,
    name: str | None = None,
    status_: DepartmentStatus | None = None,
):
    search_params = DepartmentSearchParams(name=name, status=status_)
    return DepartmentService(db).search_departments(search_params, pagination)


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Get a department by ID",
)
def get_department(department_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return DepartmentService(db).get_department(department_id)


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update a department",
    dependencies=[Depends(can_manage_departments)],
)
def update_department(department_id: uuid.UUID, payload: DepartmentUpdateRequest, db: DbSession):
    return DepartmentService(db).update_department(department_id, payload)


@router.delete(
    "/{department_id}",
    response_model=MessageResponse,
    summary="Deactivate (soft-delete) a department",
    dependencies=[Depends(can_manage_departments)],
)
def delete_department(department_id: uuid.UUID, db: DbSession):
    DepartmentService(db).delete_department(department_id)
    return MessageResponse(message="Department deactivated successfully")
