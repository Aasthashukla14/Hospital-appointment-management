"""
Department repository.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.department import Department, DepartmentStatus
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Session):
        super().__init__(Department, db)

    def get_by_name(self, name: str) -> Department | None:
        stmt = select(Department).where(func.lower(Department.name) == name.lower())
        return self.db.scalar(stmt)

    def has_active_doctors(self, department_id) -> bool:
        from app.models.doctor import Doctor, DoctorStatus

        stmt = select(func.count()).select_from(Doctor).where(
            Doctor.department_id == department_id,
            Doctor.status == DoctorStatus.ACTIVE,
        )
        return (self.db.scalar(stmt) or 0) > 0

    def search(
        self,
        *,
        name: str | None = None,
        status: DepartmentStatus | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> tuple[list[Department], int]:
        conditions = []
        if name:
            conditions.append(Department.name.ilike(f"%{name}%"))
        if status:
            conditions.append(Department.status == status)

        base_stmt = select(Department)
        count_stmt = select(func.count()).select_from(Department)
        for cond in conditions:
            base_stmt = base_stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        sortable_fields = {"name": Department.name, "created_at": Department.created_at}
        sort_col = sortable_fields.get(sort_by, Department.name)
        base_stmt = base_stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
        base_stmt = base_stmt.offset(skip).limit(limit)

        items = list(self.db.scalars(base_stmt).all())
        total = self.db.scalar(count_stmt) or 0
        return items, total
