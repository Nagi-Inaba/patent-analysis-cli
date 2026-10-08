"""Shared unordered-pair counting for cooccurrence and collaboration only."""
from __future__ import annotations

from collections import Counter
from itertools import combinations

from . import _advanced_common as c


def accumulate(rows, role, *, include_singletons):
    nodes, pairs = Counter(), Counter()
    budget = c.Budget()
    visible = 0
    for row in rows:
        values = tuple(sorted(row[role]))
        if not values or (len(values) == 1 and not include_singletons):
            continue
        amount = c.preflight_pair_size(len(values))
        # Preflight the quadratic expansion before even enumerating its pairs.
        if budget.contributions + amount > c.MAX_CONTRIBUTIONS:
            raise c.AnalysisCapacityError('pair expansion exceeds limit')
        new_keys = sum(v not in nodes for v in values)
        new_keys += sum(pair not in pairs for pair in combinations(values, 2))
        budget.reserve(amount, new_keys)
        visible += 1
        nodes.update(values)
        pairs.update(combinations(values, 2))
    return nodes, pairs, visible, budget
