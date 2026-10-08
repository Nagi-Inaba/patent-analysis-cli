"""Deterministic yearly series analysis over canonically normalized years."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from patent_analysis.analyses._aggregation import (
    canonical_year,
    dedupe_rows,
    measure_rows,
    row_values,
    unique_aggregate_label,
    validate_measure,
)
from patent_analysis.analysis_inputs import prepare_records_population
from patent_analysis.normalization import NormalizedRow
from patent_analysis.population import PopulationResult

TIMELINE_ALGORITHM_VERSION = "1.0.0"
OTHER_LABEL = "その他（上位外）"
MAX_TOP_N = 100
MAX_EXPANDED_CONTRIBUTIONS = 1_000_000


class TimelineBudgetError(ValueError):
    """Raised before a timeline contribution would exceed the fixed budget."""


def _validate_parameters(parameters: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(parameters, Mapping):
        raise ValueError("timeline parameters must be an object")
    allowed = {
        "date_role",
        "series_role",
        "start_year",
        "end_year",
        "top_n",
        "include_other",
        "measure",
        "measure_role",
    }
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise ValueError(f"unsupported timeline parameters: {unknown}")

    date_role = parameters.get("date_role")
    series_role = parameters.get("series_role")
    if not isinstance(date_role, str) or not date_role.strip():
        raise ValueError("date_role must be a non-empty string")
    if not isinstance(series_role, str) or not series_role.strip():
        raise ValueError("series_role must be a non-empty string")

    start_year = parameters.get("start_year")
    end_year = parameters.get("end_year")
    if (start_year is None) != (end_year is None):
        raise ValueError("start_year and end_year must be specified together")
    if start_year is not None and (
        type(start_year) is not int
        or type(end_year) is not int
        or not 1800 <= start_year <= end_year <= 2199
    ):
        raise ValueError("year range is invalid")

    top_n = parameters.get("top_n", 10)
    if type(top_n) is not int or not 1 <= top_n <= MAX_TOP_N:
        raise ValueError("top_n must be an integer from 1 through 100")
    include_other = parameters.get("include_other", True)
    if type(include_other) is not bool:
        raise ValueError("include_other must be boolean")
    measure, measure_role = validate_measure(parameters)
    return {
        "date_role": date_role.strip(),
        "series_role": series_role.strip(),
        "start_year": start_year,
        "end_year": end_year,
        "top_n": top_n,
        "include_other": include_other,
        "measure": measure,
        "measure_role": measure_role,
    }


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    validated = _validate_parameters(parameters)
    output = [str(validated["date_role"]), str(validated["series_role"])]
    measure_role = validated["measure_role"]
    if isinstance(measure_role, str) and measure_role not in output:
        output.append(measure_role)
    return tuple(output)


def analyze_timeline(
    population: PopulationResult,
    parameters: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(population, PopulationResult):
        raise TypeError("population must be a PopulationResult")
    validated = _validate_parameters(parameters)
    date_role = str(validated["date_role"])
    series_role = str(validated["series_role"])
    mode = str(validated["measure"])
    measure_role = validated["measure_role"]
    assert measure_role is None or isinstance(measure_role, str)
    start_year = validated["start_year"]
    end_year = validated["end_year"]
    top_n = int(validated["top_n"])

    eligible: list[tuple[int, NormalizedRow, tuple[str, ...]]] = []
    invalid_year_rows = 0
    outside_year_range_rows = 0
    blank_series_rows = 0
    contributions = 0

    for row in population.rows:
        year = canonical_year(row_values(row, date_role))
        if year is None:
            invalid_year_rows += 1
            continue
        if (
            start_year is not None
            and end_year is not None
            and not int(start_year) <= year <= int(end_year)
        ):
            outside_year_range_rows += 1
            continue
        labels = row_values(row, series_role)
        if not labels:
            blank_series_rows += 1
            continue
        if contributions + len(labels) > MAX_EXPANDED_CONTRIBUTIONS:
            raise TimelineBudgetError(
                f"expanded contributions exceed limit {MAX_EXPANDED_CONTRIBUTIONS}"
            )
        contributions += len(labels)
        eligible.append((year, row, labels))

    overall_rows: dict[str, list[NormalizedRow]] = defaultdict(list)
    for _, row, labels in eligible:
        for label in labels:
            overall_rows[label].append(row)

    ranked = sorted(
        (
            (
                label,
                tuple(bucket_rows),
                measure_rows(bucket_rows, mode=mode, measure_role=measure_role),
            )
            for label, bucket_rows in overall_rows.items()
        ),
        key=lambda item: (-float(item[2]), -len(item[1]), item[0]),
    )
    top = tuple(label for label, _, _ in ranked[:top_n])
    top_set = frozenset(top)
    use_other = bool(validated["include_other"]) and len(ranked) > len(top)

    years = sorted({year for year, _, _ in eligible})
    per_series_year: dict[str, dict[int, list[NormalizedRow]]] = {
        label: defaultdict(list) for label in top
    }
    other_by_year: dict[int, list[NormalizedRow]] = defaultdict(list)

    for year, row, labels in eligible:
        for label in labels:
            if label in top_set:
                per_series_year[label][year].append(row)
        if use_other and any(label not in top_set for label in labels):
            other_by_year[year].append(row)

    series_documents: list[dict[str, object]] = []
    for label in top:
        series_documents.append(
            {
                "label": label,
                "values": [
                    measure_rows(
                        per_series_year[label].get(year, ()),
                        mode=mode,
                        measure_role=measure_role,
                    )
                    for year in years
                ],
                "row_counts": [
                    len(per_series_year[label].get(year, ())) for year in years
                ],
                "is_other": False,
            }
        )

    if use_other:
        other_values: list[float | int] = []
        other_counts: list[int] = []
        for year in years:
            deduped = dedupe_rows(other_by_year.get(year, ()))
            other_values.append(
                measure_rows(deduped, mode=mode, measure_role=measure_role)
            )
            other_counts.append(len(deduped))
        series_documents.append(
            {
                "label": unique_aggregate_label(OTHER_LABEL, overall_rows),
                "values": other_values,
                "row_counts": other_counts,
                "is_other": True,
            }
        )

    visible_rows = len(eligible)
    input_rows = population.receipt.included_rows
    return {
        "schema_version": "1.0.0",
        "analysis_id": "timeline.v1",
        "algorithm_version": TIMELINE_ALGORITHM_VERSION,
        "measure": {"mode": mode, "role": measure_role},
        "x": [str(year) for year in years],
        "series": series_documents,
        "population": {
            "input_rows": input_rows,
            "visible_rows": visible_rows,
            "invalid_year_rows": invalid_year_rows,
            "outside_year_range_rows": outside_year_range_rows,
            "blank_series_rows": blank_series_rows,
            "excluded_rows": input_rows - visible_rows,
        },
        "contributions": contributions,
        "limits": {
            "max_top_n": MAX_TOP_N,
            "max_expanded_contributions": MAX_EXPANDED_CONTRIBUTIONS,
        },
    }


def analyze_timeline_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    """Run the shared records pipeline and return the common v2 result envelope."""

    if not isinstance(spec, Mapping) or spec.get("analysis_id") != "timeline.v1":
        raise ValueError("timeline analysis spec is invalid")
    parameters = spec.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("timeline parameters must be an object")
    roles = required_roles(parameters)
    dataset, population = prepare_records_population(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_roles=roles,
    )
    data = analyze_timeline(population, parameters)
    analyzed_rows = int(data["population"]["visible_rows"])
    return {
        "analysis_id": "timeline.v1",
        "algorithm_version": TIMELINE_ALGORITHM_VERSION,
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
