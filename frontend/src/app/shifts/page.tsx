"use client";

import { useEffect, useState } from "react";
import {
  getShiftTypes,
  getCoverage,
  createCoverage,
  updateCoverage,
  ShiftType,
  CoverageRequirement,
} from "@/lib/api";

export default function ShiftsPage() {
  const [shifts, setShifts] = useState<ShiftType[]>([]);
  const [coverage, setCoverage] = useState<CoverageRequirement[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    Promise.all([getShiftTypes(), getCoverage()])
      .then(([s, c]) => {
        setShifts(s);
        setCoverage(c);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCoverageChange = async (
    covId: string,
    field: string,
    value: number
  ) => {
    await updateCoverage(covId, { [field]: value });
    load();
  };

  const dayTypeLabels: Record<string, string> = {
    weekday: "Semaine",
    saturday: "Samedi",
    sunday: "Dimanche",
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Configuration des shifts</h2>

      {/* Shift types */}
      <div className="card mb-6">
        <h3 className="text-lg font-semibold mb-4">Types de shifts</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {shifts.map((shift) => (
            <div
              key={shift.id}
              className="border border-gray-200 rounded-lg p-4"
            >
              <p className="font-semibold text-lg">{shift.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                {shift.start_time} — {shift.end_time}
              </p>
              <p className="text-sm text-gray-500">
                {shift.duration_hours}h
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Coverage requirements */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">
          Besoins de couverture (minimum par créneau)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                  Shift
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                  Jour
                </th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                  Min. employés
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                  Rôles requis
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {coverage.map((cov) => (
                <tr key={cov.id}>
                  <td className="px-4 py-3 font-medium">
                    {cov.shift_types?.name || cov.shift_type_id}
                  </td>
                  <td className="px-4 py-3">
                    {dayTypeLabels[cov.day_type] || cov.day_type}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <input
                      type="number"
                      min={1}
                      max={20}
                      className="w-16 text-center input"
                      value={cov.min_employees}
                      onChange={(e) =>
                        handleCoverageChange(
                          cov.id,
                          "min_employees",
                          Number(e.target.value)
                        )
                      }
                    />
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {cov.required_roles
                      ?.map((r) => `${r.min}× ${r.role}`)
                      .join(", ") || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {coverage.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              Aucune couverture configurée
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
