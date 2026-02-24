from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from app.db.supabase_client import get_supabase

router = APIRouter()

VALID_DAYS = {"lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"}
VALID_RATES = {20, 40, 60, 80, 100}


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    role: str  # infirmier, assc, aide-soignant
    activity_rate: int = 100
    working_days: list[str] = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]

    @field_validator("activity_rate")
    @classmethod
    def validate_rate(cls, v: int) -> int:
        if v not in VALID_RATES:
            raise ValueError(f"Taux invalide : {v}. Valeurs acceptées : {sorted(VALID_RATES)}")
        return v

    @field_validator("working_days")
    @classmethod
    def validate_days(cls, v: list[str]) -> list[str]:
        invalid = set(v) - VALID_DAYS
        if invalid:
            raise ValueError(f"Jours invalides : {invalid}")
        return v

    @model_validator(mode="after")
    def validate_days_count(self):
        expected = self.activity_rate // 20
        if len(self.working_days) != expected:
            raise ValueError(
                f"Taux {self.activity_rate}% → {expected} jours attendus, "
                f"mais {len(self.working_days)} fournis"
            )
        return self


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    activity_rate: Optional[int] = None
    working_days: Optional[list[str]] = None

    @field_validator("activity_rate")
    @classmethod
    def validate_rate(cls, v: int | None) -> int | None:
        if v is not None and v not in VALID_RATES:
            raise ValueError(f"Taux invalide : {v}. Valeurs acceptées : {sorted(VALID_RATES)}")
        return v

    @field_validator("working_days")
    @classmethod
    def validate_days(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            invalid = set(v) - VALID_DAYS
            if invalid:
                raise ValueError(f"Jours invalides : {invalid}")
        return v

    @model_validator(mode="after")
    def validate_days_count(self):
        if self.activity_rate is not None and self.working_days is not None:
            expected = self.activity_rate // 20
            if len(self.working_days) != expected:
                raise ValueError(
                    f"Taux {self.activity_rate}% → {expected} jours attendus, "
                    f"mais {len(self.working_days)} fournis"
                )
        return self


@router.get("")
def list_employees():
    sb = get_supabase()
    result = sb.table("employees").select("*").order("last_name").execute()
    return result.data


@router.get("/{employee_id}")
def get_employee(employee_id: str):
    sb = get_supabase()
    result = sb.table("employees").select("*").eq("id", employee_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return result.data[0]


@router.post("", status_code=201)
def create_employee(employee: EmployeeCreate):
    sb = get_supabase()
    result = sb.table("employees").insert(employee.model_dump()).execute()
    return result.data[0]


@router.put("/{employee_id}")
def update_employee(employee_id: str, employee: EmployeeUpdate):
    sb = get_supabase()
    data = {k: v for k, v in employee.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = sb.table("employees").update(data).eq("id", employee_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return result.data[0]


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: str):
    sb = get_supabase()
    sb.table("employees").delete().eq("id", employee_id).execute()
