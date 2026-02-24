"""Soft objectives for the nurse scheduling solver."""


def add_shift_regularity_objective(model, shifts_var, employees, shift_types, days, weight=10):
    """Maximize regularity: same shift pattern each week.

    For each employee, reward having the same shift on the same weekday across weeks.
    """
    bonus_vars = []
    num_days = len(days)

    for e_idx in range(len(employees)):
        for s_idx in range(len(shift_types)):
            # Compare same weekday across consecutive weeks
            for d_idx in range(num_days):
                next_week = d_idx + 7
                if next_week < num_days:
                    # both = 1 iff employee works same shift same weekday both weeks
                    both = model.NewBoolVar(f"reg_{e_idx}_{s_idx}_{d_idx}")
                    model.AddBoolAnd([
                        shifts_var[(e_idx, d_idx, s_idx)],
                        shifts_var[(e_idx, next_week, s_idx)],
                    ]).OnlyEnforceIf(both)
                    model.AddBoolOr([
                        shifts_var[(e_idx, d_idx, s_idx)].Not(),
                        shifts_var[(e_idx, next_week, s_idx)].Not(),
                    ]).OnlyEnforceIf(both.Not())
                    bonus_vars.append(both)

    return bonus_vars, weight


def add_night_weekend_equity_objective(model, shifts_var, employees, shift_types, days, weight=8):
    """Distribute night and weekend shifts equitably.

    Minimize the max-min difference in undesirable shift counts across employees.
    """
    night_indices = [i for i, s in enumerate(shift_types) if s.is_night]
    weekend_day_indices = [i for i, d in enumerate(days) if d.weekday() >= 5]

    if not night_indices and not weekend_day_indices:
        return [], 0

    # Count undesirable shifts per employee
    counts = []
    eligible = [e_idx for e_idx, emp in enumerate(employees)
                if "samedi" in emp.working_days or "dimanche" in emp.working_days]

    if len(eligible) < 2:
        return [], 0

    for e_idx in eligible:
        count = sum(
            shifts_var[(e_idx, d_idx, s_idx)]
            for d_idx in weekend_day_indices
            for s_idx in range(len(shift_types))
        ) + sum(
            shifts_var[(e_idx, d_idx, s_idx)]
            for d_idx in range(len(days))
            for s_idx in night_indices
        )
        counts.append(count)

    # Minimize max - min using auxiliary variables
    max_count = model.NewIntVar(0, len(days) * len(shift_types), "max_undesirable")
    min_count = model.NewIntVar(0, len(days) * len(shift_types), "min_undesirable")

    for count in counts:
        model.Add(max_count >= count)
        model.Add(min_count <= count)

    spread = model.NewIntVar(0, len(days) * len(shift_types), "spread_undesirable")
    model.Add(spread == max_count - min_count)

    # Return as penalty (negative weight)
    return [spread], -weight
