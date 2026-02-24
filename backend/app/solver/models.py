from dataclasses import dataclass, field
from datetime import date, time


@dataclass
class Employee:
    id: str
    first_name: str
    last_name: str
    role: str
    activity_rate: int
    working_days: list = field(default_factory=lambda: ["lundi", "mardi", "mercredi", "jeudi", "vendredi"])

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
        """Detect night shift by schedule: starts >= 20h or crosses midnight."""
        start = self.start_hour()
        end = self.end_hour()
        return start >= 20 or end < start

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
    min_infirmier: int = 0
    min_assc: int = 0
    min_aide_soignant: int = 0

    @property
    def min_employees(self) -> int:
        """Total minimum = sum of all role minimums."""
        return self.min_infirmier + self.min_assc + self.min_aide_soignant

    @property
    def role_minimums(self) -> dict[str, int]:
        """Dict of role -> minimum count (only non-zero)."""
        mins = {
            "infirmier": self.min_infirmier,
            "assc": self.min_assc,
            "aide-soignant": self.min_aide_soignant,
        }
        return {k: v for k, v in mins.items() if v > 0}


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
