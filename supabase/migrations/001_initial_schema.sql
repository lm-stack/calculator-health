-- Calculator Health — Initial Schema
-- Run this in Supabase SQL Editor

-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- ============================================
-- Table: employees
-- ============================================
create table if not exists employees (
    id uuid primary key default uuid_generate_v4(),
    first_name text not null,
    last_name text not null,
    role text not null check (role in ('infirmier', 'assc', 'aide-soignant')),
    activity_rate integer not null default 100 check (activity_rate between 10 and 100),
    can_do_night boolean not null default true,
    can_do_weekend boolean not null default true,
    preferred_shifts jsonb default '[]'::jsonb,
    created_at timestamptz not null default now()
);

-- ============================================
-- Table: shift_types
-- ============================================
create table if not exists shift_types (
    id uuid primary key default uuid_generate_v4(),
    name text not null unique,
    start_time time not null,
    end_time time not null,
    duration_hours numeric(4,2) not null,
    created_at timestamptz not null default now()
);

-- ============================================
-- Table: coverage_requirements
-- ============================================
create table if not exists coverage_requirements (
    id uuid primary key default uuid_generate_v4(),
    shift_type_id uuid not null references shift_types(id) on delete cascade,
    day_type text not null check (day_type in ('weekday', 'saturday', 'sunday')),
    min_employees integer not null default 1,
    required_roles jsonb default '[]'::jsonb,
    unique (shift_type_id, day_type)
);

-- ============================================
-- Table: absences
-- ============================================
create table if not exists absences (
    id uuid primary key default uuid_generate_v4(),
    employee_id uuid not null references employees(id) on delete cascade,
    date_start date not null,
    date_end date not null,
    type text not null check (type in ('vacances', 'maladie', 'congé')),
    check (date_end >= date_start)
);

-- ============================================
-- Table: schedules
-- ============================================
create table if not exists schedules (
    id uuid primary key default uuid_generate_v4(),
    period_start date not null,
    period_end date not null,
    status text not null default 'draft' check (status in ('draft', 'published')),
    solver_stats jsonb default '{}'::jsonb,
    created_at timestamptz not null default now(),
    check (period_end > period_start)
);

-- ============================================
-- Table: schedule_assignments
-- ============================================
create table if not exists schedule_assignments (
    id uuid primary key default uuid_generate_v4(),
    schedule_id uuid not null references schedules(id) on delete cascade,
    employee_id uuid not null references employees(id) on delete cascade,
    shift_type_id uuid not null references shift_types(id) on delete cascade,
    date date not null,
    is_locked boolean not null default false,
    unique (schedule_id, employee_id, date)
);

-- ============================================
-- Table: constraint_rules
-- ============================================
create table if not exists constraint_rules (
    id uuid primary key default uuid_generate_v4(),
    name text not null unique,
    type text not null check (type in ('hard', 'soft')),
    parameter jsonb default '{}'::jsonb,
    is_active boolean not null default true
);

-- ============================================
-- Indexes
-- ============================================
create index if not exists idx_absences_employee on absences(employee_id);
create index if not exists idx_absences_dates on absences(date_start, date_end);
create index if not exists idx_assignments_schedule on schedule_assignments(schedule_id);
create index if not exists idx_assignments_employee on schedule_assignments(employee_id);
create index if not exists idx_assignments_date on schedule_assignments(date);

-- ============================================
-- Row Level Security (optional, for Supabase)
-- ============================================
alter table employees enable row level security;
alter table shift_types enable row level security;
alter table coverage_requirements enable row level security;
alter table absences enable row level security;
alter table schedules enable row level security;
alter table schedule_assignments enable row level security;
alter table constraint_rules enable row level security;

-- Allow all operations for authenticated users (adjust for production)
create policy "Allow all for authenticated" on employees for all using (true);
create policy "Allow all for authenticated" on shift_types for all using (true);
create policy "Allow all for authenticated" on coverage_requirements for all using (true);
create policy "Allow all for authenticated" on absences for all using (true);
create policy "Allow all for authenticated" on schedules for all using (true);
create policy "Allow all for authenticated" on schedule_assignments for all using (true);
create policy "Allow all for authenticated" on constraint_rules for all using (true);

-- ============================================
-- Default constraint rules
-- ============================================
insert into constraint_rules (name, type, parameter, is_active) values
    ('max_one_shift_per_day', 'hard', '{}', true),
    ('min_coverage', 'hard', '{}', true),
    ('min_rest_hours', 'hard', '{"hours": 11}', true),
    ('max_weekly_hours', 'hard', '{"base_hours": 42}', true),
    ('respect_absences', 'hard', '{}', true),
    ('required_roles', 'hard', '{}', true),
    ('weekend_rest', 'hard', '{"min_free_weekends_per_2weeks": 1}', true),
    ('shift_regularity', 'soft', '{"weight": 10}', true),
    ('respect_preferences', 'soft', '{"weight": 5}', true),
    ('night_weekend_equity', 'soft', '{"weight": 8}', true)
on conflict (name) do nothing;

-- ============================================
-- Default shift types
-- ============================================
insert into shift_types (name, start_time, end_time, duration_hours) values
    ('Matin', '06:30', '14:30', 8.0),
    ('Après-midi', '14:00', '22:00', 8.0),
    ('Nuit', '21:30', '06:30', 9.0)
on conflict (name) do nothing;
