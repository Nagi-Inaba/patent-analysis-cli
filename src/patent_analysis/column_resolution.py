"""Immutable v2 patent-column candidate and role resolution."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

from patent_analysis.canonical_v2 import canonical_sha256
from patent_analysis.receipts_v2 import DatasetResolutionReceipt

if TYPE_CHECKING:
    from patent_analysis.dataset_v2 import DatasetManifestV2

COLUMN_ALIAS_PROFILE = "column-alias.v2"
EXPECTED_CATALOG_SHA256 = "1f6fc11abcf7b37753c85e88534c3eacdef0dcff294329f07064369629b6cac2"

_ECMASCRIPT_WHITESPACE = frozenset(
    {
        "\u0009",
        "\u000b",
        "\u000c",
        "\u0020",
        "\u00a0",
        "\u1680",
        "\u2000",
        "\u2001",
        "\u2002",
        "\u2003",
        "\u2004",
        "\u2005",
        "\u2006",
        "\u2007",
        "\u2008",
        "\u2009",
        "\u200a",
        "\u2028",
        "\u2029",
        "\u202f",
        "\u205f",
        "\u3000",
        "\ufeff",
        "\u000a",
        "\u000d",
    }
)
_NUMERIC_SUFFIX = re.compile(r"^(.+)_([0-9]+)$")
_ERROR_CODES = frozenset(
    {
        "resolution.invalid",
        "resolution.missing_binding",
        "resolution.missing",
        "resolution.ambiguous",
    }
)


def trim_ecmascript_whitespace(value: str) -> str:
    """Apply the explicit ECMAScript WhiteSpace/LineTerminator edge trim."""

    start = 0
    end = len(value)
    while start < end and value[start] in _ECMASCRIPT_WHITESPACE:
        start += 1
    while end > start and value[end - 1] in _ECMASCRIPT_WHITESPACE:
        end -= 1
    return value[start:end]


def normalize_header(value: str) -> str:
    """Match the pinned Matrix Desktop header normalization behavior."""

    normalized = unicodedata.normalize("NFKC", value).replace("\ufeff", "")
    normalized = trim_ecmascript_whitespace(normalized).lower()
    output: list[str] = []
    in_whitespace = False
    for character in normalized:
        if character in _ECMASCRIPT_WHITESPACE:
            if not in_whitespace:
                output.append(" ")
            in_whitespace = True
        else:
            output.append(character)
            in_whitespace = False
    return "".join(output)


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    sources: tuple[str, ...]
    header: str
    role: str
    normalized_name: str
    display_label: str
    identifier_like: bool
    allow_numeric_suffix: bool
    active: bool


@dataclass(frozen=True, slots=True)
class PreamblePolicy:
    source_id: str
    marker: str
    host: str
    header_signature: tuple[str, ...]


def catalog_resource_bytes() -> bytes:
    return (
        files("patent_analysis")
        .joinpath("resources", "column-alias.v2.json")
        .read_bytes()
    )


def _load_catalog() -> tuple[tuple[CatalogEntry, ...], tuple[PreamblePolicy, ...]]:
    raw = catalog_resource_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_CATALOG_SHA256:
        raise RuntimeError("column alias catalog resource is invalid")
    try:
        document = json.loads(raw)
        sources = document["sources"]
        raw_entries = document["entries"]
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("column alias catalog resource is invalid") from None
    if document.get("catalog_version") != "2.0.0" or not isinstance(sources, dict):
        raise RuntimeError("column alias catalog resource is invalid")

    active_sources = {
        source_id
        for source_id, source in sources.items()
        if isinstance(source, dict) and source.get("support_status") == "active"
    }
    entries: list[CatalogEntry] = []
    for item in raw_entries:
        try:
            source_ids = tuple(item["sources"])
            entry = CatalogEntry(
                sources=source_ids,
                header=item["header"],
                role=item["role"],
                normalized_name=item["normalized_name"],
                display_label=item["display_label"],
                identifier_like=item["identifier_like"],
                allow_numeric_suffix=item.get("allow_numeric_suffix", False),
                active=any(source_id in active_sources for source_id in source_ids),
            )
        except (KeyError, TypeError):
            raise RuntimeError("column alias catalog resource is invalid") from None
        if (
            not all(isinstance(source_id, str) and source_id for source_id in entry.sources)
            or not all(
                isinstance(value, str) and value
                for value in (
                    entry.header,
                    entry.role,
                    entry.normalized_name,
                    entry.display_label,
                )
            )
            or type(entry.identifier_like) is not bool
            or type(entry.allow_numeric_suffix) is not bool
        ):
            raise RuntimeError("column alias catalog resource is invalid")
        entries.append(entry)

    policies: list[PreamblePolicy] = []
    for source_id, source in sources.items():
        detection = source.get("header_detection") if isinstance(source, dict) else None
        if detection is None:
            continue
        try:
            policies.append(
                PreamblePolicy(
                    source_id=source_id,
                    marker=detection["preamble_prefix"],
                    host=detection["preamble_host"],
                    header_signature=tuple(detection["header_signature"]),
                )
            )
        except (KeyError, TypeError):
            raise RuntimeError("column alias catalog resource is invalid") from None

    normalized_keys = [normalize_header(entry.header) for entry in entries]
    if len(entries) != 230 or len(normalized_keys) != len(set(normalized_keys)):
        raise RuntimeError("column alias catalog resource is invalid")
    return tuple(entries), tuple(policies)


_CATALOG_ENTRIES, _PREAMBLE_POLICIES = _load_catalog()
_ALL_ENTRIES = MappingProxyType(
    {normalize_header(entry.header): entry for entry in _CATALOG_ENTRIES}
)
_ACTIVE_ENTRIES = MappingProxyType(
    {
        normalize_header(entry.header): entry
        for entry in _CATALOG_ENTRIES
        if entry.active
    }
)


def get_preamble_policies() -> tuple[PreamblePolicy, ...]:
    return _PREAMBLE_POLICIES


@dataclass(frozen=True, slots=True)
class _ActiveMatch:
    entry: CatalogEntry
    numeric_suffix: str | None


def _resolve_active(value: str) -> _ActiveMatch | None:
    normalized = normalize_header(value)
    direct = _ACTIVE_ENTRIES.get(normalized)
    if direct is not None:
        return _ActiveMatch(direct, None)
    suffix_match = _NUMERIC_SUFFIX.fullmatch(normalized)
    if suffix_match is None:
        return None
    base = _ACTIVE_ENTRIES.get(suffix_match.group(1))
    if base is None or not base.allow_numeric_suffix:
        return None
    return _ActiveMatch(base, suffix_match.group(2))


def _candidate_status(
    value: str,
) -> tuple[Literal["active", "staged", "unmatched"], _ActiveMatch | None]:
    active = _resolve_active(value)
    if active is not None:
        return "active", active
    normalized = normalize_header(value)
    direct = _ALL_ENTRIES.get(normalized)
    if direct is not None and not direct.active:
        return "staged", None
    suffix_match = _NUMERIC_SUFFIX.fullmatch(normalized)
    if suffix_match is not None:
        base = _ALL_ENTRIES.get(suffix_match.group(1))
        if base is not None and not base.active:
            return "staged", None
    return "unmatched", None


def describe_header_candidates(raw_header: tuple[str, ...]) -> dict[str, Any]:
    candidates: list[dict[str, object]] = []
    warning_counts = {"staged_aliases": 0, "unmatched_headers": 0}
    for ordinal, header in enumerate(raw_header):
        status, match = _candidate_status(header)
        if status == "staged":
            warning_counts["staged_aliases"] += 1
        elif status == "unmatched":
            warning_counts["unmatched_headers"] += 1
        candidates.append(
            {
                "header_ordinal": ordinal,
                "raw_header": header,
                "status": status,
                "role": None if match is None else match.entry.role,
                "normalized_name": None if match is None else match.entry.normalized_name,
                "display_label": None if match is None else match.entry.display_label,
                "numeric_suffix": None if match is None else match.numeric_suffix,
                "identifier_like": None if match is None else match.entry.identifier_like,
            }
        )
    return {
        "profile": COLUMN_ALIAS_PROFILE,
        "candidates": candidates,
        "warning_counts": warning_counts,
    }


class ResolutionError(ValueError):
    """Closed sanitized error for v2 role resolution failures."""

    def __init__(self, code: str) -> None:
        if code not in _ERROR_CODES:
            code = "resolution.invalid"
        super().__init__(code)
        self.code = code
        self.safe_message = code
        self.retryable = False
        self.details: dict[str, object] = {}
        self.__suppress_context__ = True

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.safe_message,
            "retryable": self.retryable,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class ResolvedRoleBinding:
    role: str
    source_header_ordinal: int
    raw_header: str


@dataclass(frozen=True, slots=True)
class RoleResolution:
    mapping: Mapping[str, ResolvedRoleBinding]
    receipt: DatasetResolutionReceipt

    def __post_init__(self) -> None:
        copied = dict(self.mapping)
        if not all(
            isinstance(role, str)
            and role
            and isinstance(binding, ResolvedRoleBinding)
            and binding.role == role
            for role, binding in copied.items()
        ):
            raise TypeError("role mapping is invalid")
        object.__setattr__(self, "mapping", MappingProxyType(copied))


def _validate_role_inputs(
    resolution_spec: Mapping[str, object],
    required_roles: tuple[str, ...],
    optional_roles: tuple[str, ...],
) -> tuple[str | None, Mapping[str, str], tuple[str, ...]]:
    if (
        not isinstance(resolution_spec, Mapping)
        or not isinstance(required_roles, tuple)
        or not isinstance(optional_roles, tuple)
        or any(key not in {"profile", "bindings"} for key in resolution_spec)
    ):
        raise ResolutionError("resolution.invalid")
    roles = required_roles + optional_roles
    if (
        not all(isinstance(role, str) and role for role in roles)
        or len(set(roles)) != len(roles)
    ):
        raise ResolutionError("resolution.invalid")
    profile = resolution_spec.get("profile")
    if profile is not None and profile != COLUMN_ALIAS_PROFILE:
        raise ResolutionError("resolution.invalid")
    bindings_value = resolution_spec.get("bindings", {})
    if not isinstance(bindings_value, Mapping):
        raise ResolutionError("resolution.invalid")
    bindings: dict[str, str] = {}
    for role, raw_header in bindings_value.items():
        if (
            not isinstance(role, str)
            or role not in roles
            or not isinstance(raw_header, str)
            or not raw_header
        ):
            raise ResolutionError("resolution.invalid")
        bindings[role] = raw_header
    return profile, MappingProxyType(bindings), roles


def resolve_roles(
    manifest: DatasetManifestV2,
    resolution_spec: Mapping[str, object],
    *,
    required_roles: tuple[str, ...],
    optional_roles: tuple[str, ...] = (),
) -> RoleResolution:
    """Bind canonical roles without catalog- or input-order tie breaking."""

    profile, explicit_bindings, roles = _validate_role_inputs(
        resolution_spec, required_roles, optional_roles
    )
    try:
        raw_header = tuple(manifest.raw_header)
    except (AttributeError, TypeError):
        raise ResolutionError("resolution.invalid") from None
    if len(set(raw_header)) != len(raw_header):
        raise ResolutionError("resolution.invalid")

    candidates = (
        describe_header_candidates(raw_header)
        if profile is not None
        else {"candidates": [], "warning_counts": {}}
    )
    candidate_items = candidates["candidates"]
    resolved: dict[str, ResolvedRoleBinding] = {}
    used_ordinals: set[int] = set()

    for role in roles:
        explicit = explicit_bindings.get(role)
        if explicit is not None:
            try:
                ordinal = raw_header.index(explicit)
            except ValueError:
                raise ResolutionError("resolution.invalid") from None
            if profile is not None:
                candidate = candidate_items[ordinal]
                if candidate["status"] != "active" or candidate["role"] != role:
                    raise ResolutionError("resolution.invalid")
        elif profile is None:
            if role in required_roles:
                raise ResolutionError("resolution.missing_binding")
            continue
        else:
            matching = [
                item
                for item in candidate_items
                if item["status"] == "active" and item["role"] == role
            ]
            if not matching:
                if role in required_roles:
                    raise ResolutionError("resolution.missing")
                continue
            if len(matching) > 1:
                raise ResolutionError("resolution.ambiguous")
            ordinal = int(matching[0]["header_ordinal"])
            explicit = raw_header[ordinal]
        if ordinal in used_ordinals:
            raise ResolutionError("resolution.invalid")
        used_ordinals.add(ordinal)
        resolved[role] = ResolvedRoleBinding(
            role=role,
            source_header_ordinal=ordinal,
            raw_header=explicit,
        )

    mapping_document = {
        role: {
            "source_header_ordinal": binding.source_header_ordinal,
            "raw_header": binding.raw_header,
        }
        for role, binding in resolved.items()
    }
    receipt = DatasetResolutionReceipt(
        dataset_contract_version=manifest.dataset_contract_version,
        source_input_sha256=manifest.source_input_sha256,
        resolution_profile=profile,
        column_catalog_sha256=EXPECTED_CATALOG_SHA256 if profile is not None else None,
        raw_header_sha256=canonical_sha256(list(raw_header)),
        resolved_role_mapping_sha256=canonical_sha256(mapping_document),
        input_rows=manifest.input_rows,
        input_columns=manifest.input_columns,
        warning_counts=candidates["warning_counts"],
    )
    return RoleResolution(mapping=resolved, receipt=receipt)
