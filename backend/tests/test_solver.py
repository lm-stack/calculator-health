"""Tests for the OR-Tools scheduling solver."""

import pytest
from app.solver.engine import solve_schedule


def _make_employees(count=10):
    roles = ["infirmier", "assc", "aide-soignant"]
    employees = []
    for i in range(count):
        employees.append({
            "id": f"emp-{i}",
            "first_name": f"Prénom{i}",
            "last_name": f"Nom{i}",
            "role": roles[i % 3],
            "activity_rate": 100,
            "can_do_night": i % 4 != 0,  # emp 0,4,8 can't do nights
            "can_do_weekend": True,       # all can do weekends
            "preferred_shifts": [],
        })
    return employees


def _make_shift_types():
    return [
        {"id": "shift-matin", "name": "Matin", "start_time": "06:30", "end_time": "14:30", "duration_hours": 8.0},
        {"id": "shift-apm", "name": "Après-midi", "start_time": "14:00", "end_time": "22:00", "duration_hours": 8.0},
        {"id": "shift-nuit", "name": "Nuit", "start_time": "21:30", "end_time": "06:30", "duration_hours": 9.0},
    ]


def _make_coverage():
    shifts = _make_shift_types()
    coverage = []
    for s in shifts:
        for day_type in ["weekday", "saturday", "sunday"]:
            if s["name"] == "Nuit":
                min_emp = 1
            elif day_type == "weekday":
                min_emp = 2
            else:
                min_emp = 1
            # Only require infirmier role on weekday day shifts
            roles = []
            if day_type == "weekday" and s["name"] != "Nuit":
                roles = [{"role": "infirmier", "min": 1}]
            coverage.append({
                "shift_type_id": s["id"],
                "day_type": day_type,
                "min_employees": min_emp,
                "required_roles": roles,
            })
    return coverage


def _make_constraint_rules():
    return [
        {"name": "min_rest_hours", "type": "hard", "parameter": {"hours": 11}, "is_active": True},
        {"name": "max_weekly_hours", "type": "hard", "parameter": {"base_hours": 42}, "is_active": True},
        {"name": "weekend_rest", "type": "hard", "parameter": {"min_free_weekends_per_2weeks": 1}, "is_active": True},
        {"name": "shift_regularity", "type": "soft", "parameter": {"weight": 10}, "is_active": True},
        {"name": "respect_preferences", "type": "soft", "parameter": {"weight": 5}, "is_active": True},
        {"name": "night_weekend_equity", "type": "soft", "parameter": {"weight": 8}, "is_active": True},
    ]


class TestSolverBasic:
    """Basic solver functionality tests."""

    def test_solve_one_week(self):
        """Solver produces a valid schedule for 1 week with 10 employees."""
        result = solve_schedule(
            employees=_make_employees(10),
            shift_types=_make_shift_types(),
            coverage_requirements=_make_coverage(),
            absences=[],
            constraint_rules=_make_constraint_rules(),
            period_start="2026-03-02",  # Monday
            period_end="2026-03-08",    # Sunday
        )

        assert result is not None
        assert result["stats"]["status"] in ("optimal", "feasible")
        assert len(result["assignments"]) > 0

    def test_solve_two_weeks(self):
        """Solver handles a 2-week period."""
        result = solve_schedule(
            employees=_make_employees(15),
            shift_types=_make_shift_types(),
            coverage_requirements=_make_coverage(),
            absences=[],
            constraint_rules=_make_constraint_rules(),
            period_start="2026-03-02",
            period_end="2026-03-15",
        )

        assert result is not None
        assert result["stats"]["num_days"] == 14

    def test_one_shift_per_day(self):
        """No employee has more than one shift per day."""
        result = solve_schedule(
            employees=_make_employees(10),
            shift_types=_make_shift_types(),
            coverage_requirements=_make_coverage(),
            absences=[],
            constraint_rules=_make_constraint_rules(),
            period_start="2026-03-02",
            period_end="2026-03-08",
        )

        assert result is not None
        # Check no duplicate (employee, date)
        seen = set()
        for a in result["assignments"]:
            key = (a["employee_id"], a["date"])
            assert key not in seen, f"Employee {a['employee_id']} has multiple shifts on {a['date']}"
            seen.add(key)

    def test_absences_respected(self):
        """Employees on leave are not assigned shifts."""
        absences = [
            {"employee_id": "emp-0", "date_start": "2026-03-02", "date_end": "2026-03-05", "type": "vacances"},
        ]

        result = solve_schedule(
            employees=_make_employees(10),
            shift_types=_make_shift_types(),
            coverage_requirements=_make_coverage(),
            absences=absences,
            constraint_rules=_make_constraint_rules(),
            period_start="2026-03-02",
            period_end="2026-03-08",
        )

        assert result is not None
        for a in result["assignments"]:
            if a["employee_id"] == "emp-0":
                assert a["date"] > "2026-03-05", f"emp-0 assigned on {a['date']} during absence"

    def test_no_employees_returns_none(self):
        """Solver returns None if no feasible solution (no employees)."""
        result = solve_schedule(
            employees=[],
            shift_types=_make_shift_types(),
            coverage_requirements=_make_coverage(),
            absences=[],
            constraint_rules=_make_constraint_rules(),
            period_start="2026-03-02",
            period_end="2026-03-08",
        )

        # With coverage requirements but no employees, should be infeasible
        # However if no coverage, it could return empty. Our coverage needs min 1-3
        # So this should be None (infeasible) or return with 0 assignments
        # With empty employees list, no variables are created, coverage can't be met
        assert result is None or len(result["assignments"]) == 0


class TestSolverConstraints:
    """Test specific constraints."""

    def test_night_shift_capability(self):
        """Employees who can't do night shifts are never assigned nights."""
        employees = _make_employees(10)
        # emp-0 has can_do_night = False (i%4 == 0)

        result = solve_schedule(
            employees=employees,
            shift_types=_make_shift_types(),
            coverage_requirements=_make_coverage(),
            absences=[],
            constraint_rules=_make_constraint_rules(),
            period_start="2026-03-02",
            period_end="2026-03-08",
        )

        assert result is not None
        for a in result["assignments"]:
            if a["employee_id"] == "emp-0":
                assert a["shift_type_id"] != "shift-nuit", "emp-0 should not do night shifts"

    def test_locked_assignments(self):
        """Locked assignments are preserved in the solution."""
        locked = [
            {"employee_id": "emp-1", "shift_type_id": "shift-matin", "date": "2026-03-02"},
        ]

        result = solve_schedule(
            employees=_make_employees(10),
            shift_types=_make_shift_types(),
            coverage_requirements=_make_coverage(),
            absences=[],
            constraint_rules=_make_constraint_rules(),
            period_start="2026-03-02",
            period_end="2026-03-08",
            locked_assignments=locked,
        )

        assert result is not None
        found = False
        for a in result["assignments"]:
            if a["employee_id"] == "emp-1" and a["date"] == "2026-03-02":
                assert a["shift_type_id"] == "shift-matin"
                assert a["is_locked"] is True
                found = True
        assert found, "Locked assignment not found in result"


class TestSolverScale:
    """Test solver with larger inputs."""

    def test_solve_25_employees_one_month(self):
        """Solver handles 25 employees over 1 month (the pilot scenario)."""
        result = solve_schedule(
            employees=_make_employees(25),
            shift_types=_make_shift_types(),
            coverage_requirements=_make_coverage(),
            absences=[
                {"employee_id": "emp-2", "date_start": "2026-03-10", "date_end": "2026-03-17", "type": "vacances"},
                {"employee_id": "emp-5", "date_start": "2026-03-15", "date_end": "2026-03-20", "type": "maladie"},
            ],
            constraint_rules=_make_constraint_rules(),
            period_start="2026-03-01",
            period_end="2026-03-31",
            time_limit_seconds=30,
        )

        assert result is not None
        assert result["stats"]["status"] in ("optimal", "feasible")
        assert result["stats"]["num_employees"] == 25
        assert result["stats"]["num_days"] == 31
        # Should have a reasonable number of assignments
        assert result["stats"]["num_assignments"] > 100
