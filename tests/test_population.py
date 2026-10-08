from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator

from patent_analysis.normalization import (
    NormalizationReceipt,
    NormalizedDataset,
    NormalizedRow,
)


def _normalized_fixture() -> NormalizedDataset:
    rows = (
        NormalizedRow(
            source_ordinal=1,
            source_fields=("A社", "2021"),
            values_by_role={"applicant": ("A社",), "year": ("2021",)},
        ),
        NormalizedRow(
            source_ordinal=2,
            source_fields=("B社", "2022"),
            values_by_role={"applicant": ("B社",), "year": ("2022",)},
        ),
        NormalizedRow(
            source_ordinal=3,
            source_fields=("A社", ""),
            values_by_role={"applicant": ("A社",), "year": ()},
        ),
    )
    receipt = NormalizationReceipt(
        normalization_contract_version="1.0.0",
        source_input_sha256="1" * 64,
        resolved_role_mapping_sha256="2" * 64,
        requested_roles=("applicant", "year"),
        multi_value_policy="all",
        classification_levels={},
        input_rows=3,
        output_rows=3,
        normalized_contributions=5,
        normalized_row_stream_sha256="3" * 64,
    )
    return NormalizedDataset(rows=rows, receipt=receipt)


def test_population_filters_are_anded_in_declaration_order() -> None:
    from patent_analysis.population import apply_population

    result = apply_population(
        _normalized_fixture(),
        {
            "filters": [
                {
                    "role": "year",
                    "match": "year_range",
                    "start": 2020,
                    "end": 2022,
                    "exclude": False,
                },
                {
                    "role": "applicant",
                    "match": "one_of",
                    "values": ["A社"],
                    "exclude": False,
                },
            ],
            "family_mode": "records",
        },
    )

    assert tuple(row.source_ordinal for row in result.rows) == (1,)
    assert result.receipt.input_rows == 3
    assert result.receipt.included_rows == 1
    assert result.receipt.filtered_rows == 2
    assert len(result.receipt.population_spec_sha256) == 64


def test_population_excludes_exact_values_and_keeps_unknown_years_outside_range() -> None:
    from patent_analysis.population import apply_population

    exact = apply_population(
        _normalized_fixture(),
        {
            "filters": [
                {
                    "role": "applicant",
                    "match": "exact",
                    "value": "A社",
                    "exclude": True,
                }
            ],
            "family_mode": "records",
        },
    )
    outside_years = apply_population(
        _normalized_fixture(),
        {
            "filters": [
                {
                    "role": "year",
                    "match": "year_range",
                    "start": 2020,
                    "end": 2022,
                    "exclude": True,
                }
            ],
            "family_mode": "records",
        },
    )

    assert tuple(row.source_ordinal for row in exact.rows) == (2,)
    assert tuple(row.source_ordinal for row in outside_years.rows) == (3,)


@pytest.mark.parametrize(
    "spec",
    [
        {
            "filters": [
                {"role": "applicant", "match": "contains", "value": "A"}
            ],
            "family_mode": "records",
        },
        {
            "filters": [
                {
                    "role": "applicant",
                    "match": "exact",
                    "value": "A社",
                    "regex": "A.*",
                }
            ],
            "family_mode": "records",
        },
        {
            "filters": [],
            "family_mode": "families",
        },
        {
            "filters": [],
            "family_mode": "records",
            "or": [],
        },
        {
            "filters": [],
            "family_mode": "records",
            "selection_sets": [],
        },
    ],
)
def test_population_rejects_open_or_future_contract_fields(
    spec: dict[str, object],
) -> None:
    from patent_analysis.population import PopulationError, apply_population

    with pytest.raises(PopulationError):
        apply_population(_normalized_fixture(), spec)


def test_population_schema_is_public_closed_and_matches_runtime_contract() -> None:
    from patent_analysis.api import get_public_schema

    schema = get_public_schema("population-v1.schema.json")
    assert schema["$id"] == "urn:patent-analysis:population:1.0.0"
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    valid = {
        "filters": [
            {
                "role": "year",
                "match": "year_range",
                "start": 2020,
                "end": 2022,
                "exclude": False,
            }
        ],
        "family_mode": "records",
    }
    assert not list(validator.iter_errors(valid))
    assert list(validator.iter_errors({**valid, "selection_sets": []}))
    assert list(validator.iter_errors({**valid, "family_mode": "families"}))


def test_population_result_rejects_mutable_direct_rows() -> None:
    from patent_analysis.population import (
        PopulationError,
        PopulationReceipt,
        PopulationResult,
    )

    row = _normalized_fixture().rows[0]
    receipt = PopulationReceipt(
        population_contract_version="1.0.0",
        normalization_row_stream_sha256="1" * 64,
        population_spec_sha256="2" * 64,
        family_mode="records",
        filter_count=0,
        input_rows=1,
        included_rows=1,
        filtered_rows=0,
    )
    with pytest.raises(PopulationError, match="result"):
        PopulationResult(
            rows=[row],  # type: ignore[arg-type]
            receipt=receipt,
        )
