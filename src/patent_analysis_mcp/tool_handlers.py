"""Six pure handlers over the shared public Python facade."""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from patent_analysis import api as public_api
from patent_analysis.canonical_v2 import CanonicalizationError, canonical_json_bytes
from patent_analysis.render_palettes import RENDER_PALETTES
from patent_analysis_mcp.contracts import (
    MAX_TOOL_ARGUMENT_BYTES,
    MAX_TOOL_RESPONSE_BYTES,
    McpContractError,
    decode_tool_arguments,
    failure_envelope,
    schema_success_envelope,
    success_envelope,
)
from patent_analysis_mcp.exposure import (
    ExposureError,
    describe_mcp_capabilities,
    require_visible_analysis,
    require_visible_schema,
    visible_render_marks,
)
from patent_analysis_mcp.roots import RootRegistry

_TOOL_NAMES = (
    "patent_analysis.capabilities",
    "patent_analysis.schema",
    "patent_analysis.inspect",
    "patent_analysis.validate_spec",
    "patent_analysis.analyze",
    "patent_analysis.render",
)

_ARGUMENT_KEYS = {
    "patent_analysis.capabilities": frozenset(),
    "patent_analysis.schema": frozenset({"schema_name"}),
    "patent_analysis.inspect": frozenset({"input_root_id", "path"}),
    "patent_analysis.validate_spec": frozenset({"spec"}),
    "patent_analysis.analyze": frozenset({"input_root_id", "path", "spec"}),
    "patent_analysis.render": frozenset(
        {"output_root_id", "output_path", "analysis_handle", "mark"}
    ),
}
# Optional keys are display choices; omitting them keeps the default rendering.
_OPTIONAL_ARGUMENT_KEYS = {
    "patent_analysis.render": frozenset({"value_labels", "palette"}),
}
_VALUE_LABEL_CHOICES = ("hidden", "shown")
_PALETTE_CHOICES = RENDER_PALETTES
_MAX_RENDER_HANDLES = 4


class ToolHandlers:
    __slots__ = (
        "api",
        "_render_documents",
        "argument_maximum_bytes",
        "node_executable",
        "response_maximum_bytes",
        "roots",
    )

    def __init__(
        self,
        *,
        roots: RootRegistry,
        api: object | None = None,
        node_executable: str | Path | None = None,
        argument_maximum_bytes: int = MAX_TOOL_ARGUMENT_BYTES,
        response_maximum_bytes: int = MAX_TOOL_RESPONSE_BYTES,
    ) -> None:
        if not isinstance(roots, RootRegistry):
            raise TypeError("roots must be a RootRegistry")
        if type(argument_maximum_bytes) is not int or argument_maximum_bytes <= 0:
            raise ValueError("invalid argument maximum")
        if type(response_maximum_bytes) is not int or response_maximum_bytes <= 0:
            raise ValueError("invalid response maximum")
        if node_executable is not None and not isinstance(node_executable, (str, Path)):
            raise TypeError("invalid node executable")
        self.roots = roots
        self.api = public_api if api is None else api
        self._render_documents: dict[str, tuple[str, bytes]] = {}
        self.node_executable = node_executable
        self.argument_maximum_bytes = argument_maximum_bytes
        self.response_maximum_bytes = response_maximum_bytes

    @staticmethod
    def tool_names() -> tuple[str, ...]:
        return _TOOL_NAMES

    def call(self, tool_name: object, raw_arguments: object) -> dict[str, object]:
        # Commit handle allocation/eviction only when a safe bounded reply is returned.
        # Stored values are immutable (analysis ID, canonical document bytes).
        previous_handles = self._render_documents.copy()
        try:
            if not isinstance(tool_name, str) or tool_name not in _ARGUMENT_KEYS:
                raise McpContractError("input.invalid")
            arguments = decode_tool_arguments(
                raw_arguments,
                maximum_bytes=self.argument_maximum_bytes,
            )
            required_keys = _ARGUMENT_KEYS[tool_name]
            allowed_keys = required_keys | _OPTIONAL_ARGUMENT_KEYS.get(tool_name, frozenset())
            supplied_keys = frozenset(arguments)
            if not required_keys <= supplied_keys <= allowed_keys:
                raise McpContractError("input.invalid")
            result = self._dispatch(tool_name, arguments)
            if tool_name == "patent_analysis.schema":
                return schema_success_envelope(result, maximum_bytes=self.response_maximum_bytes)
            return success_envelope(result, maximum_bytes=self.response_maximum_bytes)
        except Exception as error:
            self._render_documents.clear()
            self._render_documents.update(previous_handles)
            return failure_envelope(error)

    def _api_callable(self, name: str):
        value = getattr(self.api, name, None)
        if not callable(value):
            raise RuntimeError("public API is unavailable")
        return value

    @staticmethod
    def _required_string(arguments: Mapping[str, Any], name: str) -> str:
        value = arguments.get(name)
        if not isinstance(value, str) or not value:
            raise McpContractError("input.invalid")
        return value

    @staticmethod
    def _choice(arguments: Mapping[str, Any], name: str, choices: tuple[str, ...]) -> str:
        value = arguments.get(name)
        if not isinstance(value, str) or value not in choices:
            raise McpContractError("input.invalid")
        return value

    @staticmethod
    def _required_mapping(arguments: Mapping[str, Any], name: str) -> Mapping[str, object]:
        value = arguments.get(name)
        if not isinstance(value, Mapping):
            raise McpContractError("input.invalid")
        return value

    def _dispatch(self, tool_name: str, arguments: Mapping[str, Any]) -> object:
        if tool_name == "patent_analysis.capabilities":
            return describe_mcp_capabilities()
        if tool_name == "patent_analysis.schema":
            schema_name = require_visible_schema(self._required_string(arguments, "schema_name"))
            return {
                "schema_name": schema_name,
                "schema": self._api_callable("get_public_schema")(schema_name),
            }
        if tool_name == "patent_analysis.inspect":
            return self._inspect(arguments)
        if tool_name == "patent_analysis.validate_spec":
            return self._validated_spec(arguments)[1]
        if tool_name == "patent_analysis.analyze":
            return self._analyze(arguments)
        if tool_name == "patent_analysis.render":
            return self._render(arguments)
        raise McpContractError("input.invalid")

    def _input_reference(self, arguments: Mapping[str, Any]) -> tuple[Path, str]:
        root_id = self._required_string(arguments, "input_root_id")
        relative_path = self._required_string(arguments, "path")
        resolved = self.roots.resolve_input(root_id, relative_path)
        allowed_root = self.roots.input_roots[root_id]
        return allowed_root, resolved.relative_to(allowed_root).as_posix()

    def _inspect(self, arguments: Mapping[str, Any]) -> object:
        allowed_root, relative = self._input_reference(arguments)
        return self._api_callable("inspect_dataset")(
            relative,
            allowed_root=allowed_root,
            include_samples=False,
        )

    def _validated_spec(
        self,
        arguments: Mapping[str, Any],
    ) -> tuple[bytes, Mapping[str, object]]:
        spec = self._required_mapping(arguments, "spec")
        try:
            spec_bytes = canonical_json_bytes(spec)
        except (CanonicalizationError, TypeError, ValueError, UnicodeError):
            raise McpContractError("input.invalid") from None
        validation = self._api_callable("validate_analysis_spec_bytes")(spec_bytes)
        if not isinstance(validation, Mapping):
            raise RuntimeError("public validation result is invalid")
        require_visible_analysis(validation.get("analysis_id"))
        return spec_bytes, validation

    def _analyze(self, arguments: Mapping[str, Any]) -> object:
        allowed_root, relative = self._input_reference(arguments)
        spec_bytes, validation = self._validated_spec(arguments)
        document = self._api_callable("run_analysis_csv")(
            relative,
            spec_bytes,
            allowed_root=allowed_root,
        )
        if not isinstance(document, Mapping):
            raise RuntimeError("public analysis result is invalid")
        try:
            document_bytes = canonical_json_bytes(document)
        except (CanonicalizationError, TypeError, ValueError, UnicodeError):
            raise RuntimeError("public analysis result is invalid") from None
        analysis_id = validation.get("analysis_id")
        if not isinstance(analysis_id, str):
            raise RuntimeError("public validation result is invalid")
        definition = require_visible_analysis(analysis_id)
        projected = self._without_linkable_provenance(document)
        if not definition.compatible_render_marks:
            # Analysis-only results must not evict usable render documents or
            # advertise an artifact handle that no renderer can consume.
            return projected
        render_handle = secrets.token_urlsafe(32)
        while render_handle in self._render_documents:
            render_handle = secrets.token_urlsafe(32)
        if len(self._render_documents) >= _MAX_RENDER_HANDLES:
            del self._render_documents[next(iter(self._render_documents))]
        self._render_documents[render_handle] = (analysis_id, document_bytes)
        projected["render_handle"] = render_handle
        return projected

    @classmethod
    def _without_linkable_provenance(cls, value: Mapping[str, object]) -> dict[str, object]:
        def project(item: object) -> object:
            if isinstance(item, Mapping):
                return cls._without_linkable_provenance(item)
            if isinstance(item, list):
                return [project(child) for child in item]
            return item

        result: dict[str, object] = {}
        for key, item in value.items():
            if key == "receipt" or key.casefold().endswith("sha256"):
                continue
            result[key] = project(item)
        return result

    def _render(self, arguments: Mapping[str, Any]) -> object:
        root_id = self._required_string(arguments, "output_root_id")
        output_path = self._required_string(arguments, "output_path")
        analysis_handle = self._required_string(arguments, "analysis_handle")
        mark = self._required_string(arguments, "mark")
        if mark not in visible_render_marks():
            raise ExposureError("analysis.unknown")
        try:
            analysis_id, analysis_document = self._render_documents[analysis_handle]
        except KeyError:
            raise ExposureError("analysis.unknown") from None
        definition = require_visible_analysis(analysis_id)
        if mark not in definition.compatible_render_marks:
            raise ExposureError("analysis.unknown")
        options: dict[str, str] = {}
        if "value_labels" in arguments:
            options["value_labels"] = self._choice(arguments, "value_labels", _VALUE_LABEL_CHOICES)
        if "palette" in arguments:
            options["palette"] = self._choice(arguments, "palette", _PALETTE_CHOICES)
        output_directory = self.roots.resolve_output_directory(root_id, output_path)
        return self._api_callable("render_analysis_svg")(
            analysis_document,
            mark=mark,
            output_directory=output_directory,
            node_executable=self.node_executable,
            **options,
        )


__all__ = ("ToolHandlers",)
