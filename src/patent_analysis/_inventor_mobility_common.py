"""Shared mobility limits, row budgets and stable identifiers."""

from __future__ import annotations

import hashlib
import json

from patent_analysis.corporate_history import MAX_OUTPUT_BYTES
from patent_analysis.errors import DatasetInputError

MAX_PERSONS = 200
MAX_OBSERVATIONS = 5000
MAX_ROWS = 5000
MAX_COMPARISONS = 200000
DISCLAIMERS = [
    "patent_applicant_association_is_not_employment",
    "candidate_period_is_not_guaranteed_employment_interval",
    "calendar_gaps_are_not_proof_of_absence_or_retirement",
    "corporate_completion_does_not_confirm_personal_employment_move",
]


def _fail(budget=False):
    raise DatasetInputError(
        "dataset input exceeds published limits" if budget else "input is invalid"
    )


def _stable_id(prefix, facts):
    raw = json.dumps(facts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return prefix + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class _RowBudget:
    def __init__(self):
        self.bytes = 0

    def spend(self, value):
        self.bytes += len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8"))
        if self.bytes > MAX_OUTPUT_BYTES:
            _fail(True)

    def append(self, rows, value):
        if len(rows) >= MAX_ROWS:
            _fail(True)
        self.spend(value)
        rows.append(value)
