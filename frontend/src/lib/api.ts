const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API error");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Employees
export const getEmployees = () => request<Employee[]>("/api/employees");
export const getEmployee = (id: string) => request<Employee>(`/api/employees/${id}`);
export const createEmployee = (data: EmployeeCreate) =>
  request<Employee>("/api/employees", { method: "POST", body: JSON.stringify(data) });
export const updateEmployee = (id: string, data: Partial<EmployeeCreate>) =>
  request<Employee>(`/api/employees/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteEmployee = (id: string) =>
  request<void>(`/api/employees/${id}`, { method: "DELETE" });

// Shift Types
export const getShiftTypes = () => request<ShiftType[]>("/api/shifts");
export const createShiftType = (data: ShiftTypeCreate) =>
  request<ShiftType>("/api/shifts", { method: "POST", body: JSON.stringify(data) });
export const deleteShiftType = (id: string) =>
  request<void>(`/api/shifts/${id}`, { method: "DELETE" });

// Coverage
export const getCoverage = () => request<CoverageRequirement[]>("/api/coverage");
export const createCoverage = (data: CoverageCreate) =>
  request<CoverageRequirement>("/api/coverage", { method: "POST", body: JSON.stringify(data) });
export const updateCoverage = (id: string, data: Partial<CoverageCreate>) =>
  request<CoverageRequirement>(`/api/coverage/${id}`, { method: "PUT", body: JSON.stringify(data) });

// Absences
export const getAbsences = (employeeId?: string) =>
  request<Absence[]>(`/api/absences${employeeId ? `?employee_id=${employeeId}` : ""}`);
export const createAbsence = (data: AbsenceCreate) =>
  request<Absence>("/api/absences", { method: "POST", body: JSON.stringify(data) });
export const deleteAbsence = (id: string) =>
  request<void>(`/api/absences/${id}`, { method: "DELETE" });

// Schedules
export const getSchedules = () => request<Schedule[]>("/api/schedules");
export const getSchedule = (id: string) => request<ScheduleDetail>(`/api/schedules/${id}`);
export const generateSchedule = (data: ScheduleGenerateRequest) =>
  request<ScheduleDetail>("/api/schedules/generate", { method: "POST", body: JSON.stringify(data) });
export const deleteSchedule = (id: string) =>
  request<void>(`/api/schedules/${id}`, { method: "DELETE" });

// Constraints
export const getConstraints = () => request<ConstraintRule[]>("/api/constraints");
export const updateConstraint = (id: string, data: { parameter?: object; is_active?: boolean }) =>
  request<ConstraintRule>(`/api/constraints/${id}`, { method: "PUT", body: JSON.stringify(data) });

// Types
export interface Employee {
  id: string;
  first_name: string;
  last_name: string;
  role: string;
  activity_rate: number;
  can_do_night: boolean;
  can_do_weekend: boolean;
  preferred_shifts: string[];
  created_at: string;
}

export interface EmployeeCreate {
  first_name: string;
  last_name: string;
  role: string;
  activity_rate: number;
  can_do_night: boolean;
  can_do_weekend: boolean;
  preferred_shifts: string[];
}

export interface ShiftType {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  created_at: string;
}

export interface ShiftTypeCreate {
  name: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
}

export interface CoverageRequirement {
  id: string;
  shift_type_id: string;
  day_type: string;
  min_employees: number;
  required_roles: { role: string; min: number }[];
  shift_types?: { name: string };
}

export interface CoverageCreate {
  shift_type_id: string;
  day_type: string;
  min_employees: number;
  required_roles: { role: string; min: number }[];
}

export interface Absence {
  id: string;
  employee_id: string;
  date_start: string;
  date_end: string;
  type: string;
  employees?: { first_name: string; last_name: string };
}

export interface AbsenceCreate {
  employee_id: string;
  date_start: string;
  date_end: string;
  type: string;
}

export interface Schedule {
  id: string;
  period_start: string;
  period_end: string;
  status: string;
  solver_stats: object;
  created_at: string;
}

export interface ScheduleAssignment {
  id: string;
  schedule_id: string;
  employee_id: string;
  shift_type_id: string;
  date: string;
  is_locked: boolean;
  employees?: { first_name: string; last_name: string; role: string };
  shift_types?: { name: string; start_time: string; end_time: string };
}

export interface ScheduleDetail extends Schedule {
  assignments: ScheduleAssignment[];
}

export interface ScheduleGenerateRequest {
  period_start: string;
  period_end: string;
  locked_assignments?: { employee_id: string; shift_type_id: string; date: string }[];
}

export interface ConstraintRule {
  id: string;
  name: string;
  type: string;
  parameter: object;
  is_active: boolean;
}
