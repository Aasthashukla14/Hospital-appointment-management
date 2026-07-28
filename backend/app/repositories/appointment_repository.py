"""
Appointment repository.
"""
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.appointment import (
    Appointment,
    AppointmentPriority,
    AppointmentStatus,
    AppointmentType,
    RELEASED_STATUSES,
)
from app.models.patient import Patient
from app.repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, db: Session):
        super().__init__(Appointment, db)

    def generate_next_appointment_number(self) -> str:
        count = self.count()
        return f"APT{count + 1:07d}"

    def get_by_id(self, id_: uuid.UUID) -> Appointment | None:
        stmt = (
            select(Appointment)
            .options(joinedload(Appointment.patient), joinedload(Appointment.doctor))
            .where(Appointment.id == id_)
        )
        return self.db.scalar(stmt)

    def get_active_for_doctor_on_date(
        self, doctor_id: uuid.UUID, appointment_date: date, exclude_id: uuid.UUID | None = None
    ) -> list[Appointment]:
        stmt = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.notin_(RELEASED_STATUSES),
        )
        if exclude_id:
            stmt = stmt.where(Appointment.id != exclude_id)
        return list(self.db.scalars(stmt).all())

    def get_active_for_patient_on_date(
        self, patient_id: uuid.UUID, appointment_date: date, exclude_id: uuid.UUID | None = None
    ) -> list[Appointment]:
        stmt = select(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.notin_(RELEASED_STATUSES),
        )
        if exclude_id:
            stmt = stmt.where(Appointment.id != exclude_id)
        return list(self.db.scalars(stmt).all())

    def get_history_for_patient(self, patient_id: uuid.UUID) -> list[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_followup_chain(self, appointment_id: uuid.UUID) -> list[Appointment]:
        """All follow-up appointments that reference this one, most recent first."""
        stmt = (
            select(Appointment)
            .where(Appointment.parent_appointment_id == appointment_id)
            .order_by(Appointment.appointment_date.desc())
        )
        return list(self.db.scalars(stmt).all())

    def search(
        self,
        *,
        patient_id: uuid.UUID | None = None,
        doctor_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
        status: AppointmentStatus | None = None,
        appointment_type: AppointmentType | None = None,
        priority: AppointmentPriority | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        uhid: str | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> tuple[list[Appointment], int]:
        base_stmt = select(Appointment)
        count_stmt = select(func.count()).select_from(Appointment)

        if uhid:
            base_stmt = base_stmt.join(Patient, Appointment.patient_id == Patient.id)
            count_stmt = count_stmt.join(Patient, Appointment.patient_id == Patient.id)

        conditions = []
        if patient_id:
            conditions.append(Appointment.patient_id == patient_id)
        if doctor_id:
            conditions.append(Appointment.doctor_id == doctor_id)
        if department_id:
            conditions.append(Appointment.department_id == department_id)
        if status:
            conditions.append(Appointment.status == status)
        if appointment_type:
            conditions.append(Appointment.appointment_type == appointment_type)
        if priority:
            conditions.append(Appointment.priority == priority)
        if date_from:
            conditions.append(Appointment.appointment_date >= date_from)
        if date_to:
            conditions.append(Appointment.appointment_date <= date_to)
        if uhid:
            conditions.append(Patient.uhid.ilike(f"%{uhid}%"))

        for cond in conditions:
            base_stmt = base_stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        sortable_fields = {
            "appointment_date": Appointment.appointment_date,
            "created_at": Appointment.created_at,
            "status": Appointment.status,
        }
        sort_col = sortable_fields.get(sort_by, Appointment.appointment_date)
        base_stmt = base_stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
        base_stmt = base_stmt.offset(skip).limit(limit)

        items = list(self.db.scalars(base_stmt).all())
        total = self.db.scalar(count_stmt) or 0
        return items, total
