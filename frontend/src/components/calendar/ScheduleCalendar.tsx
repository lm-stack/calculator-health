"use client";

import { useMemo } from "react";
import { ScheduleDetail, ScheduleAssignment } from "@/lib/api";
import { format, parseISO, eachDayOfInterval, isWeekend } from "date-fns";
import { fr } from "date-fns/locale";

interface Props {
  schedule: ScheduleDetail;
}

const SHIFT_COLOR_PALETTE = [
  "bg-amber-200 text-amber-800",
  "bg-blue-200 text-blue-800",
  "bg-indigo-300 text-indigo-900",
  "bg-emerald-200 text-emerald-800",
  "bg-rose-200 text-rose-800",
  "bg-violet-200 text-violet-800",
  "bg-cyan-200 text-cyan-800",
  "bg-orange-200 text-orange-800",
];

export default function ScheduleCalendar({ schedule }: Props) {
  const days = useMemo(
    () =>
      eachDayOfInterval({
        start: parseISO(schedule.period_start),
        end: parseISO(schedule.period_end),
      }),
    [schedule.period_start, schedule.period_end]
  );

  // Build dynamic color map + label map from shift data in assignments
  const { shiftColors, shiftLabels } = useMemo(() => {
    const nameSet = new Set<string>();
    const labels: Record<string, string> = {};
    for (const a of schedule.assignments) {
      const name = a.shift_types?.name;
      if (name) {
        nameSet.add(name);
        if (!labels[name]) {
          labels[name] = a.shift_types?.short_label || name.charAt(0);
        }
      }
    }
    const colors: Record<string, string> = {};
    const sorted = [...nameSet].sort();
    sorted.forEach((name, i) => {
      colors[name] = SHIFT_COLOR_PALETTE[i % SHIFT_COLOR_PALETTE.length];
    });
    return { shiftColors: colors, shiftLabels: labels };
  }, [schedule.assignments]);

  // Group assignments by employee
  const employeeList = useMemo(() => {
    const map: Record<string, { name: string; role: string; assignments: Record<string, ScheduleAssignment> }> = {};

    for (const a of schedule.assignments) {
      const empId = a.employee_id;
      if (!map[empId]) {
        map[empId] = {
          name: a.employees
            ? `${a.employees.first_name} ${a.employees.last_name}`
            : empId,
          role: a.employees?.role || "",
          assignments: {},
        };
      }
      map[empId].assignments[a.date] = a;
    }

    // Sort by name and return as array of [id, data]
    return Object.entries(map).sort((a, b) => a[1].name.localeCompare(b[1].name));
  }, [schedule.assignments]);

  const stats = schedule.solver_stats as Record<string, unknown>;

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header stats */}
      <div className="px-4 py-3 bg-gray-50 border-b flex items-center gap-6 text-sm">
        <span>
          <strong>{schedule.period_start}</strong> →{" "}
          <strong>{schedule.period_end}</strong>
        </span>
        {stats && (
          <>
            <span className="text-gray-500">
              Résolu en {String(stats.solve_time_ms || "?")}ms
            </span>
            <span className="text-gray-500">
              {String(stats.num_assignments || "?")} affectations
            </span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                stats.status === "optimal"
                  ? "bg-green-100 text-green-700"
                  : "bg-yellow-100 text-yellow-700"
              }`}
            >
              {String(stats.status || "?")}
            </span>
          </>
        )}
      </div>

      {/* Calendar grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-gray-600 sticky left-0 bg-gray-50 min-w-[160px] z-10">
                Collaborateur
              </th>
              {days.map((day) => (
                <th
                  key={day.toISOString()}
                  className={`px-1 py-2 text-center font-medium min-w-[48px] ${
                    isWeekend(day) ? "bg-gray-100 text-gray-500" : "text-gray-600"
                  }`}
                >
                  <div>{format(day, "EEE", { locale: fr })}</div>
                  <div>{format(day, "d")}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {employeeList.map(([empId, emp]) => (
              <tr key={empId} className="hover:bg-gray-50">
                <td className="px-3 py-1.5 font-medium sticky left-0 bg-white z-10 border-r">
                  <div>{emp.name}</div>
                  <div className="text-gray-400 text-[10px]">{emp.role}</div>
                </td>
                {days.map((day) => {
                  const dateStr = format(day, "yyyy-MM-dd");
                  const assignment = emp.assignments[dateStr];
                  const shiftName = assignment?.shift_types?.name || "";
                  const shiftLabel = assignment?.shift_types?.short_label || shiftName.charAt(0);
                  return (
                    <td
                      key={dateStr}
                      className={`px-0.5 py-1 text-center ${
                        isWeekend(day) ? "bg-gray-50" : ""
                      }`}
                    >
                      {assignment ? (
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${
                            shiftColors[shiftName] || "bg-gray-200 text-gray-700"
                          } ${assignment.is_locked ? "ring-2 ring-red-400" : ""}`}
                        >
                          {shiftLabel}
                        </span>
                      ) : (
                        <span className="text-gray-300">·</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="px-4 py-3 border-t bg-gray-50 flex items-center gap-4 text-xs text-gray-600">
        <span className="font-medium">Légende :</span>
        {Object.entries(shiftColors).map(([name, cls]) => (
          <span key={name} className="flex items-center gap-1">
            <span className={`inline-block w-4 h-4 rounded text-center text-[9px] leading-4 ${cls}`}>
              {shiftLabels[name] || name.charAt(0)}
            </span>
            {name}
          </span>
        ))}
        <span className="flex items-center gap-1">
          <span className="inline-block w-4 h-4 rounded bg-gray-200 ring-2 ring-red-400" />
          Verrouillé
        </span>
      </div>
    </div>
  );
}
