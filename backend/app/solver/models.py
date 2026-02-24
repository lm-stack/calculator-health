from dataclasses import dataclass, field
from datetime import date, time


@dataclass
class Employee:
    id: str
    first_name: str
    last_name: str
    role: str
    activity_rate: int
    can_do_night: bool
    can_do_weekend: bool
    preferred_shifts: list = field(default_factory=list)

    @property
    def max_weekly_hours(self) -> float:
        return 42.0 * self.activity_rate / 100.0


@dataclass
class ShiftType:
    id: str
    name: str
    start_time: str  # HH:MM
    end_time: str
    duration_hours: float

    @property
    def is_night(self) -> bool:
        return self.name.lower() in ("nuit", "night")

    def start_hour(self) -> float:
        parts = self.start_time.split(":")
        return int(parts[0]) + int(parts[1]) / 60.0

    def end_hour(self) -> float:
        parts = self.end_time.split(":")
        return int(parts[0]) + int(parts[1]) / 60.0


@dataclass
class CoverageRequirement:
    shift_type_id: str
    day_type: str  # weekday, saturday, sunday
    min_employees: int
    required_roles: list = field(default_factory=list)


@dataclass
class Absence:
    employee_id: str
    date_start: str  # YYYY-MM-DD
    date_end: str
    type: str


@dataclass
class LockedAssignment:
    employee_id: str
    shift_type_id: str
    date: str  # YYYY-MM-DD


@dataclass
class SolverResult:
    assignments: list  # [{employee_id, shift_type_id, date, is_locked}]
    stats: dict  # {solve_time_ms, status, objective_value}
