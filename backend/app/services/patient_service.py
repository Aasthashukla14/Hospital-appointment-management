"""
Patient service — business logic for the Patient module.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.core.logging import get_logger
from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.patient import (
    PatientCreateRequest,
    PatientResponse,
    PatientSearchParams,
    PatientUpdateRequest,
)

logger = get_logger(__name__)


class PatientService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PatientRepository(db)

    def create_patient(self, payload: PatientCreateRequest) -> Patient:
        if self.repo.get_by_mobile(payload.mobile_number):
            raise DuplicateResourceException("Patient", "mobile_number", payload.mobile_number)
        if payload.email and self.repo.get_by_email(payload.email):
            raise DuplicateResourceException("Patient", "email", payload.email)

        uhid = self.repo.generate_next_uhid()
        data = payload.model_dump()
        data["uhid"] = uhid
        patient = self.repo.create(data)
        self.repo.commit()
        logger.info("Patient created: uhid=%s id=%s", patient.uhid, patient.id)
        return patient

    def get_patient(self, patient_id: uuid.UUID) -> Patient:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException("Patient", str(patient_id))
        return patient

    def update_patient(self, patient_id: uuid.UUID, payload: PatientUpdateRequest) -> Patient:
        patient = self.get_patient(patient_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "mobile_number" in update_data:
            existing = self.repo.get_by_mobile(update_data["mobile_number"])
            if existing and existing.id != patient.id:
                raise DuplicateResourceException("Patient", "mobile_number", update_data["mobile_number"])

        if "email" in update_data and update_data["email"]:
            existing = self.repo.get_by_email(update_data["email"])
            if existing and existing.id != patient.id:
                raise DuplicateResourceException("Patient", "email", update_data["email"])

        patient = self.repo.update(patient, update_data)
        self.repo.commit()
        logger.info("Patient updated: id=%s", patient.id)
        return patient

    def deactivate_patient(self, patient_id: uuid.UUID) -> Patient:
        from app.models.patient import PatientStatus

        patient = self.get_patient(patient_id)
        patient = self.repo.update(patient, {"status": PatientStatus.INACTIVE})
        self.repo.commit()
        logger.info("Patient deactivated: id=%s", patient.id)
        return patient

    def search_patients(
        self, search: PatientSearchParams, pagination: PaginationParams
    ) -> PaginatedResponse[PatientResponse]:
        items, total = self.repo.search(
            name=search.name,
            uhid=search.uhid,
            mobile_number=search.mobile_number,
            status=search.status,
            skip=pagination.offset,
            limit=pagination.page_size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
        )
        response_items = [PatientResponse.model_validate(p) for p in items]
        return PaginatedResponse.create(response_items, total, pagination.page, pagination.page_size)
