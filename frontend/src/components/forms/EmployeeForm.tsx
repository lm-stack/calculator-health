"use client";

import { useState } from "react";
import { EmployeeCreate } from "@/lib/api";

interface Props {
  onSubmit: (data: EmployeeCreate) => Promise<void>;
  onCancel: () => void;
  initial?: Partial<EmployeeCreate>;
}

export default function EmployeeForm({ onSubmit, onCancel, initial }: Props) {
  const [form, setForm] = useState<EmployeeCreate>({
    first_name: initial?.first_name || "",
    last_name: initial?.last_name || "",
    role: initial?.role || "infirmier",
    activity_rate: initial?.activity_rate || 100,
    can_do_night: initial?.can_do_night ?? true,
    can_do_weekend: initial?.can_do_weekend ?? true,
    preferred_shifts: initial?.preferred_shifts || [],
  });
  const [submitting, setSubmitting] = useState(false);

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
        <label className="label">Prénom</label>
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
        <label className="label">Rôle</label>
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
        <label className="label">Taux d&apos;activité (%)</label>
        <select
          className="input"
          value={form.activity_rate}
          onChange={(e) => setForm({ ...form, activity_rate: Number(e.target.value) })}
        >
          <option value={100}>100%</option>
          <option value={80}>80%</option>
          <option value={60}>60%</option>
          <option value={50}>50%</option>
        </select>
      </div>
      <div className="flex items-center gap-6">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.can_do_night}
            onChange={(e) => setForm({ ...form, can_do_night: e.target.checked })}
            className="rounded border-gray-300"
          />
          <span className="text-sm">Peut faire des nuits</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.can_do_weekend}
            onChange={(e) => setForm({ ...form, can_do_weekend: e.target.checked })}
            className="rounded border-gray-300"
          />
          <span className="text-sm">Peut faire des week-ends</span>
        </label>
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
