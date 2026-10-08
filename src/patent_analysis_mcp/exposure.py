"""Registry-derived analysis, renderer, and schema exposure for MCP."""

from __future__ import annotations

from copy import deepcopy
from pathlib import PurePosixPath

from patent_analysis.analysis_registry import (
    AnalysisDefinition,
    get_analysis_definition,
    list_analysis_definitions,
)
from patent_analysis.api import describe_capabilities, get_public_schema
from patent_analysis.renderer_registry import get_renderer_definition

MCP_CAPABILITY_CONTRACT_VERSION = "1.0.0"


class ExposureError(ValueError):
    def __init__(self, code: str) -> None:
        if code not in {"analysis.unknown", "schema.unknown"}:
            raise ValueError("unknown exposure error")
        self.code = code
        super().__init__("requested capability is unavailable")


def _visible_definitions() -> tuple[AnalysisDefinition, ...]:
    return tuple(
        definition for definition in list_analysis_definitions() if definition.mcp_public
    )


def visible_analysis_ids() -> tuple[str, ...]:
    return tuple(definition.analysis_id for definition in _visible_definitions())


def visible_render_marks() -> tuple[str, ...]:
    marks: list[str] = []
    seen: set[str] = set()
    for definition in _visible_definitions():
        for mark in definition.compatible_render_marks:
            get_renderer_definition(mark)
            if mark not in seen:
                seen.add(mark)
                marks.append(mark)
    return tuple(marks)


def _schema_name(path: str) -> str | None:
    candidate = PurePosixPath(path)
    if len(candidate.parts) != 2 or candidate.parts[0] != "schemas":
        return None
    try:
        get_public_schema(candidate.name)
    except ValueError:
        return None
    return candidate.name


def visible_schema_names() -> tuple[str, ...]:
    names: set[str] = set()
    for definition in _visible_definitions():
        for path in (definition.spec_schema, definition.result_schema):
            name = _schema_name(path)
            if name is not None:
                names.add(name)
    return tuple(sorted(names))


def require_visible_analysis(analysis_id: object) -> AnalysisDefinition:
    if not isinstance(analysis_id, str) or analysis_id not in visible_analysis_ids():
        raise ExposureError("analysis.unknown")
    try:
        return get_analysis_definition(analysis_id)
    except ValueError:
        raise ExposureError("analysis.unknown") from None


def require_visible_schema(schema_name: object) -> str:
    if not isinstance(schema_name, str) or schema_name not in visible_schema_names():
        raise ExposureError("schema.unknown")
    return schema_name


def describe_mcp_capabilities() -> dict[str, object]:
    visible = frozenset(visible_analysis_ids())
    analyses = [
        deepcopy(item)
        for item in describe_capabilities()["analyses"]
        if item["analysis_id"] in visible
    ]
    return {
        "mcp_capability_contract_version": MCP_CAPABILITY_CONTRACT_VERSION,
        "analyses": analyses,
        "render_marks": list(visible_render_marks()),
        "schemas": list(visible_schema_names()),
    }


__all__ = (
    "describe_mcp_capabilities",
    "require_visible_analysis",
    "require_visible_schema",
    "visible_analysis_ids",
    "visible_render_marks",
    "visible_schema_names",
)
