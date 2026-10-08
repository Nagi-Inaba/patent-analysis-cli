"""Deterministic yearly HHI concentration analysis."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path

from patent_analysis.analyses._aggregation import canonical_year, row_values
from patent_analysis.analysis_inputs import prepare_records_population
from patent_analysis.population import PopulationResult

CONCENTRATION_ALGORITHM_VERSION = "1.0.0"
MAX_YEAR_BUCKETS = 400
MAX_DISTINCT_BUCKETS = 100_000
MAX_EXPANDED_CONTRIBUTIONS = 1_000_000


class ConcentrationBudgetError(ValueError):
    """Raised before a concentration operation would exceed a fixed budget."""

    code = "analysis.invalid"


def concentration_hhi(counts: Iterable[int]) -> float:
    materialized = tuple(counts)
    if not materialized or any(type(value) is not int or value < 0 for value in materialized):
        raise ValueError("concentration counts are invalid")
    total = sum(materialized)
    if total <= 0:
        raise ValueError("concentration counts must be positive")
    numerator = sum(value * value for value in materialized)
    denominator = total * total
    scaled_numerator = numerator * 1000
    quotient, remainder = divmod(scaled_numerator, denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return quotient / 1000


def classify_hhi(value: float) -> str:
    if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
        raise ValueError("HHI is invalid")
    if value < 0.15:
        return "competitive"
    if value <= 0.25:
        return "moderate"
    return "concentrated"


def _validate_parameters(parameters: Mapping[str, object]) -> dict[str, str]:
    if not isinstance(parameters, Mapping):
        raise ValueError("concentration parameters must be an object")
    allowed = {"date_role", "category_role"}
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError(f"unsupported concentration parameters: {unknown}")
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
    return {"date_role": date_role, "category_role": category_role}


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    validated = _validate_parameters(parameters)
    return validated["date_role"], validated["category_role"]


def analyze_concentration(
    population: PopulationResult,
    parameters: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(population, PopulationResult):
        raise TypeError("population must be a PopulationResult")
    validated = _validate_parameters(parameters)
    date_role = validated["date_role"]
    category_role = validated["category_role"]

    year_categories: dict[int, dict[str, int]] = {}
    year_rows: dict[int, set[int]] = defaultdict(set)
    invalid_year_rows = 0
    blank_category_rows = 0
    visible_rows = 0
    contributions = 0
    distinct_buckets = 0

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
            raise ConcentrationBudgetError(
                f"expanded contributions exceed limit {MAX_EXPANDED_CONTRIBUTIONS}"
            )
        if year not in year_categories:
            if len(year_categories) + 1 > MAX_YEAR_BUCKETS:
                raise ConcentrationBudgetError(f"year buckets exceed limit {MAX_YEAR_BUCKETS}")
            year_categories[year] = {}
        bucket = year_categories[year]
        new_count = sum(1 for category in categories if category not in bucket)
        if distinct_buckets + new_count > MAX_DISTINCT_BUCKETS:
            raise ConcentrationBudgetError(f"distinct buckets exceed limit {MAX_DISTINCT_BUCKETS}")
        distinct_buckets += new_count
        contributions += len(categories)
        visible_rows += 1
        year_rows[year].add(row.source_ordinal)
        for category in categories:
            bucket[category] = bucket.get(category, 0) + 1

    years = sorted(year_categories)
    values: list[float] = []
    row_counts: list[int] = []
    contribution_counts: list[int] = []
    classifications: list[str] = []
    for year in years:
        counts = tuple(year_categories[year].values())
        hhi = concentration_hhi(counts)
        values.append(hhi)
        row_counts.append(len(year_rows[year]))
        contribution_counts.append(sum(counts))
        classifications.append(classify_hhi(hhi))

    input_rows = population.receipt.included_rows
    series: list[dict[str, object]] = []
    if years:
        series.append(
            {
                "label": "HHI",
                "values": values,
                "row_counts": row_counts,
                "contribution_counts": contribution_counts,
                "classifications": classifications,
                "is_other": False,
            }
        )
    return {
        "schema_version": "1.0.0",
        "analysis_id": "concentration.v1",
        "algorithm_version": CONCENTRATION_ALGORITHM_VERSION,
        "measure": {"mode": "count", "role": None},
        "x": [str(year) for year in years],
        "series": series,
        "population": {
            "input_rows": input_rows,
            "visible_rows": visible_rows,
            "invalid_year_rows": invalid_year_rows,
            "blank_category_rows": blank_category_rows,
            "excluded_rows": input_rows - visible_rows,
        },
        "contributions": contributions,
        "limits": {
            "max_year_buckets": MAX_YEAR_BUCKETS,
            "max_expanded_contributions": MAX_EXPANDED_CONTRIBUTIONS,
            "max_distinct_buckets": MAX_DISTINCT_BUCKETS,
        },
    }


def analyze_concentration_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    if not isinstance(spec, Mapping) or spec.get("analysis_id") != "concentration.v1":
        raise ValueError("concentration analysis spec is invalid")
    parameters = spec.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("concentration parameters must be an object")
    roles = required_roles(parameters)
    dataset, population = prepare_records_population(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_roles=roles,
    )
    data = analyze_concentration(population, parameters)
    analyzed_rows = int(data["population"]["visible_rows"])
    return {
        "analysis_id": "concentration.v1",
        "algorithm_version": CONCENTRATION_ALGORITHM_VERSION,
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
    "CONCENTRATION_ALGORITHM_VERSION",
    "ConcentrationBudgetError",
    "analyze_concentration",
    "analyze_concentration_csv",
    "classify_hhi",
    "concentration_hhi",
    "required_roles",
)
