"""
Doctor service — business logic for the Doctor module.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, DuplicateResourceException, NotFoundException
from app.core.logging import get_logger
from app.models.department import DepartmentStatus
from app.models.doctor import Doctor, DoctorStatus
from app.repositories.department_repository import DepartmentRepository
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.doctor import (
    DoctorCreateRequest,
    DoctorResponse,
    DoctorSearchParams,
    DoctorUpdateRequest,
)

logger = get_logger(__name__)


class DoctorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DoctorRepository(db)
        self.department_repo = DepartmentRepository(db)

    def _validate_department(self, department_id: uuid.UUID) -> None:
        department = self.department_repo.get_by_id(department_id)
        if not department:
            raise NotFoundException("Department", str(department_id))
        if department.status != DepartmentStatus.ACTIVE:
            raise BadRequestException(
                f"Department '{department.name}' is inactive and cannot accept new doctors"
            )

    def create_doctor(self, payload: DoctorCreateRequest) -> Doctor:
        self._validate_department(payload.department_id)

        if self.repo.get_by_mobile(payload.mobile_number):
            raise DuplicateResourceException("Doctor", "mobile_number", payload.mobile_number)
        if self.repo.get_by_email(payload.email):
            raise DuplicateResourceException("Doctor", "email", payload.email)

        employee_id = self.repo.generate_next_employee_id()
        data = payload.model_dump()
        data["employee_id"] = employee_id
        doctor = self.repo.create(data)
        self.repo.commit()
        logger.info("Doctor created: employee_id=%s id=%s", doctor.employee_id, doctor.id)
        return doctor

    def get_doctor(self, doctor_id: uuid.UUID) -> Doctor:
        doctor = self.repo.get_by_id(doctor_id)
        if not doctor:
            raise NotFoundException("Doctor", str(doctor_id))
        return doctor

    def update_doctor(self, doctor_id: uuid.UUID, payload: DoctorUpdateRequest) -> Doctor:
        doctor = self.get_doctor(doctor_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "department_id" in update_data:
            self._validate_department(update_data["department_id"])

        if "mobile_number" in update_data:
            existing = self.repo.get_by_mobile(update_data["mobile_number"])
            if existing and existing.id != doctor.id:
                raise DuplicateResourceException("Doctor", "mobile_number", update_data["mobile_number"])

        if "email" in update_data:
            existing = self.repo.get_by_email(update_data["email"])
            if existing and existing.id != doctor.id:
                raise DuplicateResourceException("Doctor", "email", update_data["email"])

        doctor = self.repo.update(doctor, update_data)
        self.repo.commit()
        logger.info("Doctor updated: id=%s", doctor.id)
        return doctor

    def deactivate_doctor(self, doctor_id: uuid.UUID) -> Doctor:
        doctor = self.get_doctor(doctor_id)
        doctor = self.repo.update(doctor, {"status": DoctorStatus.INACTIVE})
        self.repo.commit()
        logger.info("Doctor deactivated: id=%s", doctor.id)
        return doctor

    def search_doctors(
        self, search: DoctorSearchParams, pagination: PaginationParams
    ) -> PaginatedResponse[DoctorResponse]:
        items, total = self.repo.search(
            name=search.name,
            department_id=search.department_id,
            specialization=search.specialization,
            status=search.status,
            skip=pagination.offset,
            limit=pagination.page_size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
        )
        response_items = [DoctorResponse.model_validate(d) for d in items]
        return PaginatedResponse.create(response_items, total, pagination.page, pagination.page_size)
