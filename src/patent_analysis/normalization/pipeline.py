"""Immutable canonical normalized row pipeline."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from patent_analysis.canonical_v2 import canonical_json_bytes, canonical_sha256
from patent_analysis.column_resolution import RoleResolution
from patent_analysis.dataset_v2 import DatasetV2
from patent_analysis.normalization.applicant import applicant_key, normalize_applicant
from patent_analysis.normalization.classification import (
    CLASSIFICATION_LEVELS,
    derive_classification_values,
)
from patent_analysis.normalization.multi_value import (
    is_classification_role,
    split_patent_values,
    stable_dedupe,
)
from patent_analysis.normalization.year import extract_year

NORMALIZATION_CONTRACT_VERSION = "1.0.0"
MAX_NORMALIZED_CONTRIBUTIONS = 2_000_000
MAX_NORMALIZATION_ROLES = 64
MultiValuePolicy = Literal["all", "first"]
_APPLICANT_ROLES = frozenset({"applicant", "assignee", "owner"})
_YEAR_ROLES = frozenset(
    {
        "date",
        "filing_date",
        "priority_date",
        "publication_date",
        "registration_date",
        "year",
    }
)


class NormalizationError(ValueError):
    """Raised when canonical normalization cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class NormalizationConfig:
    """Closed source-independent normalization choices."""

    roles: tuple[str, ...]
    multi_value_policy: MultiValuePolicy = "all"
    classification_levels: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.roles, tuple)
            or not self.roles
            or len(self.roles) > MAX_NORMALIZATION_ROLES
            or len(set(self.roles)) != len(self.roles)
            or not all(
                isinstance(role, str) and 0 < len(role) <= 64 for role in self.roles
            )
            or self.multi_value_policy not in {"all", "first"}
            or not isinstance(self.classification_levels, Mapping)
        ):
            raise NormalizationError("normalization config is invalid")
        levels = dict(self.classification_levels)
        if len(levels) > MAX_NORMALIZATION_ROLES or any(
            not isinstance(role, str)
            or role not in self.roles
            or level not in CLASSIFICATION_LEVELS
            for role, level in levels.items()
        ):
            raise NormalizationError("classification level is invalid")
        object.__setattr__(self, "classification_levels", MappingProxyType(levels))

    def to_dict(self) -> dict[str, object]:
        return {
            "roles": list(self.roles),
            "multi_value_policy": self.multi_value_policy,
            "classification_levels": dict(self.classification_levels),
        }


@dataclass(frozen=True, slots=True)
class NormalizedRow:
    source_ordinal: int
    source_fields: tuple[str, ...]
    values_by_role: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        copied = dict(self.values_by_role)
        if (
            type(self.source_ordinal) is not int
            or self.source_ordinal < 1
            or not isinstance(self.source_fields, tuple)
            or not all(isinstance(value, str) for value in self.source_fields)
            or not all(
                isinstance(role, str)
                and role
                and isinstance(values, tuple)
                and all(isinstance(value, str) for value in values)
                for role, values in copied.items()
            )
        ):
            raise NormalizationError("normalized row is invalid")
        object.__setattr__(self, "values_by_role", MappingProxyType(copied))

    def values(self, role: str) -> tuple[str, ...]:
        return self.values_by_role.get(role, ())

    def to_dict(self) -> dict[str, object]:
        return {
            "source_ordinal": self.source_ordinal,
            "source_fields": list(self.source_fields),
            "values_by_role": {
                role: list(values) for role, values in self.values_by_role.items()
            },
        }


@dataclass(frozen=True, slots=True)
class NormalizationReceipt:
    normalization_contract_version: str
    source_input_sha256: str
    resolved_role_mapping_sha256: str
    requested_roles: tuple[str, ...]
    multi_value_policy: str
    classification_levels: Mapping[str, str]
    input_rows: int
    output_rows: int
    normalized_contributions: int
    normalized_row_stream_sha256: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.requested_roles, tuple)
            or not self.requested_roles
            or len(self.requested_roles) > MAX_NORMALIZATION_ROLES
            or len(set(self.requested_roles)) != len(self.requested_roles)
            or not all(
                isinstance(role, str) and 0 < len(role) <= 64
                for role in self.requested_roles
            )
            or self.multi_value_policy not in {"all", "first"}
            or not isinstance(self.classification_levels, Mapping)
        ):
            raise NormalizationError("normalization receipt is invalid")
        levels = dict(self.classification_levels)
        if len(levels) > MAX_NORMALIZATION_ROLES or any(
            not isinstance(role, str)
            or role not in self.requested_roles
            or level not in CLASSIFICATION_LEVELS
            for role, level in levels.items()
        ):
            raise NormalizationError("normalization receipt is invalid")
        object.__setattr__(self, "classification_levels", MappingProxyType(levels))

    def to_dict(self) -> dict[str, object]:
        return {
            "normalization_contract_version": self.normalization_contract_version,
            "source_input_sha256": self.source_input_sha256,
            "resolved_role_mapping_sha256": self.resolved_role_mapping_sha256,
            "requested_roles": list(self.requested_roles),
            "multi_value_policy": self.multi_value_policy,
            "classification_levels": dict(self.classification_levels),
            "input_rows": self.input_rows,
            "output_rows": self.output_rows,
            "normalized_contributions": self.normalized_contributions,
            "normalized_row_stream_sha256": self.normalized_row_stream_sha256,
        }


@dataclass(frozen=True, slots=True)
class NormalizedDataset:
    rows: tuple[NormalizedRow, ...]
    receipt: NormalizationReceipt

    def __post_init__(self) -> None:
        if (
            not isinstance(self.rows, tuple)
            or not all(isinstance(row, NormalizedRow) for row in self.rows)
            or not isinstance(self.receipt, NormalizationReceipt)
        ):
            raise NormalizationError("normalized dataset is invalid")

    def to_dict(self) -> dict[str, object]:
        return {
            "rows": [row.to_dict() for row in self.rows],
            "receipt": self.receipt.to_dict(),
        }


def _row_fields(row: object) -> tuple[str, ...]:
    if isinstance(row, tuple):
        return tuple(str(value) for value in row)
    for attribute in ("values", "fields", "source_fields"):
        value = getattr(row, attribute, None)
        if isinstance(value, tuple):
            return tuple(str(item) for item in value)
        if isinstance(value, list):
            return tuple(str(item) for item in value)
    raise NormalizationError("dataset row is invalid")


def _source_ordinal(row: object, fallback: int) -> int:
    value = getattr(row, "source_ordinal", fallback)
    return value if type(value) is int and value >= 1 else fallback


def _validate_binding(dataset: DatasetV2, resolution: RoleResolution) -> None:
    manifest = dataset.manifest
    receipt = resolution.receipt
    try:
        valid = (
            receipt.dataset_contract_version == manifest.dataset_contract_version
            and receipt.source_input_sha256 == manifest.source_input_sha256
            and receipt.input_rows == manifest.input_rows
            and receipt.input_columns == manifest.input_columns
            and receipt.raw_header_sha256 == canonical_sha256(list(manifest.raw_header))
        )
    except AttributeError:
        valid = False
    if not valid:
        raise NormalizationError("dataset binding does not match role resolution")


def _role_key(role: str) -> str:
    return role.strip().casefold().replace("-", "_").replace(" ", "_")


def _normalize_values(
    role: str,
    raw: str,
    *,
    config: NormalizationConfig,
) -> tuple[str, ...]:
    level = config.classification_levels.get(role, "full")
    classification = is_classification_role(role) or role in config.classification_levels
    split_role = "classification" if classification else role
    try:
        values = split_patent_values(raw, role=split_role)
    except ValueError:
        raise NormalizationError("normalized value limit exceeded") from None

    role_key = _role_key(role)
    if role_key in _APPLICANT_ROLES:
        normalized = tuple(normalize_applicant(value) for value in values)
        keys = tuple(applicant_key(value) for value in normalized)
        values = stable_dedupe(normalized, keys=keys)
    elif classification:
        values = derive_classification_values(values, level=level)
    elif role_key in _YEAR_ROLES:
        values = stable_dedupe(extract_year(value) for value in values)

    if config.multi_value_policy == "first":
        return values[:1]
    return values


def _row_stream_sha256(rows: tuple[NormalizedRow, ...]) -> str:
    digest = hashlib.sha256(b"patent-analysis-normalized-row-stream-v1\0")
    for row in rows:
        encoded = canonical_json_bytes(row.to_dict())
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
    return digest.hexdigest()


def normalize_dataset(
    dataset: DatasetV2,
    resolution: RoleResolution,
    config: NormalizationConfig,
) -> NormalizedDataset:
    """Normalize selected semantic roles without source-product runtime modes."""

    if not isinstance(config, NormalizationConfig):
        raise NormalizationError("normalization config is invalid")
    _validate_binding(dataset, resolution)
    for role in config.roles:
        if role not in resolution.mapping:
            raise NormalizationError("required normalized role is unresolved")

    normalized_rows: list[NormalizedRow] = []
    contributions = 0
    for fallback, row in enumerate(dataset.rows, start=1):
        fields = _row_fields(row)
        values_by_role: dict[str, tuple[str, ...]] = {}
        for role in config.roles:
            binding = resolution.mapping[role]
            ordinal = binding.source_header_ordinal
            if type(ordinal) is not int or ordinal < 0 or ordinal >= len(fields):
                raise NormalizationError("resolved role ordinal is invalid")
            if dataset.manifest.raw_header[ordinal] != binding.raw_header:
                raise NormalizationError("dataset binding does not match role resolution")
            values = _normalize_values(role, fields[ordinal], config=config)
            contributions += len(values)
            if contributions > MAX_NORMALIZED_CONTRIBUTIONS:
                raise NormalizationError("normalized contribution limit exceeded")
            values_by_role[role] = values
        normalized_rows.append(
            NormalizedRow(
                source_ordinal=_source_ordinal(row, fallback),
                source_fields=fields,
                values_by_role=values_by_role,
            )
        )

    rows = tuple(normalized_rows)
    receipt = NormalizationReceipt(
        normalization_contract_version=NORMALIZATION_CONTRACT_VERSION,
        source_input_sha256=dataset.manifest.source_input_sha256,
        resolved_role_mapping_sha256=resolution.receipt.resolved_role_mapping_sha256,
        requested_roles=config.roles,
        multi_value_policy=config.multi_value_policy,
        classification_levels=config.classification_levels,
        input_rows=dataset.manifest.input_rows,
        output_rows=len(rows),
        normalized_contributions=contributions,
        normalized_row_stream_sha256=_row_stream_sha256(rows),
    )
    return NormalizedDataset(rows=rows, receipt=receipt)
