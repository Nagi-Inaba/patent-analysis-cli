from __future__ import annotations

import ast
import json
import tomllib
from importlib.resources import files
from pathlib import Path

import patent_analysis
from patent_analysis._version import PACKAGE_VERSION
from patent_analysis.chart_model import (
    build_ranking_chart_model,
    build_ranking_render_spec,
)

BASE_PACKAGE_EXPORTS = {
    "ANALYSIS_CONTRACT_VERSION",
    "AnalysisContractError",
    "CONTRACT_VERSION",
    "DatasetInputError",
    "OperationContractError",
    "analyze_csv",
    "describe_contract",
    "get_analysis_result_schema",
    "get_analysis_spec_schema",
    "get_operation_plan_cases",
    "get_operation_schema",
    "inspect_csv",
    "list_operations",
    "validate_analysis_result",
    "validate_analysis_spec",
    "validate_operation_plan",
}
NEW_SCHEMA_NAMES = (
    "label-overlay-pack.schema.json",
    "chart-model.schema.json",
    "chart-model-build-receipt.schema.json",
    "render-spec.schema.json",
)


def test_trusted_local_render_adds_only_the_accepted_package_root_symbols() -> None:
    assert patent_analysis.build_ranking_chart_model is build_ranking_chart_model
    assert patent_analysis.build_ranking_render_spec is build_ranking_render_spec
    assert set(patent_analysis.__all__) == BASE_PACKAGE_EXPORTS | {
        "build_ranking_chart_model",
        "build_ranking_render_spec",
        "RenderError",
        "render_ranking_svg",
        "describe_capabilities",
        "get_public_schema",
        "inspect_dataset",
        "render_analysis_svg",
        "run_analysis",
        "run_analysis_csv",
        "validate_analysis_spec_bytes",
    }
    assert not hasattr(patent_analysis, "RenderContractError")
    assert not hasattr(patent_analysis, "validate_chart_model")
    assert not hasattr(patent_analysis, "render_matrix_svg")


def test_slice_a_package_resources_and_version_are_synchronized() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == PACKAGE_VERSION == patent_analysis.__version__
    assert project["project"]["dependencies"] == [
        "jsonschema>=4.23",
        "regex==2026.4.4",
    ]
    package = files("patent_analysis").joinpath("schemas")
    for name in (*NEW_SCHEMA_NAMES, "render-contract-cases.json"):
        resource = package.joinpath(name)
        assert resource.is_file()
        json.loads(resource.read_text(encoding="utf-8"))


def test_slice_a_python_surface_has_no_provider_imports() -> None:
    package_root = Path("src/patent_analysis")
    forbidden_import_roots = {
        "sqlite3",
        "pmgs",
        "echarts",
        "node",
    }
    for source in package_root.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        if any(isinstance(node, ast.ImportFrom) and node.module for node in ast.walk(tree)):
            imported |= {
                node.module.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
        assert imported.isdisjoint(forbidden_import_roots), source

    forbidden_source_terms = {
        "PATENT_ANALYSIS_RENDER_OUTPUT_ROOT",
        "PATENT_ANALYSIS_NODE_EXECUTABLE",
        "pmgs",
        "render_to_svg",
        "artifact_id",
        "AppContainer",
        "JobObject",
    }
    slice_a_sources = [
        package_root / "_render_canonical.py",
        package_root / "_render_contracts.py",
        package_root / "_render_text.py",
        package_root / "chart_model.py",
    ]
    for source in slice_a_sources:
        text = source.read_text(encoding="utf-8")
        for term in forbidden_source_terms:
            assert term not in text, (source, term)


def test_slice_a_schemas_are_provider_neutral() -> None:
    forbidden_values = {
        "pmgs",
        "sqlite",
        "release_id",
        "scheme",
        "official",
        "ipc",
        "fi",
        "fterm",
        "cpc",
    }

    def strings(value: object):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key.casefold()
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)
        elif isinstance(value, str):
            yield value.casefold()

    schema_root = files("patent_analysis").joinpath("schemas")
    for name in (*NEW_SCHEMA_NAMES, "render-contract-cases.json"):
        value = json.loads(schema_root.joinpath(name).read_text(encoding="utf-8"))
        assert forbidden_values.isdisjoint(strings(value)), name


def test_b1_package_tree_has_only_approved_internal_runtime_javascript() -> None:
    package_root = Path("src/patent_analysis")
    expected_javascript = {
        package_root / "renderer/bootstrap.js",
        package_root / "renderer/advanced-bootstrap.js",
        package_root / "renderer/renderer.bundle.js",
        package_root / "renderer/matrix-bootstrap.js",
        package_root / "renderer/matrix-renderer.bundle.js",
        package_root / "renderer/categorical-bootstrap.js",
        package_root / "renderer/points-bootstrap.js",
        package_root / "renderer/points-renderer.bundle.js",
        package_root / "renderer/categorical-renderer.bundle.js",
    }
    actual_javascript = {
        path
        for path in package_root.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".js"
    }
    assert actual_javascript == expected_javascript

    forbidden_suffixes = {".exe", ".sqlite", ".sqlite3"}
    forbidden_names = {
        "node_modules",
        "pmgs.py",
        "svg_writer.py",
        "artifact_writer.py",
        "output_root.py",
    }
    for path in package_root.rglob("*"):
        assert path.suffix.casefold() not in forbidden_suffixes, path
        assert path.name.casefold() not in forbidden_names, path
