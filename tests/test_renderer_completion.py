from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

import pytest

from patent_analysis import AnalysisContractError
from patent_analysis.api import run_analysis_csv
from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis_mcp.contracts import MAX_TOOL_RESPONSE_BYTES
from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
from patent_analysis_mcp.tool_handlers import ToolHandlers


def spec(analysis_id: str) -> dict[str, object]:
    parameters: dict[str, object] = {"date_role": "year"}
    if analysis_id == "growth.v1":
        parameters.update(series_role="category", start_year=2020, end_year=2024)
    else:
        parameters["category_role"] = "category"
    return {
        "analysis_contract_version": "2.0.0",
        "analysis_id": analysis_id,
        "resolution": {"bindings": {"year": "year", "category": "category"}},
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
        "parameters": parameters,
    }


def _roots(tmp_path: Path) -> RootRegistry:
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    return RootRegistry(
        input_roots=(ApprovedRoot("input", tmp_path / "input"),),
        output_roots=(ApprovedRoot("output", tmp_path / "output"),),
    )


def _csv(path: Path, rows: list[tuple[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("year", "category"))
        writer.writerows(rows)


@pytest.mark.parametrize("analysis_id", ["growth.v1", "lifecycle.v1"])
def test_oversized_serialized_labels_fail_before_mcp_projection(
    tmp_path: Path,
    analysis_id: str,
) -> None:
    source = tmp_path / "input.csv"
    _csv(source, [("2024", "\U0001f9ea" * 4096)])
    with pytest.raises(AnalysisContractError, match="analysis exceeds published limits"):
        run_analysis_csv(
            source.name, canonical_json_bytes(spec(analysis_id)), allowed_root=tmp_path
        )


@pytest.mark.parametrize("analysis_id", ["growth.v1", "lifecycle.v1"])
@pytest.mark.parametrize("unit", ["a", "\U0001f9ea", '"', "\\", "\x01"])
def test_maximum_bounded_labels_fit_real_mcp_response(
    tmp_path: Path,
    analysis_id: str,
    unit: str,
) -> None:
    roots = _roots(tmp_path)
    labels = []
    for index in range(20):
        label = f"{index:02d}:"
        low, high = 0, 4096
        while low < high:
            middle = (low + high + 1) // 2
            if len(canonical_json_bytes(label + unit * middle)) <= 4096:
                low = middle
            else:
                high = middle - 1
        label += unit * low
        labels.append(label)
    _csv(tmp_path / "input/input.csv", [("2024", label) for label in labels])
    handlers = ToolHandlers(roots=roots)
    result = handlers.call(
        "patent_analysis.analyze",
        {
            "input_root_id": "input",
            "path": "input.csv",
            "spec": spec(analysis_id),
        },
    )
    assert result["ok"] is True, result
    assert len(canonical_json_bytes(result)) <= MAX_TOOL_RESPONSE_BYTES
    data = result["content"]["data"]
    assert len(data["series"] if analysis_id == "growth.v1" else data["points"]) == 20
    assert "receipt" not in result["content"]
    assert "source_fields" not in result["content"]
    assert str(tmp_path) not in repr(result)


def test_concentration_full_400_year_output_fits_mcp(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    _csv(tmp_path / "input/input.csv", [(str(year), "A") for year in range(1800, 2200)])
    result = ToolHandlers(roots=roots).call(
        "patent_analysis.analyze",
        {
            "input_root_id": "input",
            "path": "input.csv",
            "spec": spec("concentration.v1"),
        },
    )
    assert result["ok"] is True
    assert len(result["content"]["data"]["x"]) == 400
    assert len(canonical_json_bytes(result)) <= MAX_TOOL_RESPONSE_BYTES


def test_points_builder_rejects_duplicate_labels(tmp_path: Path) -> None:
    from patent_analysis.chart_models.points import build_points_chart_model

    _csv(tmp_path / "input.csv", [("2024", "A"), ("2024", "B")])
    result = run_analysis_csv(
        "input.csv", canonical_json_bytes(spec("lifecycle.v1")), allowed_root=tmp_path
    )
    result["data"]["points"][1]["label"] = "A"
    with pytest.raises(ValueError):
        build_points_chart_model(result, mark="points-bubble-svg.v1")


@pytest.mark.skipif(
    sys.platform not in {"win32", "darwin"} or shutil.which("node") is None,
    reason="trusted-local SVG E2E requires Windows x64 or macOS and exact Node",
)
@pytest.mark.parametrize(
    "analysis_id,mark",
    [
        ("growth.v1", "series-line-svg.v1"),
        ("concentration.v1", "series-line-svg.v1"),
        ("lifecycle.v1", "points-bubble-svg.v1"),
    ],
)
def test_real_svg_creation_reuse_and_hostile_labels(
    tmp_path: Path,
    analysis_id: str,
    mark: str,
) -> None:
    from patent_analysis.rendering import render_analysis_svg

    label = '{a}<script>"&'
    _csv(tmp_path / "input.csv", [("2020", label), ("2024", label), ("2024", "B")])
    result = run_analysis_csv(
        "input.csv", canonical_json_bytes(spec(analysis_id)), allowed_root=tmp_path
    )
    raw = canonical_json_bytes(result)
    output = tmp_path / "artifacts"
    output.mkdir()
    first = render_analysis_svg(
        raw, mark=mark, output_directory=output, node_executable=shutil.which("node")
    )
    second = render_analysis_svg(
        raw, mark=mark, output_directory=output, node_executable=shutil.which("node")
    )
    assert first["status"] == "created"
    assert second["status"] == "reused"
    assert first["svg_sha256"] == second["svg_sha256"]
    svg = (output / str(first["svg"])).read_bytes()
    assert b'role="img"' in svg and b"<title id=" in svg and b"<desc id=" in svg
    assert b"<script" not in svg and b"<foreignObject" not in svg
    if analysis_id == "lifecycle.v1":
        assert b"{a}&lt;script&gt;" in svg
    other_output = tmp_path / "cold-output"
    other_output.mkdir()
    third = render_analysis_svg(
        raw, mark=mark, output_directory=other_output, node_executable=shutil.which("node")
    )
    assert first["svg_sha256"] == third["svg_sha256"]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is not installed")
@pytest.mark.parametrize("empty", [False, True])
def test_packaged_points_bootstrap_runs_in_cold_processes(tmp_path: Path, empty: bool) -> None:
    import subprocess

    from patent_analysis.chart_models.points import (
        build_points_chart_model,
        build_points_render_spec,
    )
    from patent_analysis.renderer_protocol import decode_renderer_response
    from patent_analysis.renderer_resources import load_verified_points_renderer_resources
    from patent_analysis.renderer_runtime import build_renderer_request

    node = shutil.which("node")
    assert node is not None
    assert subprocess.check_output([node, "--version"], text=True).strip() == "v22.23.4"
    label = '{a}<script>"&'
    rows = [] if empty else [("2020", label), ("2024", label), ("2024", label)]
    _csv(tmp_path / "input.csv", rows)
    result = run_analysis_csv(
        "input.csv", canonical_json_bytes(spec("lifecycle.v1")), allowed_root=tmp_path
    )
    model, _ = build_points_chart_model(result, mark="points-bubble-svg.v1")
    render_spec = build_points_render_spec(mark="points-bubble-svg.v1", point_count=len(rows))
    resources = load_verified_points_renderer_resources()
    frame = build_renderer_request(
        canonical_json_bytes(model), canonical_json_bytes(render_spec), resources
    )
    command = [
        node,
        "--permission",
        "--max-old-space-size=192",
        "--disable-proto=throw",
        "--eval",
        resources.bootstrap_bytes.decode("utf-8"),
    ]
    svgs = []
    for _ in range(2):
        process = subprocess.run(command, input=frame, capture_output=True, timeout=10, check=True)
        svgs.append(decode_renderer_response(process.stdout, resources.runtime))
    assert svgs[0] == svgs[1]
    assert b"<script" not in svgs[0] and b"<foreignObject" not in svgs[0]
    if not empty:
        assert b"{a}&lt;script&gt;" in svgs[0]


@pytest.mark.parametrize("analysis_id", ["growth.v1", "concentration.v1", "lifecycle.v1"])
def test_renderer_budget_failure_is_safe_input_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    analysis_id: str,
) -> None:
    import importlib

    module = importlib.import_module(f"patent_analysis.analyses.{analysis_id.split('.')[0]}")
    monkeypatch.setattr(module, "MAX_EXPANDED_CONTRIBUTIONS", 1)
    roots = _roots(tmp_path)
    _csv(tmp_path / "input/input.csv", [("2024", "A"), ("2024", "B")])
    result = ToolHandlers(roots=roots).call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "input.csv", "spec": spec(analysis_id)},
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "input.invalid"
    assert str(tmp_path) not in repr(result)


@pytest.mark.parametrize("analysis_id", ["growth.v1", "lifecycle.v1"])
def test_all_contributing_labels_have_the_same_bound_before_top_n(
    tmp_path: Path,
    analysis_id: str,
) -> None:
    _csv(tmp_path / "input.csv", [("2024", "A"), ("2024", "A"), ("2024", "\U0001f9ea" * 4096)])
    request = spec(analysis_id)
    request["parameters"]["top_n"] = 1
    with pytest.raises(AnalysisContractError, match="analysis exceeds published limits"):
        run_analysis_csv("input.csv", canonical_json_bytes(request), allowed_root=tmp_path)
