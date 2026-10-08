"""Citation counts must not be fabricated by deleting malformed punctuation."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext

import pytest

from patent_analysis.analyses.citation import compute, parse_citation_count

PARAMETERS = {"date_role": "year", "label_role": "label", "citation_role": "cites"}


@pytest.mark.parametrize("text", [
    "1,2", "12,34", "1234,567", ",123", "123,", "1,,000", "1,000,",
    "1,000.0,1", "1.2,3", "ci,tations: 10", "cited, by: 5", "被引,用件数: 7",
])
def test_rejects_malformed_commas_instead_of_changing_the_number(text: str) -> None:
    assert parse_citation_count(text) is None


@pytest.mark.parametrize("text", [
    "1000000000000.00001",
    "1,000,000,000,000.000000001",
    "被引用件数: 1000000000000.0000000000000000000000000000001",
])
def test_enforces_upper_bound_before_binary_float_rounding(text: str) -> None:
    assert parse_citation_count(text) is None


@pytest.mark.parametrize(("text", "expected"), [
    ("0", 0), ("00012", 12), ("12.5", 12.5), ("1,000", 1000),
    ("12,345,678", 12345678), ("1,234.5", 1234.5),
    ("  cited by: 1,000  ", 1000), ("FORWARD CITATIONS: 1,234.5", 1234.5),
    ("被引用件数： 1,234", 1234), ("引用回数: 0.5", 0.5),
    ("1000000000000", 1000000000000), ("1,000,000,000,000.000", 1000000000000),
    ("１０００", 1000), ("１,０００.５", 1000.5),
])
def test_preserves_supported_numbers_and_prefixes(text: str, expected: float) -> None:
    assert parse_citation_count(text) == expected


@pytest.mark.parametrize("text", [
    "", "NaN", "Infinity", "-1", "1e3", "1 000", "1_000", "10 patents",
    "1000000000001", "9" * 129,
])
def test_existing_invalid_forms_stay_excluded(text: str) -> None:
    assert parse_citation_count(text) is None


def test_parsing_does_not_depend_on_callers_decimal_precision() -> None:
    with localcontext() as context:
        context.prec = 2
        assert parse_citation_count("1000000000000.00001") is None
        assert parse_citation_count("1,234.5") == 1234.5


def test_normalized_kernel_excludes_invalid_counts_before_ranking_and_population() -> None:
    rows = [
        {"year": ("2020",), "label": ("valid",), "cites": ("1,000",)},
        {"year": ("2021",), "label": ("comma typo",), "cites": ("99,99",)},
        {"year": ("2022",), "label": ("too high",), "cites": ("1000000000000.00001",)},
        {"year": ("2023",), "label": ("valid zero",), "cites": ("0",)},
    ]
    original = deepcopy(rows)
    result = compute(rows, PARAMETERS)
    assert [(p["label"], p["citation_value"]) for p in result["points"]] == [
        ("valid", 1000), ("valid zero", 0),
    ]
    assert result["population"] == {"input_rows": 4, "visible_rows": 2, "excluded_rows": 2}
    assert result["contributions"] == 2
    assert compute(list(reversed(rows)), PARAMETERS) == result
    assert rows == original


def test_valid_grouped_and_ungrouped_numbers_have_identical_results() -> None:
    # Fixed Decimal construction supplies an independent numeric oracle. All
    # fractions are exactly representable in the public float result contract.
    for integer in (0, 1, 12, 999, 1000, 1000000, 999999999999):
        for suffix in ("", ".00", ".25", ".5", ".75"):
            plain = f"{integer}{suffix}"
            grouped = f"{integer:,}{suffix}"
            expected = float(Decimal(plain))
            assert parse_citation_count(plain) == expected
            assert parse_citation_count(grouped) == expected


@pytest.mark.parametrize(("raw", "count"), [
    ("1,000", 1000), ("1,2", None),
    ("1000000000000.00001", None), ("2;3", None),
])
def test_actual_role_splitter_preserves_commas_but_rejects_ambiguous_counts(
    raw: str, count: float | None,
) -> None:
    from patent_analysis.normalization.multi_value import split_patent_values

    tokens = split_patent_values(raw, role="cites")
    result = compute([
        {"year": ("2024",), "label": ("A",), "cites": tokens},
    ], PARAMETERS)
    if count is None:
        assert result["points"] == []
        assert result["population"]["excluded_rows"] == 1
    else:
        assert result["points"][0]["citation_value"] == count
        assert result["population"]["visible_rows"] == 1


def test_all_small_comma_placements_match_independent_grouping_oracle() -> None:
    from itertools import product

    for digits in ("1", "12", "123", "1234", "12345", "123456"):
        for commas in product(("", ","), repeat=len(digits) + 1):
            text = commas[0] + "".join(
                digit + comma for digit, comma in zip(digits, commas[1:], strict=True)
            )
            groups = text.split(",")
            valid = len(groups) == 1 or (
                1 <= len(groups[0]) <= 3 and all(len(group) == 3 for group in groups[1:])
            )
            expected = int(digits) if valid else None
            assert parse_citation_count(text) == expected, text
