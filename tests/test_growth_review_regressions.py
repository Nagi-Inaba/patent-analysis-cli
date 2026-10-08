"""Regressions for PR #24's two independent Codex review findings."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import MappingProxyType

import pytest

from patent_analysis import api
from patent_analysis.analyses import growth
from patent_analysis.analysis_contracts import AnalysisContractError
from patent_analysis.analysis_dispatch import dispatch_and_validate_spec_bytes
from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis.normalization import NormalizedRow
from patent_analysis.population import PopulationReceipt, PopulationResult
from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
from patent_analysis_mcp.tool_handlers import ToolHandlers


def _spec(start: int = 2018, end: int = 2022) -> dict[str, object]:
    return {
        "analysis_contract_version": "2.0.0",
        "analysis_id": "growth.v1",
        "resolution": {"bindings": {"year": "year", "category": "category"}},
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
        "parameters": {
            "date_role": "year",
            "series_role": "category",
            "start_year": start,
            "end_year": end,
        },
    }


@pytest.mark.parametrize("start,end", [(2022, 2018), (2022, 2022)])
def test_dispatch_and_public_validation_reject_unusable_growth_period(start: int, end: int) -> None:
    raw = canonical_json_bytes(_spec(start, end))
    for validate in (dispatch_and_validate_spec_bytes, api.validate_analysis_spec_bytes):
        with pytest.raises(AnalysisContractError) as caught:
            validate(raw)
        assert caught.value.code == "analysis.invalid"


@pytest.mark.parametrize("start,end", [(2022, 2018), (2022, 2022)])
def test_mcp_validation_does_not_approve_unusable_growth_period(
    tmp_path: Path, start: int, end: int
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    roots = RootRegistry(
        input_roots=(ApprovedRoot("input", input_root),),
        output_roots=(ApprovedRoot("output", output_root),),
    )
    response = ToolHandlers(roots=roots).call(
        "patent_analysis.validate_spec", {"spec": _spec(start, end)}
    )
    assert response["ok"] is False
    assert response["error"]["code"] == "input.invalid"
    assert str(tmp_path) not in repr(response)


@pytest.mark.parametrize("start,end", [(2018, 2022), (1800, 2199)])
def test_valid_growth_spec_retains_original_bytes_and_parameters(start: int, end: int) -> None:
    original = _spec(start, end)
    snapshot = deepcopy(original)
    raw = canonical_json_bytes(original)
    assert dispatch_and_validate_spec_bytes(raw).to_dict() == original
    assert api.validate_analysis_spec_bytes(raw)["valid"] is True
    assert original == snapshot


def test_growth_role_relationship_is_checked_by_the_same_validator() -> None:
    document = _spec()
    document["parameters"]["series_role"] = "year"
    with pytest.raises(AnalysisContractError):
        dispatch_and_validate_spec_bytes(canonical_json_bytes(document))


def _population(*entries: tuple[str, str]) -> PopulationResult:
    rows = tuple(
        NormalizedRow(
            source_ordinal=index,
            source_fields=(year, category),
            values_by_role=MappingProxyType({"year": (year,), "category": (category,)}),
        )
        for index, (year, category) in enumerate(entries, 1)
    )
    return PopulationResult(
        rows=rows,
        receipt=PopulationReceipt(
            population_contract_version="1.0.0",
            normalization_row_stream_sha256="a" * 64,
            population_spec_sha256="b" * 64,
            family_mode="records",
            filter_count=0,
            input_rows=len(rows),
            included_rows=len(rows),
            filtered_rows=0,
        ),
    )


def test_growth_same_label_at_two_endpoints_consumes_two_buckets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(growth, "MAX_DISTINCT_BUCKETS", 1)
    population = _population(("2018", "A"), ("2022", "A"))
    with pytest.raises(growth.GrowthBudgetError, match="distinct buckets"):
        growth.analyze_growth(population, _spec()["parameters"])


def test_growth_repeated_membership_at_one_endpoint_consumes_one_bucket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(growth, "MAX_DISTINCT_BUCKETS", 1)
    result = growth.analyze_growth(
        _population(("2018", "A"), ("2018", "A")), _spec()["parameters"]
    )
    assert result["series"][0]["values"] == [2, 0]
    assert result["contributions"] == 2


def test_growth_endpoint_bucket_boundary_accepts_exact_limit_and_rejects_next(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(growth, "MAX_DISTINCT_BUCKETS", 2)
    result = growth.analyze_growth(
        _population(("2018", "A"), ("2022", "A")), _spec()["parameters"]
    )
    assert result["series"][0]["values"] == [1, 1]
    with pytest.raises(growth.GrowthBudgetError, match="distinct buckets"):
        growth.analyze_growth(
            _population(("2018", "A"), ("2022", "A"), ("2022", "B")),
            _spec()["parameters"],
        )
