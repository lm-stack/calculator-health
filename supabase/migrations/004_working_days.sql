-- Migration: Replace can_do_night / can_do_weekend / preferred_shifts
-- with a single working_days jsonb column.

ALTER TABLE employees
  ADD COLUMN IF NOT EXISTS working_days jsonb
    NOT NULL
    DEFAULT '["lundi","mardi","mercredi","jeudi","vendredi"]'::jsonb;

-- Migrate existing data: employees who can_do_weekend get all 7 days
UPDATE employees
SET working_days = CASE
  WHEN can_do_weekend = true
    THEN '["lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"]'::jsonb
  ELSE '["lundi","mardi","mercredi","jeudi","vendredi"]'::jsonb
END;

-- Drop obsolete columns
ALTER TABLE employees
  DROP COLUMN IF EXISTS can_do_night,
  DROP COLUMN IF EXISTS can_do_weekend,
  DROP COLUMN IF EXISTS preferred_shifts;

NOTIFY pgrst, 'reload schema';
