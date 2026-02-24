import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()


class ShiftTypeCreate(BaseModel):
    name: str
    start_time: str  # HH:MM
    end_time: str
    duration_hours: float
    short_label: str = ""  # single char for calendar display


class ShiftTypeUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_hours: Optional[float] = None
    short_label: Optional[str] = None


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
    data = shift.model_dump()
    if not data.get("short_label"):
        data["short_label"] = shift.name[0].upper() if shift.name else "X"
    result = sb.table("shift_types").insert(data).execute()
    new_shift = result.data[0]

    # Auto-create coverage requirements for all 3 day types
    for day_type in ("weekday", "saturday", "sunday"):
        try:
            sb.table("coverage_requirements").insert({
                "shift_type_id": new_shift["id"],
                "day_type": day_type,
                "min_infirmier": 0,
                "min_assc": 0,
                "min_aide_soignant": 0,
            }).execute()
        except Exception as e:
            logger.error(f"Failed to create coverage for {day_type}: {e}")

    return new_shift


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
