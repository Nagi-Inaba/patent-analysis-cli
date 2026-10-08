"""Closed, ordered population filtering over canonical normalized records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from patent_analysis.canonical_v2 import canonical_sha256
from patent_analysis.column_resolution import trim_ecmascript_whitespace
from patent_analysis.normalization import NormalizedDataset, NormalizedRow
from patent_analysis.normalization.family import FamilySelectionReceipt, select_family_population

POPULATION_CONTRACT_VERSION = "1.0.0"
MAX_POPULATION_FILTERS = 64
MAX_ONE_OF_VALUES = 1000
_ALLOWED_POPULATION_FIELDS = frozenset({"filters", "family_mode"})
_ALLOWED_COMMON_FILTER_FIELDS = frozenset({"role", "match", "exclude"})


class PopulationError(ValueError):
    """Raised when a population request is open or invalid."""


@dataclass(frozen=True, slots=True)
class PopulationReceipt:
    population_contract_version: str
    normalization_row_stream_sha256: str
    population_spec_sha256: str
    family_mode: str
    filter_count: int
    input_rows: int
    included_rows: int
    filtered_rows: int
    family_selection: FamilySelectionReceipt | None = None

    def analysis_metadata(self) -> dict[str, object]:
        """Attach selection provenance only to opt-in family results."""
        return (
            {}
            if self.family_selection is None
            else {
                "family_selection": self.family_selection.to_dict(),
            }
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "population_contract_version": self.population_contract_version,
            "normalization_row_stream_sha256": self.normalization_row_stream_sha256,
            "population_spec_sha256": self.population_spec_sha256,
            "family_mode": self.family_mode,
            "filter_count": self.filter_count,
            "input_rows": self.input_rows,
            "included_rows": self.included_rows,
            "filtered_rows": self.filtered_rows,
            **self.analysis_metadata(),
        }


@dataclass(frozen=True, slots=True)
class PopulationResult:
    rows: tuple[NormalizedRow, ...]
    receipt: PopulationReceipt

    def __post_init__(self) -> None:
        if (
            not isinstance(self.rows, tuple)
            or not all(isinstance(row, NormalizedRow) for row in self.rows)
            or not isinstance(self.receipt, PopulationReceipt)
        ):
            raise PopulationError("population result is invalid")

    def to_dict(self) -> dict[str, object]:
        return {
            "source_ordinals": [row.source_ordinal for row in self.rows],
            "receipt": self.receipt.to_dict(),
        }


def _validate_filter(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PopulationError("population filter is invalid")
    role = value.get("role")
    match = value.get("match")
    exclude = value.get("exclude", False)
    if not isinstance(role, str) or not role or len(role) > 64 or type(exclude) is not bool:
        raise PopulationError("population filter is invalid")

    if match == "selection":
        date_fields = {"date_role", "start", "end"}
        has_date = bool(set(value) & date_fields)
        required = {"role", "match", "values"} | (date_fields if has_date else set())
        if not required <= set(value) <= required | {"exclude"}:
            raise PopulationError("population selection is invalid")
        result = _validate_filter({
            "role": role, "match": "one_of", "values": value["values"], "exclude": exclude,
        })
        result["match"] = "selection"
        if has_date:
            date = _validate_filter({
                "role": value["date_role"], "match": "year_range",
                "start": value["start"], "end": value["end"],
            })
            result.update(date_role=date["role"], start=date["start"], end=date["end"])
        return result

    if match == "exact":
        if set(value) != (_ALLOWED_COMMON_FILTER_FIELDS | {"value"}) and set(value) != (
            {"role", "match", "value"}
        ):
            raise PopulationError("population filter is invalid")
        target = value.get("value")
        if not isinstance(target, str) or not target:
            raise PopulationError("population filter is invalid")
        return {
            "role": role,
            "match": match,
            "value": target,
            "exclude": exclude,
        }

    if match == "one_of":
        if set(value) != (_ALLOWED_COMMON_FILTER_FIELDS | {"values"}) and set(value) != (
            {"role", "match", "values"}
        ):
            raise PopulationError("population filter is invalid")
        targets = value.get("values")
        if (
            not isinstance(targets, list)
            or not targets
            or len(targets) > MAX_ONE_OF_VALUES
            or not all(isinstance(item, str) and item for item in targets)
            or len(set(targets)) != len(targets)
        ):
            raise PopulationError("population filter is invalid")
        return {
            "role": role,
            "match": match,
            "values": list(targets),
            "exclude": exclude,
        }

    if match == "year_range":
        allowed = _ALLOWED_COMMON_FILTER_FIELDS | {"start", "end"}
        required = {"role", "match", "start", "end"}
        if set(value) != allowed and set(value) != required:
            raise PopulationError("population filter is invalid")
        start = value.get("start")
        end = value.get("end")
        if type(start) is not int or type(end) is not int or not (1800 <= start <= end <= 2199):
            raise PopulationError("population filter is invalid")
        return {
            "role": role,
            "match": match,
            "start": start,
            "end": end,
            "exclude": exclude,
        }

    raise PopulationError("unsupported filter match")


def family_roles(population_spec: Mapping[str, object]) -> tuple[str, ...]:
    """Roles resolved to original scalar columns, not normalized token values."""
    if population_spec.get("family_mode") != "earliest":
        return ()
    roles = (population_spec.get("family_role"),)
    if "date_role" in population_spec:
        roles += (population_spec["date_role"],)
    if any(
        not isinstance(role, str) or not role or role != role.strip() or len(role) > 64
        for role in roles
    ):
        raise PopulationError("family selection roles are invalid")
    return tuple(dict.fromkeys(roles))


def _validate_population_spec(
    population_spec: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(population_spec, Mapping):
        raise PopulationError("population specification is invalid")
    mode = population_spec.get("family_mode")
    required = _ALLOWED_POPULATION_FIELDS
    allowed = required
    if mode == "earliest":
        required = required | {"family_role"}
        allowed = required | {"date_role"}
        family_roles(population_spec)
    elif mode != "records":
        raise PopulationError("population specification is invalid")
    if not required <= set(population_spec) <= allowed:
        raise PopulationError("population specification is invalid")
    filters = population_spec.get("filters")
    if not isinstance(filters, list) or len(filters) > MAX_POPULATION_FILTERS:
        raise PopulationError("population filter limit exceeded")
    return {**population_spec, "filters": [_validate_filter(value) for value in filters]}


def _matches(row: NormalizedRow, spec: Mapping[str, Any]) -> bool:
    values = row.values(str(spec["role"]))
    match = spec["match"]
    if match == "exact":
        return str(spec["value"]) in values
    if match in {"one_of", "selection"}:
        targets = frozenset(str(value) for value in spec["values"])
        matched = any(value in targets for value in values)
        if match == "one_of" or "date_role" not in spec:
            return matched
        if not matched:
            return False
        values = row.values(str(spec["date_role"]))
    start = int(spec["start"])
    end = int(spec["end"])
    return any(
        len(value) == 4 and value.isdecimal() and start <= int(value) <= end for value in values
    )


def apply_population(
    dataset: NormalizedDataset,
    population_spec: Mapping[str, object],
    *,
    source_role_ordinals: Mapping[str, int] | None = None,
) -> PopulationResult:
    """Apply AND filters, then optional family selection, before analysis eligibility."""

    if not isinstance(dataset, NormalizedDataset):
        raise PopulationError("normalized dataset is invalid")
    validated = _validate_population_spec(population_spec)
    filters = validated["filters"]
    assert isinstance(filters, list)
    available_roles = frozenset(dataset.receipt.requested_roles)
    if any(spec["role"] not in available_roles
           or ("date_role" in spec and spec["date_role"] not in available_roles)
           for spec in filters):
        raise PopulationError("population filter role is unavailable")

    selection_roles = family_roles(validated)
    if selection_roles and (
        source_role_ordinals is None
        or any(role not in source_role_ordinals for role in selection_roles)
    ):
        raise PopulationError("family selection columns are unresolved")

    included: list[NormalizedRow] = []
    for row in dataset.rows:
        keep = True
        for spec in filters:
            matched = _matches(row, spec)
            if bool(spec["exclude"]):
                matched = not matched
            if not matched:
                keep = False
                break
        if keep:
            included.append(row)

    rows = tuple(included)
    selection = None
    if selection_roles:
        assert source_role_ordinals is not None
        family_role = str(validated["family_role"])
        date_role = validated.get("date_role")
        family_column = source_role_ordinals[family_role]
        date_column = None if date_role is None else source_role_ordinals[str(date_role)]
        try:
            rows = select_family_population(
                rows,
                family_column=family_column,
                date_column=date_column,
            )
        except ValueError:
            raise PopulationError("family representative selection is invalid") from None
        selection = FamilySelectionReceipt(
            family_role=family_role,
            date_role=None if date_role is None else str(date_role),
            matched_rows=len(included),
            representative_rows=len(rows),
            collapsed_rows=len(included) - len(rows),
            unidentified_rows=sum(
                not trim_ecmascript_whitespace(row.source_fields[family_column]) for row in rows
            ),
        )
    receipt = PopulationReceipt(
        population_contract_version=POPULATION_CONTRACT_VERSION,
        normalization_row_stream_sha256=dataset.receipt.normalized_row_stream_sha256,
        population_spec_sha256=canonical_sha256(validated),
        family_mode=str(validated["family_mode"]),
        filter_count=len(filters),
        input_rows=len(dataset.rows),
        included_rows=len(rows),
        filtered_rows=len(dataset.rows) - len(included),
        family_selection=selection,
    )
    return PopulationResult(rows=rows, receipt=receipt)
