"""The colour palette choice: closed set, default-preserving specs, and real renders."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from functools import cache, lru_cache
from pathlib import Path

import pytest

from patent_analysis._render_canonical import canonical_json_bytes
from patent_analysis.categorical_chart_model import (
    build_categorical_render_spec as build_family_render_spec,
)
from patent_analysis.chart_model import build_ranking_render_spec
from patent_analysis.chart_models._common import validate_schema
from patent_analysis.chart_models.advanced import build_advanced_render_spec
from patent_analysis.chart_models.composition import build_composition_render_spec
from patent_analysis.chart_models.matrix import build_matrix_render_spec
from patent_analysis.chart_models.points import build_points_render_spec
from patent_analysis.chart_models.series import build_series_render_spec
from patent_analysis.render_errors import RenderError
from patent_analysis.render_palettes import (
    DEFAULT_RENDER_PALETTE,
    RENDER_PALETTES,
    apply_render_palette,
)
from tests.test_matrix_chart_model import MATRIX_RESULT

ALTERNATES = tuple(palette for palette in RENDER_PALETTES if palette != DEFAULT_RENDER_PALETTE)

BUILDERS = {
    "ranking": (lambda palette: build_ranking_render_spec(row_count=3, palette=palette),
                "render-spec.schema.json"),
    "matrix-bubble": (
        lambda palette: build_matrix_render_spec(
            mark="matrix-bubble-svg.v1", x_count=2, y_count=2, palette=palette
        ),
        "matrix-render-spec-v1.schema.json",
    ),
    "matrix-heatmap": (
        lambda palette: build_matrix_render_spec(
            mark="matrix-heatmap-svg.v1", x_count=2, y_count=2, palette=palette
        ),
        "matrix-render-spec-v1.schema.json",
    ),
    "series": (
        lambda palette: build_series_render_spec(
            mark="series-line-svg.v1", x_count=3, series_count=2, palette=palette
        ),
        "categorical-render-spec-v1.schema.json",
    ),
    "composition": (
        lambda palette: build_composition_render_spec(
            mark="composition-bar-svg.v1", item_count=3, palette=palette
        ),
        "categorical-render-spec-v1.schema.json",
    ),
    "categorical-wrapper": (
        lambda palette: build_family_render_spec(
            mark="series-line-svg.v1",
            chart_model={"x": ["2020"], "series": [{}]},
            palette=palette,
        ),
        "categorical-render-spec-v1.schema.json",
    ),
    "points": (
        lambda palette: build_points_render_spec(
            mark="points-bubble-svg.v1", point_count=2, palette=palette
        ),
        "points-render-spec-v1.schema.json",
    ),
    "advanced": (
        lambda palette: build_advanced_render_spec(palette),
        "advanced-render-spec-v1.schema.json",
    ),
}


def test_palette_set_is_closed_and_led_by_the_default() -> None:
    assert RENDER_PALETTES == ("standard", "colorblind", "monochrome", "high-contrast")
    assert DEFAULT_RENDER_PALETTE == "standard"


@pytest.mark.parametrize("bad", ["neon", "", "Standard", 1, ["standard"], b"standard"])
def test_apply_render_palette_rejects_anything_outside_the_set(bad: object) -> None:
    with pytest.raises(ValueError):
        apply_render_palette({}, bad)  # type: ignore[arg-type]


def test_apply_render_palette_leaves_the_default_out_of_the_spec() -> None:
    assert apply_render_palette({"a": 1}, None) == {"a": 1}
    assert apply_render_palette({"a": 1}, "standard") == {"a": 1}
    assert apply_render_palette({"a": 1}, "monochrome") == {"a": 1, "palette": "monochrome"}


@pytest.mark.parametrize("name", sorted(BUILDERS))
def test_every_family_spec_records_only_a_non_default_palette(name: str) -> None:
    build, schema = BUILDERS[name]
    default = build(None)

    assert "palette" not in default
    # Choosing "standard" explicitly must not change the spec bytes (and so not its hash).
    assert canonical_json_bytes(build("standard")) == canonical_json_bytes(default)
    for palette in ALTERNATES:
        spec = build(palette)
        assert spec["palette"] == palette
        assert {key: value for key, value in spec.items() if key != "palette"} == default
        validate_schema(spec, schema)
    with pytest.raises(ValueError):
        build("neon")


@pytest.mark.parametrize("schema", sorted({schema for _build, schema in BUILDERS.values()}))
def test_render_spec_schemas_accept_only_listed_palettes(schema: str) -> None:
    build = next(build for build, name in BUILDERS.values() if name == schema)
    spec = build("colorblind")

    for bad in ("neon", "", 1, None):
        with pytest.raises(ValueError):
            validate_schema({**spec, "palette": bad}, schema)


def test_render_rejects_an_unknown_palette_before_touching_the_output(tmp_path: Path) -> None:
    from patent_analysis.api import render_analysis_svg

    with pytest.raises(RenderError) as caught:
        render_analysis_svg(
            canonical_json_bytes(MATRIX_RESULT),
            mark="matrix-bubble-svg.v1",
            output_directory=tmp_path,
            palette="neon",
        )

    assert caught.value.code == "render.invalid"
    assert list(tmp_path.iterdir()) == []


# --- real renders (trusted-local Windows x64 / macOS Node 22.23.4) -------------------------------

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
RENDER_CASES = (
    ("ranking.v1", None),
    ("matrix.v1", "matrix-bubble-svg.v1"),
    ("matrix.v1", "matrix-heatmap-svg.v1"),
    ("timeline.v1", "series-line-svg.v1"),
    ("timeline.v1", "series-stacked-bar-svg.v1"),
    ("composition.v1", "composition-pie-svg.v1"),
    ("lifecycle.v1", None),
    ("cooccurrence.v1", None),
    ("inventor-tracking.v1", None),
)


@lru_cache(maxsize=1)
def _exact_renderer_node() -> str | None:
    if sys.platform not in {"win32", "darwin"}:
        return None
    node = shutil.which("node")
    if node is None:
        return None
    probe = subprocess.run(
        [node, "-p", "process.versions.node + '/' + process.arch"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return node if probe.returncode == 0 and probe.stdout.strip() == (
        "22.23.4/arm64" if platform.machine().lower() == "arm64" else "22.23.4/x64"
    ) else None


@cache
def _analysis_document(analysis_id: str) -> bytes:
    from patent_analysis import api

    catalog = json.loads((EXAMPLES / "analysis-catalog.json").read_text(encoding="utf-8"))
    case = next(item for item in catalog["cases"] if item["analysis_id"] == analysis_id)
    result = api.run_analysis(
        str(EXAMPLES / case["csv"]),
        (EXAMPLES / case["spec"]).read_bytes(),
        allowed_root=EXAMPLES,
    )
    return canonical_json_bytes(result)


@pytest.mark.skipif(
    _exact_renderer_node() is None,
    reason="requires Windows x64 or macOS and Node 22.23.4",
)
@pytest.mark.parametrize(("analysis_id", "mark"), RENDER_CASES)
def test_every_palette_renders_each_family_and_changes_only_the_colours(
    tmp_path: Path, analysis_id: str, mark: str | None
) -> None:
    from patent_analysis.api import render_analysis_svg

    document = _analysis_document(analysis_id)
    artifacts: dict[str, bytes] = {}
    for palette in (None, "standard", *ALTERNATES):
        output = tmp_path / str(palette)
        output.mkdir()
        receipt = render_analysis_svg(
            document,
            mark=mark,
            output_directory=output,
            node_executable=_exact_renderer_node(),
            palette=palette,
        )
        assert receipt["ok"] is True
        artifacts[str(palette)] = (output / str(receipt["svg"])).read_bytes()

    # "standard" is the default: same bytes whether named or left out.
    assert artifacts["standard"] == artifacts["None"]
    seen = {artifacts["None"]}
    for palette in ALTERNATES:
        assert artifacts[palette] not in seen
        seen.add(artifacts[palette])
        assert b"<svg" in artifacts[palette]
