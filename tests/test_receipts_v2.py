from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from patent_analysis.receipts_v2 import (
    SENSITIVE_RECEIPT_FIELDS,
    DatasetResolutionReceipt,
    ExecutionReceipt,
    NormalizationReceipt,
    PopulationReceipt,
)


def _receipts() -> tuple[
    DatasetResolutionReceipt, NormalizationReceipt, PopulationReceipt, ExecutionReceipt
]:
    resolution = DatasetResolutionReceipt(
        dataset_contract_version="2.0.0",
        source_input_sha256="1" * 64,
        resolution_profile="column-alias.v2",
        column_catalog_sha256="2" * 64,
        raw_header_sha256="3" * 64,
        resolved_role_mapping_sha256="4" * 64,
        input_rows=10,
        input_columns=3,
        warning_counts={"staged_alias": 1},
    )
    normalization = NormalizationReceipt(
        normalization_contract_version="2.0.0",
        effective_profiles=("year-workbench.v1",),
        profile_versions={"year-workbench.v1": "1.0.0"},
        profile_resource_sha256={"year-workbench.v1": "5" * 64},
        dictionary_sha256_by_profile={},
        normalized_row_stream_sha256="6" * 64,
        output_rows=10,
        changed_values=2,
        unchanged_values=28,
        unresolved_values=0,
        warning_counts={},
    )
    population = PopulationReceipt(
        input_rows=10,
        input_sha256="7" * 64,
        normalized_rows=10,
        normalized_sha256="8" * 64,
        post_filter_rows=9,
        post_filter_sha256="9" * 64,
        post_selection_rows=8,
        post_selection_sha256="a" * 64,
        post_family_rows=7,
        post_family_sha256="b" * 64,
        history_population_rows=None,
        history_population_sha256=None,
        display_population_rows=None,
        display_population_sha256=None,
    )
    execution = ExecutionReceipt(
        input_sha256="1" * 64,
        dataset_resolution_receipt=resolution,
        normalization_receipt=normalization,
        normalization_spec_sha256="c" * 64,
        normalization_result_sha256="d" * 64,
        population_receipt=population,
        population_result_sha256="e" * 64,
        analysis_spec_sha256="f" * 64,
        result_sha256="0" * 64,
        analysis_id="timeline.v1",
        algorithm_version="1.0.0",
        package_version="0.2.0",
    )
    return resolution, normalization, population, execution


def test_v2_receipts_are_frozen_and_have_exact_json_fields() -> None:
    resolution, normalization, population, execution = _receipts()

    for receipt in (resolution, normalization, population, execution):
        json.dumps(receipt.to_dict())

    assert set(resolution.to_dict()) == {
        "dataset_contract_version",
        "source_input_sha256",
        "resolution_profile",
        "column_catalog_sha256",
        "raw_header_sha256",
        "resolved_role_mapping_sha256",
        "input_rows",
        "input_columns",
        "warning_counts",
    }
    assert set(normalization.to_dict()) == {
        "normalization_contract_version",
        "effective_profiles",
        "profile_versions",
        "profile_resource_sha256",
        "dictionary_sha256_by_profile",
        "normalized_row_stream_sha256",
        "output_rows",
        "changed_values",
        "unchanged_values",
        "unresolved_values",
        "warning_counts",
    }
    assert set(population.to_dict()) == {
        "input_rows",
        "input_sha256",
        "normalized_rows",
        "normalized_sha256",
        "post_filter_rows",
        "post_filter_sha256",
        "post_selection_rows",
        "post_selection_sha256",
        "post_family_rows",
        "post_family_sha256",
        "history_population_rows",
        "history_population_sha256",
        "display_population_rows",
        "display_population_sha256",
    }
    assert set(execution.to_dict()) == {
        "input_sha256",
        "dataset_resolution_receipt",
        "normalization_receipt",
        "normalization_spec_sha256",
        "normalization_result_sha256",
        "population_receipt",
        "population_result_sha256",
        "analysis_spec_sha256",
        "result_sha256",
        "analysis_id",
        "algorithm_version",
        "package_version",
    }

    with pytest.raises(FrozenInstanceError):
        execution.analysis_id = "mutated"  # type: ignore[misc]
    with pytest.raises(TypeError):
        resolution.warning_counts["mutated"] = 1  # type: ignore[index]


def test_v2_receipt_hashes_are_identifiable_for_mcp_omission() -> None:
    assert SENSITIVE_RECEIPT_FIELDS["DatasetResolutionReceipt"] == frozenset(
        {
            "source_input_sha256",
            "column_catalog_sha256",
            "raw_header_sha256",
            "resolved_role_mapping_sha256",
        }
    )
    assert "dictionary_sha256_by_profile" in SENSITIVE_RECEIPT_FIELDS["NormalizationReceipt"]
    assert "post_family_sha256" in SENSITIVE_RECEIPT_FIELDS["PopulationReceipt"]
    assert "analysis_spec_sha256" in SENSITIVE_RECEIPT_FIELDS["ExecutionReceipt"]
