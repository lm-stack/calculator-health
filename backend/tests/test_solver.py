"""Tests for the OR-Tools scheduling solver."""

import pytest
from app.solver.engine import solve_schedule
from app.solver.models import ShiftType

ALL_DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
WEEKDAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]


def _make_employees(count=10):
    roles = ["infirmier", "assc", "aide-soignant"]
    employees = []
    for i in range(count):
        # emp 0, 4, 8 = weekdays only (no weekend)
        if i % 4 == 0:
            days = WEEKDAYS
        else:
            days = ALL_DAYS
        employees.append({
            "id": f"emp-{i}",
            "first_name": f"Prenom{i}",
            "last_name": f"Nom{i}",
            "role": roles[i % 3],
            "activity_rate": 100,
            "working_days": days,
        })
    return employees


def _make_shift_types():
    return [
        {"id": "shift-matin", "name": "Matin", "start_time": "06:30", "end_time": "14:30", "duration_hours": 8.0},
        {"id": "shift-apm", "name": "Apres-midi", "start_time": "14:00", "end_time": "22:00", "duration_hours": 8.0},
        {"id": "shift-nuit", "name": "Nuit", "start_time": "21:30", "end_time": "06:30", "duration_hours": 9.0},
    ]


def _make_coverage():
    """Build coverage requirements feasible for 10+ employees.

    Spread roles across shifts so no single role is overwhelmed:
      - Matin weekday: 1 infirmier
      - Apres-midi weekday: 1 ASSC
      - Nuit weekday: 1 aide-soignant (night-capable)
      - Weekends: no per-role requirement (total = 0)
    """
    shifts = _make_shift_types()
    coverage = []
    for s in shifts:
        for day_type in ["weekday", "saturday", "sunday"]:
            if day_type != "weekday":
                inf, assc, aide = 0, 0, 0
            elif s["name"] == "Matin":
                inf, assc, aide = 1, 0, 0
            elif "midi" in s["name"]:
                inf, assc, aide = 0, 1, 0
            else:  # Nuit
                inf, assc, aide = 0, 0, 1
            coverage.append({
                "shift_type_id": s["id"],
                "day_type": day_type,
                "min_infirmier": inf,
                "min_assc": assc,
                "min_aide_soignant": aide,
            })
    return coverage


def _make_constraint_rules():
    return [
        {"name": "min_rest_hours", "type": "hard", "parameter": {"hours": 11}, "is_active": True},
        {"name": "max_weekly_hours", "type": "hard", "parameter": {"base_hours": 42}, "is_active": True},
        {"name": "weekend_rest", "type": "hard", "parameter": {"min_free_weekends_per_2weeks": 1}, "is_active": True},
        {"name": "shift_regularity", "type": "soft", "parameter": {"weight": 10}, "is_active": True},
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


class TestNightDetection:
    """Test night shift detection by schedule (not by name)."""

    def test_nuit_shift_detected(self):
        """Standard 'Nuit' shift (21:30-06:30) is detected as night."""
        s = ShiftType(id="1", name="Nuit", start_time="21:30", end_time="06:30", duration_hours=9)
        assert s.is_night is True

    def test_evening_crossing_midnight(self):
        """A shift starting at 22:00 and ending at 06:00 is night."""
        s = ShiftType(id="2", name="Veille", start_time="22:00", end_time="06:00", duration_hours=8)
        assert s.is_night is True

    def test_late_evening_start(self):
        """A shift starting at 20:00 is night even if ending before midnight."""
        s = ShiftType(id="3", name="Soir+", start_time="20:00", end_time="23:59", duration_hours=4)
        assert s.is_night is True

    def test_matin_not_night(self):
        """Morning shift is not night."""
        s = ShiftType(id="4", name="Matin", start_time="06:30", end_time="14:30", duration_hours=8)
        assert s.is_night is False

    def test_aprem_not_night(self):
        """Afternoon shift is not night."""
        s = ShiftType(id="5", name="Apres-midi", start_time="14:00", end_time="22:00", duration_hours=8)
        assert s.is_night is False

    def test_custom_name_still_night(self):
        """A shift with a custom name is night if schedule says so."""
        s = ShiftType(id="6", name="Custom Late", start_time="21:00", end_time="05:00", duration_hours=8)
        assert s.is_night is True


class TestSolverConstraints:
    """Test specific constraints."""

    def test_working_days_constraint(self):
        """Employees with weekdays-only working_days are never assigned on weekends."""
        employees = _make_employees(10)
        # emp-0 has working_days = WEEKDAYS (i%4 == 0)

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
                # 2026-03-07 = Saturday, 2026-03-08 = Sunday
                assert a["date"] not in ("2026-03-07", "2026-03-08"), \
                    "emp-0 should not work on weekends"

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
