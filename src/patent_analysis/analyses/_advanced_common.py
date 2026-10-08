"""Bounded arithmetic support for the registered advanced JSON analyses.

``compute`` inputs are internal normalized role-token mappings, not raw CSV rows.
CSV preparation remains owned by analysis_inputs; no transport logic is duplicated.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_ROWS = 100_000
MAX_INPUT_TOKENS = 2_000_000
MAX_VALUES_PER_ROLE = 100
MAX_LABEL_BYTES = 4096
MAX_CONTRIBUTIONS = 1_000_000
MAX_BUCKETS = 100_000
MAX_RESULT_BYTES = 96 * 1024
MAX_TOP_N = 20
Record = Mapping[str, tuple[str, ...]]


class AnalysisCapacityError(ValueError):
    """A fixed analysis bound would be exceeded; no partial result is returned."""


def integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def text(value: object, name: str, *, role: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    value = value.strip()
    if role and len(value) > 64:
        raise ValueError("role exceeds 64 code points")
    try:
        size = len(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    except UnicodeError:
        raise ValueError("invalid Unicode label") from None
    if size > MAX_LABEL_BYTES:
        raise AnalysisCapacityError("serialized label exceeds 4096 bytes")
    return value


def parameters(
    value: object, roles: tuple[str, ...], extra: tuple[str, ...] = (), *, top_max: int = MAX_TOP_N
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) - {*roles, *extra, "top_n"}:
        raise ValueError("unsupported analysis parameters")
    result = dict(value)
    for key in roles:
        result[key] = text(result.get(key), key, role=True)
    if len({result[key] for key in roles}) != len(roles):
        raise ValueError("analysis roles must differ")
    result["top_n"] = integer(result.get("top_n", min(20, top_max)), "top_n", 1, top_max)
    return result


def year_span(p: Mapping[str, Any], start: str, end: str) -> tuple[int, int]:
    a = integer(p.get(start), start, 1800, 2199)
    b = integer(p.get(end), end, 1800, 2199)
    if a >= b:
        raise ValueError("year span must have distinct ordered endpoints")
    return a, b


def checked_records(
    rows: Iterable[Record], roles: tuple[str, ...]
) -> list[dict[str, tuple[str, ...]]]:
    result: list[dict[str, tuple[str, ...]]] = []
    token_count = 0
    for row in rows:
        if len(result) >= MAX_ROWS:
            raise AnalysisCapacityError("too many normalized records")
        if not isinstance(row, Mapping):
            raise ValueError("normalized record must be a role-token mapping")
        projected = {}
        for role in roles:
            values = row.get(role, ())
            if not isinstance(values, tuple) or not all(isinstance(v, str) for v in values):
                raise ValueError("normalized role values must be a tuple of strings")
            # Match canonical row_values membership: a repeated label contributes once.
            values = tuple(dict.fromkeys(v.strip() for v in values if v.strip()))
            if len(values) > MAX_VALUES_PER_ROLE:
                raise AnalysisCapacityError("too many values in one normalized role")
            if token_count + len(values) > MAX_INPUT_TOKENS:
                raise AnalysisCapacityError("normalized token budget exceeded")
            token_count += len(values)
            projected[role] = tuple(text(v, "label") for v in values)
        result.append(projected)
    return result


def year(row: Record, role: str) -> int | None:
    for value in row.get(role, ()):
        if len(value) == 4 and value.isascii() and value.isdigit() and 1800 <= int(value) <= 2199:
            return int(value)
    return None


@dataclass
class Budget:
    contributions: int = 0
    buckets: int = 0

    def reserve(self, amount: int, new_buckets: int) -> None:
        if self.contributions + amount > MAX_CONTRIBUTIONS:
            raise AnalysisCapacityError("expanded contributions exceed limit")
        if self.buckets + new_buckets > MAX_BUCKETS:
            raise AnalysisCapacityError("distinct analysis buckets exceed limit")
        self.contributions += amount
        self.buckets += new_buckets


def guard_budget(*, contributions: int = 0, buckets: int = 0) -> None:
    integer(contributions, "contributions", 0, MAX_CONTRIBUTIONS)
    integer(buckets, "buckets", 0, MAX_BUCKETS)


def finish(
    analysis_id: str, input_rows: int, visible_rows: int, contributions: int,
    *, result_byte_limit: int | None = None, **payload: Any,
) -> dict[str, Any]:
    result = {
        "schema_version": "1.0.0",
        "analysis_id": analysis_id,
        "algorithm_version": "1.0.0",
        "population": {
            "input_rows": input_rows,
            "visible_rows": visible_rows,
            "excluded_rows": input_rows - visible_rows,
        },
        "contributions": contributions,
        **payload,
    }
    raw = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    limit = MAX_RESULT_BYTES if result_byte_limit is None else result_byte_limit
    if len(raw.encode("utf-8")) > limit:
        raise AnalysisCapacityError("advanced analysis result exceeds its byte limit")
    return result


def run_population(
    population: object,
    p: Mapping[str, Any],
    roles: tuple[str, ...],
    compute: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    from patent_analysis.analyses._aggregation import row_values
    from patent_analysis.population import PopulationResult

    if not isinstance(population, PopulationResult):
        raise TypeError("population must be a PopulationResult")
    if len(population.rows) != population.receipt.included_rows:
        raise ValueError("population row count disagrees with receipt")
    return compute(({role: row_values(row, role) for role in roles} for row in population.rows), p)


def run_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
    analysis_id: str,
    variant: str,
    validator: Callable[..., dict[str, Any]],
    role_keys: tuple[str, ...],
    compute: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    from patent_analysis.analysis_contracts import AnalysisContractError
    from patent_analysis.analysis_inputs import prepare_records_population
    from patent_analysis.data import DatasetInputError

    if not isinstance(spec, Mapping) or spec.get("analysis_id") != analysis_id:
        raise ValueError("analysis spec does not match the requested analysis")
    try:
        p = validator(spec.get("parameters"))
    except ValueError:
        raise AnalysisContractError(
            "invalid advanced analysis parameters", code="analysis.invalid", details={}
        ) from None
    roles = tuple(p[key] for key in role_keys)
    try:
        dataset, population = prepare_records_population(
            source, spec, allowed_root=allowed_root, analysis_roles=roles
        )
        data = run_population(population, p, roles, compute)
    except ValueError:
        raise DatasetInputError("Dataset cannot satisfy the bounded analysis contract") from None
    visible = data["population"]["visible_rows"]
    return {
        "analysis_id": analysis_id,
        "algorithm_version": "1.0.0",
        "result_variant": variant,
        "population": {
            "input_rows": dataset.manifest.input_rows,
            "analyzed_rows": visible,
            "excluded_rows": dataset.manifest.input_rows - visible,
        },
        "data": data,
        "warnings": [],
        **population.receipt.analysis_metadata(),
    }


def preflight_pair_size(value_count: int) -> int:
    n = integer(value_count, "value_count", 0, MAX_VALUES_PER_ROLE)
    return n * (n - 1) // 2


def preflight_cartesian_size(*axis_lengths: int) -> int:
    if not axis_lengths or len(axis_lengths) > 3:
        raise ValueError("one through three concrete membership axes are required")
    size = math.prod(integer(n, "axis_length", 0, MAX_VALUES_PER_ROLE) for n in axis_lengths)
    if size > MAX_CONTRIBUTIONS:
        raise AnalysisCapacityError("membership expansion exceeds limit")
    return size
