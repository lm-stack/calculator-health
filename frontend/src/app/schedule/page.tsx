"use client";

import { useEffect, useState } from "react";
import {
  getSchedules,
  getSchedule,
  generateSchedule,
  deleteSchedule,
  Schedule,
  ScheduleDetail,
} from "@/lib/api";
import ScheduleCalendar from "@/components/calendar/ScheduleCalendar";
import { Play, Trash2, Loader } from "lucide-react";

export default function SchedulePage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [selected, setSelected] = useState<ScheduleDetail | null>(null);
  const [generating, setGenerating] = useState(false);
  const [periodStart, setPeriodStart] = useState("2026-03-02");
  const [periodEnd, setPeriodEnd] = useState("2026-03-31");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    getSchedules()
      .then(setSchedules)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    try {
      const result = await generateSchedule({
        period_start: periodStart,
        period_end: periodEnd,
      });
      setSelected(result);
      load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur de génération");
    } finally {
      setGenerating(false);
    }
  };

  const handleSelect = async (id: string) => {
    const detail = await getSchedule(id);
    setSelected(detail);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Supprimer ce planning ?")) return;
    await deleteSchedule(id);
    if (selected?.id === id) setSelected(null);
    load();
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Planning</h2>

      {/* Generator */}
      <div className="card mb-6">
        <h3 className="text-lg font-semibold mb-4">Générer un planning</h3>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="label">Début</label>
            <input
              type="date"
              className="input"
              value={periodStart}
              onChange={(e) => setPeriodStart(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Fin</label>
            <input
              type="date"
              className="input"
              value={periodEnd}
              onChange={(e) => setPeriodEnd(e.target.value)}
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="btn-primary flex items-center gap-2"
          >
            {generating ? (
              <Loader size={18} className="animate-spin" />
            ) : (
              <Play size={18} />
            )}
            {generating ? "Résolution en cours..." : "Générer"}
          </button>
        </div>
        {error && (
          <p className="text-red-600 text-sm mt-3">{error}</p>
        )}
      </div>

      {/* Schedule list */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <div className="card p-0">
            <h3 className="text-sm font-semibold text-gray-500 uppercase px-4 pt-4 pb-2">
              Plannings
            </h3>
            <div className="divide-y divide-gray-100">
              {schedules.map((s) => (
                <div
                  key={s.id}
                  className={`flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50 ${
                    selected?.id === s.id ? "bg-primary-50" : ""
                  }`}
                  onClick={() => handleSelect(s.id)}
                >
                  <div>
                    <p className="text-sm font-medium">
                      {s.period_start} → {s.period_end}
                    </p>
                    <p className="text-xs text-gray-500">
                      {s.status === "published" ? "Publié" : "Brouillon"}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(s.id);
                    }}
                    className="text-red-400 hover:text-red-600"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {schedules.length === 0 && !loading && (
                <p className="text-sm text-gray-500 px-4 py-6 text-center">
                  Aucun planning
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Calendar view */}
        <div className="lg:col-span-3">
          {selected ? (
            <ScheduleCalendar schedule={selected} />
          ) : (
            <div className="card flex items-center justify-center h-64 text-gray-400">
              Sélectionnez ou générez un planning
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
