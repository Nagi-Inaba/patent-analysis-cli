"""Deterministic two-endpoint count growth analysis."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from patent_analysis.analyses._aggregation import canonical_year, row_values
from patent_analysis.analysis_inputs import prepare_records_population
from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis.population import PopulationResult

GROWTH_ALGORITHM_VERSION = "1.0.0"
MAX_LABEL_JSON_BYTES = 4096
MAX_TOP_N = 20
MAX_EXPANDED_CONTRIBUTIONS = 1_000_000
MAX_DISTINCT_BUCKETS = 100_000


class GrowthBudgetError(ValueError):
    """Raised before a growth operation would exceed a fixed budget."""

    code = "analysis.invalid"


def _validate_parameters(parameters: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(parameters, Mapping):
        raise ValueError("growth parameters must be an object")
    allowed = {"date_role", "series_role", "start_year", "end_year", "top_n"}
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError(f"unsupported growth parameters: {unknown}")
    date_role = parameters.get("date_role")
    series_role = parameters.get("series_role")
    if not isinstance(date_role, str) or not date_role.strip():
        raise ValueError("date_role must be a non-empty string")
    if not isinstance(series_role, str) or not series_role.strip():
        raise ValueError("series_role must be a non-empty string")
    date_role = date_role.strip()
    series_role = series_role.strip()
    if date_role == series_role:
        raise ValueError("date_role and series_role must differ")
    start_year = parameters.get("start_year")
    end_year = parameters.get("end_year")
    if (
        type(start_year) is not int
        or type(end_year) is not int
        or not 1800 <= start_year < end_year <= 2199
    ):
        raise ValueError("year range is invalid")
    top_n = parameters.get("top_n", MAX_TOP_N)
    if type(top_n) is not int or not 1 <= top_n <= MAX_TOP_N:
        raise ValueError("top_n must be an integer from 1 through 20")
    return {
        "date_role": date_role,
        "series_role": series_role,
        "start_year": start_year,
        "end_year": end_year,
        "top_n": top_n,
    }


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    validated = _validate_parameters(parameters)
    return str(validated["date_role"]), str(validated["series_role"])


def analyze_growth(
    population: PopulationResult,
    parameters: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(population, PopulationResult):
        raise TypeError("population must be a PopulationResult")
    validated = _validate_parameters(parameters)
    date_role = str(validated["date_role"])
    series_role = str(validated["series_role"])
    start_year = int(validated["start_year"])
    end_year = int(validated["end_year"])

    counts: dict[str, list[int]] = {}
    invalid_year_rows = 0
    outside_endpoint_rows = 0
    blank_series_rows = 0
    visible_rows = 0
    contributions = 0
    distinct_buckets = 0

    for row in population.rows:
        year = canonical_year(row_values(row, date_role))
        if year is None:
            invalid_year_rows += 1
            continue
        if year not in {start_year, end_year}:
            outside_endpoint_rows += 1
            continue
        labels = row_values(row, series_role)
        if not labels:
            blank_series_rows += 1
            continue
        if contributions + len(labels) > MAX_EXPANDED_CONTRIBUTIONS:
            raise GrowthBudgetError(
                f"expanded contributions exceed limit {MAX_EXPANDED_CONTRIBUTIONS}"
            )
        index = 0 if year == start_year else 1
        new_buckets = sum(
            1 for label in set(labels) if label not in counts or counts[label][index] == 0
        )
        if distinct_buckets + new_buckets > MAX_DISTINCT_BUCKETS:
            raise GrowthBudgetError(f"distinct buckets exceed limit {MAX_DISTINCT_BUCKETS}")
        if any(len(canonical_json_bytes(label)) > MAX_LABEL_JSON_BYTES for label in labels):
            raise GrowthBudgetError("serialized label exceeds limit 4096 bytes")

        contributions += len(labels)
        visible_rows += 1
        distinct_buckets += new_buckets
        for label in labels:
            bucket = counts.setdefault(label, [0, 0])
            bucket[index] += 1

    candidates = sorted(
        counts.items(),
        key=lambda item: (-(item[1][0] + item[1][1]), item[0]),
    )[: int(validated["top_n"])]

    def document(item: tuple[str, list[int]]) -> dict[str, object]:
        label, values = item
        start_value, end_value = values
        if start_value == 0:
            growth_rate: float | None = None
            growth_state = "new"
        else:
            growth_rate = (end_value - start_value) / start_value
            growth_state = "measured"
        return {
            "label": label,
            "values": list(values),
            "row_counts": list(values),
            "is_other": False,
            "growth_rate": growth_rate,
            "growth_state": growth_state,
        }

    series = [document(item) for item in candidates]
    series.sort(
        key=lambda item: (
            0 if item["growth_state"] == "new" else 1,
            -float(item["growth_rate"] or 0.0),
            -sum(item["values"]),
            str(item["label"]),
        )
    )
    input_rows = population.receipt.included_rows
    return {
        "schema_version": "1.0.0",
        "analysis_id": "growth.v1",
        "algorithm_version": GROWTH_ALGORITHM_VERSION,
        "measure": {"mode": "count", "role": None},
        "start_year": start_year,
        "end_year": end_year,
        "x": [str(start_year), str(end_year)],
        "series": series,
        "population": {
            "input_rows": input_rows,
            "visible_rows": visible_rows,
            "invalid_year_rows": invalid_year_rows,
            "outside_endpoint_rows": outside_endpoint_rows,
            "blank_series_rows": blank_series_rows,
            "excluded_rows": input_rows - visible_rows,
        },
        "contributions": contributions,
        "limits": {
            "max_top_n": MAX_TOP_N,
            "max_expanded_contributions": MAX_EXPANDED_CONTRIBUTIONS,
            "max_distinct_buckets": MAX_DISTINCT_BUCKETS,
        },
    }


def analyze_growth_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    if not isinstance(spec, Mapping) or spec.get("analysis_id") != "growth.v1":
        raise ValueError("growth analysis spec is invalid")
    parameters = spec.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("growth parameters must be an object")
    roles = required_roles(parameters)
    dataset, population = prepare_records_population(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_roles=roles,
    )
    data = analyze_growth(population, parameters)
    analyzed_rows = int(data["population"]["visible_rows"])
    return {
        "analysis_id": "growth.v1",
        "algorithm_version": GROWTH_ALGORITHM_VERSION,
        "result_variant": "series",
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
    "GROWTH_ALGORITHM_VERSION",
    "GrowthBudgetError",
    "analyze_growth",
    "analyze_growth_csv",
    "required_roles",
)
