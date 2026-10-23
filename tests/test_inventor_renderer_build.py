"""Real pinned builds use isolated output roots and never rewrite checkout files."""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "renderer/scripts/build-advanced-bundle.mjs"
BUILT_MARKS = [
    "growth-quadrant-svg.v1", "entry-exit-svg.v1", "citation-svg.v1",
    "matrix-composition-svg.v1", "new-entrants-svg.v1", "compara-svg.v1",
    "cooccurrence-svg.v1", "collaboration-network-svg.v1", "uniqueness-svg.v1",
    "shared-involvement-svg.v1", "inventor-tracking-svg.v1",
    "inventor-network-svg.v1", "inventor-ego-network-svg.v1", "inventor-technology-svg.v1",
    "inventor-activity-svg.v1", "inventor-cluster-flow-svg.v1", "inventor-similarity-svg.v1",
    "inventor-impact-svg.v1", "inventor-mobility-svg.v1", "inventor-mobility-flow-svg.v1",
]


@pytest.fixture(scope="module")
def pinned_node() -> str:
    node = shutil.which("node")
    if node is None:
        pytest.skip("requires Node 24.22.1 (x64 or macOS arm64) in the build workspace")
    probe = subprocess.run(
        [node, "-p", "process.versions.node + '/' + process.arch"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if probe.returncode or probe.stdout.strip() not in (
        {"24.22.1/x64", "24.22.1/arm64"} if sys.platform == "darwin" else {"24.22.1/x64"}
    ):
        pytest.skip("requires exact Node 24.22.1 (x64 or macOS arm64)")
    if not (ROOT / "renderer/node_modules/vite/package.json").is_file():
        pytest.skip("requires the already-installed locked renderer build dependencies")
    return node


def _build(node: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [node, str(SCRIPT), *args], cwd=ROOT,
        capture_output=True, text=True, timeout=120, check=False,
    )


def _checkout_snapshot() -> dict[str, tuple[str, int]]:
    paths = [
        ROOT / "src/patent_analysis/advanced_renderer_build.py",
        ROOT / "renderer/src/generated/advanced-standalone-validators.js",
        *sorted((ROOT / "src/patent_analysis/renderer").glob("advanced-*")),
    ]
    return {
        str(path): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in paths if path.is_file()
    }


def test_inventor_sources_build_with_the_closed_runtime_module_policy(pinned_node, tmp_path):
    output = tmp_path / "isolated-package"
    output.mkdir()
    activation = output / "advanced_renderer_build.py"
    activation.write_text("sentinel activation\n", encoding="utf-8")
    before = _checkout_snapshot()
    result = _build(pinned_node, "--stage-only", "--output-root", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "advanced renderer staged:" in result.stdout
    assert (output / "renderer/advanced-renderer-candidate-pins.json").is_file()
    assert activation.read_text(encoding="utf-8") == "sentinel activation\n"
    assert _checkout_snapshot() == before


def test_verified_build_activates_only_the_finite_source_supported_marks(
    pinned_node, tmp_path, monkeypatch,
):
    from patent_analysis import advanced_renderer_resources as resources

    output = tmp_path / "isolated-package"
    before = _checkout_snapshot()
    result = _build(pinned_node, "--output-root", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    text = (output / "advanced_renderer_build.py").read_text(encoding="utf-8")
    assignment, = (node for node in ast.parse(text).body if isinstance(node, ast.AnnAssign))
    pins = ast.literal_eval(assignment.value)
    assert pins.get("built_marks") == BUILT_MARKS
    assert ast.unparse(assignment.annotation) == "dict[str, str | list[str]] | None"
    assert all(len(line) <= 100 for line in text.splitlines())
    candidate = json.loads((output / "renderer/advanced-renderer-candidate-pins.json").read_bytes())
    assert pins == {key: value for key, value in candidate.items()
                    if key not in {"candidate_pin_version", "render_profile_id"}}
    monkeypatch.setattr(resources, "ADVANCED_BUILD", pins)
    monkeypatch.setattr(resources, "_renderer_resource_root", lambda: output / "renderer")
    verified = resources.load_verified_advanced_renderer_resources()
    assert verified.renderer_build_digest == pins["build_digest"]
    assert hashlib.sha256(verified.bundle_bytes).hexdigest() == pins["bundle_sha256"]
    assert _checkout_snapshot() == before


@pytest.mark.parametrize("name", [
    "advanced-renderer.bundle.js.gz", "advanced-bootstrap.js",
    "advanced-renderer-build-manifest.json", "advanced-renderer-candidate-pins.json",
])
def test_changed_output_is_rejected_before_activation(pinned_node, tmp_path, name):
    output = tmp_path / "isolated-package"
    output.mkdir()
    activation = output / "advanced_renderer_build.py"
    activation.write_text("sentinel activation\n", encoding="utf-8")
    # Real filesystem fault injection in a child, not a fake build or fake bundle.
    preload = tmp_path / "corrupt-output.mjs"
    preload.write_text(
        'import fs from "node:fs/promises";\n'
        'import { syncBuiltinESMExports } from "node:module";\n'
        'const original = fs.writeFile;\n'
        'fs.writeFile = async (path, ...args) => {\n'
        '  await original(path, ...args);\n'
        f'  if (String(path).endsWith({json.dumps(name)})) '
        'await original(path, "corrupted output");\n'
        '};\n'
        'syncBuiltinESMExports();\n', encoding="utf-8",
    )
    before = _checkout_snapshot()
    result = subprocess.run(
        [pinned_node, "--import", preload.as_uri(), str(SCRIPT), "--output-root", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Advanced output verification failed" in result.stderr
    assert activation.read_text(encoding="utf-8") == "sentinel activation\n"
    assert _checkout_snapshot() == before


@pytest.mark.parametrize("failure", ["interrupted", "corrupted"])
def test_activation_publication_is_atomic_and_verified(pinned_node, tmp_path, failure):
    output = tmp_path / "isolated-package"
    output.mkdir()
    activation = output / "advanced_renderer_build.py"
    activation.write_text("sentinel activation\n", encoding="utf-8")
    preload = tmp_path / "fail-activation.mjs"
    preload.write_text(
        'import fs from "node:fs/promises";\n'
        'import { syncBuiltinESMExports } from "node:module";\n'
        'const original = fs.writeFile;\n'
        'fs.writeFile = async (path, ...args) => {\n'
        '  if (String(path).includes("advanced_renderer_build.py")) {\n'
        '    await original(path, "partial activation");\n'
        + ('    throw new Error("interrupted activation write");\n' if failure == "interrupted"
           else '    return;\n')
        + '  }\n  await original(path, ...args);\n};\nsyncBuiltinESMExports();\n',
        encoding="utf-8",
    )
    before = _checkout_snapshot()
    result = subprocess.run(
        [pinned_node, "--import", preload.as_uri(), str(SCRIPT), "--output-root", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert activation.read_text(encoding="utf-8") == "sentinel activation\n"
    assert sorted(path.name for path in output.iterdir()) == [
        "advanced_renderer_build.py", "renderer",
    ]
    assert _checkout_snapshot() == before


def test_schema_change_during_build_cannot_activate_mismatched_validator_pins(
    pinned_node, tmp_path,
):
    output = tmp_path / "isolated-package"
    output.mkdir()
    activation = output / "advanced_renderer_build.py"
    activation.write_text("sentinel activation\n", encoding="utf-8")
    preload = tmp_path / "change-schema.mjs"
    preload.write_text(
        'import fs from "node:fs/promises";\n'
        'import { syncBuiltinESMExports } from "node:module";\n'
        'const original = fs.readFile;\nlet reads = 0;\n'
        'fs.readFile = async (path, ...args) => {\n'
        '  const bytes = await original(path, ...args);\n'
        '  if (String(path).endsWith("advanced-chart-model-v1.schema.json") && ++reads > 1) {\n'
        '    return typeof bytes === "string" ? bytes + " " '
        ': Buffer.concat([bytes, Buffer.from(" ")]);\n'
        '  }\n  return bytes;\n};\nsyncBuiltinESMExports();\n', encoding="utf-8",
    )
    before = _checkout_snapshot()
    result = subprocess.run(
        [pinned_node, "--import", preload.as_uri(), str(SCRIPT), "--output-root", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Advanced schema changed during build" in result.stderr
    assert activation.read_text(encoding="utf-8") == "sentinel activation\n"
    assert _checkout_snapshot() == before


@pytest.mark.parametrize(("args", "message"), [
    (["--unknown"], "Unknown advanced build argument"),
    (["--stage-only", "trailing"], "Unknown advanced build argument"),
    (["--stage-only", "--stage-only"], "Duplicate advanced build argument"),
    (["--output-root"], "Output root requires an absolute directory"),
    (["--output-root", "relative"], "Output root requires an absolute directory"),
    (["--output-root", ""], "Output root requires an absolute directory"),
    (["--output-root", str(ROOT)], "Explicit output root must be outside the checkout"),
])
def test_invalid_build_arguments_fail_without_writing_outputs(pinned_node, args, message):
    before = _checkout_snapshot()
    result = _build(pinned_node, *args)
    assert result.returncode != 0
    assert result.stdout == ""
    assert message in result.stderr
    assert _checkout_snapshot() == before


def test_duplicate_output_roots_are_rejected_before_writes(pinned_node, tmp_path):
    output = str(tmp_path / "isolated-package")
    before = _checkout_snapshot()
    result = _build(pinned_node, "--output-root", output, "--output-root", output)
    assert result.returncode != 0
    assert "Duplicate advanced build argument" in result.stderr
    assert not Path(output).exists()
    assert _checkout_snapshot() == before


@pytest.mark.parametrize(("property_name", "value"), [
    ("version", "v22.20.0"), ("arch", "ia32"),
])
def test_build_enforces_real_node_policy_before_any_output(
    pinned_node, tmp_path, property_name, value,
):
    output = tmp_path / "isolated-package"
    preload = tmp_path / "unsupported-node.mjs"
    preload.write_text(
        f"Object.defineProperty(process, {json.dumps(property_name)}, "
        f"{{ value: {json.dumps(value)} }});\n", encoding="utf-8",
    )
    before = _checkout_snapshot()
    result = subprocess.run(
        [pinned_node, "--import", preload.as_uri(), str(SCRIPT), "--output-root", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode != 0
    assert "Requires Node 24.22.1 (x64 or macOS arm64)" in result.stderr
    assert not output.exists()
    assert _checkout_snapshot() == before


def test_release_inventory_expects_only_nine_native_inventor_svg_marks():
    import advanced_inventory as inventory

    expected = BUILT_MARKS[11:]
    capabilities = inventory.expected_inventor_capabilities()
    assert [entry["render_marks"] for entry in capabilities] == [
        *([mark] for mark in expected), [],
    ]
    assert inventory.INVENTOR_MARKS == tuple(expected)
    assert inventory.MCP_MARKS[-9:] == tuple(expected)
    assert "inventor-mobility-evidence-svg.v1" not in inventory.MCP_MARKS
    assert inventory.ADVANCED_MARKS == tuple(BUILT_MARKS[:11])


def test_interrupted_output_write_never_creates_an_activation(pinned_node, tmp_path):
    output = tmp_path / "isolated-package"
    (output / "renderer/advanced-renderer.bundle.js.gz").mkdir(parents=True)
    before = _checkout_snapshot()
    result = _build(pinned_node, "--output-root", str(output))
    assert result.returncode != 0
    assert not (output / "advanced_renderer_build.py").exists()
    assert _checkout_snapshot() == before


@pytest.mark.parametrize(("name", "replacement", "message"), [
    ("advanced-chart-model-v1.schema.json", None, "Closed validator mark inventory changed"),
    ("advanced-inventor-options.ts", "inventor-future-svg.v1",
     "Inventor source mark inventory changed"),
])
def test_growing_declarations_cannot_expand_the_reviewed_build_inventory(
    pinned_node, tmp_path, name, replacement, message,
):
    output = tmp_path / "isolated-package"
    preload = tmp_path / "expand-inventory.mjs"
    transform = (
        'const model = JSON.parse(bytes); model.anyOf.push(model.anyOf[0]); '
        'return Buffer.from(JSON.stringify(model));'
        if replacement is None else
        f'return String(bytes).replace("inventor-network-svg.v1", {json.dumps(replacement)});'
    )
    preload.write_text(
        'import fs from "node:fs/promises";\n'
        'import { syncBuiltinESMExports } from "node:module";\n'
        'const original = fs.readFile;\n'
        'fs.readFile = async (path, ...args) => {\n'
        '  const bytes = await original(path, ...args);\n'
        f'  if (String(path).endsWith({json.dumps(name)})) {{ {transform} }}\n'
        '  return bytes;\n};\nsyncBuiltinESMExports();\n', encoding="utf-8",
    )
    before = _checkout_snapshot()
    result = subprocess.run(
        [pinned_node, "--import", preload.as_uri(), str(SCRIPT), "--output-root", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode != 0
    assert message in result.stderr
    assert not output.exists()
    assert _checkout_snapshot() == before


def test_output_changed_while_preparing_activation_is_not_published(pinned_node, tmp_path):
    output = tmp_path / "isolated-package"
    output.mkdir()
    activation = output / "advanced_renderer_build.py"
    activation.write_text("sentinel activation\n", encoding="utf-8")
    preload = tmp_path / "late-output-change.mjs"
    preload.write_text(
        'import fs from "node:fs/promises";\n'
        'import { dirname, resolve } from "node:path";\n'
        'import { syncBuiltinESMExports } from "node:module";\n'
        'const original = fs.writeFile;\n'
        'fs.writeFile = async (path, ...args) => {\n'
        '  await original(path, ...args);\n'
        '  if (String(path).includes("advanced_renderer_build.py")) {\n'
        '    await original(resolve(dirname(path), "renderer/advanced-bootstrap.js"), '
        '"late corruption");\n'
        '  }\n};\nsyncBuiltinESMExports();\n', encoding="utf-8",
    )
    before = _checkout_snapshot()
    result = subprocess.run(
        [pinned_node, "--import", preload.as_uri(), str(SCRIPT), "--output-root", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Advanced output verification failed" in result.stderr
    assert activation.read_text(encoding="utf-8") == "sentinel activation\n"
    assert _checkout_snapshot() == before
