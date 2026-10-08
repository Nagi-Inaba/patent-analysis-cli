"""Shared bounded input preparation for registered native v2 analyses."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from patent_analysis.column_resolution import resolve_roles
from patent_analysis.dataset_v2 import DatasetV2, read_dataset_v2
from patent_analysis.normalization import NormalizationConfig, normalize_dataset
from patent_analysis.population import PopulationResult, apply_population, family_roles


def stable_roles(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError("role must be a string")
        text = value.strip()
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return tuple(output)


def records_population_spec(value: object) -> tuple[dict[str, object], tuple[str, ...]]:
    """Translate a public records/earliest population contract into core form."""

    if not isinstance(value, Mapping):
        raise ValueError("population must be an object")
    mode = value.get("family_mode")
    if mode not in ("records", "earliest"):
        raise ValueError("analysis supports records or earliest population")
    selection_roles = family_roles(value)
    selection_sets = value.get("selection_sets")
    if not isinstance(selection_sets, list):
        raise ValueError("selection sets must be an array")
    filters = value.get("filters")
    if not isinstance(filters, list):
        raise ValueError("population filters must be an array")

    converted: list[dict[str, object]] = []
    roles: list[str] = []
    for item in filters:
        if not isinstance(item, Mapping):
            raise ValueError("population filter is invalid")
        role = item.get("role")
        effect = item.get("effect")
        match = item.get("match")
        if (
            not isinstance(role, str) or not role or role != role.strip()
            or effect not in {"include", "exclude"}
        ):
            raise ValueError("population filter is invalid")
        roles.append(role)
        base: dict[str, object] = {
            "role": role,
            "match": match,
            "exclude": effect == "exclude",
        }
        if match == "exact":
            base["value"] = item.get("value")
        elif match == "one_of":
            base["values"] = item.get("values")
        elif match == "year":
            base.update(match="year_range", start=item.get("value"), end=item.get("value"))
        elif match in {"year_range", "outside_year_range"}:
            base["match"] = "year_range"
            base["start"] = item.get("start_year")
            base["end"] = item.get("end_year")
            if match == "outside_year_range":
                base["exclude"] = not base["exclude"]
        else:
            raise ValueError("population filter match is unavailable")
        converted.append(base)

    for item in selection_sets:
        if not isinstance(item, Mapping):
            raise ValueError("selection set is invalid")
        role = item.get("dimension_role")
        if (not isinstance(role, str) or not role or role != role.strip()
                or item.get("mode") not in {"include", "exclude"}):
            raise ValueError("selection set is invalid")
        roles.append(role)
        selection: dict[str, object] = {
            "role": role, "match": "selection", "values": item.get("values"),
            "exclude": item["mode"] == "exclude",
        }
        if any(key in item for key in ("source_date_role", "start_year", "end_year")):
            date_role = item.get("source_date_role")
            if (not isinstance(date_role, str) or not date_role
                    or date_role != date_role.strip()):
                raise ValueError("selection date role is invalid")
            roles.append(date_role)
            selection.update(date_role=date_role, start=item.get("start_year"),
                             end=item.get("end_year"))
        converted.append(selection)

    converted_spec: dict[str, object] = {"filters": converted, "family_mode": mode}
    if selection_roles:
        converted_spec["family_role"] = value["family_role"]
        if "date_role" in value:
            converted_spec["date_role"] = value["date_role"]
    return converted_spec, stable_roles(roles)


def _project_resolution_spec(
    value: Mapping[str, object], roles: tuple[str, ...]
) -> dict[str, object]:
    """Project one public resolution object onto the roles this analysis consumes.

    Complete explicit bindings are authoritative. The alias profile is retained only
    when at least one required role still needs catalogue-based resolution.
    """

    bindings_value = value.get("bindings", {})
    if not isinstance(bindings_value, Mapping):
        raise ValueError("analysis resolution bindings must be an object")

    bindings: dict[str, object] = {
        role: bindings_value[role] for role in roles if role in bindings_value
    }
    projected: dict[str, object] = {"bindings": bindings}
    if len(bindings) != len(roles) and "profile" in value:
        projected["profile"] = value["profile"]
    return projected


def prepare_records_population(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
    analysis_roles: Iterable[str],
) -> tuple[DatasetV2, PopulationResult]:
    """Resolve and normalize analysis roles, filter, then select family representatives."""

    if not isinstance(spec, Mapping):
        raise ValueError("analysis spec must be an object")
    normalization = spec.get("normalization")
    if not isinstance(normalization, Mapping) or normalization.get("profiles") != []:
        raise ValueError("analysis accepts no source-product normalization profile")

    population_spec, filter_roles = records_population_spec(spec.get("population"))
    roles = stable_roles((*analysis_roles, *filter_roles))
    if not roles:
        raise ValueError("analysis requires at least one role")

    dataset = read_dataset_v2(source, allowed_root=allowed_root)
    resolution_value = spec.get("resolution")
    if not isinstance(resolution_value, Mapping):
        raise ValueError("analysis resolution must be an object")
    selection_roles = family_roles(population_spec)
    required = stable_roles((*roles, *selection_roles))
    resolution = resolve_roles(
        dataset.manifest,
        _project_resolution_spec(resolution_value, required),
        required_roles=required,
    )
    normalized = normalize_dataset(
        dataset,
        resolution,
        NormalizationConfig(roles=roles, multi_value_policy="all"),
    )
    return dataset, apply_population(
        normalized,
        population_spec,
        source_role_ordinals={
            role: resolution.mapping[role].source_header_ordinal for role in selection_roles
        },
    )
