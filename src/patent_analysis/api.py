"""Public Python facade shared by command-line and local stdio MCP adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Any

from patent_analysis.analyses._advanced_registration import (
    PUBLIC_SCHEMA_NAMES as ADVANCED_SCHEMA_NAMES,
)
from patent_analysis.analyses._inventor_registration import (
    MODULE_BY_ID as INVENTOR_MODULE_BY_ID,
)
from patent_analysis.analyses._inventor_registration import (
    PUBLIC_SCHEMA_NAMES as INVENTOR_SCHEMA_NAMES,
)
from patent_analysis.analysis_dispatch import (
    ValidatedV1Spec,
    dispatch_and_validate_spec_bytes,
)
from patent_analysis.analysis_runner import run_analysis, run_analysis_csv
from patent_analysis.analysis_tables import run_analysis_table as _legacy_analysis_table
from patent_analysis.capabilities import describe_capabilities
from patent_analysis.column_resolution import describe_header_candidates
from patent_analysis.dataset_v2 import (
    DATASET_CONTRACT_VERSION,
    manifest_to_public_dict,
    read_dataset_v2,
)

_PUBLIC_SCHEMA_NAMES = (
    frozenset(
        {
            "analysis-spec.schema.json",
            "analysis-result.schema.json",
            "analysis-spec-v2.schema.json",
            "analysis-result-v2.schema.json",
            "analysis-error-v2.schema.json",
            "categorical-chart-model-v1.schema.json",
            "categorical-render-spec-v1.schema.json",
            "composition-parameters-v1.schema.json",
            "composition-result-v1.schema.json",
            "matrix-chart-model-v1.schema.json",
            "matrix-parameters-v1.schema.json",
            "matrix-render-spec-v1.schema.json",
            "matrix-result-v1.schema.json",
            "normalization-v1.schema.json",
            "operation.schema.json",
            "population-v1.schema.json",
            "timeline-parameters-v1.schema.json",
            "timeline-result-v1.schema.json",
            "growth-parameters-v1.schema.json",
            "growth-result-v1.schema.json",
            "concentration-parameters-v1.schema.json",
            "concentration-result-v1.schema.json",
            "lifecycle-parameters-v1.schema.json",
            "lifecycle-result-v1.schema.json",
            "points-chart-model-v1.schema.json",
            "points-render-spec-v1.schema.json",
            "points-renderer-response.schema.json",
            "advanced-projection-v1.schema.json",
            "advanced-chart-model-v1.schema.json",
            "advanced-render-spec-v1.schema.json",
            "advanced-renderer-response.schema.json",
        }
    )
    | ADVANCED_SCHEMA_NAMES
    | INVENTOR_SCHEMA_NAMES
    | {"inventor-sidecar-v1.schema.json"}
)


def inspect_dataset(
    source: str | Path,
    *,
    allowed_root: str | Path,
    include_samples: bool = False,
) -> dict[str, object]:
    if include_samples:
        raise ValueError("samples are not available through the public core API")
    dataset = read_dataset_v2(source, allowed_root=allowed_root)
    return {
        "dataset_contract_version": DATASET_CONTRACT_VERSION,
        "dataset": manifest_to_public_dict(dataset.manifest),
        "resolution": describe_header_candidates(dataset.manifest.raw_header),
    }


def render_analysis_svg(
    analysis_document: bytes,
    *,
    mark: str | None = None,
    overlay: bytes | Mapping[str, object] | None = None,
    output_directory: str | Path,
    node_executable: str | Path | None = None,
    value_labels: str | None = None,
    palette: str | None = None,
) -> dict[str, object]:
    if overlay is not None and type(overlay) is not bytes:
        raise ValueError("render overlay must be bytes")

    from patent_analysis import rendering as rendering_module
    from patent_analysis.advanced_presentation import ADVANCED_MARK_TO_ID, ADVANCED_PRESENTATIONS
    from patent_analysis.advanced_rendering import render_advanced_svg
    from patent_analysis.render_errors import _make_render_error

    # Route only finite native IDs/marks. Use the same bounded strict document
    # parser as legacy rendering; no data or code is accepted as chart options.
    if type(analysis_document) is not bytes:
        raise _make_render_error("input.invalid")
    document = rendering_module._parse_document(
        analysis_document, rendering_module.MAX_ANALYSIS_DOCUMENT_BYTES
    )
    analysis_id = document.get("analysis_id")
    is_advanced = isinstance(analysis_id, str) and analysis_id in ADVANCED_PRESENTATIONS
    is_advanced_mark = isinstance(mark, str) and mark in ADVANCED_MARK_TO_ID
    if is_advanced or is_advanced_mark:
        if not is_advanced or value_labels is not None:
            raise _make_render_error("render.invalid")
        return render_advanced_svg(
            analysis_document,
            analysis_id=analysis_id,
            mark=mark,
            overlay_document=overlay,
            output_directory=output_directory,
            node_executable=node_executable,
            palette=palette,
        )

    return rendering_module.render_analysis_svg(
        analysis_document,
        mark=mark,
        overlay_document=overlay,
        output_directory=output_directory,
        node_executable=node_executable,
        value_labels=value_labels,
        palette=palette,
    )


def run_analysis_table(
    source, spec_bytes, *, allowed_root, table_format="csv", include_context=False
):
    # Preserve legacy table-option validation precedence without touching its exporter.
    if table_format not in ("csv", "text") or type(include_context) is not bool:
        return _legacy_analysis_table(
            source,
            spec_bytes,
            allowed_root=allowed_root,
            table_format=table_format,
            include_context=include_context,
        )
    validated = dispatch_and_validate_spec_bytes(spec_bytes)
    if validated.spec.get("analysis_id") in INVENTOR_MODULE_BY_ID:
        from patent_analysis.analyses._inventor_common import inventor_table

        return inventor_table(
            source,
            spec_bytes,
            allowed_root=allowed_root,
            table_format=table_format,
            include_context=include_context,
        )
    return _legacy_analysis_table(
        source,
        spec_bytes,
        allowed_root=allowed_root,
        table_format=table_format,
        include_context=include_context,
    )


def get_public_schema(schema_name: str) -> dict[str, Any]:
    if schema_name not in _PUBLIC_SCHEMA_NAMES:
        raise ValueError("unknown public schema")
    resource = files("patent_analysis").joinpath("schemas", schema_name)
    try:
        value = json.loads(resource.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
        raise ValueError("public schema is unavailable") from None
    if not isinstance(value, dict):
        raise ValueError("public schema is invalid")
    return deepcopy(value)


def validate_analysis_spec_bytes(spec_bytes: bytes) -> dict[str, object]:
    """Validate one byte-first analysis spec without returning source fields."""

    validated = dispatch_and_validate_spec_bytes(spec_bytes)
    if isinstance(validated, ValidatedV1Spec):
        analysis_id = "ranking.v1"
        spec_variant = "versionless-ranking"
    else:
        analysis_id = validated.definition.analysis_id
        spec_variant = "analysis-spec-v2"
    return {
        "valid": True,
        "analysis_id": analysis_id,
        "spec_variant": spec_variant,
    }


__all__ = (
    "describe_capabilities",
    "get_public_schema",
    "inspect_dataset",
    "render_analysis_svg",
    "run_analysis",
    "run_analysis_csv",
    "run_analysis_table",
    "validate_analysis_spec_bytes",
)
