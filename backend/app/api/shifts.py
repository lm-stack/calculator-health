from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_supabase

router = APIRouter()


class ShiftTypeCreate(BaseModel):
    name: str
    start_time: str  # HH:MM
    end_time: str
    duration_hours: float


class ShiftTypeUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_hours: Optional[float] = None


@router.get("")
def list_shift_types():
    sb = get_supabase()
    result = sb.table("shift_types").select("*").order("start_time").execute()
    return result.data


@router.get("/{shift_id}")
def get_shift_type(shift_id: str):
    sb = get_supabase()
    result = sb.table("shift_types").select("*").eq("id", shift_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Shift type not found")
    return result.data[0]


@router.post("", status_code=201)
def create_shift_type(shift: ShiftTypeCreate):
    sb = get_supabase()
    result = sb.table("shift_types").insert(shift.model_dump()).execute()
    return result.data[0]


@router.put("/{shift_id}")
def update_shift_type(shift_id: str, shift: ShiftTypeUpdate):
    sb = get_supabase()
    data = {k: v for k, v in shift.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = sb.table("shift_types").update(data).eq("id", shift_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Shift type not found")
    return result.data[0]


@router.delete("/{shift_id}", status_code=204)
def delete_shift_type(shift_id: str):
    sb = get_supabase()
    sb.table("shift_types").delete().eq("id", shift_id).execute()
