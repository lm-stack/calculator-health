from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_supabase

router = APIRouter()


class ConstraintUpdate(BaseModel):
    parameter: Optional[dict] = None
    is_active: Optional[bool] = None


@router.get("")
def list_constraints():
    sb = get_supabase()
    result = sb.table("constraint_rules").select("*").order("type,name").execute()
    return result.data


@router.put("/{constraint_id}")
def update_constraint(constraint_id: str, constraint: ConstraintUpdate):
    sb = get_supabase()
    data = {k: v for k, v in constraint.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = sb.table("constraint_rules").update(data).eq("id", constraint_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Constraint not found")
    return result.data[0]
