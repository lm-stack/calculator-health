"""Hard constraints for the nurse scheduling solver."""

from datetime import date, timedelta
from app.solver.models import Employee, ShiftType, CoverageRequirement, Absence


def add_one_shift_per_day(model, shifts_var, employees, shift_types, days):
    """Each employee works at most one shift per day."""
    for e_idx, emp in enumerate(employees):
        for d_idx in range(len(days)):
            model.AddAtMostOne(
                shifts_var[(e_idx, d_idx, s_idx)]
                for s_idx in range(len(shift_types))
            )


def add_coverage_constraints(model, shifts_var, employees, shift_types, days, coverage_reqs):
    """Each shift on each day must meet minimum staffing requirements."""
    for d_idx, day in enumerate(days):
        day_type = _get_day_type(day)
        for s_idx, shift in enumerate(shift_types):
            # Find matching coverage requirement
            matching = [c for c in coverage_reqs
                        if c.shift_type_id == shift.id and c.day_type == day_type]
            if not matching:
                continue
            cov = matching[0]

            # Minimum total employees
            model.Add(
                sum(shifts_var[(e_idx, d_idx, s_idx)] for e_idx in range(len(employees)))
                >= cov.min_employees
            )

            # Required roles
            for role_req in cov.required_roles:
                role_name = role_req.get("role", "")
                min_count = role_req.get("min", 1)
                eligible = [e_idx for e_idx, emp in enumerate(employees)
                            if emp.role == role_name]
                if eligible:
                    model.Add(
                        sum(shifts_var[(e_idx, d_idx, s_idx)] for e_idx in eligible)
                        >= min_count
                    )


def add_rest_between_shifts(model, shifts_var, employees, shift_types, days, min_rest_hours=11):
    """Minimum rest hours between consecutive shifts.

    For non-night shifts ending on day d, rest = (24 - end_hour) + start_hour_next.
    For night shifts ending on morning of day d+1, rest = start_hour_next - end_hour.
    """
    for e_idx in range(len(employees)):
        for d_idx in range(len(days) - 1):
            for s1_idx, s1 in enumerate(shift_types):
                for s2_idx, s2 in enumerate(shift_types):
                    end_hour = s1.end_hour()
                    start_hour = s2.start_hour()

                    if s1.is_night:
                        # Night shift ends next morning (day d+1), s2 also starts day d+1
                        gap = start_hour - end_hour
                        if gap < 0:
                            gap += 24
                    else:
                        # Normal shift ends on day d, s2 starts on day d+1
                        gap = (24 - end_hour) + start_hour

                    if gap < min_rest_hours:
                        model.AddBoolOr([
                            shifts_var[(e_idx, d_idx, s1_idx)].Not(),
                            shifts_var[(e_idx, d_idx + 1, s2_idx)].Not(),
                        ])


def add_max_weekly_hours(model, shifts_var, employees, shift_types, days):
    """Enforce maximum weekly hours based on activity rate."""
    num_days = len(days)
    # Process week by week
    for week_start in range(0, num_days, 7):
        week_end = min(week_start + 7, num_days)
        for e_idx, emp in enumerate(employees):
            # Sum of hours this week * 10 to work with integers
            weekly_hours_x10 = sum(
                shifts_var[(e_idx, d_idx, s_idx)] * int(shift_types[s_idx].duration_hours * 10)
                for d_idx in range(week_start, week_end)
                for s_idx in range(len(shift_types))
            )
            max_hours_x10 = int(emp.max_weekly_hours * 10)
            model.Add(weekly_hours_x10 <= max_hours_x10)


def add_absence_constraints(model, shifts_var, employees, shift_types, days, absences):
    """No assignments on absence days."""
    for absence in absences:
        e_idx = next(
            (i for i, emp in enumerate(employees) if emp.id == absence.employee_id),
            None,
        )
        if e_idx is None:
            continue

        abs_start = date.fromisoformat(absence.date_start)
        abs_end = date.fromisoformat(absence.date_end)

        for d_idx, day in enumerate(days):
            if abs_start <= day <= abs_end:
                for s_idx in range(len(shift_types)):
                    model.Add(shifts_var[(e_idx, d_idx, s_idx)] == 0)


def add_night_capability(model, shifts_var, employees, shift_types, days):
    """Only employees with can_do_night can work night shifts."""
    night_indices = [s_idx for s_idx, s in enumerate(shift_types) if s.is_night]
    for e_idx, emp in enumerate(employees):
        if not emp.can_do_night:
            for d_idx in range(len(days)):
                for s_idx in night_indices:
                    model.Add(shifts_var[(e_idx, d_idx, s_idx)] == 0)


def add_weekend_capability(model, shifts_var, employees, shift_types, days):
    """Only employees with can_do_weekend can work weekends."""
    for e_idx, emp in enumerate(employees):
        if not emp.can_do_weekend:
            for d_idx, day in enumerate(days):
                if day.weekday() >= 5:  # Saturday=5, Sunday=6
                    for s_idx in range(len(shift_types)):
                        model.Add(shifts_var[(e_idx, d_idx, s_idx)] == 0)


def add_weekend_rest(model, shifts_var, employees, shift_types, days, min_free_weekends=1):
    """At least 1 free weekend per 2-week period."""
    num_days = len(days)
    for e_idx in range(len(employees)):
        # Find all weekends (Saturday + Sunday pairs)
        weekends = []
        for d_idx, day in enumerate(days):
            if day.weekday() == 5:  # Saturday
                sun_idx = d_idx + 1
                if sun_idx < num_days and days[sun_idx].weekday() == 6:
                    weekends.append((d_idx, sun_idx))

        # For each 2-consecutive-weekend window
        for w in range(0, len(weekends) - 1, 2):
            weekend_pair = weekends[w:w + 2]
            if len(weekend_pair) < 2:
                break

            # For each weekend, create a bool var: is this weekend free?
            free_weekend_vars = []
            for sat_idx, sun_idx in weekend_pair:
                is_free = model.NewBoolVar(f"free_we_{e_idx}_{sat_idx}")
                # is_free = 1 iff no shifts on Saturday and Sunday
                all_shifts = []
                for s_idx in range(len(shift_types)):
                    all_shifts.append(shifts_var[(e_idx, sat_idx, s_idx)])
                    all_shifts.append(shifts_var[(e_idx, sun_idx, s_idx)])

                # is_free => all shifts are 0
                for sv in all_shifts:
                    model.Add(sv == 0).OnlyEnforceIf(is_free)
                # not is_free => at least one shift is 1
                model.AddBoolOr(all_shifts).OnlyEnforceIf(is_free.Not())

                free_weekend_vars.append(is_free)

            model.Add(sum(free_weekend_vars) >= min_free_weekends)


def add_locked_assignments(model, shifts_var, employees, shift_types, days, locked):
    """Force locked (manually set) assignments."""
    for lock in locked:
        e_idx = next(
            (i for i, emp in enumerate(employees) if emp.id == lock.employee_id),
            None,
        )
        s_idx = next(
            (i for i, s in enumerate(shift_types) if s.id == lock.shift_type_id),
            None,
        )
        d_idx = next(
            (i for i, d in enumerate(days) if d.isoformat() == lock.date),
            None,
        )
        if e_idx is not None and s_idx is not None and d_idx is not None:
            model.Add(shifts_var[(e_idx, d_idx, s_idx)] == 1)


def _get_day_type(day: date) -> str:
    weekday = day.weekday()
    if weekday < 5:
        return "weekday"
    elif weekday == 5:
        return "saturday"
    else:
        return "sunday"
