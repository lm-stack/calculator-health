"use client";

import { useEffect, useState } from "react";
import {
  getShiftTypes,
  getCoverage,
  getConstraints,
  createCoverage,
  updateCoverage,
  createShiftType,
  updateShiftType,
  deleteShiftType,
  ShiftType,
  CoverageRequirement,
} from "@/lib/api";
import { Plus, Save, Trash2, X } from "lucide-react";

const LABEL_OPTIONS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export default function ShiftsPage() {
  const [shifts, setShifts] = useState<ShiftType[]>([]);
  const [coverage, setCoverage] = useState<CoverageRequirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [weekendEnabled, setWeekendEnabled] = useState(false);

  // Shift editing state
  const [editingShift, setEditingShift] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ name: "", start_time: "", end_time: "", duration_hours: 0, short_label: "" });
  const [addingShift, setAddingShift] = useState(false);
  const [newShift, setNewShift] = useState({ name: "", start_time: "08:00", end_time: "16:00", duration_hours: 8, short_label: "" });

  const load = () => {
    Promise.all([getShiftTypes(), getCoverage(), getConstraints()])
      .then(([s, c, constraints]) => {
        setShifts(s);
        setCoverage(c);
        const weekendRule = constraints.find((r) => r.name === "weekend_work");
        setWeekendEnabled(weekendRule?.is_active ?? false);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  // Labels already used by other shifts
  const usedLabels = shifts.map((s) => s.short_label?.toUpperCase()).filter(Boolean);

  // Shift CRUD
  const handleEditShift = (shift: ShiftType) => {
    setEditingShift(shift.id);
    setEditForm({
      name: shift.name,
      start_time: shift.start_time,
      end_time: shift.end_time,
      duration_hours: shift.duration_hours,
      short_label: shift.short_label || shift.name.charAt(0).toUpperCase(),
    });
  };

  const handleSaveShift = async (id: string) => {
    await updateShiftType(id, editForm);
    setEditingShift(null);
    load();
  };

  const handleDeleteShift = async (id: string) => {
    await deleteShiftType(id);
    load();
  };

  const handleAddShift = async () => {
    if (!newShift.name.trim()) return;
    const label = newShift.short_label || newShift.name.charAt(0).toUpperCase();
    await createShiftType({ ...newShift, short_label: label });
    setAddingShift(false);
    setNewShift({ name: "", start_time: "08:00", end_time: "16:00", duration_hours: 8, short_label: "" });
    load();
  };

  // Coverage
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

      {/* Shift types — editable table */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Types de shifts</h3>
          {!addingShift && (
            <button
              className="btn btn-primary flex items-center gap-1 text-sm"
              onClick={() => setAddingShift(true)}
            >
              <Plus size={16} /> Ajouter
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-center px-3 py-3 text-xs font-medium text-gray-500 uppercase w-16">Label</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Nom</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Début</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Fin</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Durée (h)</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {shifts.map((shift) => (
                <tr key={shift.id}>
                  {editingShift === shift.id ? (
                    <>
                      <td className="px-3 py-2 text-center">
                        <select
                          className="input w-14 text-center font-bold"
                          value={editForm.short_label}
                          onChange={(e) => setEditForm({ ...editForm, short_label: e.target.value })}
                        >
                          {LABEL_OPTIONS.map((l) => (
                            <option key={l} value={l} disabled={usedLabels.includes(l) && l !== shift.short_label?.toUpperCase()}>
                              {l}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="text"
                          className="input w-full"
                          value={editForm.name}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <input
                          type="time"
                          className="input w-28 text-center"
                          value={editForm.start_time}
                          onChange={(e) => setEditForm({ ...editForm, start_time: e.target.value })}
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <input
                          type="time"
                          className="input w-28 text-center"
                          value={editForm.end_time}
                          onChange={(e) => setEditForm({ ...editForm, end_time: e.target.value })}
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <input
                          type="number"
                          step="0.5"
                          min={1}
                          max={24}
                          className="input w-20 text-center"
                          value={editForm.duration_hours}
                          onChange={(e) => setEditForm({ ...editForm, duration_hours: Number(e.target.value) })}
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <div className="flex justify-center gap-1">
                          <button
                            className="p-1.5 rounded hover:bg-green-100 text-green-600"
                            onClick={() => handleSaveShift(shift.id)}
                            title="Sauvegarder"
                          >
                            <Save size={16} />
                          </button>
                          <button
                            className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
                            onClick={() => setEditingShift(null)}
                            title="Annuler"
                          >
                            <X size={16} />
                          </button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-3 py-3 text-center">
                        <span className="inline-block w-8 h-8 leading-8 rounded bg-gray-100 font-bold text-sm">
                          {shift.short_label || shift.name.charAt(0)}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium">{shift.name}</td>
                      <td className="px-4 py-3 text-center">{shift.start_time}</td>
                      <td className="px-4 py-3 text-center">{shift.end_time}</td>
                      <td className="px-4 py-3 text-center">{shift.duration_hours}h</td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex justify-center gap-1">
                          <button
                            className="p-1.5 rounded hover:bg-blue-100 text-blue-600 text-xs"
                            onClick={() => handleEditShift(shift)}
                            title="Modifier"
                          >
                            Modifier
                          </button>
                          <button
                            className="p-1.5 rounded hover:bg-red-100 text-red-500"
                            onClick={() => handleDeleteShift(shift.id)}
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
              {/* Add row */}
              {addingShift && (
                <tr className="bg-green-50">
                  <td className="px-3 py-2 text-center">
                    <select
                      className="input w-14 text-center font-bold"
                      value={newShift.short_label || (newShift.name ? newShift.name.charAt(0).toUpperCase() : "")}
                      onChange={(e) => setNewShift({ ...newShift, short_label: e.target.value })}
                    >
                      <option value="">—</option>
                      {LABEL_OPTIONS.map((l) => (
                        <option key={l} value={l} disabled={usedLabels.includes(l)}>
                          {l}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-2">
                    <input
                      type="text"
                      placeholder="Nom du shift"
                      className="input w-full"
                      value={newShift.name}
                      onChange={(e) => {
                        const name = e.target.value;
                        const autoLabel = name ? name.charAt(0).toUpperCase() : "";
                        setNewShift({
                          ...newShift,
                          name,
                          short_label: newShift.short_label || (!usedLabels.includes(autoLabel) ? autoLabel : ""),
                        });
                      }}
                    />
                  </td>
                  <td className="px-4 py-2 text-center">
                    <input
                      type="time"
                      className="input w-28 text-center"
                      value={newShift.start_time}
                      onChange={(e) => setNewShift({ ...newShift, start_time: e.target.value })}
                    />
                  </td>
                  <td className="px-4 py-2 text-center">
                    <input
                      type="time"
                      className="input w-28 text-center"
                      value={newShift.end_time}
                      onChange={(e) => setNewShift({ ...newShift, end_time: e.target.value })}
                    />
                  </td>
                  <td className="px-4 py-2 text-center">
                    <input
                      type="number"
                      step="0.5"
                      min={1}
                      max={24}
                      className="input w-20 text-center"
                      value={newShift.duration_hours}
                      onChange={(e) => setNewShift({ ...newShift, duration_hours: Number(e.target.value) })}
                    />
                  </td>
                  <td className="px-4 py-2 text-center">
                    <div className="flex justify-center gap-1">
                      <button
                        className="p-1.5 rounded hover:bg-green-100 text-green-600"
                        onClick={handleAddShift}
                        title="Créer"
                      >
                        <Save size={16} />
                      </button>
                      <button
                        className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
                        onClick={() => setAddingShift(false)}
                        title="Annuler"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Coverage requirements — per-role columns */}
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
                  Inf.
                </th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                  ASSC
                </th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                  A-S
                </th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">
                  Total
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {coverage
                .filter((cov) => weekendEnabled || (cov.day_type !== "saturday" && cov.day_type !== "sunday"))
                .map((cov) => (
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
                      min={0}
                      max={20}
                      className="w-16 text-center input"
                      value={cov.min_infirmier}
                      onChange={(e) =>
                        handleCoverageChange(cov.id, "min_infirmier", Number(e.target.value))
                      }
                    />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <input
                      type="number"
                      min={0}
                      max={20}
                      className="w-16 text-center input"
                      value={cov.min_assc}
                      onChange={(e) =>
                        handleCoverageChange(cov.id, "min_assc", Number(e.target.value))
                      }
                    />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <input
                      type="number"
                      min={0}
                      max={20}
                      className="w-16 text-center input"
                      value={cov.min_aide_soignant}
                      onChange={(e) =>
                        handleCoverageChange(cov.id, "min_aide_soignant", Number(e.target.value))
                      }
                    />
                  </td>
                  <td className="px-4 py-3 text-center font-semibold text-gray-700">
                    {cov.min_infirmier + cov.min_assc + cov.min_aide_soignant}
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
