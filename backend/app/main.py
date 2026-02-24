from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import employees, shifts, coverage, schedules, absences, constraints

app = FastAPI(
    title="Calculator Health API",
    description="API de planification des horaires du personnel soignant — CHUV",
    version="0.1.0",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(shifts.router, prefix="/api/shifts", tags=["Shift Types"])
app.include_router(coverage.router, prefix="/api/coverage", tags=["Coverage"])
app.include_router(absences.router, prefix="/api/absences", tags=["Absences"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["Schedules"])
app.include_router(constraints.router, prefix="/api/constraints", tags=["Constraints"])


@app.get("/")
def root():
    return {"status": "ok", "app": "Calculator Health"}


@app.get("/health")
def health():
    return {"status": "healthy"}
