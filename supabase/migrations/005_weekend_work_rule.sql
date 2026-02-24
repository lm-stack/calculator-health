-- Add weekend_work toggle (disabled by default = weekdays only)
INSERT INTO constraint_rules (name, type, parameter, is_active)
VALUES ('weekend_work', 'hard', '{}', false)
ON CONFLICT (name) DO NOTHING;

-- Remove obsolete respect_preferences rule
DELETE FROM constraint_rules WHERE name = 'respect_preferences';
