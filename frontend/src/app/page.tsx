"use client";

import { useEffect, useState } from "react";
import { getEmployees, getSchedules, getShiftTypes, Employee, Schedule, ShiftType } from "@/lib/api";
import { Users, Calendar, Clock, Activity } from "lucide-react";

export default function Dashboard() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [shiftTypes, setShiftTypes] = useState<ShiftType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getEmployees(), getSchedules(), getShiftTypes()])
      .then(([emps, scheds, shifts]) => {
        setEmployees(emps);
        setSchedules(scheds);
        setShiftTypes(shifts);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    {
      label: "Collaborateurs",
      value: employees.length,
      icon: Users,
      color: "text-blue-600 bg-blue-100",
    },
    {
      label: "Types de shifts",
      value: shiftTypes.length,
      icon: Clock,
      color: "text-green-600 bg-green-100",
    },
    {
      label: "Plannings générés",
      value: schedules.length,
      icon: Calendar,
      color: "text-purple-600 bg-purple-100",
    },
    {
      label: "Taux activité moyen",
      value: employees.length
        ? `${Math.round(employees.reduce((s, e) => s + e.activity_rate, 0) / employees.length)}%`
        : "—",
      icon: Activity,
      color: "text-orange-600 bg-orange-100",
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.label} className="card flex items-center gap-4">
            <div className={`p-3 rounded-lg ${stat.color}`}>
              <stat.icon size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Répartition par rôle</h3>
          {["infirmier", "assc", "aide-soignant"].map((role) => {
            const count = employees.filter((e) => e.role === role).length;
            const pct = employees.length ? (count / employees.length) * 100 : 0;
            return (
              <div key={role} className="mb-3">
                <div className="flex justify-between text-sm mb-1">
                  <span className="capitalize">{role}</span>
                  <span className="font-medium">{count}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-500 h-2 rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Derniers plannings</h3>
          {schedules.length === 0 ? (
            <p className="text-gray-500 text-sm">Aucun planning généré</p>
          ) : (
            <div className="space-y-3">
              {schedules.slice(0, 5).map((s) => (
                <div
                  key={s.id}
                  className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {s.period_start} → {s.period_end}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(s.created_at).toLocaleDateString("fr-CH")}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      s.status === "published"
                        ? "bg-green-100 text-green-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {s.status === "published" ? "Publié" : "Brouillon"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
