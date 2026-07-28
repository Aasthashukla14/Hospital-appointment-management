"""
Patient repository.
"""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.patient import Patient, PatientStatus
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    def __init__(self, db: Session):
        super().__init__(Patient, db)

    def get_by_uhid(self, uhid: str) -> Patient | None:
        stmt = select(Patient).where(Patient.uhid == uhid)
        return self.db.scalar(stmt)

    def get_by_mobile(self, mobile_number: str) -> Patient | None:
        stmt = select(Patient).where(Patient.mobile_number == mobile_number)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> Patient | None:
        stmt = select(Patient).where(Patient.email == email)
        return self.db.scalar(stmt)

    def generate_next_uhid(self) -> str:
        """Generates a sequential UHID like UHID000001 based on current row count."""
        count = self.count()
        return f"UHID{count + 1:06d}"

    def search(
        self,
        *,
        name: str | None = None,
        uhid: str | None = None,
        mobile_number: str | None = None,
        status: PatientStatus | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> tuple[list[Patient], int]:
        conditions = []
        if name:
            pattern = f"%{name.lower()}%"
            conditions.append(
                or_(
                    func.lower(Patient.first_name).like(pattern),
                    func.lower(Patient.last_name).like(pattern),
                    func.lower(func.concat(Patient.first_name, " ", Patient.last_name)).like(pattern),
                )
            )
        if uhid:
            conditions.append(Patient.uhid.ilike(f"%{uhid}%"))
        if mobile_number:
            conditions.append(Patient.mobile_number.ilike(f"%{mobile_number}%"))
        if status:
            conditions.append(Patient.status == status)

        base_stmt = select(Patient)
        count_stmt = select(func.count()).select_from(Patient)
        for cond in conditions:
            base_stmt = base_stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        sortable_fields = {
            "first_name": Patient.first_name,
            "last_name": Patient.last_name,
            "created_at": Patient.created_at,
            "uhid": Patient.uhid,
        }
        sort_col = sortable_fields.get(sort_by, Patient.created_at)
        base_stmt = base_stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
        base_stmt = base_stmt.offset(skip).limit(limit)

        items = list(self.db.scalars(base_stmt).all())
        total = self.db.scalar(count_stmt) or 0
        return items, total
