"""Closed immutable receipt types for the v2 analysis pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


def _freeze_string_map(value: Mapping[str, str]) -> Mapping[str, str]:
    if not all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()):
        raise TypeError("receipt mappings must contain strings")
    return MappingProxyType(dict(value))


def _freeze_count_map(value: Mapping[str, int]) -> Mapping[str, int]:
    if not all(
        isinstance(key, str) and key and type(item) is int and item >= 0
        for key, item in value.items()
    ):
        raise TypeError("warning counts must be non-negative integer mappings")
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class DatasetResolutionReceipt:
    dataset_contract_version: str
    source_input_sha256: str
    resolution_profile: str | None
    column_catalog_sha256: str | None
    raw_header_sha256: str
    resolved_role_mapping_sha256: str
    input_rows: int
    input_columns: int
    warning_counts: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "warning_counts", _freeze_count_map(self.warning_counts))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_contract_version": self.dataset_contract_version,
            "source_input_sha256": self.source_input_sha256,
            "resolution_profile": self.resolution_profile,
            "column_catalog_sha256": self.column_catalog_sha256,
            "raw_header_sha256": self.raw_header_sha256,
            "resolved_role_mapping_sha256": self.resolved_role_mapping_sha256,
            "input_rows": self.input_rows,
            "input_columns": self.input_columns,
            "warning_counts": dict(self.warning_counts),
        }


@dataclass(frozen=True, slots=True)
class NormalizationReceipt:
    normalization_contract_version: str
    effective_profiles: tuple[str, ...]
    profile_versions: Mapping[str, str]
    profile_resource_sha256: Mapping[str, str]
    dictionary_sha256_by_profile: Mapping[str, str]
    normalized_row_stream_sha256: str
    output_rows: int
    changed_values: int
    unchanged_values: int
    unresolved_values: int
    warning_counts: Mapping[str, int]

    def __post_init__(self) -> None:
        if not isinstance(self.effective_profiles, tuple):
            raise TypeError("effective_profiles must be a tuple")
        for name in (
            "profile_versions",
            "profile_resource_sha256",
            "dictionary_sha256_by_profile",
        ):
            object.__setattr__(self, name, _freeze_string_map(getattr(self, name)))
        object.__setattr__(self, "warning_counts", _freeze_count_map(self.warning_counts))

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalization_contract_version": self.normalization_contract_version,
            "effective_profiles": list(self.effective_profiles),
            "profile_versions": dict(self.profile_versions),
            "profile_resource_sha256": dict(self.profile_resource_sha256),
            "dictionary_sha256_by_profile": dict(self.dictionary_sha256_by_profile),
            "normalized_row_stream_sha256": self.normalized_row_stream_sha256,
            "output_rows": self.output_rows,
            "changed_values": self.changed_values,
            "unchanged_values": self.unchanged_values,
            "unresolved_values": self.unresolved_values,
            "warning_counts": dict(self.warning_counts),
        }


@dataclass(frozen=True, slots=True)
class PopulationReceipt:
    input_rows: int
    input_sha256: str
    normalized_rows: int
    normalized_sha256: str
    post_filter_rows: int
    post_filter_sha256: str
    post_selection_rows: int
    post_selection_sha256: str
    post_family_rows: int
    post_family_sha256: str
    history_population_rows: int | None
    history_population_sha256: str | None
    display_population_rows: int | None
    display_population_sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_rows": self.input_rows,
            "input_sha256": self.input_sha256,
            "normalized_rows": self.normalized_rows,
            "normalized_sha256": self.normalized_sha256,
            "post_filter_rows": self.post_filter_rows,
            "post_filter_sha256": self.post_filter_sha256,
            "post_selection_rows": self.post_selection_rows,
            "post_selection_sha256": self.post_selection_sha256,
            "post_family_rows": self.post_family_rows,
            "post_family_sha256": self.post_family_sha256,
            "history_population_rows": self.history_population_rows,
            "history_population_sha256": self.history_population_sha256,
            "display_population_rows": self.display_population_rows,
            "display_population_sha256": self.display_population_sha256,
        }


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    input_sha256: str
    dataset_resolution_receipt: DatasetResolutionReceipt
    normalization_receipt: NormalizationReceipt
    normalization_spec_sha256: str
    normalization_result_sha256: str
    population_receipt: PopulationReceipt
    population_result_sha256: str
    analysis_spec_sha256: str
    result_sha256: str
    analysis_id: str
    algorithm_version: str
    package_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_sha256": self.input_sha256,
            "dataset_resolution_receipt": self.dataset_resolution_receipt.to_dict(),
            "normalization_receipt": self.normalization_receipt.to_dict(),
            "normalization_spec_sha256": self.normalization_spec_sha256,
            "normalization_result_sha256": self.normalization_result_sha256,
            "population_receipt": self.population_receipt.to_dict(),
            "population_result_sha256": self.population_result_sha256,
            "analysis_spec_sha256": self.analysis_spec_sha256,
            "result_sha256": self.result_sha256,
            "analysis_id": self.analysis_id,
            "algorithm_version": self.algorithm_version,
            "package_version": self.package_version,
        }


SENSITIVE_RECEIPT_FIELDS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "DatasetResolutionReceipt": frozenset(
            {
                "source_input_sha256",
                "column_catalog_sha256",
                "raw_header_sha256",
                "resolved_role_mapping_sha256",
            }
        ),
        "NormalizationReceipt": frozenset(
            {
                "profile_resource_sha256",
                "dictionary_sha256_by_profile",
                "normalized_row_stream_sha256",
            }
        ),
        "PopulationReceipt": frozenset(
            {
                "input_sha256",
                "normalized_sha256",
                "post_filter_sha256",
                "post_selection_sha256",
                "post_family_sha256",
                "history_population_sha256",
                "display_population_sha256",
            }
        ),
        "ExecutionReceipt": frozenset(
            {
                "input_sha256",
                "dataset_resolution_receipt",
                "normalization_receipt",
                "normalization_spec_sha256",
                "normalization_result_sha256",
                "population_receipt",
                "population_result_sha256",
                "analysis_spec_sha256",
                "result_sha256",
            }
        ),
    }
)
