"""
Doctor repository.
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor, DoctorStatus
from app.repositories.base import BaseRepository


class DoctorRepository(BaseRepository[Doctor]):
    def __init__(self, db: Session):
        super().__init__(Doctor, db)

    def get_by_employee_id(self, employee_id: str) -> Doctor | None:
        stmt = select(Doctor).where(Doctor.employee_id == employee_id)
        return self.db.scalar(stmt)

    def get_by_mobile(self, mobile_number: str) -> Doctor | None:
        stmt = select(Doctor).where(Doctor.mobile_number == mobile_number)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> Doctor | None:
        stmt = select(Doctor).where(Doctor.email == email)
        return self.db.scalar(stmt)

    def generate_next_employee_id(self) -> str:
        count = self.count()
        return f"EMP{count + 1:05d}"

    def search(
        self,
        *,
        name: str | None = None,
        department_id: uuid.UUID | None = None,
        specialization: str | None = None,
        status: DoctorStatus | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> tuple[list[Doctor], int]:
        conditions = []
        if name:
            conditions.append(Doctor.full_name.ilike(f"%{name}%"))
        if department_id:
            conditions.append(Doctor.department_id == department_id)
        if specialization:
            conditions.append(Doctor.specialization.ilike(f"%{specialization}%"))
        if status:
            conditions.append(Doctor.status == status)

        base_stmt = select(Doctor)
        count_stmt = select(func.count()).select_from(Doctor)
        for cond in conditions:
            base_stmt = base_stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        sortable_fields = {
            "full_name": Doctor.full_name,
            "created_at": Doctor.created_at,
            "consultation_fee": Doctor.consultation_fee,
        }
        sort_col = sortable_fields.get(sort_by, Doctor.full_name)
        base_stmt = base_stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
        base_stmt = base_stmt.offset(skip).limit(limit)

        items = list(self.db.scalars(base_stmt).all())
        total = self.db.scalar(count_stmt) or 0
        return items, total
