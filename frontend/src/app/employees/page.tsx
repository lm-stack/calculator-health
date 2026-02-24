"use client";

import { useEffect, useState } from "react";
import {
  getEmployees,
  createEmployee,
  deleteEmployee,
  Employee,
  EmployeeCreate,
} from "@/lib/api";
import { Plus, Trash2, Moon, Sun } from "lucide-react";
import EmployeeForm from "@/components/forms/EmployeeForm";

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const load = () => {
    getEmployees()
      .then(setEmployees)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async (data: EmployeeCreate) => {
    await createEmployee(data);
    setShowForm(false);
    load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Supprimer ce collaborateur ?")) return;
    await deleteEmployee(id);
    load();
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
          <EmployeeForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} />
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
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Nom</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Rôle</th>
                <th className="text-center px-6 py-3 text-xs font-medium text-gray-500 uppercase">Taux</th>
                <th className="text-center px-6 py-3 text-xs font-medium text-gray-500 uppercase">Nuit</th>
                <th className="text-center px-6 py-3 text-xs font-medium text-gray-500 uppercase">Week-end</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Préférences</th>
                <th className="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {employees.map((emp) => (
                <tr key={emp.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">
                    {emp.first_name} {emp.last_name}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${roleColors[emp.role] || "bg-gray-100"}`}>
                      {emp.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">{emp.activity_rate}%</td>
                  <td className="px-6 py-4 text-center">
                    {emp.can_do_night ? (
                      <Moon size={16} className="inline text-indigo-500" />
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {emp.can_do_weekend ? (
                      <Sun size={16} className="inline text-amber-500" />
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {emp.preferred_shifts?.join(", ") || "—"}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleDelete(emp.id)}
                      className="text-red-400 hover:text-red-600 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
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
