"""OR-Tools CP-SAT solver for the Nurse Scheduling Problem."""

import time
from datetime import date, timedelta
from ortools.sat.python import cp_model

from app.solver.models import (
    Employee, ShiftType, CoverageRequirement, Absence, LockedAssignment,
)
from app.solver.constraints import (
    add_one_shift_per_day,
    add_coverage_constraints,
    add_rest_between_shifts,
    add_max_weekly_hours,
    add_absence_constraints,
    add_night_capability,
    add_weekend_capability,
    add_weekend_rest,
    add_locked_assignments,
)
from app.solver.objectives import (
    add_shift_regularity_objective,
    add_preference_objective,
    add_night_weekend_equity_objective,
)


def _parse_employees(raw: list) -> list[Employee]:
    return [
        Employee(
            id=e["id"],
            first_name=e["first_name"],
            last_name=e["last_name"],
            role=e["role"],
            activity_rate=e["activity_rate"],
            can_do_night=e["can_do_night"],
            can_do_weekend=e["can_do_weekend"],
            preferred_shifts=e.get("preferred_shifts") or [],
        )
        for e in raw
    ]


def _parse_shift_types(raw: list) -> list[ShiftType]:
    return [
        ShiftType(
            id=s["id"],
            name=s["name"],
            start_time=s["start_time"],
            end_time=s["end_time"],
            duration_hours=float(s["duration_hours"]),
        )
        for s in raw
    ]


def _parse_coverage(raw: list) -> list[CoverageRequirement]:
    return [
        CoverageRequirement(
            shift_type_id=c["shift_type_id"],
            day_type=c["day_type"],
            min_employees=c["min_employees"],
            required_roles=c.get("required_roles") or [],
        )
        for c in raw
    ]


def _parse_absences(raw: list) -> list[Absence]:
    return [
        Absence(
            employee_id=a["employee_id"],
            date_start=a["date_start"],
            date_end=a["date_end"],
            type=a["type"],
        )
        for a in raw
    ]


def _parse_locked(raw: list) -> list[LockedAssignment]:
    return [
        LockedAssignment(
            employee_id=l["employee_id"],
            shift_type_id=l["shift_type_id"],
            date=l["date"],
        )
        for l in raw
    ]


def _generate_days(start: str, end: str) -> list[date]:
    d_start = date.fromisoformat(start)
    d_end = date.fromisoformat(end)
    days = []
    current = d_start
    while current <= d_end:
        days.append(current)
        current += timedelta(days=1)
    return days


def solve_schedule(
    employees: list,
    shift_types: list,
    coverage_requirements: list,
    absences: list,
    constraint_rules: list,
    period_start: str,
    period_end: str,
    locked_assignments: list = None,
    time_limit_seconds: int = 30,
) -> dict | None:
    """Solve the nurse scheduling problem and return assignments + stats."""

    start_time = time.time()

    # Parse input data
    emps = _parse_employees(employees)
    shifts = _parse_shift_types(shift_types)
    coverage = _parse_coverage(coverage_requirements)
    abs_list = _parse_absences(absences)
    locked = _parse_locked(locked_assignments or [])
    days = _generate_days(period_start, period_end)

    num_employees = len(emps)
    num_shifts = len(shifts)
    num_days = len(days)

    # Build constraint rule lookup
    rule_params = {}
    for r in constraint_rules:
        rule_params[r["name"]] = r.get("parameter") or {}

    # Create model
    model = cp_model.CpModel()

    # Decision variables: shifts_var[(e, d, s)] = 1 if employee e works shift s on day d
    shifts_var = {}
    for e_idx in range(num_employees):
        for d_idx in range(num_days):
            for s_idx in range(num_shifts):
                shifts_var[(e_idx, d_idx, s_idx)] = model.NewBoolVar(
                    f"shift_e{e_idx}_d{d_idx}_s{s_idx}"
                )

    # === Hard constraints ===
    add_one_shift_per_day(model, shifts_var, emps, shifts, days)
    add_coverage_constraints(model, shifts_var, emps, shifts, days, coverage)

    min_rest = rule_params.get("min_rest_hours", {}).get("hours", 11)
    add_rest_between_shifts(model, shifts_var, emps, shifts, days, min_rest)

    add_max_weekly_hours(model, shifts_var, emps, shifts, days)
    add_absence_constraints(model, shifts_var, emps, shifts, days, abs_list)
    add_night_capability(model, shifts_var, emps, shifts, days)
    add_weekend_capability(model, shifts_var, emps, shifts, days)

    min_free_we = rule_params.get("weekend_rest", {}).get("min_free_weekends_per_2weeks", 1)
    add_weekend_rest(model, shifts_var, emps, shifts, days, min_free_we)

    if locked:
        add_locked_assignments(model, shifts_var, emps, shifts, days, locked)

    # === Soft objectives ===
    objective_terms = []

    reg_weight = rule_params.get("shift_regularity", {}).get("weight", 10)
    reg_vars, reg_w = add_shift_regularity_objective(
        model, shifts_var, emps, shifts, days, reg_weight
    )
    for v in reg_vars:
        objective_terms.append(v * reg_w)

    pref_weight = rule_params.get("respect_preferences", {}).get("weight", 5)
    pref_vars, pref_w = add_preference_objective(
        model, shifts_var, emps, shifts, days, pref_weight
    )
    for v in pref_vars:
        objective_terms.append(v * pref_w)

    eq_vars, eq_w = add_night_weekend_equity_objective(
        model, shifts_var, emps, shifts, days,
        rule_params.get("night_weekend_equity", {}).get("weight", 8),
    )
    for v in eq_vars:
        objective_terms.append(v * eq_w)

    if objective_terms:
        model.Maximize(sum(objective_terms))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_workers = 4

    status = solver.Solve(model)
    solve_time_ms = int((time.time() - start_time) * 1000)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    # Extract assignments
    assignments = []
    locked_set = {(l.employee_id, l.date) for l in locked}
    for e_idx, emp in enumerate(emps):
        for d_idx, day in enumerate(days):
            for s_idx, shift in enumerate(shifts):
                if solver.Value(shifts_var[(e_idx, d_idx, s_idx)]) == 1:
                    assignments.append({
                        "employee_id": emp.id,
                        "shift_type_id": shift.id,
                        "date": day.isoformat(),
                        "is_locked": (emp.id, day.isoformat()) in locked_set,
                    })

    return {
        "assignments": assignments,
        "stats": {
            "solve_time_ms": solve_time_ms,
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "objective_value": solver.ObjectiveValue() if objective_terms else 0,
            "num_employees": num_employees,
            "num_days": num_days,
            "num_assignments": len(assignments),
        },
    }
