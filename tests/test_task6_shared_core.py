from __future__ import annotations

from types import MappingProxyType

import pytest

from patent_analysis.normalization.pipeline import NormalizedRow


def _row(ordinal: int, **roles: tuple[str, ...]) -> NormalizedRow:
    return NormalizedRow(
        source_ordinal=ordinal,
        source_fields=tuple(value for values in roles.values() for value in values),
        values_by_role=MappingProxyType(dict(roles)),
    )


def test_analysis_inputs_stable_roles_and_records_population_translation() -> None:
    from patent_analysis.analysis_inputs import records_population_spec, stable_roles

    assert stable_roles(("applicant", "year", "applicant", " ", "year")) == (
        "applicant",
        "year",
    )

    translated, roles = records_population_spec(
        {
            "family_mode": "records",
            "selection_sets": [],
            "filters": [
                {
                    "role": "applicant",
                    "effect": "include",
                    "match": "one_of",
                    "values": ["A社", "B社"],
                },
                {
                    "role": "year",
                    "effect": "exclude",
                    "match": "year_range",
                    "start_year": 2018,
                    "end_year": 2019,
                },
            ],
        }
    )

    assert roles == ("applicant", "year")
    assert translated == {
        "family_mode": "records",
        "filters": [
            {
                "role": "applicant",
                "match": "one_of",
                "exclude": False,
                "values": ["A社", "B社"],
            },
            {
                "role": "year",
                "match": "year_range",
                "exclude": True,
                "start": 2018,
                "end": 2019,
            },
        ],
    }


def test_records_population_translation_rejects_future_population_features() -> None:
    from patent_analysis.analysis_inputs import records_population_spec

    with pytest.raises(ValueError, match="records"):
        records_population_spec(
            {"family_mode": "representative", "selection_sets": [], "filters": []}
        )
    with pytest.raises(ValueError, match="selection"):
        records_population_spec(
            {"family_mode": "records", "selection_sets": [{"id": "x"}], "filters": []}
        )


def test_generic_numeric_parser_does_not_import_citation_semantics() -> None:
    from patent_analysis.analyses._aggregation import parse_number

    assert parse_number("1,234.5") == 1234.5
    assert parse_number("-12") == -12.0
    assert parse_number("0") == 0.0
    assert parse_number("NaN") is None
    assert parse_number("Infinity") is None
    assert parse_number("被引用件数: 12") is None
    assert parse_number("citation count: 12") is None


def test_measure_engine_operates_on_canonical_normalized_rows() -> None:
    from patent_analysis.analyses._aggregation import measure_rows, row_values

    rows = (
        _row(1, applicant=("A社",), score=("10",)),
        _row(2, applicant=("A社", "B社"), score=("20",)),
        _row(3, applicant=("B社",), score=("invalid",)),
    )

    assert row_values(rows[1], "applicant") == ("A社", "B社")
    assert measure_rows(rows, mode="count", measure_role=None) == 3
    assert measure_rows(rows, mode="sum", measure_role="score") == 30
    assert measure_rows(rows, mode="average", measure_role="score") == 15
    assert measure_rows(rows, mode="max", measure_role="score") == 20
    assert measure_rows(rows, mode="min", measure_role="score") == 10


def test_measure_validation_is_closed() -> None:
    from patent_analysis.analyses._aggregation import validate_measure

    assert validate_measure({"measure": "count"}) == ("count", None)
    assert validate_measure({"measure": "sum", "measure_role": "score"}) == (
        "sum",
        "score",
    )
    with pytest.raises(ValueError, match="unsupported"):
        validate_measure({"measure": "median", "measure_role": "score"})
    with pytest.raises(ValueError, match="required"):
        validate_measure({"measure": "sum"})
