from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree

import pytest
from advanced_inventory import ADVANCED_MARKS, INVENTOR_MARKS

from patent_analysis._render_canonical import canonical_json_bytes
from tests.test_matrix_chart_model import MATRIX_RESULT


def test_renderer_registry_exposes_all_completed_closed_marks() -> None:
    from patent_analysis.renderer_registry import (
        get_renderer_definition,
        list_renderer_definitions,
    )

    definitions = list_renderer_definitions()
    assert tuple(definition.mark for definition in definitions) == (
        "ranking-svg.v1",
        "matrix-bubble-svg.v1",
        "matrix-heatmap-svg.v1",
        "series-line-svg.v1",
        "series-stacked-bar-svg.v1",
        "composition-bar-svg.v1",
        "composition-pie-svg.v1",
        "points-bubble-svg.v1",
        *ADVANCED_MARKS,
        *INVENTOR_MARKS,
    )
    assert get_renderer_definition("matrix-bubble-svg.v1").result_variant == "matrix"
    assert get_renderer_definition("matrix-heatmap-svg.v1").result_variant == "matrix"
    assert get_renderer_definition("ranking-svg.v1").result_variant == "ranking"
    assert get_renderer_definition("series-line-svg.v1").result_variant == "series"
    assert get_renderer_definition("series-stacked-bar-svg.v1").result_variant == "series"
    assert get_renderer_definition("composition-bar-svg.v1").result_variant == "composition"
    assert get_renderer_definition("composition-pie-svg.v1").result_variant == "composition"
    with pytest.raises(ValueError):
        get_renderer_definition("caller-echarts-option")


def test_matrix_renderer_resources_are_separate_from_ranking_resources() -> None:
    from patent_analysis.renderer_resources import (
        load_verified_matrix_renderer_resources,
        load_verified_renderer_resources,
    )

    ranking = load_verified_renderer_resources()
    matrix = load_verified_matrix_renderer_resources()

    assert matrix.runtime.render_profile_id == "matrix-svg-ja-jp-node22-echarts6.v1"
    assert matrix.runtime.renderer_build_digest != ranking.runtime.renderer_build_digest
    assert matrix.bootstrap_bytes != ranking.bootstrap_bytes
    assert matrix.bundle_bytes != ranking.bundle_bytes


def test_renderer_response_schemas_are_closed_per_profile() -> None:
    from patent_analysis.renderer_resources import _load_verified_renderer_schema_bytes

    ranking_schema = json.loads(
        _load_verified_renderer_schema_bytes("renderer-response.schema.json")
    )
    matrix_schema = json.loads(
        _load_verified_renderer_schema_bytes("matrix-renderer-response.schema.json")
    )
    ranking_profile = ranking_schema["$defs"]["runtime"]["properties"]["render_profile_id"]
    matrix_profile = matrix_schema["$defs"]["runtime"]["properties"]["render_profile_id"]

    assert ranking_profile == {"const": "ranking-svg-ja-jp-node22-echarts6.v1"}
    assert matrix_profile == {"const": "matrix-svg-ja-jp-node22-echarts6.v1"}


def test_render_analysis_svg_rejects_matrix_overlay_and_unknown_mark(
    tmp_path: Path,
) -> None:
    from patent_analysis.api import render_analysis_svg

    document = canonical_json_bytes(MATRIX_RESULT)
    with pytest.raises(ValueError):
        render_analysis_svg(
            document,
            mark="matrix-bubble-svg.v1",
            overlay={"rows": []},
            output_directory=tmp_path,
        )
    with pytest.raises(ValueError):
        render_analysis_svg(
            document,
            mark="caller-echarts-option",
            output_directory=tmp_path,
        )


def test_public_render_facade_preserves_bounded_input_error(tmp_path: Path) -> None:
    from patent_analysis.api import render_analysis_svg
    from patent_analysis.render_errors import RenderError
    from patent_analysis.rendering import MAX_ANALYSIS_DOCUMENT_BYTES

    with pytest.raises(RenderError) as caught:
        render_analysis_svg(
            b" " * (MAX_ANALYSIS_DOCUMENT_BYTES + 1),
            output_directory=tmp_path,
        )

    assert caught.value.code == "input.invalid"


def test_matrix_value_labels_are_a_bubble_only_choice_that_keeps_default_spec_bytes() -> None:
    from patent_analysis.chart_models.matrix import build_matrix_render_spec

    def spec(mark: str, value_labels: str | None = None) -> dict[str, object]:
        return build_matrix_render_spec(mark=mark, x_count=2, y_count=2, value_labels=value_labels)

    default = spec("matrix-bubble-svg.v1")
    assert "value_labels" not in default
    # "hidden" is the default, so choosing it must not change the spec (and its hash).
    assert canonical_json_bytes(spec("matrix-bubble-svg.v1", "hidden")) == canonical_json_bytes(
        default
    )
    assert spec("matrix-bubble-svg.v1", "shown")["value_labels"] == "shown"
    assert spec("matrix-heatmap-svg.v1") == spec("matrix-heatmap-svg.v1", None)
    for mark, choice in (
        ("matrix-heatmap-svg.v1", "shown"),
        ("matrix-heatmap-svg.v1", "hidden"),
        ("matrix-bubble-svg.v1", "loud"),
        ("matrix-bubble-svg.v1", ""),
    ):
        with pytest.raises(ValueError):
            spec(mark, choice)


@pytest.mark.parametrize(
    ("document", "mark", "value_labels"),
    [
        (canonical_json_bytes(MATRIX_RESULT), "matrix-heatmap-svg.v1", "shown"),
        (canonical_json_bytes(MATRIX_RESULT), "matrix-bubble-svg.v1", "loud"),
        (canonical_json_bytes({"analysis_id": "ranking.v1"}), None, "shown"),
    ],
)
def test_render_rejects_value_labels_outside_the_matrix_bubble(
    tmp_path: Path, document: bytes, mark: str | None, value_labels: str
) -> None:
    from patent_analysis.api import render_analysis_svg
    from patent_analysis.render_errors import RenderError

    with pytest.raises(RenderError) as caught:
        render_analysis_svg(
            document, mark=mark, output_directory=tmp_path, value_labels=value_labels
        )

    assert caught.value.code == "render.invalid"
    assert list(tmp_path.iterdir()) == []


# --- pie bubbles (real renders with the exact Node 22.19.0) -----------------------------------

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@lru_cache(maxsize=1)
def _exact_renderer_node() -> str | None:
    if sys.platform not in {"win32", "darwin"}:
        return None
    node = os.environ.get("PATENT_ANALYSIS_TEST_NODE") or shutil.which("node")
    if node is None:
        return None
    probe = subprocess.run(
        [node, "-p", "process.versions.node + '/' + process.arch"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    arch = "arm64" if platform.machine().lower() == "arm64" else "x64"
    return node if probe.returncode == 0 and probe.stdout.strip() == f"22.19.0/{arch}" else None


requires_renderer_node = pytest.mark.skipif(
    _exact_renderer_node() is None,
    reason="requires Windows x64 or macOS and the exact Node 22.19.0",
)


def _analysis_document(spec_name: str) -> bytes:
    from patent_analysis import api

    result = api.run_analysis(
        str(EXAMPLES / "advanced/patents.csv"),
        (EXAMPLES / spec_name).read_bytes(),
        allowed_root=EXAMPLES,
    )
    return canonical_json_bytes(result)


@requires_renderer_node
def test_pie_matrix_example_renders_slices_and_a_legend_then_reuses_the_svg(
    tmp_path: Path,
) -> None:
    from patent_analysis.api import render_analysis_svg

    document = _analysis_document("basic/matrix-pie.json")
    first = render_analysis_svg(
        document,
        mark="matrix-bubble-svg.v1",
        output_directory=tmp_path,
        node_executable=_exact_renderer_node(),
    )
    again = render_analysis_svg(
        document,
        mark="matrix-bubble-svg.v1",
        output_directory=tmp_path,
        node_executable=_exact_renderer_node(),
    )

    assert first["ok"] is True and first["status"] == "created"
    assert again["status"] == "reused" and again["svg"] == first["svg"]
    svg = (tmp_path / str(first["svg"])).read_bytes().decode("utf-8")
    root = ElementTree.fromstring(svg)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    texts = [element.text for element in root.iterfind(".//svg:text", namespace)]
    # The legend names the pie role and every pie value the example keeps (top three plus rest).
    for label in ("円内：year", "2024", "2018", "2020", "その他（上位外）"):
        assert label in texts
    # Cells with several slices are drawn as arcs; single-slice cells as circles.
    assert any("A" in (path.get("d") or "") for path in root.iterfind(".//svg:path", namespace))
    assert root.findall(".//svg:circle", namespace)


@requires_renderer_node
def test_plain_matrix_still_renders_without_pie_marks(tmp_path: Path) -> None:
    from patent_analysis.api import render_analysis_svg

    receipt = render_analysis_svg(
        _analysis_document("basic/matrix.json"),
        mark="matrix-bubble-svg.v1",
        output_directory=tmp_path,
        node_executable=_exact_renderer_node(),
    )

    svg = (tmp_path / str(receipt["svg"])).read_bytes().decode("utf-8")
    assert "円内：" not in svg
    assert "件数は円の面積で表現" in svg


@requires_renderer_node
def test_pie_example_renders_with_every_palette_and_the_heatmap_ignores_the_pie(
    tmp_path: Path,
) -> None:
    from patent_analysis.api import render_analysis_svg

    document = _analysis_document("basic/matrix-pie.json")
    rendered = set()
    for palette in (None, "colorblind", "monochrome", "high-contrast"):
        folder = tmp_path / str(palette)
        folder.mkdir()
        receipt = render_analysis_svg(
            document,
            mark="matrix-bubble-svg.v1",
            output_directory=folder,
            node_executable=_exact_renderer_node(),
            palette=palette,
            value_labels="shown",
        )
        assert receipt["ok"] is True
        rendered.add((folder / str(receipt["svg"])).read_bytes())
    assert len(rendered) == 4

    heatmap = render_analysis_svg(
        document,
        mark="matrix-heatmap-svg.v1",
        output_directory=tmp_path,
        node_executable=_exact_renderer_node(),
    )
    assert "円内：" not in (tmp_path / str(heatmap["svg"])).read_bytes().decode("utf-8")
