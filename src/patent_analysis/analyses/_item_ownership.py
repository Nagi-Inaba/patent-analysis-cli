"""Global distinct item ownership shared by uniqueness and involvement analyses."""
from __future__ import annotations

from collections import Counter

from . import _advanced_common as c


def ownership(rows, group_role, item_role):
    group_items, owners = {}, {}
    record_counts = Counter()
    memberships = []
    budget = c.Budget()
    for row in rows:
        groups, items = row[group_role], row[item_role]
        if not groups or not items:
            continue
        amount = c.preflight_cartesian_size(len(groups), len(items))
        if budget.contributions + amount > c.MAX_CONTRIBUTIONS:
            raise c.AnalysisCapacityError('group-item membership expansion exceeds limit')
        new = sum(g not in group_items or i not in group_items[g] for g in groups for i in items)
        budget.reserve(amount, new)
        memberships.append((groups, items))
        record_counts.update(groups)
        for group in groups:
            owned = group_items.setdefault(group, set())
            for item in items:
                owned.add(item)
                owners.setdefault(item, set()).add(group)
    return group_items, owners, record_counts, memberships, budget
