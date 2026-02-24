"""Seed script to populate Supabase with realistic test data.

Usage: python seed.py
Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
    sys.exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

WEEKDAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]

# === Shift types ===
print("Seeding shift types...")
shift_types = [
    {"name": "Matin", "start_time": "06:30", "end_time": "14:30", "duration_hours": 8.0},
    {"name": "Apres-midi", "start_time": "14:00", "end_time": "22:00", "duration_hours": 8.0},
    {"name": "Nuit", "start_time": "21:30", "end_time": "06:30", "duration_hours": 9.0},
]

for st in shift_types:
    try:
        sb.table("shift_types").upsert(st, on_conflict="name").execute()
    except Exception as e:
        print(f"  Shift type '{st['name']}': {e}")

shifts_data = sb.table("shift_types").select("id, name").execute().data
shift_map = {s["name"]: s["id"] for s in shifts_data}
print(f"  -> {len(shift_map)} shift types")

# === Employees ===
# Rule: nb jours = taux / 20, all weekdays only (no weekend)
print("Seeding employees...")
employees_data = [
    # Infirmiers (10)
    {"first_name": "Marie", "last_name": "Dupont", "role": "infirmier", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Jean", "last_name": "Martin", "role": "infirmier", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Sophie", "last_name": "Bernard", "role": "infirmier", "activity_rate": 80, "working_days": WEEKDAYS[:4]},
    {"first_name": "Pierre", "last_name": "Robert", "role": "infirmier", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Claire", "last_name": "Petit", "role": "infirmier", "activity_rate": 60, "working_days": ["lundi", "mercredi", "vendredi"]},
    {"first_name": "Lucas", "last_name": "Moreau", "role": "infirmier", "activity_rate": 40, "working_days": ["lundi", "jeudi"]},
    {"first_name": "Emma", "last_name": "Leroy", "role": "infirmier", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Thomas", "last_name": "Roux", "role": "infirmier", "activity_rate": 80, "working_days": WEEKDAYS[:4]},
    {"first_name": "Julie", "last_name": "David", "role": "infirmier", "activity_rate": 60, "working_days": ["mardi", "mercredi", "jeudi"]},
    {"first_name": "Antoine", "last_name": "Bertrand", "role": "infirmier", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    # ASSC (9)
    {"first_name": "Lea", "last_name": "Garcia", "role": "assc", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Hugo", "last_name": "Martinez", "role": "assc", "activity_rate": 80, "working_days": WEEKDAYS[:4]},
    {"first_name": "Camille", "last_name": "Lopez", "role": "assc", "activity_rate": 60, "working_days": ["lundi", "mercredi", "vendredi"]},
    {"first_name": "Nathan", "last_name": "Gonzalez", "role": "assc", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Manon", "last_name": "Wilson", "role": "assc", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Louis", "last_name": "Anderson", "role": "assc", "activity_rate": 20, "working_days": ["mercredi"]},
    {"first_name": "Jade", "last_name": "Thomas", "role": "assc", "activity_rate": 40, "working_days": ["mardi", "jeudi"]},
    {"first_name": "Raphael", "last_name": "Taylor", "role": "assc", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Chloe", "last_name": "Moore", "role": "assc", "activity_rate": 80, "working_days": WEEKDAYS[:4]},
    # Aides-soignants (6)
    {"first_name": "Gabriel", "last_name": "Jackson", "role": "aide-soignant", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Ines", "last_name": "White", "role": "aide-soignant", "activity_rate": 80, "working_days": WEEKDAYS[:4]},
    {"first_name": "Arthur", "last_name": "Harris", "role": "aide-soignant", "activity_rate": 60, "working_days": ["lundi", "mercredi", "vendredi"]},
    {"first_name": "Lina", "last_name": "Clark", "role": "aide-soignant", "activity_rate": 100, "working_days": WEEKDAYS[:5]},
    {"first_name": "Adam", "last_name": "Lewis", "role": "aide-soignant", "activity_rate": 40, "working_days": ["lundi", "vendredi"]},
    {"first_name": "Rose", "last_name": "Walker", "role": "aide-soignant", "activity_rate": 20, "working_days": ["jeudi"]},
]

for emp in employees_data:
    try:
        sb.table("employees").insert(emp).execute()
    except Exception as e:
        print(f"  Employee '{emp['first_name']} {emp['last_name']}': {e}")

emp_count = len(sb.table("employees").select("id").execute().data)
print(f"  -> {emp_count} employees")

# === Coverage requirements ===
print("Seeding coverage requirements...")
coverage_data = [
    # Matin
    {"shift_type_id": shift_map["Matin"], "day_type": "weekday", "min_infirmier": 2, "min_assc": 1, "min_aide_soignant": 1},
    {"shift_type_id": shift_map["Matin"], "day_type": "saturday", "min_infirmier": 1, "min_assc": 1, "min_aide_soignant": 1},
    {"shift_type_id": shift_map["Matin"], "day_type": "sunday", "min_infirmier": 1, "min_assc": 1, "min_aide_soignant": 1},
    # Apres-midi
    {"shift_type_id": shift_map["Apres-midi"], "day_type": "weekday", "min_infirmier": 2, "min_assc": 1, "min_aide_soignant": 1},
    {"shift_type_id": shift_map["Apres-midi"], "day_type": "saturday", "min_infirmier": 1, "min_assc": 1, "min_aide_soignant": 1},
    {"shift_type_id": shift_map["Apres-midi"], "day_type": "sunday", "min_infirmier": 1, "min_assc": 1, "min_aide_soignant": 1},
    # Nuit
    {"shift_type_id": shift_map["Nuit"], "day_type": "weekday", "min_infirmier": 1, "min_assc": 1, "min_aide_soignant": 0},
    {"shift_type_id": shift_map["Nuit"], "day_type": "saturday", "min_infirmier": 1, "min_assc": 1, "min_aide_soignant": 0},
    {"shift_type_id": shift_map["Nuit"], "day_type": "sunday", "min_infirmier": 1, "min_assc": 1, "min_aide_soignant": 0},
]

for cov in coverage_data:
    try:
        sb.table("coverage_requirements").upsert(
            cov, on_conflict="shift_type_id,day_type"
        ).execute()
    except Exception as e:
        print(f"  Coverage: {e}")

cov_count = len(sb.table("coverage_requirements").select("id").execute().data)
print(f"  -> {cov_count} coverage requirements")

# === Absences (sample) ===
print("Seeding sample absences...")
emp_ids = [e["id"] for e in sb.table("employees").select("id").order("last_name").execute().data]

if len(emp_ids) >= 5:
    sample_absences = [
        {"employee_id": emp_ids[0], "date_start": "2026-03-10", "date_end": "2026-03-17", "type": "vacances"},
        {"employee_id": emp_ids[3], "date_start": "2026-03-15", "date_end": "2026-03-16", "type": "conge"},
        {"employee_id": emp_ids[4], "date_start": "2026-03-20", "date_end": "2026-03-25", "type": "maladie"},
    ]
    for absence in sample_absences:
        try:
            sb.table("absences").insert(absence).execute()
        except Exception as e:
            print(f"  Absence: {e}")

print("Seed complete!")
