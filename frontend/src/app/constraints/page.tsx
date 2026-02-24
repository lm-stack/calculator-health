"use client";

import { useEffect, useState } from "react";
import { getConstraints, updateConstraint, ConstraintRule } from "@/lib/api";
import { Shield, Sparkles } from "lucide-react";

export default function ConstraintsPage() {
  const [constraints, setConstraints] = useState<ConstraintRule[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    getConstraints()
      .then(setConstraints)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleToggle = async (id: string, isActive: boolean) => {
    await updateConstraint(id, { is_active: isActive });
    load();
  };

  const ruleLabels: Record<string, string> = {
    max_one_shift_per_day: "1 shift maximum par jour",
    min_coverage: "Couverture minimale",
    min_rest_hours: "Repos minimum entre shifts",
    max_weekly_hours: "Heures hebdomadaires max",
    respect_absences: "Respecter les absences",
    required_roles: "Rôles requis par créneau",
    weekend_rest: "Repos week-end garanti",
    shift_regularity: "Régularité des horaires",
    respect_preferences: "Préférences de shifts",
    night_weekend_equity: "Équité nuits / week-ends",
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  const hardRules = constraints.filter((c) => c.type === "hard");
  const softRules = constraints.filter((c) => c.type === "soft");

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Règles de planification</h2>

      {/* Hard constraints */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={20} className="text-red-500" />
          <h3 className="text-lg font-semibold">
            Contraintes dures (obligatoires)
          </h3>
        </div>
        <div className="space-y-3">
          {hardRules.map((rule) => (
            <div
              key={rule.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <p className="font-medium text-sm">
                  {ruleLabels[rule.name] || rule.name}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {formatParams(rule.parameter)}
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={rule.is_active}
                  onChange={(e) => handleToggle(rule.id, e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Soft objectives */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles size={20} className="text-amber-500" />
          <h3 className="text-lg font-semibold">
            Objectifs (optimisation)
          </h3>
        </div>
        <div className="space-y-3">
          {softRules.map((rule) => (
            <div
              key={rule.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <p className="font-medium text-sm">
                  {ruleLabels[rule.name] || rule.name}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {formatParams(rule.parameter)}
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={rule.is_active}
                  onChange={(e) => handleToggle(rule.id, e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function formatParams(params: object): string {
  const entries = Object.entries(params || {});
  if (entries.length === 0) return "Aucun paramètre";
  return entries
    .map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`)
    .join(", ");
}
