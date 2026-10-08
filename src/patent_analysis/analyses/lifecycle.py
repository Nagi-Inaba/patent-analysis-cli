"""Deterministic peak-year and five-year CAGR lifecycle analysis."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from math import isfinite
from pathlib import Path

from patent_analysis.analyses._aggregation import canonical_year, row_values
from patent_analysis.analysis_inputs import prepare_records_population
from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis.population import PopulationResult

LIFECYCLE_ALGORITHM_VERSION = "1.0.0"
CAGR_WINDOW_YEARS = 5
MAX_LABEL_JSON_BYTES = 4096
MAX_TOP_N = 20
MAX_OUTPUT_POINTS = 20
MAX_DISTINCT_BUCKETS = 100_000
MAX_EXPANDED_CONTRIBUTIONS = 1_000_000


class LifecycleBudgetError(ValueError):
    """Raised before a lifecycle operation would exceed a fixed budget."""

    code = "analysis.invalid"


def lifecycle_cagr_percent(start_count: int, end_count: int) -> float:
    if (
        type(start_count) is not int
        or type(end_count) is not int
        or start_count < 0
        or end_count < 0
    ):
        raise ValueError("lifecycle endpoint counts are invalid")
    if start_count > 0 and end_count > 0:
        value = ((end_count / start_count) ** (1 / (CAGR_WINDOW_YEARS - 1)) - 1) * 100
        if not isfinite(value):
            raise ValueError("lifecycle CAGR is not finite")
        return value
    if start_count == 0 and end_count > 0:
        return 100.0
    if start_count > 0 and end_count == 0:
        return -100.0
    return 0.0


def lifecycle_stage(cagr_percent: float) -> str:
    if not isinstance(cagr_percent, (int, float)) or not isfinite(float(cagr_percent)):
        raise ValueError("lifecycle CAGR is invalid")
    if cagr_percent > 10:
        return "growth"
    if cagr_percent >= 0:
        return "stable"
    if cagr_percent >= -10:
        return "slowing"
    return "decline"


def _validate_parameters(parameters: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(parameters, Mapping):
        raise ValueError("lifecycle parameters must be an object")
    allowed = {"date_role", "category_role", "top_n"}
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError(f"unsupported lifecycle parameters: {unknown}")
    date_role = parameters.get("date_role")
    category_role = parameters.get("category_role")
    if not isinstance(date_role, str) or not date_role.strip():
        raise ValueError("date_role must be a non-empty string")
    if not isinstance(category_role, str) or not category_role.strip():
        raise ValueError("category_role must be a non-empty string")
    date_role = date_role.strip()
    category_role = category_role.strip()
    if date_role == category_role:
        raise ValueError("date_role and category_role must differ")
    top_n = parameters.get("top_n", MAX_TOP_N)
    if type(top_n) is not int or not 1 <= top_n <= MAX_TOP_N:
        raise ValueError("top_n must be an integer from 1 through 20")
    return {"date_role": date_role, "category_role": category_role, "top_n": top_n}


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    validated = _validate_parameters(parameters)
    return str(validated["date_role"]), str(validated["category_role"])


def analyze_lifecycle(
    population: PopulationResult,
    parameters: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(population, PopulationResult):
        raise TypeError("population must be a PopulationResult")
    validated = _validate_parameters(parameters)
    date_role = str(validated["date_role"])
    category_role = str(validated["category_role"])

    counts: dict[str, dict[int, int]] = {}
    totals: dict[str, int] = defaultdict(int)
    invalid_year_rows = 0
    blank_category_rows = 0
    visible_rows = 0
    contributions = 0
    distinct_buckets = 0
    max_year: int | None = None

    for row in population.rows:
        year = canonical_year(row_values(row, date_role))
        if year is None:
            invalid_year_rows += 1
            continue
        categories = row_values(row, category_role)
        if not categories:
            blank_category_rows += 1
            continue
        if contributions + len(categories) > MAX_EXPANDED_CONTRIBUTIONS:
            raise LifecycleBudgetError(
                f"expanded contributions exceed limit {MAX_EXPANDED_CONTRIBUTIONS}"
            )
        new_count = sum(
            1 for category in categories if category not in counts or year not in counts[category]
        )
        if distinct_buckets + new_count > MAX_DISTINCT_BUCKETS:
            raise LifecycleBudgetError(f"distinct buckets exceed limit {MAX_DISTINCT_BUCKETS}")
        if any(len(canonical_json_bytes(label)) > MAX_LABEL_JSON_BYTES for label in categories):
            raise LifecycleBudgetError("serialized label exceeds limit 4096 bytes")
        distinct_buckets += new_count
        contributions += len(categories)
        visible_rows += 1
        max_year = year if max_year is None else max(max_year, year)
        for category in categories:
            by_year = counts.setdefault(category, {})
            by_year[year] = by_year.get(year, 0) + 1
            totals[category] += 1

    input_rows = population.receipt.included_rows
    if max_year is None:
        return {
            "schema_version": "1.0.0",
            "analysis_id": "lifecycle.v1",
            "algorithm_version": LIFECYCLE_ALGORITHM_VERSION,
            "window": None,
            "points": [],
            "population": {
                "input_rows": input_rows,
                "visible_rows": 0,
                "invalid_year_rows": invalid_year_rows,
                "blank_category_rows": blank_category_rows,
                "excluded_rows": input_rows,
            },
            "contributions": 0,
            "limits": {
                "max_top_n": MAX_TOP_N,
                "max_output_points": MAX_OUTPUT_POINTS,
                "max_distinct_buckets": MAX_DISTINCT_BUCKETS,
                "max_expanded_contributions": MAX_EXPANDED_CONTRIBUTIONS,
            },
        }

    start_year = max_year - (CAGR_WINDOW_YEARS - 1)
    ranked = sorted(totals, key=lambda label: (-totals[label], label))[: int(validated["top_n"])]
    points: list[dict[str, object]] = []
    for label in ranked:
        by_year = counts[label]
        peak_count = max(by_year.values())
        peak_year = min(year for year, count in by_year.items() if count == peak_count)
        cagr = lifecycle_cagr_percent(
            by_year.get(start_year, 0),
            by_year.get(max_year, 0),
        )
        points.append(
            {
                "label": label,
                "x": peak_year,
                "y": cagr,
                "size": totals[label],
                "stage": lifecycle_stage(cagr),
            }
        )

    return {
        "schema_version": "1.0.0",
        "analysis_id": "lifecycle.v1",
        "algorithm_version": LIFECYCLE_ALGORITHM_VERSION,
        "window": {
            "start_year": start_year,
            "end_year": max_year,
            "years": CAGR_WINDOW_YEARS,
        },
        "points": points,
        "population": {
            "input_rows": input_rows,
            "visible_rows": visible_rows,
            "invalid_year_rows": invalid_year_rows,
            "blank_category_rows": blank_category_rows,
            "excluded_rows": input_rows - visible_rows,
        },
        "contributions": contributions,
        "limits": {
            "max_top_n": MAX_TOP_N,
            "max_output_points": MAX_OUTPUT_POINTS,
            "max_distinct_buckets": MAX_DISTINCT_BUCKETS,
            "max_expanded_contributions": MAX_EXPANDED_CONTRIBUTIONS,
        },
    }


def analyze_lifecycle_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    if not isinstance(spec, Mapping) or spec.get("analysis_id") != "lifecycle.v1":
        raise ValueError("lifecycle analysis spec is invalid")
    parameters = spec.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("lifecycle parameters must be an object")
    roles = required_roles(parameters)
    dataset, population = prepare_records_population(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_roles=roles,
    )
    data = analyze_lifecycle(population, parameters)
    analyzed_rows = int(data["population"]["visible_rows"])
    return {
        "analysis_id": "lifecycle.v1",
        "algorithm_version": LIFECYCLE_ALGORITHM_VERSION,
        "result_variant": "points",
        "population": {
            "input_rows": dataset.manifest.input_rows,
            "analyzed_rows": analyzed_rows,
            "excluded_rows": dataset.manifest.input_rows - analyzed_rows,
        },
        "data": data,
        "warnings": [],
        **population.receipt.analysis_metadata(),
    }


__all__ = (
    "LIFECYCLE_ALGORITHM_VERSION",
    "LifecycleBudgetError",
    "analyze_lifecycle",
    "analyze_lifecycle_csv",
    "lifecycle_cagr_percent",
    "lifecycle_stage",
    "required_roles",
)
