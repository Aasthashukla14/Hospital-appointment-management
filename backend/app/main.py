"Hello, FASTAPI"

from fastapi import FastAPI

app = FastAPI(
    title="Hospital Appointment Management API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Hospital Appointment Management System API"}