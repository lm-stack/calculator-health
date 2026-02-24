"use client";

import { useState } from "react";
import { EmployeeCreate } from "@/lib/api";

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

interface Props {
  onSubmit: (data: EmployeeCreate) => Promise<void>;
  onCancel: () => void;
  initial?: Partial<EmployeeCreate>;
  weekendEnabled?: boolean;
}

export default function EmployeeForm({ onSubmit, onCancel, initial, weekendEnabled = false }: Props) {
  const defaultRate = initial?.activity_rate || 100;
  const defaultMaxDays = defaultRate / 20;
  const defaultDays = initial?.working_days || WEEKDAY_KEYS.slice(0, defaultMaxDays);

  const [form, setForm] = useState<EmployeeCreate>({
    first_name: initial?.first_name || "",
    last_name: initial?.last_name || "",
    role: initial?.role || "infirmier",
    activity_rate: defaultRate,
    working_days: defaultDays,
  });
  const [submitting, setSubmitting] = useState(false);

  const maxDays = form.activity_rate / 20;
  const visibleDays = weekendEnabled
    ? ALL_DAY_LABELS
    : ALL_DAY_LABELS.filter((d) => WEEKDAY_KEYS.includes(d.key));

  const toggleDay = (day: string) => {
    setForm((prev) => {
      const isSelected = prev.working_days.includes(day);
      if (isSelected) {
        return { ...prev, working_days: prev.working_days.filter((d) => d !== day) };
      }
      // Already at max → don't add
      if (prev.working_days.length >= maxDays) return prev;
      return { ...prev, working_days: [...prev.working_days, day] };
    });
  };

  const handleRateChange = (newRate: number) => {
    const newMax = newRate / 20;
    setForm((prev) => {
      // Filter to only visible days, then truncate to new max
      const allowedKeys = weekendEnabled ? undefined : WEEKDAY_KEYS;
      let days = allowedKeys
        ? prev.working_days.filter((d) => allowedKeys.includes(d))
        : prev.working_days;
      if (days.length > newMax) {
        days = days.slice(0, newMax);
      }
      // If not enough days, fill with available weekdays
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(form);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label className="label">Prenom</label>
        <input
          className="input"
          required
          value={form.first_name}
          onChange={(e) => setForm({ ...form, first_name: e.target.value })}
        />
      </div>
      <div>
        <label className="label">Nom</label>
        <input
          className="input"
          required
          value={form.last_name}
          onChange={(e) => setForm({ ...form, last_name: e.target.value })}
        />
      </div>
      <div>
        <label className="label">Role</label>
        <select
          className="input"
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
        >
          <option value="infirmier">Infirmier</option>
          <option value="assc">ASSC</option>
          <option value="aide-soignant">Aide-soignant</option>
        </select>
      </div>
      <div>
        <label className="label">Taux d&apos;activite (%)</label>
        <select
          className="input"
          value={form.activity_rate}
          onChange={(e) => handleRateChange(Number(e.target.value))}
        >
          {RATE_OPTIONS.map((r) => (
            <option key={r} value={r}>{r}%</option>
          ))}
        </select>
      </div>
      <div className="md:col-span-2">
        <label className="label mb-2">
          Jours de travail ({form.working_days.length}/{maxDays})
        </label>
        <div className="flex gap-1">
          {visibleDays.map(({ key, label }) => {
            const isSelected = form.working_days.includes(key);
            const isDisabled = !isSelected && form.working_days.length >= maxDays;
            return (
              <button
                key={key}
                type="button"
                onClick={() => toggleDay(key)}
                disabled={isDisabled}
                className={`w-9 h-9 rounded-full text-xs font-bold transition-colors ${
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
      </div>
      <div className="md:col-span-2 flex gap-3 pt-2">
        <button type="submit" disabled={submitting} className="btn-primary">
          {submitting ? "Enregistrement..." : "Enregistrer"}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary">
          Annuler
        </button>
      </div>
    </form>
  );
}
