from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_supabase

router = APIRouter()


class AbsenceCreate(BaseModel):
    employee_id: str
    date_start: str  # YYYY-MM-DD
    date_end: str
    type: str  # vacances, maladie, congé


class AbsenceUpdate(BaseModel):
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    type: Optional[str] = None


@router.get("")
def list_absences(employee_id: Optional[str] = None):
    sb = get_supabase()
    query = sb.table("absences").select("*, employees(first_name, last_name)")
    if employee_id:
        query = query.eq("employee_id", employee_id)
    result = query.order("date_start").execute()
    return result.data


@router.post("", status_code=201)
def create_absence(absence: AbsenceCreate):
    sb = get_supabase()
    result = sb.table("absences").insert(absence.model_dump()).execute()
    return result.data[0]


@router.put("/{absence_id}")
def update_absence(absence_id: str, absence: AbsenceUpdate):
    sb = get_supabase()
    data = {k: v for k, v in absence.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = sb.table("absences").update(data).eq("id", absence_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Absence not found")
    return result.data[0]


@router.delete("/{absence_id}", status_code=204)
def delete_absence(absence_id: str):
    sb = get_supabase()
    sb.table("absences").delete().eq("id", absence_id).execute()
