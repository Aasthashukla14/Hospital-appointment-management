"""
Aggregates all v1 routers. Future parts (Department, Doctor, Appointment)
will register their routers here as they are added.
"""
from fastapi import APIRouter

from app.api.v1 import appointment, audit, auth, department, doctor, patient

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(patient.router)
api_router.include_router(department.router)
api_router.include_router(doctor.router)
api_router.include_router(appointment.router)
api_router.include_router(audit.router)
