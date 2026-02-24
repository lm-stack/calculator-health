from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_supabase

router = APIRouter()


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    role: str  # infirmier, assc, aide-soignant
    activity_rate: int = 100
    can_do_night: bool = True
    can_do_weekend: bool = True
    preferred_shifts: list = []


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    activity_rate: Optional[int] = None
    can_do_night: Optional[bool] = None
    can_do_weekend: Optional[bool] = None
    preferred_shifts: Optional[list] = None


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
