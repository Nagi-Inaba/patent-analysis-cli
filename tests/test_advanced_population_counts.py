"""Supplied chart counts must describe a possible native analysis population."""
from __future__ import annotations

import itertools
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from patent_analysis.advanced_projection import project_advanced_data
from patent_analysis.analyses.growth_quadrant import compute as growth
from patent_analysis.analyses.matrix_composition import compute as composition

SCHEMAS = Path(__file__).resolve().parents[1] / "src/patent_analysis/schemas"
SPANS = (
    ((2020, 2023), (2020, 2023)),  # Identical.
    ((2020, 2024), (2022, 2023)),  # Contained.
    ((2022, 2023), (2020, 2024)),  # Reverse containment is also supported.
    ((2020, 2023), (2021, 2024)),  # Crossing halves.
    ((2021, 2024), (2020, 2023)),
    ((2020, 2022), (2022, 2024)),  # Shared inclusive endpoint.
    ((2020, 2021), (2022, 2024)),  # Adjacent, no overlap.
    ((2020, 2021), (2023, 2024)),  # A gap is outside both spans.
)


def _validate(data):
    name = data["analysis_id"].removesuffix(".v1") + "-result-v1.schema.json"
    schema = json.loads((SCHEMAS / name).read_bytes())
    Draft202012Validator(schema).validate(data)


def _growth(spans, years=(2020, 2021, 2022, 2023, 2024)):
    return growth([{"year": (str(year),), "category": ("A",)} for year in years], {
        "date_role": "year", "category_role": "category",
        "long_start_year": spans[0][0], "long_end_year": spans[0][1],
        "short_start_year": spans[1][0], "short_end_year": spans[1][1],
    })


@pytest.mark.parametrize("spans", SPANS)
def test_native_growth_union_is_preserved_for_all_span_arrangements(spans):
    data = _growth(spans)
    before = deepcopy(data)
    _validate(data)
    projected = project_advanced_data("growth-quadrant.v1", data)
    assert projected["points"][0]["size"] == data["points"][0]["total_count"]
    assert data == before


@pytest.mark.parametrize("total", [0, 1, 3, 4])
def test_rejects_inconsistent_identical_span_total(total):
    data = _growth(((2020, 2021), (2020, 2021)), years=(2020, 2021))
    data["points"][0]["total_count"] = total
    _validate(data)  # The structural schema alone accepts the contradiction.
    before = deepcopy(data)
    with pytest.raises(ValueError, match="Growth total"):
        project_advanced_data("growth-quadrant.v1", data)
    assert data == before


@pytest.mark.parametrize("spans", SPANS[1:])
def test_rejects_total_above_union_or_below_a_proven_span(spans):
    for total in (0, 100):
        data = _growth(spans)
        data["points"][0]["total_count"] = total
        _validate(data)
        with pytest.raises(ValueError, match="Growth total"):
            project_advanced_data("growth-quadrant.v1", data)


def test_undefined_rate_does_not_bypass_the_total_check():
    data = _growth(((2020, 2023), (2022, 2023)), years=(2023,))
    assert project_advanced_data("growth-quadrant.v1", data)["unplottable"][0]["count"] == 1
    data["points"][0]["total_count"] = 0
    with pytest.raises(ValueError, match="Growth total"):
        project_advanced_data("growth-quadrant.v1", data)


def test_later_invalid_point_is_not_ignored():
    data = _growth(SPANS[0])
    second = deepcopy(data["points"][0])
    second.update(label="B", total_count=0)
    data["points"].append(second)
    with pytest.raises(ValueError, match="Growth total"):
        project_advanced_data("growth-quadrant.v1", data)


def _set_counts(data, values):
    point = data["points"][0]
    for side, (previous, recent) in zip(("long", "short"), (values[:2], values[2:4]), strict=True):
        point[side] = {
            "previous": previous, "recent": recent,
            "rate_percent": (recent - previous) / previous * 100
            if previous else None if recent else 0.0,
            "state": "measured" if previous else "new" if recent else "empty",
        }
    x, y = point["long"]["rate_percent"], point["short"]["rate_percent"]
    point["quadrant"] = "new" if x is None or y is None else (
        "sustained_growth" if x >= 0 and y >= 0 else
        "recovery" if x < 0 <= y else "slowing" if y < 0 <= x else "decline"
    )
    point["total_count"] = values[4]


@pytest.mark.parametrize("spans", SPANS)
def test_growth_consistency_matches_small_exhaustive_population_oracle(spans):
    # Enumerate actual zero-, one- and two-record populations independently.
    years = [year for year in range(2020, 2025)
             if any(start <= year <= end for start, end in spans)]
    possible = set()
    for total in range(3):
        for records in itertools.combinations_with_replacement(years, total):
            counts = []
            for start, end in spans:
                midpoint = (start + end) // 2
                counts.extend((sum(start <= y <= midpoint for y in records),
                               sum(midpoint < y <= end for y in records)))
            possible.add((*counts, total))
    data = _growth(spans)
    for values in itertools.product(range(3), repeat=5):
        _set_counts(data, values)
        try:
            project_advanced_data("growth-quadrant.v1", data)
        except ValueError:
            accepted = False
        else:
            accepted = True
        assert accepted == (values in possible), (spans, values)


def _composition(labels=("A", "B"), top_n=20):
    return composition([{"x": ("X",), "y": ("Y",), "category": labels}], {
        "x_role": "x", "y_role": "y", "category_role": "category",
        "x_value": "X", "y_value": "Y", "top_n": top_n,
    })


@pytest.mark.parametrize(("rows", "count"), [(0, 1), (1, 2), (1, 100), (2, 3)])
def test_composition_category_cannot_exceed_selected_rows(rows, count):
    data = _composition(("A",))
    data.update(cell_rows=rows, category_memberships=count, contributions=count)
    data["items"][0].update(count=count, share=1.0)
    _validate(data)
    before = deepcopy(data)
    with pytest.raises(ValueError, match="selected rows"):
        project_advanced_data("matrix-composition.v1", data)
    assert data == before


def test_composition_checks_every_category_not_only_the_first():
    data = _composition()
    data.update(category_memberships=3, contributions=3)
    data["items"][0].update(count=1, share=1 / 3)
    data["items"][1].update(count=2, share=2 / 3)
    _validate(data)
    with pytest.raises(ValueError, match="selected rows"):
        project_advanced_data("matrix-composition.v1", data)


@pytest.mark.parametrize("top_n", [1, 20])
def test_multilabel_memberships_can_exceed_rows_without_renormalizing(top_n):
    data = _composition(("A", "A", "B"), top_n=top_n)
    before = deepcopy(data)
    _validate(data)
    assert data["cell_rows"] == 1 and data["category_memberships"] == 2
    projected = project_advanced_data("matrix-composition.v1", data)
    assert all(item["value"] == item["record_count"] == 1 for item in projected["items"])
    assert all(item["denominator"] == 2 and item["share"] == 0.5
               for item in projected["items"])
    assert data == before


def test_empty_results_remain_valid():
    data = _growth(SPANS[0], years=())
    assert project_advanced_data("growth-quadrant.v1", data)["points"] == []
    data = _composition(labels=())
    assert project_advanced_data("matrix-composition.v1", data)["items"] == []
