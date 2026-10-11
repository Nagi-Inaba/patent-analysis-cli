"""Console entry point and MCP 2.0 low-level server wiring."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import anyio
import mcp_types as types
from mcp.server.lowlevel import Server

from patent_analysis import PACKAGE_VERSION
from patent_analysis_mcp.contracts import MAX_MCP_SERIALIZED_RESPONSE_BYTES
from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
from patent_analysis_mcp.tool_handlers import ToolHandlers
from patent_analysis_mcp.transport import run_stdio_server

_INPUT_SCHEMAS: Mapping[str, dict[str, Any]] = {
    "patent_analysis.capabilities": {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
    },
    "patent_analysis.schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"schema_name": {"type": "string", "minLength": 1}},
        "required": ["schema_name"],
    },
    "patent_analysis.inspect": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "input_root_id": {"type": "string", "minLength": 1},
            "path": {"type": "string", "minLength": 1},
        },
        "required": ["input_root_id", "path"],
    },
    "patent_analysis.validate_spec": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"spec": {"type": "object"}},
        "required": ["spec"],
    },
    "patent_analysis.analyze": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "input_root_id": {"type": "string", "minLength": 1},
            "path": {"type": "string", "minLength": 1},
            "spec": {"type": "object"},
        },
        "required": ["input_root_id", "path", "spec"],
    },
    "patent_analysis.render": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "output_root_id": {"type": "string", "minLength": 1},
            "output_path": {"type": "string", "minLength": 1},
            "analysis_handle": {"type": "string", "minLength": 32},
            "mark": {"type": "string", "minLength": 1},
        },
        "required": ["output_root_id", "output_path", "analysis_handle", "mark"],
    },
}


def _tool_descriptions() -> Mapping[str, str]:
    return {
        "patent_analysis.capabilities": "List local MCP-approved analyses and schemas.",
        "patent_analysis.schema": "Return one MCP-approved public JSON Schema.",
        "patent_analysis.inspect": (
            "Inspect local CSV or JSON metadata without raw rows or samples."
        ),
        "patent_analysis.validate_spec": "Validate one closed analysis spec without execution.",
        "patent_analysis.analyze": "Run one MCP-approved local aggregate analysis.",
        "patent_analysis.render": "Render one approved analysis to a relative local receipt.",
    }


def build_server(handlers: ToolHandlers) -> Server[object]:
    descriptions = _tool_descriptions()

    async def list_tools(
        _context: object,
        _params: types.PaginatedRequestParams | None,
    ) -> types.ListToolsResult:
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name=name,
                    description=descriptions[name],
                    inputSchema=_INPUT_SCHEMAS[name],
                )
                for name in handlers.tool_names()
            ]
        )

    async def call_tool(
        _context: object,
        params: types.CallToolRequestParams,
    ) -> types.CallToolResult:
        result = handlers.call(params.name, params.arguments or {})
        if result["ok"]:
            summary = "Structured local result available."
        else:
            summary = str(result["error"]["message"])
        response = types.CallToolResult(
            content=[types.TextContent(text=summary)],
            structuredContent=result,
            isError=not bool(result["ok"]),
        )
        if len(response.model_dump_json(by_alias=True, exclude_unset=True).encode("utf-8")) > (
            MAX_MCP_SERIALIZED_RESPONSE_BYTES
        ):
            fallback = {
                "ok": False,
                "error": {
                    "code": "response.too_large",
                    "message": "Tool response is too large",
                },
            }
            return types.CallToolResult(
                content=[types.TextContent(text="Tool response is too large")],
                structuredContent=fallback,
                isError=True,
            )
        return response

    return Server(
        "patent-analysis-cli",
        version=PACKAGE_VERSION,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


def _parse_root_declarations(values: Sequence[str]) -> tuple[ApprovedRoot, ...]:
    declarations: list[ApprovedRoot] = []
    for value in values:
        if "=" not in value:
            raise ValueError("invalid root declaration")
        root_id, raw_path = value.split("=", 1)
        if not raw_path:
            raise ValueError("invalid root declaration")
        declarations.append(ApprovedRoot(root_id, Path(raw_path)))
    return tuple(declarations)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="patent-analysis-mcp", allow_abbrev=False)
    parser.add_argument("--input-root", action="append", required=True)
    parser.add_argument("--output-root", action="append", required=True)
    parser.add_argument("--node")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    try:
        roots = RootRegistry(
            input_roots=_parse_root_declarations(arguments.input_root),
            output_roots=_parse_root_declarations(arguments.output_root),
        )
        handlers = ToolHandlers(
            roots=roots,
            node_executable=arguments.node,
        )
        server = build_server(handlers)
    except (OSError, TypeError, ValueError):
        sys.stderr.write("MCP startup configuration is invalid\n")
        return 2

    try:
        # On Windows NumPy's DLL initialization can wait on CRT stdin locks.
        # Import the *installed, pinned optional extra* before starting the reader
        # thread. Base/mcp-only installs neither require nor import NumPy.
        if sys.platform == "win32":
            try:
                numpy_version = importlib.metadata.version("numpy")
            except importlib.metadata.PackageNotFoundError:
                numpy_version = None
            if numpy_version == "2.4.3":
                importlib.import_module("numpy")
        anyio.run(run_stdio_server, server)
    except KeyboardInterrupt:
        return 130
    except Exception:
        sys.stderr.write("MCP transport failed\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ("build_server", "main")
