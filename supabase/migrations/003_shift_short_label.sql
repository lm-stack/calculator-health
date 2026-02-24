-- Migration: Add short_label to shift_types for calendar display
ALTER TABLE shift_types ADD COLUMN IF NOT EXISTS short_label char(1) NOT NULL DEFAULT 'X';
UPDATE shift_types SET short_label = LEFT(name, 1);
