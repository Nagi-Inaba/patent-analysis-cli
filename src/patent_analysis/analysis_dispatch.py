"""Single byte-level version dispatcher for v1 and registered v2 analysis specs."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Any, Literal

from patent_analysis.analyses._advanced_registration import (
    MODULE_BY_ID,
)
from patent_analysis.analyses._advanced_registration import (
    validate_parameters as validate_advanced_parameters,
)
from patent_analysis.analyses._inventor_registration import MODULE_BY_ID as INVENTOR_MODULE_BY_ID
from patent_analysis.analyses.composition import required_roles as composition_required_roles
from patent_analysis.analyses.concentration import required_roles as concentration_required_roles
from patent_analysis.analyses.growth import required_roles as growth_required_roles
from patent_analysis.analyses.lifecycle import required_roles as lifecycle_required_roles
from patent_analysis.analyses.matrix import _validate_parameters as validate_matrix_parameters
from patent_analysis.analyses.ranking import required_roles as ranking_required_roles
from patent_analysis.analyses.timeline import required_roles as timeline_required_roles
from patent_analysis.analysis_budgets import (
    MAX_ANALYSIS_SPEC_BYTES,
    MAX_ANALYSIS_SPEC_DEPTH,
    MAX_ANALYSIS_SPEC_NODES,
    MAX_ANALYSIS_SPEC_STRING_CODE_POINTS,
)
from patent_analysis.analysis_contracts import (
    ANALYSIS_CONTRACT_VERSION,
    AnalysisContractError,
    StrictDraft202012Validator,
    validate_analysis_spec,
)
from patent_analysis.analysis_inputs import records_population_spec, stable_roles
from patent_analysis.analysis_registry import (
    AnalysisDefinition,
    RegistryError,
    get_analysis_definition,
)
from patent_analysis.canonical_v2 import CanonicalizationError, parse_strict_json_bytes
from patent_analysis.normalization import MAX_NORMALIZATION_ROLES
from patent_analysis.population import _validate_population_spec, family_roles
from patent_analysis.v2_contracts import V2_ANALYSIS_CONTRACT_VERSION, validate_analysis_spec_v2


@dataclass(frozen=True, slots=True)
class ValidatedV1Spec:
    spec: dict[str, Any]
    contract_version: Literal["1.0.0"] = field(default="1.0.0", init=False)

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self.spec)


@dataclass(frozen=True, slots=True)
class ValidatedV2Spec:
    spec: dict[str, Any]
    definition: AnalysisDefinition
    contract_version: Literal["2.0.0"] = field(default="2.0.0", init=False)

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self.spec)


def _raise_invalid(message: str) -> None:
    raise AnalysisContractError(message, code="analysis.invalid", details={}) from None


def _reject_legacy_constant(_value: str) -> None:
    raise ValueError("non-standard JSON constant")


def _parse_legacy_json_bytes(raw: bytes) -> object:
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return json.loads(raw.decode("utf-8"), parse_constant=_reject_legacy_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        _raise_invalid("analysis spec is not legacy JSON")


def _validate_spec_size_and_complexity(raw: bytes, value: object) -> None:
    nodes = 0
    string_code_points = 0
    stack: list[tuple[object, int]] = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_ANALYSIS_SPEC_NODES or depth > MAX_ANALYSIS_SPEC_DEPTH:
            _raise_invalid("analysis spec exceeds structural limits")
        if isinstance(item, str):
            string_code_points += len(item)
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
        elif isinstance(item, dict):
            for key, child in item.items():
                nodes += 1
                string_code_points += len(key)
                stack.append((child, depth + 1))
        if nodes > MAX_ANALYSIS_SPEC_NODES:
            _raise_invalid("analysis spec exceeds structural limits")
        if string_code_points > MAX_ANALYSIS_SPEC_STRING_CODE_POINTS:
            _raise_invalid("analysis spec exceeds the decoded string limit")


def _load_definition_schema(definition: AnalysisDefinition) -> dict[str, Any]:
    schema_path = definition.spec_schema.split("/")
    try:
        resource = files("patent_analysis")
        for part in schema_path:
            resource = resource.joinpath(part)
        return json.loads(resource.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
        _raise_invalid("registered analysis schema is unavailable")


def _validate_definition_specific_spec(
    spec: dict[str, Any], definition: AnalysisDefinition
) -> dict[str, Any]:
    schema = _load_definition_schema(definition)
    errors = sorted(
        StrictDraft202012Validator(schema).iter_errors(spec),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        _raise_invalid("analysis spec violates the registered definition schema")
    if definition.analysis_id == "growth.v1":
        try:
            growth_required_roles(spec["parameters"])
        except ValueError as error:
            _raise_invalid(str(error))
    try:
        validate_advanced_parameters(definition.analysis_id, spec["parameters"])
    except ValueError as error:
        _raise_invalid(str(error))
    validators = {
        "ranking.v2": ranking_required_roles,
        "matrix.v1": validate_matrix_parameters,
        "timeline.v1": timeline_required_roles,
        "composition.v1": composition_required_roles,
        "concentration.v1": concentration_required_roles,
        "lifecycle.v1": lifecycle_required_roles,
    }
    try:
        if validator := validators.get(definition.analysis_id):
            validated_parameters = validator(spec["parameters"])
            roles = (
                (validated_parameters["x_role"], validated_parameters["y_role"])
                if definition.analysis_id == "matrix.v1" else validated_parameters
            )
        elif definition.analysis_id == "growth.v1":
            roles = growth_required_roles(spec["parameters"])
        elif module := MODULE_BY_ID.get(definition.analysis_id):
            roles = module.required_roles(spec["parameters"])
        elif module := INVENTOR_MODULE_BY_ID.get(definition.analysis_id):
            roles = module.required_roles(spec["parameters"])
        else:
            roles = definition.required_roles
        population, filter_roles = records_population_spec(spec["population"])
        _validate_population_spec(population)
        if definition.analysis_id in INVENTOR_MODULE_BY_ID:
            from patent_analysis.analyses._inventor_common import executable_roles
            roles = executable_roles(spec, roles, filter_roles)
            filter_roles = ()
        normalized_roles = stable_roles((*roles, *filter_roles))
        if len(normalized_roles) > MAX_NORMALIZATION_ROLES:
            raise ValueError("analysis and selection roles exceed the normalization limit")
        required = stable_roles((*normalized_roles, *family_roles(population)))
        resolution = spec["resolution"]
        profile = resolution.get("profile")
        if profile is not None and profile not in definition.allowed_resolution_profiles:
            raise ValueError("resolution profile is unavailable")
        if resolution.get("profile") is None and any(
            role not in resolution.get("bindings", {}) for role in required
        ):
            raise ValueError("required role has no binding or resolution profile")
        bindings = resolution.get("bindings", {})
        columns = [bindings[role] for role in required if role in bindings]
        if len(columns) != len(set(columns)):
            raise ValueError("required roles must bind distinct columns")
    except ValueError:
        _raise_invalid("analysis parameters or population conditions are not executable")
    return deepcopy(spec)


def dispatch_and_validate_spec_bytes(raw: bytes) -> ValidatedV1Spec | ValidatedV2Spec:
    """Preserve absent-version legacy parsing and strictly reparse explicit v2 bytes."""

    if type(raw) is not bytes:
        _raise_invalid("analysis spec input must be bytes")
    if len(raw) > MAX_ANALYSIS_SPEC_BYTES:
        _raise_invalid("analysis spec exceeds the byte limit")
    legacy_value = _parse_legacy_json_bytes(raw)
    if not isinstance(legacy_value, dict):
        _raise_invalid("analysis spec must be an object")
    if "analysis_contract_version" not in legacy_value:
        return ValidatedV1Spec(validate_analysis_spec(legacy_value))

    try:
        value = parse_strict_json_bytes(raw, allow_bom=True)
    except CanonicalizationError:
        _raise_invalid("analysis spec is not strict JSON")
    _validate_spec_size_and_complexity(raw, value)
    if not isinstance(value, dict):
        _raise_invalid("analysis spec must be an object")

    version = value.get("analysis_contract_version")
    if version == ANALYSIS_CONTRACT_VERSION:
        _raise_invalid("explicit v1 analysis contract version is not legacy v1")
    if version != V2_ANALYSIS_CONTRACT_VERSION:
        _raise_invalid("unsupported analysis contract version")

    common_spec = validate_analysis_spec_v2(value)
    analysis_id = common_spec["analysis_id"]
    try:
        definition = get_analysis_definition(analysis_id)
    except RegistryError:
        _raise_invalid("unknown analysis_id for analysis contract v2")
    validated = _validate_definition_specific_spec(common_spec, definition)
    return ValidatedV2Spec(validated, definition)
