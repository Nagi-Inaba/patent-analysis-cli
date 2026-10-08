from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from types import MappingProxyType

import pytest

from patent_analysis.canonical_v2 import canonical_sha256

EXPECTED_CATALOG_SHA256 = "1f6fc11abcf7b37753c85e88534c3eacdef0dcff294329f07064369629b6cac2"


def _manifest(*headers: str):
    from patent_analysis.dataset_v2 import DatasetManifestV2

    return DatasetManifestV2(
        dataset_contract_version="2.0.0",
        raw_header=tuple(headers),
        input_rows=3,
        input_columns=len(headers),
        byte_size=100,
        encoding="utf-8",
        source_input_sha256="a" * 64,
        preamble=None,
    )


def test_catalog_resource_bytes_counts_and_normalized_keys_are_fixed() -> None:
    from patent_analysis.column_resolution import (
        catalog_resource_bytes,
        normalize_header,
    )

    raw = catalog_resource_bytes()
    document = json.loads(raw)
    entries = document["entries"]
    active_sources = {
        source_id
        for source_id, source in document["sources"].items()
        if source["support_status"] == "active"
    }
    active = [
        entry
        for entry in entries
        if any(source_id in active_sources for source_id in entry["sources"])
    ]
    staged = [entry for entry in entries if entry not in active]
    normalized_keys = [normalize_header(entry["header"]) for entry in entries]

    assert hashlib.sha256(raw).hexdigest() == EXPECTED_CATALOG_SHA256
    assert len(entries) == 230
    assert len(active) == 195
    assert len(staged) == 35
    assert len(normalized_keys) == len(set(normalized_keys))


def test_catalog_resource_is_declared_as_wheel_package_data() -> None:
    project_root = Path(__file__).resolve().parents[1]
    with (project_root / "pyproject.toml").open("rb") as stream:
        package_data = tomllib.load(stream)["tool"]["setuptools"]["package-data"]

    assert "resources/*.json" in package_data["patent_analysis"]


def test_header_normalization_matches_ecmascript_nfkc_bom_whitespace_and_lower() -> None:
    from patent_analysis.column_resolution import normalize_header

    assert normalize_header("\ufeff\u00a0 ＰＵＢＬＩＣＡＴＩＯＮ\u2028\tＤＡＴＥ \ufeff") == (
        "publication date"
    )
    assert normalize_header("A\u001cB") == "a\u001cb"


@pytest.mark.parametrize(
    ("header", "status", "role", "suffix"),
    [
        ("PA_2", "active", "applicant", "2"),
        ("Display Key_2", "unmatched", None, None),
        ("Application/Filing Date", "staged", None, None),
        ("Applicants", "active", "applicant", None),
    ],
)
def test_candidate_status_covers_suffix_staged_and_shared_source_rules(
    header: str,
    status: str,
    role: str | None,
    suffix: str | None,
) -> None:
    from patent_analysis.column_resolution import describe_header_candidates

    candidate = describe_header_candidates((header,))["candidates"][0]

    assert candidate["status"] == status
    assert candidate["role"] == role
    assert candidate["numeric_suffix"] == suffix
    if status != "active":
        assert candidate == {
            "header_ordinal": 0,
            "raw_header": header,
            "status": status,
            "role": None,
            "normalized_name": None,
            "display_label": None,
            "numeric_suffix": None,
            "identifier_like": None,
        }


def test_candidate_order_and_warning_counts_follow_input_headers() -> None:
    from patent_analysis.column_resolution import describe_header_candidates

    resolution = describe_header_candidates(
        ("Mystery", "Application/Filing Date", "Applicants")
    )

    assert [item["raw_header"] for item in resolution["candidates"]] == [
        "Mystery",
        "Application/Filing Date",
        "Applicants",
    ]
    assert resolution["warning_counts"] == {
        "staged_aliases": 1,
        "unmatched_headers": 1,
    }


def test_profileless_resolution_requires_explicit_exact_required_binding() -> None:
    from patent_analysis.column_resolution import ResolutionError, resolve_roles

    with pytest.raises(ResolutionError) as caught:
        resolve_roles(_manifest("Applicants"), {}, required_roles=("applicant",))

    assert caught.value.code == "resolution.missing_binding"
    assert str(caught.value) == "resolution.missing_binding"


def test_profileless_exact_binding_and_optional_omission_succeed() -> None:
    from patent_analysis.column_resolution import resolve_roles

    resolution = resolve_roles(
        _manifest("Applicants", "Publication date"),
        {"bindings": {"applicant": "Applicants"}},
        required_roles=("applicant",),
        optional_roles=("date",),
    )

    assert resolution.mapping["applicant"].source_header_ordinal == 0
    assert resolution.mapping["applicant"].raw_header == "Applicants"
    assert "date" not in resolution.mapping
    assert resolution.receipt.resolution_profile is None
    assert resolution.receipt.column_catalog_sha256 is None
    assert dict(resolution.receipt.warning_counts) == {}


def test_profile_unique_candidate_auto_binds_required_role() -> None:
    from patent_analysis.column_resolution import resolve_roles

    resolution = resolve_roles(
        _manifest("Applicants", "Title"),
        {"profile": "column-alias.v2"},
        required_roles=("applicant",),
    )

    assert resolution.mapping["applicant"].source_header_ordinal == 0
    assert resolution.mapping["applicant"].raw_header == "Applicants"


@pytest.mark.parametrize(
    ("headers", "code"),
    [
        (("Title",), "resolution.missing"),
        (("Applicants", "PA"), "resolution.ambiguous"),
    ],
)
def test_profile_resolution_rejects_missing_and_ambiguous_required_roles(
    headers: tuple[str, ...],
    code: str,
) -> None:
    from patent_analysis.column_resolution import ResolutionError, resolve_roles

    with pytest.raises(ResolutionError) as caught:
        resolve_roles(
            _manifest(*headers),
            {"profile": "column-alias.v2"},
            required_roles=("applicant",),
        )

    assert caught.value.code == code


def test_profile_explicit_binding_must_be_active_candidate_for_exact_role() -> None:
    from patent_analysis.column_resolution import ResolutionError, resolve_roles

    manifest = _manifest("Application/Filing Date", "Publication date")
    for raw_header in ("Application/Filing Date", "Publication date"):
        role = "applicant" if raw_header == "Publication date" else "date"
        with pytest.raises(ResolutionError) as caught:
            resolve_roles(
                manifest,
                {
                    "profile": "column-alias.v2",
                    "bindings": {role: raw_header},
                },
                required_roles=(role,),
            )
        assert caught.value.code == "resolution.invalid"


def test_role_mapping_is_defensive_immutable_and_receipt_hashes_are_exact() -> None:
    from patent_analysis.column_resolution import resolve_roles

    bindings = {"applicant": "PA"}
    manifest = _manifest("Applicants", "PA", "Application/Filing Date", "Mystery")
    resolution = resolve_roles(
        manifest,
        {"profile": "column-alias.v2", "bindings": bindings},
        required_roles=("applicant",),
    )
    bindings["applicant"] = "Applicants"

    assert isinstance(resolution.mapping, MappingProxyType)
    assert resolution.mapping["applicant"].source_header_ordinal == 1
    with pytest.raises(TypeError):
        resolution.mapping["applicant"] = resolution.mapping["applicant"]  # type: ignore[index]

    receipt = resolution.receipt
    assert receipt.source_input_sha256 == "a" * 64
    assert receipt.raw_header_sha256 == canonical_sha256(list(manifest.raw_header))
    assert receipt.column_catalog_sha256 == EXPECTED_CATALOG_SHA256
    assert receipt.resolved_role_mapping_sha256 == canonical_sha256(
        {"applicant": {"source_header_ordinal": 1, "raw_header": "PA"}}
    )
    assert dict(receipt.warning_counts) == {
        "staged_aliases": 1,
        "unmatched_headers": 1,
    }


def test_one_raw_header_cannot_bind_two_roles() -> None:
    from patent_analysis.column_resolution import ResolutionError, resolve_roles

    with pytest.raises(ResolutionError) as caught:
        resolve_roles(
            _manifest("Applicants"),
            {"bindings": {"applicant": "Applicants", "other": "Applicants"}},
            required_roles=("applicant", "other"),
        )

    assert caught.value.code == "resolution.invalid"
