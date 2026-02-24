"use client";

import { useEffect, useState } from "react";
import {
  getEmployees,
  getConstraints,
  createEmployee,
  updateEmployee,
  deleteEmployee,
  Employee,
  EmployeeCreate,
} from "@/lib/api";
import { Plus, Save, Trash2, X, Pencil } from "lucide-react";
import EmployeeForm from "@/components/forms/EmployeeForm";

const ALL_DAY_LABELS = [
  { key: "lundi", label: "L" },
  { key: "mardi", label: "M" },
  { key: "mercredi", label: "M" },
  { key: "jeudi", label: "J" },
  { key: "vendredi", label: "V" },
  { key: "samedi", label: "S" },
  { key: "dimanche", label: "D" },
];

const WEEKDAY_KEYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"];
const RATE_OPTIONS = [20, 40, 60, 80, 100];

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [weekendEnabled, setWeekendEnabled] = useState(false);

  // Inline editing state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    first_name: "",
    last_name: "",
    role: "",
    activity_rate: 100,
    working_days: [] as string[],
  });

  const load = () => {
    Promise.all([getEmployees(), getConstraints()])
      .then(([emps, constraints]) => {
        setEmployees(emps);
        const weekendRule = constraints.find((c) => c.name === "weekend_work");
        setWeekendEnabled(weekendRule?.is_active ?? false);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const visibleDays = weekendEnabled
    ? ALL_DAY_LABELS
    : ALL_DAY_LABELS.filter((d) => WEEKDAY_KEYS.includes(d.key));

  const handleCreate = async (data: EmployeeCreate) => {
    await createEmployee(data);
    setShowForm(false);
    load();
  };

  const handleEdit = (emp: Employee) => {
    setEditingId(emp.id);
    setEditForm({
      first_name: emp.first_name,
      last_name: emp.last_name,
      role: emp.role,
      activity_rate: emp.activity_rate,
      working_days: emp.working_days || [],
    });
  };

  const handleSave = async (id: string) => {
    await updateEmployee(id, editForm);
    setEditingId(null);
    load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Supprimer ce collaborateur ?")) return;
    await deleteEmployee(id);
    load();
  };

  const editMaxDays = editForm.activity_rate / 20;

  const toggleEditDay = (day: string) => {
    setEditForm((prev) => {
      const isSelected = prev.working_days.includes(day);
      if (isSelected) {
        return { ...prev, working_days: prev.working_days.filter((d) => d !== day) };
      }
      if (prev.working_days.length >= editMaxDays) return prev;
      return { ...prev, working_days: [...prev.working_days, day] };
    });
  };

  const handleEditRateChange = (newRate: number) => {
    const newMax = newRate / 20;
    setEditForm((prev) => {
      let days = [...prev.working_days];
      if (days.length > newMax) {
        days = days.slice(0, newMax);
      }
      if (days.length < newMax) {
        const pool = weekendEnabled
          ? ALL_DAY_LABELS.map((d) => d.key)
          : WEEKDAY_KEYS;
        for (const d of pool) {
          if (days.length >= newMax) break;
          if (!days.includes(d)) days.push(d);
        }
      }
      return { ...prev, activity_rate: newRate, working_days: days };
    });
  };

  const roleColors: Record<string, string> = {
    infirmier: "bg-blue-100 text-blue-700",
    assc: "bg-green-100 text-green-700",
    "aide-soignant": "bg-orange-100 text-orange-700",
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Collaborateurs</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus size={18} />
          Ajouter
        </button>
      </div>

      {showForm && (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4">Nouveau collaborateur</h3>
          <EmployeeForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            weekendEnabled={weekendEnabled}
          />
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Nom</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Prenom</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Taux</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Jours</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase w-28">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {employees.map((emp) => (
                <tr key={emp.id} className="hover:bg-gray-50">
                  {editingId === emp.id ? (
                    <>
                      <td className="px-4 py-2">
                        <input
                          type="text"
                          className="input w-full"
                          value={editForm.last_name}
                          onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="text"
                          className="input w-full"
                          value={editForm.first_name}
                          onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <select
                          className="input"
                          value={editForm.role}
                          onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                        >
                          <option value="infirmier">Infirmier</option>
                          <option value="assc">ASSC</option>
                          <option value="aide-soignant">Aide-soignant</option>
                        </select>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <select
                          className="input w-20 text-center"
                          value={editForm.activity_rate}
                          onChange={(e) => handleEditRateChange(Number(e.target.value))}
                        >
                          {RATE_OPTIONS.map((r) => (
                            <option key={r} value={r}>{r}%</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex justify-center gap-1">
                          {visibleDays.map(({ key, label }) => {
                            const isSelected = editForm.working_days.includes(key);
                            const isDisabled = !isSelected && editForm.working_days.length >= editMaxDays;
                            return (
                              <button
                                key={key}
                                type="button"
                                onClick={() => toggleEditDay(key)}
                                disabled={isDisabled}
                                className={`w-7 h-7 rounded-full text-xs font-bold transition-colors ${
                                  isSelected
                                    ? "bg-primary-600 text-white"
                                    : isDisabled
                                      ? "bg-gray-50 text-gray-300 cursor-not-allowed"
                                      : "bg-gray-100 text-gray-400"
                                }`}
                              >
                                {label}
                              </button>
                            );
                          })}
                        </div>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <div className="flex justify-center gap-1">
                          <button
                            className="p-1.5 rounded hover:bg-green-100 text-green-600"
                            onClick={() => handleSave(emp.id)}
                            title="Sauvegarder"
                          >
                            <Save size={16} />
                          </button>
                          <button
                            className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
                            onClick={() => setEditingId(null)}
                            title="Annuler"
                          >
                            <X size={16} />
                          </button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3 font-medium">{emp.last_name}</td>
                      <td className="px-4 py-3">{emp.first_name}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${roleColors[emp.role] || "bg-gray-100"}`}>
                          {emp.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">{emp.activity_rate}%</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-center gap-1">
                          {visibleDays.map(({ key, label }) => (
                            <span
                              key={key}
                              className={`w-7 h-7 rounded-full text-xs font-bold inline-flex items-center justify-center ${
                                emp.working_days?.includes(key)
                                  ? "bg-primary-100 text-primary-700"
                                  : "bg-gray-50 text-gray-300"
                              }`}
                            >
                              {label}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex justify-center gap-1">
                          <button
                            className="p-1.5 rounded hover:bg-blue-100 text-blue-600"
                            onClick={() => handleEdit(emp)}
                            title="Modifier"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(emp.id)}
                            className="p-1.5 rounded hover:bg-red-100 text-red-500"
                            title="Supprimer"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          {employees.length === 0 && (
            <p className="text-center text-gray-500 py-8">Aucun collaborateur</p>
          )}
        </div>
      )}
    </div>
  );
}
