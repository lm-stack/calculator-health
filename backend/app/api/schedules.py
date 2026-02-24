from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase_client import get_supabase
from app.solver.engine import solve_schedule

router = APIRouter()


class ScheduleGenerateRequest(BaseModel):
    period_start: str  # YYYY-MM-DD
    period_end: str
    locked_assignments: list = []  # [{employee_id, shift_type_id, date}]


class SchedulePublish(BaseModel):
    status: str  # draft / published


@router.get("")
def list_schedules():
    sb = get_supabase()
    result = sb.table("schedules").select("*").order("created_at", desc=True).execute()
    return result.data


@router.get("/{schedule_id}")
def get_schedule(schedule_id: str):
    sb = get_supabase()
    schedule = sb.table("schedules").select("*").eq("id", schedule_id).execute()
    if not schedule.data:
        raise HTTPException(status_code=404, detail="Schedule not found")

    assignments = (
        sb.table("schedule_assignments")
        .select("*, employees(first_name, last_name, role), shift_types(name, start_time, end_time, short_label)")
        .eq("schedule_id", schedule_id)
        .order("date,employee_id")
        .execute()
    )

    return {
        **schedule.data[0],
        "assignments": assignments.data,
    }


@router.post("/generate", status_code=201)
def generate_schedule(req: ScheduleGenerateRequest):
    sb = get_supabase()

    # Fetch all needed data
    employees = sb.table("employees").select("*").execute().data
    shift_types = sb.table("shift_types").select("*").execute().data
    coverage = sb.table("coverage_requirements").select("*").execute().data
    absences = sb.table("absences").select("*").execute().data
    constraints = sb.table("constraint_rules").select("*").eq("is_active", True).execute().data

    if not employees:
        raise HTTPException(status_code=400, detail="No employees configured")
    if not shift_types:
        raise HTTPException(status_code=400, detail="No shift types configured")

    # Solve
    result = solve_schedule(
        employees=employees,
        shift_types=shift_types,
        coverage_requirements=coverage,
        absences=absences,
        constraint_rules=constraints,
        period_start=req.period_start,
        period_end=req.period_end,
        locked_assignments=req.locked_assignments,
    )

    if result is None:
        raise HTTPException(status_code=422, detail="No feasible schedule found")

    # Save schedule
    schedule = sb.table("schedules").insert({
        "period_start": req.period_start,
        "period_end": req.period_end,
        "status": "draft",
        "solver_stats": result["stats"],
    }).execute()

    schedule_id = schedule.data[0]["id"]

    # Save assignments
    assignments_to_insert = []
    for a in result["assignments"]:
        assignments_to_insert.append({
            "schedule_id": schedule_id,
            "employee_id": a["employee_id"],
            "shift_type_id": a["shift_type_id"],
            "date": a["date"],
            "is_locked": a.get("is_locked", False),
        })

    if assignments_to_insert:
        sb.table("schedule_assignments").insert(assignments_to_insert).execute()

    return get_schedule(schedule_id)


@router.put("/{schedule_id}/status")
def update_schedule_status(schedule_id: str, body: SchedulePublish):
    sb = get_supabase()
    result = sb.table("schedules").update({"status": body.status}).eq("id", schedule_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return result.data[0]


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: str):
    sb = get_supabase()
    sb.table("schedule_assignments").delete().eq("schedule_id", schedule_id).execute()
    sb.table("schedules").delete().eq("id", schedule_id).execute()
