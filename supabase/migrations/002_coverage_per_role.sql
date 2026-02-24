-- Migration: Replace min_employees + required_roles with per-role minimums
-- Run this in Supabase SQL Editor after 001_initial_schema.sql

-- Step 1: Add per-role columns
alter table coverage_requirements
  add column if not exists min_infirmier integer not null default 0,
  add column if not exists min_assc integer not null default 0,
  add column if not exists min_aide_soignant integer not null default 0;

-- Step 2: Migrate existing data from required_roles JSON + min_employees
-- For each row, extract role minimums from the JSON array,
-- then distribute any remaining min_employees across roles
do $$
declare
  r record;
  role_entry jsonb;
  inf_min int;
  assc_min int;
  as_min int;
begin
  for r in select id, min_employees, required_roles from coverage_requirements loop
    inf_min := 0;
    assc_min := 0;
    as_min := 0;

    -- Extract minimums from required_roles JSON array
    if r.required_roles is not null and jsonb_array_length(r.required_roles) > 0 then
      for role_entry in select * from jsonb_array_elements(r.required_roles) loop
        case role_entry->>'role'
          when 'infirmier' then inf_min := (role_entry->>'min')::int;
          when 'assc' then assc_min := (role_entry->>'min')::int;
          when 'aide-soignant' then as_min := (role_entry->>'min')::int;
        end case;
      end loop;
    end if;

    -- If min_employees is higher than sum of role mins, add the difference to infirmier
    if r.min_employees > (inf_min + assc_min + as_min) then
      inf_min := inf_min + (r.min_employees - (inf_min + assc_min + as_min));
    end if;

    update coverage_requirements
      set min_infirmier = inf_min,
          min_assc = assc_min,
          min_aide_soignant = as_min
      where id = r.id;
  end loop;
end $$;

-- Step 3: Drop old columns
alter table coverage_requirements drop column if exists min_employees;
alter table coverage_requirements drop column if exists required_roles;

-- Step 4: Rename constraint rule required_roles -> min_per_role
update constraint_rules set name = 'min_per_role' where name = 'required_roles';
