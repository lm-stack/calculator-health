from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_supabase

router = APIRouter()


class CoverageCreate(BaseModel):
    shift_type_id: str
    day_type: str  # weekday, saturday, sunday
    min_infirmier: int = 0
    min_assc: int = 0
    min_aide_soignant: int = 0


class CoverageUpdate(BaseModel):
    min_infirmier: Optional[int] = None
    min_assc: Optional[int] = None
    min_aide_soignant: Optional[int] = None


@router.get("")
def list_coverage():
    sb = get_supabase()
    result = sb.table("coverage_requirements").select("*, shift_types(name)").execute()
    return result.data


@router.post("", status_code=201)
def create_coverage(cov: CoverageCreate):
    sb = get_supabase()
    result = sb.table("coverage_requirements").insert(cov.model_dump()).execute()
    return result.data[0]


@router.put("/{coverage_id}")
def update_coverage(coverage_id: str, cov: CoverageUpdate):
    sb = get_supabase()
    data = {k: v for k, v in cov.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = sb.table("coverage_requirements").update(data).eq("id", coverage_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Coverage requirement not found")
    return result.data[0]


@router.delete("/{coverage_id}", status_code=204)
def delete_coverage(coverage_id: str):
    sb = get_supabase()
    sb.table("coverage_requirements").delete().eq("id", coverage_id).execute()
