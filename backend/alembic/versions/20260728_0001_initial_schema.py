"""initial schema — departments, users, doctors, patients, appointments, audit_logs

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-28 00:00:00.000000

Creates the full baseline schema for the HIMS Appointment Management Module,
matching the ORM models in app/models/. Tables are created in dependency
order (departments -> users -> doctors -> patients -> appointments ->
audit_logs); the one circular reference (users.doctor_id -> doctors.id) is
resolved by creating the `users` table without that foreign key first, then
adding it via ALTER TABLE once `doctors` exists.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------
    # gen_random_uuid() is built into PostgreSQL 13+. pgcrypto provides
    # the same function on older server versions, so we enable it
    # unconditionally — it's a no-op / harmless on 13+ where the
    # extension isn't strictly required.
    # -----------------------------------------------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # -----------------------------------------------------------------
    # departments
    # -----------------------------------------------------------------
    op.create_table(
        "departments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", name="department_status_enum"),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.create_index("ix_departments_name", "departments", ["name"], unique=True)

    # -----------------------------------------------------------------
    # users
    # (doctor_id FK to doctors is added later, once doctors exists)
    # -----------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR", name="user_role_enum"),
            nullable=False,
            server_default="RECEPTIONIST",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # -----------------------------------------------------------------
    # doctors
    # -----------------------------------------------------------------
    op.create_table(
        "doctors",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("employee_id", sa.String(20), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("specialization", sa.String(150), nullable=False),
        sa.Column("mobile_number", sa.String(15), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("consultation_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", name="doctor_status_enum"),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.create_index("ix_doctors_employee_id", "doctors", ["employee_id"], unique=True)
    op.create_index("ix_doctors_mobile_number", "doctors", ["mobile_number"], unique=True)
    op.create_index("ix_doctors_email", "doctors", ["email"], unique=True)
    op.create_index("ix_doctors_department_id", "doctors", ["department_id"])

    # Now that `doctors` exists, wire up the deferred users.doctor_id FK.
    op.create_foreign_key(
        "fk_users_doctor_id_doctors",
        "users",
        "doctors",
        ["doctor_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # -----------------------------------------------------------------
    # patients
    # -----------------------------------------------------------------
    op.create_table(
        "patients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("uhid", sa.String(20), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("gender", sa.Enum("MALE", "FEMALE", "OTHER", name="gender_enum"), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("mobile_number", sa.String(15), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", name="patient_status_enum"),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.create_index("ix_patients_uhid", "patients", ["uhid"], unique=True)
    op.create_index("ix_patients_mobile_number", "patients", ["mobile_number"], unique=True)
    op.create_index("ix_patients_email", "patients", ["email"], unique=True)

    # -----------------------------------------------------------------
    # appointments
    # -----------------------------------------------------------------
    op.create_table(
        "appointments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("appointment_number", sa.String(20), nullable=False),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("appointment_time", sa.Time(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False, server_default="30"),
        sa.Column(
            "appointment_type",
            sa.Enum("OPD", "FOLLOW_UP", "VIDEO_CONSULTATION", name="appointment_type_enum"),
            nullable=False,
            server_default="OPD",
        ),
        sa.Column(
            "priority",
            sa.Enum("NORMAL", "EMERGENCY", name="appointment_priority_enum"),
            nullable=False,
            server_default="NORMAL",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "SCHEDULED",
                "CONFIRMED",
                "CHECKED_IN",
                "IN_CONSULTATION",
                "COMPLETED",
                "CANCELLED",
                "NO_SHOW",
                name="appointment_status_enum",
            ),
            nullable=False,
            server_default="SCHEDULED",
        ),
        sa.Column("reason_for_visit", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "parent_appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_index("ix_appointments_appointment_number", "appointments", ["appointment_number"], unique=True)
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_department_id", "appointments", ["department_id"])
    op.create_index("ix_appointments_appointment_date", "appointments", ["appointment_date"])
    op.create_index("ix_appointments_status", "appointments", ["status"])
    # Composite indexes accelerating the conflict-detection queries in
    # AppointmentRepository (get_active_for_doctor_on_date /
    # get_active_for_patient_on_date) and the search/list endpoints.
    op.create_index(
        "ix_appointments_doctor_date_status",
        "appointments",
        ["doctor_id", "appointment_date", "status"],
    )
    op.create_index(
        "ix_appointments_patient_date_status",
        "appointments",
        ["patient_id", "appointment_date", "status"],
    )

    # -----------------------------------------------------------------
    # audit_logs
    # -----------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_username", sa.String(64), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")

    op.drop_index("ix_appointments_patient_date_status", table_name="appointments")
    op.drop_index("ix_appointments_doctor_date_status", table_name="appointments")
    op.drop_table("appointments")
    sa.Enum(name="appointment_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="appointment_priority_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="appointment_type_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("patients")
    sa.Enum(name="patient_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="gender_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_constraint("fk_users_doctor_id_doctors", "users", type_="foreignkey")

    op.drop_table("doctors")
    sa.Enum(name="doctor_status_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("users")
    sa.Enum(name="user_role_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_table("departments")
    sa.Enum(name="department_status_enum").drop(op.get_bind(), checkfirst=True)
