from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from patent_analysis._render_canonical import canonical_json_bytes

TIMELINE_RESULT = {
    "analysis_id": "timeline.v1",
    "algorithm_version": "1.0.0",
    "result_variant": "series",
    "population": {"input_rows": 3, "analyzed_rows": 3, "excluded_rows": 0},
    "data": {
        "schema_version": "1.0.0",
        "analysis_id": "timeline.v1",
        "algorithm_version": "1.0.0",
        "measure": {"mode": "count", "role": None},
        "x": ["2020", "2021"],
        "series": [
            {
                "label": "A社",
                "values": [1, 2],
                "row_counts": [1, 2],
                "is_other": False,
            },
            {
                "label": "B社",
                "values": [1, 0],
                "row_counts": [1, 0],
                "is_other": False,
            },
        ],
        "population": {
            "input_rows": 3,
            "visible_rows": 3,
            "invalid_year_rows": 0,
            "outside_year_range_rows": 0,
            "blank_series_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 4,
        "limits": {"max_top_n": 100, "max_expanded_contributions": 1_000_000},
    },
    "warnings": [],
}

COMPOSITION_RESULT = {
    "analysis_id": "composition.v1",
    "algorithm_version": "1.0.0",
    "result_variant": "composition",
    "population": {"input_rows": 3, "analyzed_rows": 3, "excluded_rows": 0},
    "data": {
        "schema_version": "1.0.0",
        "analysis_id": "composition.v1",
        "algorithm_version": "1.0.0",
        "measure": {"mode": "sum", "role": "score"},
        "items": [
            {
                "label": "A社",
                "value": 20,
                "row_count": 2,
                "share": 2 / 3,
                "share_basis": "row_count",
                "is_other": False,
            },
            {
                "label": "B社",
                "value": -2,
                "row_count": 1,
                "share": 1 / 3,
                "share_basis": "row_count",
                "is_other": False,
            },
        ],
        "population": {
            "input_rows": 3,
            "visible_rows": 3,
            "blank_role_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 3,
        "limits": {"max_top_n": 100, "max_expanded_contributions": 500_000},
    },
    "warnings": [],
}

_CASES = (
    (TIMELINE_RESULT, "series-line-svg.v1"),
    (TIMELINE_RESULT, "series-stacked-bar-svg.v1"),
    (COMPOSITION_RESULT, "composition-bar-svg.v1"),
    (COMPOSITION_RESULT, "composition-pie-svg.v1"),
)


@pytest.mark.skipif(
    sys.platform not in {"win32", "darwin"} or shutil.which("node") is None,
    reason="trusted renderer E2E requires Windows x64 or macOS and exact local Node",
)
def test_real_node_categorical_marks_create_then_reuse(tmp_path: Path) -> None:
    from patent_analysis.rendering import render_categorical_svg

    node = shutil.which("node")
    assert node is not None
    assert subprocess.check_output([node, "--version"], text=True).strip() == "v24.22.1"

    artifact_ids: set[str] = set()
    forbidden = (
        b"<script",
        b"<foreignObject",
        b"xmlns:xlink",
        b"baseProfile=",
        b"xml:space",
        b"<linearGradient",
        b"<stop",
    )

    for document, mark in _CASES:
        output = tmp_path / mark.removesuffix(".v1")
        output.mkdir()
        raw = canonical_json_bytes(document)

        first = render_categorical_svg(
            raw,
            mark=mark,
            output_directory=output,
            node_executable=node,
        )
        second = render_categorical_svg(
            raw,
            mark=mark,
            output_directory=output,
            node_executable=node,
        )

        assert first["status"] == "created"
        assert second["status"] == "reused"
        assert first["mark"] == second["mark"] == mark
        assert first["artifact_id"] == second["artifact_id"]
        assert first["svg_sha256"] == second["svg_sha256"]
        assert first["renderer_build_digest"] == second["renderer_build_digest"]

        svg_path = output / str(first["svg"])
        svg = svg_path.read_bytes()
        assert hashlib.sha256(svg).hexdigest() == first["svg_sha256"]
        assert svg.startswith(b"<svg")
        for token in forbidden:
            assert token not in svg

        artifact_ids.add(str(first["artifact_id"]))

    assert len(artifact_ids) == len(_CASES)
