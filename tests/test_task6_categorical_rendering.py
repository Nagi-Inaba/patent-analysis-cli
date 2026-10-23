from __future__ import annotations

from pathlib import Path

import pytest

from patent_analysis._render_canonical import canonical_json_bytes
from patent_analysis.render_errors import RenderError

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
            }
        ],
        "population": {
            "input_rows": 3,
            "visible_rows": 3,
            "invalid_year_rows": 0,
            "outside_year_range_rows": 0,
            "blank_series_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 3,
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


@pytest.mark.parametrize(
    ("document", "mark", "renderer_kind"),
    [
        (TIMELINE_RESULT, "series-line-svg.v1", "series.line.svg"),
        (TIMELINE_RESULT, "series-stacked-bar-svg.v1", "series.stacked-bar.svg"),
        (COMPOSITION_RESULT, "composition-bar-svg.v1", "composition.bar.svg"),
        (COMPOSITION_RESULT, "composition-pie-svg.v1", "composition.pie.svg"),
    ],
)
def test_prepare_categorical_render_closes_mark_and_profile(
    document: dict[str, object],
    mark: str,
    renderer_kind: str,
) -> None:
    from patent_analysis.rendering import _prepare_categorical_render

    prepared = _prepare_categorical_render(document, mark=mark)

    assert prepared.model_sha256
    assert prepared.spec_sha256
    assert prepared.model_bytes.startswith(b"{")
    assert prepared.spec_bytes.startswith(b"{")
    assert canonical_json_bytes(document) != prepared.model_bytes
    assert renderer_kind.encode("ascii") in prepared.spec_bytes
    assert b"categorical-svg-ja-jp-node24-echarts6.v1" in prepared.spec_bytes


def test_render_categorical_svg_rejects_cross_family_and_unknown_marks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.rendering as rendering

    monkeypatch.setattr(rendering, "require_supported_platform", lambda: None)

    with pytest.raises(RenderError) as caught:
        rendering.render_categorical_svg(
            canonical_json_bytes(TIMELINE_RESULT),
            mark="composition-bar-svg.v1",
            output_directory=tmp_path,
        )
    assert caught.value.code == "render.invalid"

    with pytest.raises(ValueError, match="categorical"):
        rendering.render_categorical_svg(
            canonical_json_bytes(TIMELINE_RESULT),
            mark="caller-echarts-option",
            output_directory=tmp_path,
        )


def test_render_categorical_svg_preserves_bounded_input_error(tmp_path: Path) -> None:
    from patent_analysis.rendering import (
        MAX_ANALYSIS_DOCUMENT_BYTES,
        render_categorical_svg,
    )

    with pytest.raises(RenderError) as caught:
        render_categorical_svg(
            b" " * (MAX_ANALYSIS_DOCUMENT_BYTES + 1),
            mark="series-line-svg.v1",
            output_directory=tmp_path,
        )

    assert caught.value.code == "input.invalid"


@pytest.mark.parametrize(
    ("document", "expected_mark"),
    [
        (TIMELINE_RESULT, "series-line-svg.v1"),
        (COMPOSITION_RESULT, "composition-bar-svg.v1"),
    ],
)
def test_render_analysis_svg_dispatches_categorical_results(
    document: dict[str, object],
    expected_mark: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.rendering as rendering

    received: dict[str, object] = {}

    def fake_categorical_renderer(
        analysis_document: bytes,
        *,
        mark: str,
        output_directory: str | Path,
        node_executable: str | Path | None = None,
        palette: str | None = None,
    ) -> dict[str, object]:
        received.update(
            analysis_document=analysis_document,
            mark=mark,
            output_directory=output_directory,
            node_executable=node_executable,
        )
        return {"status": "created", "mark": mark}

    monkeypatch.setattr(rendering, "render_categorical_svg", fake_categorical_renderer)
    raw = canonical_json_bytes(document)

    result = rendering.render_analysis_svg(
        raw,
        output_directory=tmp_path,
        node_executable="C:/node.exe",
    )

    assert result == {"status": "created", "mark": expected_mark}
    assert received == {
        "analysis_document": raw,
        "mark": expected_mark,
        "output_directory": tmp_path,
        "node_executable": "C:/node.exe",
    }


def test_render_analysis_svg_rejects_categorical_overlay(tmp_path: Path) -> None:
    import patent_analysis.rendering as rendering

    with pytest.raises(RenderError) as caught:
        rendering.render_analysis_svg(
            canonical_json_bytes(TIMELINE_RESULT),
            overlay_document=b"{}",
            output_directory=tmp_path,
        )

    assert caught.value.code == "render.invalid"
