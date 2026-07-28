"""
Department service — business logic for the Department module.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, DuplicateResourceException, NotFoundException
from app.core.logging import get_logger
from app.models.department import Department, DepartmentStatus
from app.repositories.department_repository import DepartmentRepository
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.department import (
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentSearchParams,
    DepartmentUpdateRequest,
)

logger = get_logger(__name__)


class DepartmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DepartmentRepository(db)

    def create_department(self, payload: DepartmentCreateRequest) -> Department:
        if self.repo.get_by_name(payload.name):
            raise DuplicateResourceException("Department", "name", payload.name)

        department = self.repo.create(payload.model_dump())
        self.repo.commit()
        logger.info("Department created: id=%s name=%s", department.id, department.name)
        return department

    def get_department(self, department_id: uuid.UUID) -> Department:
        department = self.repo.get_by_id(department_id)
        if not department:
            raise NotFoundException("Department", str(department_id))
        return department

    def update_department(self, department_id: uuid.UUID, payload: DepartmentUpdateRequest) -> Department:
        department = self.get_department(department_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing = self.repo.get_by_name(update_data["name"])
            if existing and existing.id != department.id:
                raise DuplicateResourceException("Department", "name", update_data["name"])

        department = self.repo.update(department, update_data)
        self.repo.commit()
        logger.info("Department updated: id=%s", department.id)
        return department

    def delete_department(self, department_id: uuid.UUID) -> None:
        department = self.get_department(department_id)
        if self.repo.has_active_doctors(department.id):
            raise BadRequestException(
                "Cannot delete a department that still has active doctors assigned. "
                "Reassign or deactivate those doctors first."
            )
        self.repo.update(department, {"status": DepartmentStatus.INACTIVE})
        self.repo.commit()
        logger.info("Department deactivated: id=%s", department.id)

    def search_departments(
        self, search: DepartmentSearchParams, pagination: PaginationParams
    ) -> PaginatedResponse[DepartmentResponse]:
        items, total = self.repo.search(
            name=search.name,
            status=search.status,
            skip=pagination.offset,
            limit=pagination.page_size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
        )
        response_items = [DepartmentResponse.model_validate(d) for d in items]
        return PaginatedResponse.create(response_items, total, pagination.page, pagination.page_size)
