"""Byte-first analysis execution shared by CLI and local stdio MCP adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any

from patent_analysis import analysis_budgets
from patent_analysis.analyses.composition import CompositionBudgetError
from patent_analysis.analyses.concentration import ConcentrationBudgetError
from patent_analysis.analyses.growth import GrowthBudgetError
from patent_analysis.analyses.lifecycle import LifecycleBudgetError
from patent_analysis.analyses.matrix import MatrixBudgetError
from patent_analysis.analyses.timeline import TimelineBudgetError
from patent_analysis.analysis import analyze_csv
from patent_analysis.analysis_contracts import AnalysisContractError, StrictDraft202012Validator
from patent_analysis.analysis_dispatch import (
    ValidatedV1Spec,
    ValidatedV2Spec,
    dispatch_and_validate_spec_bytes,
)
from patent_analysis.canonical_v2 import CanonicalizationError, canonical_json_bytes
from patent_analysis.column_resolution import ResolutionError
from patent_analysis.errors import DatasetInputError
from patent_analysis.normalization.pipeline import NormalizationError


def _raise_invalid(message: str) -> None:
    raise AnalysisContractError(message, code="analysis.invalid", details={}) from None


def _load_packaged_schema(path: str) -> dict[str, Any]:
    if not path.startswith("schemas/") or ".." in path or ":" in path:
        _raise_invalid("registered analysis schema path is invalid")
    resource = files("patent_analysis")
    for part in path.split("/"):
        resource = resource.joinpath(part)
    try:
        value = json.loads(resource.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
        _raise_invalid("registered analysis schema is unavailable")
    if not isinstance(value, dict):
        _raise_invalid("registered analysis schema is invalid")
    return value


def _validate_document(value: object, schema: Mapping[str, Any], message: str) -> None:
    errors = sorted(
        StrictDraft202012Validator(schema).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        _raise_invalid(message)


def _run_registered_v2(
    source: str | Path,
    validated: ValidatedV2Spec,
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    try:
        result = validated.definition.implementation(
            source,
            validated.to_dict(),
            allowed_root=allowed_root,
        )
    except (ResolutionError, NormalizationError):
        raise DatasetInputError("input is invalid") from None
    except (
        CompositionBudgetError, ConcentrationBudgetError, GrowthBudgetError,
        LifecycleBudgetError, MatrixBudgetError, TimelineBudgetError,
    ):
        _raise_invalid("analysis exceeds published limits")
    if not isinstance(result, Mapping):
        _raise_invalid("registered analysis returned an invalid result")

    try:
        canonical_result = canonical_json_bytes(dict(result))
    except CanonicalizationError:
        _raise_invalid("registered analysis returned an invalid result")
    if len(canonical_result) > analysis_budgets.MAX_CANONICAL_NEUTRAL_RESULT_BYTES:
        _raise_invalid("registered analysis result exceeds the canonical byte limit")
    document = json.loads(canonical_result)
    specific_schema = _load_packaged_schema(validated.definition.result_schema)
    _validate_document(
        document.get("data"),
        specific_schema,
        "registered analysis result violates its definition schema",
    )
    common_schema = _load_packaged_schema("schemas/analysis-result-v2.schema.json")
    _validate_document(
        document,
        common_schema,
        "registered analysis result violates the common result schema",
    )
    return document


def run_analysis(
    source: str | Path,
    spec_bytes: bytes,
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    """Run one local CSV or JSON analysis after byte-level spec dispatch."""

    validated = dispatch_and_validate_spec_bytes(spec_bytes)
    if isinstance(validated, ValidatedV1Spec):
        return analyze_csv(
            source,
            validated.to_dict(),
            allowed_root=allowed_root,
        )
    return _run_registered_v2(source, validated, allowed_root=allowed_root)


def run_analysis_csv(
    source: str | Path,
    spec_bytes: bytes,
    *,
    allowed_root: str | Path,
) -> dict[str, object]:
    """Compatibility name for :func:`run_analysis`; JSON is also accepted."""

    return run_analysis(source, spec_bytes, allowed_root=allowed_root)
