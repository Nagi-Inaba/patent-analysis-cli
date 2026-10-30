"""Ranking over the common v2 population, retaining legacy contribution semantics."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from patent_analysis.analyses._aggregation import row_number, row_values, validate_measure
from patent_analysis.analysis import (
    BLANK_LABEL,
    MAX_DISTINCT_BUCKETS,
    MAX_EXPANDED_CONTRIBUTIONS,
    _build_rows,
    _measure_row_value,
    _measure_share,
    _merge_bucket_state,
    _new_bucket_state,
    _update_bucket_state,
    _validate_finite_measure_value,
)
from patent_analysis.analysis_contracts import validate_analysis_result
from patent_analysis.analysis_inputs import prepare_records_population
from patent_analysis.population import PopulationResult

RANKING_ALGORITHM_VERSION = "1.0.0"
MAX_TOP_N = 100


class RankingBudgetError(ValueError):
    """Raised before a ranking contribution would exceed a fixed work budget."""


def _validate_parameters(parameters: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(parameters, Mapping):
        raise ValueError("ranking parameters must be an object")
    allowed = {"role", "measure", "measure_role", "top_n", "include_other", "multi_value_mode"}
    if set(parameters) - allowed:
        raise ValueError("unsupported ranking parameters")
    role = parameters.get("role")
    if not isinstance(role, str) or not role.strip() or len(role) > 64:
        raise ValueError("role must be a non-empty string of at most 64 characters")
    mode, measure_role = validate_measure(parameters)
    if mode == "count" and "measure_role" in parameters:
        raise ValueError("measure_role is not allowed for count")
    raw_measure_role = parameters.get("measure_role")
    if isinstance(raw_measure_role, str) and len(raw_measure_role) > 64:
        raise ValueError("measure_role must contain at most 64 characters")
    top_n = parameters.get("top_n", 10)
    if type(top_n) is not int or not 1 <= top_n <= MAX_TOP_N:
        raise ValueError("top_n must be an integer from 1 through 100")
    include_other = parameters.get("include_other", True)
    if type(include_other) is not bool:
        raise ValueError("include_other must be boolean")
    multi_value_mode = parameters.get("multi_value_mode", "all")
    if not isinstance(multi_value_mode, str) or multi_value_mode not in {"all", "first"}:
        raise ValueError("multi_value_mode must be all or first")
    return {
        "role": role.strip(),
        "measure": mode,
        "measure_role": measure_role,
        "top_n": top_n,
        "include_other": include_other,
        "multi_value_mode": multi_value_mode,
    }


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    validated = _validate_parameters(parameters)
    roles = [str(validated["role"])]
    measure_role = validated["measure_role"]
    if isinstance(measure_role, str) and measure_role not in roles:
        roles.append(measure_role)
    return tuple(roles)


def analyze_ranking(
    population: PopulationResult,
    parameters: Mapping[str, object],
) -> dict[str, object]:
    """Aggregate normalized tokens without splitting them or reselecting records.

    Numeric values follow the other native v2 analyses: the first finite number
    in a row's normalized measure tokens is used. Every dimension contribution
    receives that value, including contributions subsequently grouped as other.
    Shares retain ranking.v1 semantics and always use the pre-top_n population.
    """

    if not isinstance(population, PopulationResult):
        raise TypeError("population must be a PopulationResult")
    validated = _validate_parameters(parameters)
    role = str(validated["role"])
    mode = str(validated["measure"])
    measure_role = validated["measure_role"]
    assert measure_role is None or isinstance(measure_role, str)

    buckets: dict[str, dict[str, Any]] = {}
    contributions = 0
    for row in population.rows:
        labels = row_values(row, role) or (BLANK_LABEL,)
        if validated["multi_value_mode"] == "first":
            labels = labels[:1]
        if contributions + len(labels) > MAX_EXPANDED_CONTRIBUTIONS:
            raise RankingBudgetError(
                f"expanded contributions exceed limit {MAX_EXPANDED_CONTRIBUTIONS}"
            )
        parsed = None if measure_role is None else row_number(row, measure_role)
        for label in labels:
            state = buckets.get(label)
            if state is None:
                if len(buckets) >= MAX_DISTINCT_BUCKETS:
                    raise RankingBudgetError(
                        f"distinct buckets exceed limit {MAX_DISTINCT_BUCKETS}"
                    )
                state = _new_bucket_state()
                buckets[label] = state
            _update_bucket_state(state, parsed, mode)
        contributions += len(labels)

    total_value = 0.0
    if mode in {"count", "sum"}:
        total_value = _validate_finite_measure_value(
            mode, sum(_measure_row_value(mode, state) for state in buckets.values())
        )
    rows = _build_rows(mode, buckets, total_value, contributions)[:int(validated["top_n"])]
    if validated["include_other"] and len(rows) < len(buckets):
        visible_labels = {row["label"] for row in rows}
        other = _new_bucket_state()
        for label, state in buckets.items():
            if label not in visible_labels:
                _merge_bucket_state(other, state)
        rows.append({
            "row_kind": "remainder",
            "label": "その他",
            "value": _validate_finite_measure_value(mode, _measure_row_value(mode, other)),
            "count": other["count"],
            "share": _measure_share(mode, other, total_value, contributions),
        })

    return validate_analysis_result({
        "analysis_type": "ranking",
        "dimension": role,
        "measure": {"mode": mode, "column": measure_role},
        "population": {
            "input_rows": len(population.rows),
            "analyzed_rows": contributions,
        },
        "rows": rows,
        "warnings": [],
    })


def analyze_ranking_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    """Filter, select family representatives, then rank their contributions."""

    if (not isinstance(spec, Mapping) or spec.get("analysis_id") != "ranking.v2"
            or spec.get("analysis_contract_version") != "2.0.0"):
        raise ValueError("ranking analysis spec is invalid")
    parameters = spec.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("ranking parameters must be an object")
    dataset, population = prepare_records_population(
        source, spec, allowed_root=allowed_root, analysis_roles=required_roles(parameters),
    )
    data = analyze_ranking(population, parameters)
    selected_rows = len(population.rows)
    return {
        "analysis_id": "ranking.v2",
        "algorithm_version": RANKING_ALGORITHM_VERSION,
        "result_variant": "ranking",
        "population": {
            "input_rows": dataset.manifest.input_rows,
            "analyzed_rows": selected_rows,
            "excluded_rows": dataset.manifest.input_rows - selected_rows,
        },
        "data": data,
        "warnings": [],
        **population.receipt.analysis_metadata(),
    }
