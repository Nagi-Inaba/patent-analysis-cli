from __future__ import annotations

import json
from pathlib import Path

import pytest

from patent_analysis.analysis import analyze_csv
from patent_analysis.analysis_contracts import AnalysisContractError
from patent_analysis.canonical_v2 import canonical_json_bytes

RANKING_SPEC_BYTES = (
    b'{"analysis_type":"ranking","dimension":"\\u51fa\\u9858\\u4eba",'
    b'"measure":{"mode":"count","column":null},"top_n":10,'
    b'"include_other":true,"multi_value_mode":"all"}'
)


def test_run_analysis_csv_preserves_versionless_ranking_bytes(tmp_path: Path) -> None:
    from patent_analysis.api import run_analysis_csv

    source = tmp_path / "input.csv"
    source.write_text("出願人\nA社\nB社\n", encoding="utf-8")
    direct = analyze_csv(
        source.name,
        json.loads(RANKING_SPEC_BYTES),
        allowed_root=tmp_path,
    )
    through_facade = run_analysis_csv(
        source.name,
        RANKING_SPEC_BYTES,
        allowed_root=tmp_path,
    )
    assert canonical_json_bytes(through_facade) == canonical_json_bytes(direct)


def test_run_analysis_csv_rejects_non_bytes_before_dispatch(tmp_path: Path) -> None:
    from patent_analysis.api import run_analysis_csv

    with pytest.raises(AnalysisContractError):
        run_analysis_csv("input.csv", bytearray(RANKING_SPEC_BYTES), allowed_root=tmp_path)


def test_inspect_dataset_is_bounded_and_source_independent(tmp_path: Path) -> None:
    from patent_analysis.api import inspect_dataset

    source = tmp_path / "input.csv"
    source.write_text("出願人,IPC\nA社,H01L\n", encoding="utf-8")
    document = inspect_dataset(source.name, allowed_root=tmp_path)
    assert document["dataset"]["row_count"] == 1
    assert document["dataset"]["column_count"] == 2
    assert "rows" not in document
    assert "samples" not in json.dumps(document, ensure_ascii=False).lower()
    assert "resolution" in document


def test_inspect_dataset_does_not_silently_enable_samples(tmp_path: Path) -> None:
    from patent_analysis.api import inspect_dataset

    with pytest.raises(ValueError, match="samples"):
        inspect_dataset("input.csv", allowed_root=tmp_path, include_samples=True)


def test_get_public_schema_is_closed_to_packaged_schema_names() -> None:
    from patent_analysis.api import get_public_schema

    schemas = {
        "analysis-spec.schema.json": "analysis-spec",
        "timeline-parameters-v1.schema.json": "timeline-parameters",
        "timeline-result-v1.schema.json": "timeline-result",
        "composition-parameters-v1.schema.json": "composition-parameters",
        "composition-result-v1.schema.json": "composition-result",
        "categorical-chart-model-v1.schema.json": "categorical-chart-model",
        "categorical-render-spec-v1.schema.json": "categorical-render-spec",
        "growth-parameters-v1.schema.json": "growth-parameters",
        "growth-result-v1.schema.json": "growth-result",
        "concentration-parameters-v1.schema.json": "concentration-parameters",
        "concentration-result-v1.schema.json": "concentration-result",
        "lifecycle-parameters-v1.schema.json": "lifecycle-parameters",
        "lifecycle-result-v1.schema.json": "lifecycle-result",
        "points-chart-model-v1.schema.json": "points-chart-model",
        "points-render-spec-v1.schema.json": "points-render-spec",
        "points-renderer-response.schema.json": "points-renderer-response",
    }
    for name, contract in schemas.items():
        schema = get_public_schema(name)
        assert schema["$id"] == f"urn:patent-analysis:{contract}:1.0.0", name
        assert schema["$schema"].endswith("2020-12/schema"), name
    with pytest.raises(ValueError):
        get_public_schema("../pyproject.toml")


def test_describe_capabilities_is_part_of_public_facade() -> None:
    from patent_analysis.api import describe_capabilities
    from patent_analysis.capabilities import describe_capabilities as direct_describe

    assert describe_capabilities() == direct_describe()


def test_validate_analysis_spec_bytes_preserves_the_legacy_dict_api() -> None:
    import patent_analysis
    from patent_analysis.api import validate_analysis_spec_bytes

    legacy_dict_result = patent_analysis.validate_analysis_spec(json.loads(RANKING_SPEC_BYTES))
    assert legacy_dict_result["dimension"] == "出願人"

    assert validate_analysis_spec_bytes(RANKING_SPEC_BYTES) == {
        "valid": True,
        "analysis_id": "ranking.v1",
        "spec_variant": "versionless-ranking",
    }

    matrix_spec = (
        Path(__file__).parent / "fixtures" / "cli" / "matrix" / "spec.json"
    ).read_bytes()
    assert validate_analysis_spec_bytes(matrix_spec) == {
        "valid": True,
        "analysis_id": "matrix.v1",
        "spec_variant": "analysis-spec-v2",
    }
    assert callable(patent_analysis.validate_analysis_spec_bytes)


def test_package_root_exports_shared_public_facade() -> None:
    import patent_analysis

    assert callable(patent_analysis.describe_capabilities)
    assert callable(patent_analysis.inspect_dataset)
    assert callable(patent_analysis.run_analysis)
    assert callable(patent_analysis.run_analysis_csv)
    assert callable(patent_analysis.render_analysis_svg)
    assert callable(patent_analysis.get_public_schema)


def test_analyze_cli_passes_original_spec_bytes_to_public_facade(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from patent_analysis import cli

    source = tmp_path / "input.csv"
    source.write_text("出願人\nA社\n", encoding="utf-8")
    spec = tmp_path / "spec.json"
    original = b'{ "analysis_type" : "ranking" }\n'
    spec.write_bytes(original)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    captured: dict[str, object] = {}

    def fake_run(
        source_value: str,
        spec_bytes: bytes,
        *,
        allowed_root: str | Path,
    ) -> dict[str, object]:
        captured.update(
            source=source_value,
            spec_bytes=spec_bytes,
            allowed_root=str(allowed_root),
        )
        return {"analysis_contract_version": "1.0.0", "ok": True}

    monkeypatch.setattr(cli, "run_analysis_csv", fake_run)
    exit_code = cli.main(["analyze", source.name, "--spec", spec.name, "--json"])
    assert exit_code == 0
    assert captured["source"] == source.name
    assert captured["spec_bytes"] == original
    assert captured["allowed_root"] == str(tmp_path)
    assert json.loads(capsys.readouterr().out)["ok"] is True


def test_analyze_cli_preserves_malformed_spec_input_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from patent_analysis import cli

    source = tmp_path / "input.csv"
    source.write_text("出願人\nA社\n", encoding="utf-8")
    spec = tmp_path / "spec.json"
    spec.write_bytes(b'{"analysis_type":"ranking"')
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))

    exit_code = cli.main(["analyze", source.name, "--spec", spec.name, "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == cli.EXIT_INPUT_ERROR
    assert payload["error"]["code"] == "input.invalid"
