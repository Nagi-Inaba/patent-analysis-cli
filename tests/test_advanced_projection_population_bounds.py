"""Supplied chart counts must be feasible without recounting or repairing input."""
from __future__ import annotations

import json
from collections import defaultdict
from copy import deepcopy
from itertools import combinations, product
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from patent_analysis.advanced_projection import project_advanced_data
from patent_analysis.analyses import growth_quadrant, matrix_composition

SCHEMAS = Path(__file__).resolve().parents[1] / "src/patent_analysis/schemas"
GROWTH = "growth-quadrant.v1"
COMPOSITION = "matrix-composition.v1"


def _schema_valid(data: dict) -> None:
    name = data["analysis_id"].removesuffix(".v1")
    schema = json.loads((SCHEMAS / f"{name}-result-v1.schema.json").read_bytes())
    Draft202012Validator(schema).validate(data)


def _growth(long: tuple[int, int], short: tuple[int, int], years: list[int]) -> dict:
    return growth_quadrant.compute(
        [{"date": (str(year),), "owner": ("A", "A")} for year in years],
        {"date_role": "date", "category_role": "owner",
         "long_start_year": long[0], "long_end_year": long[1],
         "short_start_year": short[0], "short_end_year": short[1]},
    )


def _unchanged_rejection(data: dict, message: str) -> None:
    _schema_valid(data)
    original = deepcopy(data)
    with pytest.raises(ValueError, match=message):
        project_advanced_data(data["analysis_id"], data)
    assert data == original


@pytest.mark.parametrize(("long", "short", "years", "wrong_total"), [
    ((2000, 2003), (2000, 2003), [2000, 2003], 0),
    ((2000, 2003), (2000, 2003), [2000, 2003], 4),
    ((2000, 2005), (2002, 2003), [2000, 2002, 2003, 2005], 6),
    ((2002, 2003), (2000, 2005), [2000, 2002, 2003, 2005], 3),
    ((2000, 2001), (2004, 2005), [2000, 2001, 2004, 2005], 3),
    ((2000, 2003), (2002, 2005), [2000, 2002, 2002, 2004, 2004, 2004], 5),
    ((2000, 2001), (2001, 2002), [2000, 2001, 2001, 2002], 6),
    ((2000, 2003), (2000, 2003), [2003], 0),
])
def test_rejects_infeasible_growth_totals(long, short, years, wrong_total):
    data = _growth(long, short, years)
    data["points"][0]["total_count"] = wrong_total
    _unchanged_rejection(data, "Growth.*count")


@pytest.mark.parametrize(("long", "short"), [
    ((2000, 2003), (2000, 2003)),
    ((2000, 2005), (2002, 2003)),
    ((2002, 2003), (2000, 2005)),
    ((2000, 2001), (2004, 2005)),
    ((2000, 2003), (2002, 2005)),
    ((2000, 2001), (2001, 2002)),
])
def test_real_core_union_counts_are_preserved(long, short):
    years = [1999, 2000, 2001, 2001, 2002, 2003, 2004, 2005, 2006]
    data = _growth(long, short, years)
    _schema_valid(data)
    original = deepcopy(data)
    projected = project_advanced_data(GROWTH, data)
    expected = sum(long[0] <= y <= long[1] or short[0] <= y <= short[1] for y in years)
    assert projected["points"][0]["size"] == expected
    assert data == original
    assert project_advanced_data(GROWTH, _growth(long, short, list(reversed(years)))) == projected


def test_rejects_conflicting_half_counts_on_identical_spans():
    data = _growth((2000, 2003), (2000, 2003), [2000, 2003])
    point = data["points"][0]
    point["short"] = {"previous": 0, "recent": 2, "rate_percent": None, "state": "new"}
    point["quadrant"] = "new"
    _unchanged_rejection(data, "Growth.*count")


def test_undefined_rates_and_empty_populations_keep_their_semantics():
    data = _growth((2000, 2003), (2000, 2003), [2003, 2003])
    projected = project_advanced_data(GROWTH, data)
    assert projected["points"] == []
    assert projected["unplottable"] == [
        {"label": "A", "long_state": "new", "short_state": "new", "count": 2},
    ]
    empty = project_advanced_data(GROWTH, _growth((2000, 2003), (2000, 2003), []))
    assert empty["points"] == empty["unplottable"] == []


def test_growth_consistency_matches_exhaustive_small_integer_populations():
    # Independent enumeration, not the projection's validation algorithm. All
    # nonnegative four-year populations with total <=3 are represented, so this
    # is an exact feasibility oracle for the candidate totals 0..3 below.
    spans = list(combinations(range(2000, 2004), 2))
    for long, short in product(spans, repeat=2):
        possible = defaultdict(set)
        for histogram in product(range(4), repeat=4):
            if sum(histogram) > 3:
                continue
            bins = []
            for start, end in (long, short):
                mid = (start + end) // 2
                bins.extend((
                    sum(n for y, n in zip(range(2000, 2004), histogram, strict=True)
                        if start <= y <= mid),
                    sum(n for y, n in zip(range(2000, 2004), histogram, strict=True)
                        if mid < y <= end),
                ))
            total = sum(n for y, n in zip(range(2000, 2004), histogram, strict=True)
                        if long[0] <= y <= long[1] or short[0] <= y <= short[1])
            possible[tuple(bins)].add(total)
        for bins, valid_totals in possible.items():
            sides = []
            for before, after in (bins[:2], bins[2:]):
                rate = (after - before) / before * 100 if before else None if after else 0.0
                sides.append({"previous": before, "recent": after, "rate_percent": rate,
                              "state": "measured" if before else "new" if after else "empty"})
            x, y = (s["rate_percent"] for s in sides)
            quadrant = "new" if x is None or y is None else (
                "sustained_growth" if x >= 0 and y >= 0 else
                "recovery" if x < 0 <= y else "slowing" if y < 0 <= x else "decline"
            )
            for total in range(4):
                data = {"analysis_id": GROWTH,
                        "long_span": {"start_year": long[0], "end_year": long[1]},
                        "short_span": {"start_year": short[0], "end_year": short[1]},
                        "points": [{"label": "A", "total_count": total,
                                    "long": sides[0], "short": sides[1], "quadrant": quadrant}]}
                if total in valid_totals:
                    project_advanced_data(GROWTH, data)
                else:
                    with pytest.raises(ValueError, match="Growth.*count"):
                        project_advanced_data(GROWTH, data)


def _composition(labels: list[tuple[str, ...]], top_n: int = 20) -> dict:
    return matrix_composition.compute(
        [{"x": ("X",), "y": ("Y",), "category": values} for values in labels],
        {"x_role": "x", "y_role": "y", "category_role": "category",
         "x_value": "X", "y_value": "Y", "top_n": top_n},
    )


@pytest.mark.parametrize("position", [0, 1])
def test_rejects_a_category_count_larger_than_selected_rows(position):
    data = _composition([("A", "B")])
    data["category_memberships"] = data["contributions"] = 101
    for i, item in enumerate(data["items"]):
        item["count"] = 100 if i == position else 1
        item["share"] = item["count"] / 101
    _unchanged_rejection(data, "Composition.*row")


def test_rejects_positive_category_with_zero_selected_rows():
    data = _composition([("A",)])
    data["cell_rows"] = 0
    _unchanged_rejection(data, "Composition.*row")


@pytest.mark.parametrize("top_n", [1, 20])
def test_multiple_categories_duplicates_and_top_n_keep_full_denominator(top_n):
    data = _composition([("A", "A", "B"), ("A", "C"), ()], top_n=top_n)
    _schema_valid(data)
    original = deepcopy(data)
    projected = project_advanced_data(COMPOSITION, data)
    assert data["cell_rows"] == 3
    assert data["category_memberships"] == 4  # May exceed row count legitimately.
    assert projected["items"][0]["value"] == 2
    assert projected["items"][0]["share"] == 0.5  # Not renormalized for top_n=1.
    assert all(p["denominator"] == 4 for p in projected["items"])
    assert data == original


def test_empty_composition_and_exact_per_row_boundary_are_valid():
    assert project_advanced_data(COMPOSITION, _composition([]))["items"] == []
    assert project_advanced_data(COMPOSITION, _composition([()]))["items"] == []
    data = _composition([("A", "B")])
    projected = project_advanced_data(COMPOSITION, data)
    assert [p["value"] for p in projected["items"]] == [1, 1]
    assert [p["share"] for p in projected["items"]] == [0.5, 0.5]
