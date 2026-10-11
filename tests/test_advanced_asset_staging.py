"""Verify explicitly generated candidates; metadata never activates a renderer."""
from __future__ import annotations

import ast
import hashlib
import json
import tomllib
from pathlib import Path
from types import MappingProxyType

import pytest
from advanced_inventory import ADVANCED_MARKS, INVENTOR_MARKS

from patent_analysis import advanced_presentation as presentation
from patent_analysis._render_canonical import canonical_json_bytes
from patent_analysis.advanced_bundle import decode_advanced_bundle
from patent_analysis.advanced_presentation import ADVANCED_PRESENTATIONS, advanced_marks_for
from patent_analysis.advanced_renderer_build import ADVANCED_BUILD

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "src" / "patent_analysis" / "renderer"
SCHEMAS = ROOT / "src" / "patent_analysis" / "schemas"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_staged_candidate_pins_match_generated_resources() -> None:
    candidate = RENDERER / "advanced-renderer-candidate-pins.json"
    if not candidate.is_file():
        pytest.skip("requires explicit advanced --stage-only build")
    pins = json.loads(candidate.read_bytes())
    expected_keys = {
        "archive_sha256", "manifest_sha256", "bootstrap_sha256", "bundle_sha256",
        "build_digest", "advanced-chart-model-v1.schema.json",
        "advanced-render-spec-v1.schema.json", "advanced-renderer-response.schema.json",
        "candidate_pin_version", "render_profile_id",
    }
    if "built_marks" in pins:
        expected_keys.add("built_marks")
        assert pins["built_marks"] == [*ADVANCED_MARKS, *INVENTOR_MARKS]
    assert set(pins) == expected_keys
    assert pins["candidate_pin_version"] == "1.0.0"
    assert pins["render_profile_id"] == "advanced-svg-ja-jp-node22-echarts6.v1"
    assert pins["archive_sha256"] == _sha256(RENDERER / "advanced-renderer.bundle.js.gz")
    manifest = RENDERER / "advanced-renderer-build-manifest.json"
    assert pins["manifest_sha256"] == _sha256(manifest)
    assert pins["bootstrap_sha256"] == _sha256(RENDERER / "advanced-bootstrap.js")
    bundle = decode_advanced_bundle(
        (RENDERER / "advanced-renderer.bundle.js.gz").read_bytes(), pins["bundle_sha256"],
    )
    assert pins["bundle_sha256"] == hashlib.sha256(bundle).hexdigest()
    content = json.loads(manifest.read_bytes())
    assert content["bootstrap_sha256"] == pins["bootstrap_sha256"]
    assert content["renderer_bundle_sha256"] == pins["bundle_sha256"]
    assert pins["build_digest"] == hashlib.sha256(canonical_json_bytes(content)).hexdigest()
    for name in (
        "advanced-chart-model-v1.schema.json", "advanced-render-spec-v1.schema.json",
        "advanced-renderer-response.schema.json",
    ):
        assert pins[name] == _sha256(SCHEMAS / name)


@pytest.mark.parametrize("activation", [
    ADVANCED_BUILD, None,
    {"archive_sha256": "legacy-without-inventory"},
    {"built_marks": []},
    {"built_marks": ["inventor-network-svg.v1"]},
])
def test_candidate_metadata_is_not_the_runtime_activation_authority(
    monkeypatch, activation,
) -> None:
    # Also valid in an explicitly built Windows acceptance checkout: do not force
    # an activated installation back to JSON-only just to satisfy a staging test.
    future = presentation.AdvancedPresentation(
        "future-native.v1", "future-native-svg.v1", "network", "Unbuilt future", "inventor-network",
    )
    definitions = {**ADVANCED_PRESENTATIONS, future.analysis_id: future}
    monkeypatch.setattr(presentation, "ADVANCED_PRESENTATIONS", MappingProxyType(definitions))
    monkeypatch.setattr(presentation, "ADVANCED_BUILD", activation)
    built = () if activation is None else activation.get("built_marks", ADVANCED_MARKS)
    for analysis_id, definition in definitions.items():
        expected = (definition.mark,) if definition.mark in built else ()
        assert advanced_marks_for(analysis_id) == expected
    assert advanced_marks_for("inventor-mobility-evidence.v1") == ()


def test_advanced_staging_resources_are_wheel_package_data() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = project["tool"]["setuptools"]["package-data"]["patent_analysis"]
    assert {"renderer/*.js", "renderer/*.json", "renderer/*.gz"} <= set(patterns)


def test_committed_activation_matches_candidate_pins_and_style_budget() -> None:
    path = ROOT / "src/patent_analysis/advanced_renderer_build.py"
    text = path.read_text(encoding="utf-8")
    assignment, = (node for node in ast.parse(text).body if isinstance(node, ast.AnnAssign))
    assert isinstance(assignment.target, ast.Name) and assignment.target.id == "ADVANCED_BUILD"
    pins = ast.literal_eval(assignment.value)
    assert isinstance(pins, dict)
    candidate = json.loads((RENDERER / "advanced-renderer-candidate-pins.json").read_bytes())
    assert pins == {k: v for k, v in candidate.items()
                    if k not in {"candidate_pin_version", "render_profile_id"}}
    assert all(len(line) <= 100 for line in text.splitlines())
