from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from patent_analysis.access import read_verified_bytes, validate_allowed_root
from patent_analysis.advanced_presentation import ADVANCED_PRESENTATIONS, advanced_marks_for
from patent_analysis.analysis_contracts import (
    ANALYSIS_CONTRACT_VERSION,
    AnalysisContractError,
)
from patent_analysis.api import (
    get_public_schema,
    render_analysis_svg,
    run_analysis_csv,
    run_analysis_table,
    validate_analysis_spec_bytes,
)
from patent_analysis.capabilities import describe_capabilities
from patent_analysis.column_resolution import COLUMN_ALIAS_PROFILE, describe_header_candidates
from patent_analysis.contracts import (
    CONTRACT_VERSION,
    OperationContractError,
    describe_contract,
    validate_operation_plan,
)
from patent_analysis.data import DatasetInputError, inspect_csv
from patent_analysis.dataset_v2 import (
    DATASET_CONTRACT_VERSION,
    manifest_to_public_dict,
    read_dataset_v2,
)
from patent_analysis.render_errors import RenderError, _make_render_error
from patent_analysis.rendering import (
    MAX_ANALYSIS_DOCUMENT_BYTES,
    MAX_OVERLAY_DOCUMENT_BYTES,
    RENDER_CONTRACT_VERSION,
)

EXIT_OK = 0
EXIT_INVALID_OPERATION_PLAN = 2
EXIT_INPUT_ERROR = 3
EXIT_USAGE_ERROR = 4
EXIT_RENDERER_UNAVAILABLE = 5
EXIT_OUTPUT_CONFLICT = 6
MAX_INPUT_BYTES = 2 * 1024 * 1024


class UsageError(ValueError):
    """Raised for invalid command-line arguments without writing parser output."""


class StableArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(message)


def _write_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _read_bounded_stdin() -> str:
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    content = stream.read(MAX_INPUT_BYTES + 1)
    if isinstance(content, str):
        if len(content.encode("utf-8")) > MAX_INPUT_BYTES:
            raise ValueError("OperationPlan input exceeds the size limit")
        return content
    if len(content) > MAX_INPUT_BYTES:
        raise ValueError("OperationPlan input exceeds the size limit")
    return content.decode("utf-8")


def _read_plan(source: str, *, allowed_root: str | Path | None) -> Any:
    if source == "-":
        text = _read_bounded_stdin()
    else:
        content = read_verified_bytes(
            source,
            allowed_root=allowed_root,  # type: ignore[arg-type]
            max_bytes=MAX_INPUT_BYTES,
        )
        text = content.decode("utf-8")
    return json.loads(
        text,
        parse_constant=_reject_json_constant,
    )


def _read_analysis_spec_bytes(
    source: str,
    *,
    allowed_root: str | Path | None,
) -> bytes:
    if source == "-":
        stream = getattr(sys.stdin, "buffer", sys.stdin)
        content = stream.read(MAX_INPUT_BYTES + 1)
        if isinstance(content, str):
            content = content.encode("utf-8")
        if type(content) is not bytes or len(content) > MAX_INPUT_BYTES:
            raise ValueError("AnalysisSpec input exceeds the size limit")
        return content
    return read_verified_bytes(
        source,
        allowed_root=allowed_root,  # type: ignore[arg-type]
        max_bytes=MAX_INPUT_BYTES,
    )


def _advanced_render_marks() -> tuple[str, ...]:
    return tuple(
        mark
        for analysis_id in ADVANCED_PRESENTATIONS
        for mark in advanced_marks_for(analysis_id)
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = StableArgumentParser(prog="patent-analysis", allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    contract_parser = subparsers.add_parser(
        "contract",
        help="Show the public OperationPlan contract",
        allow_abbrev=False,
    )
    contract_parser.add_argument("--json", action="store_true", dest="as_json")

    validate_parser = subparsers.add_parser(
        "validate-plan",
        help="Validate an OperationPlan JSON file or stdin",
        allow_abbrev=False,
    )
    validate_parser.add_argument("source", help="JSON file path, or - for stdin")
    validate_parser.add_argument("--json", action="store_true", dest="as_json")

    spec_parser = subparsers.add_parser(
        "validate-spec", help="Validate an executable AnalysisSpec without reading a dataset",
        allow_abbrev=False,
    )
    spec_parser.add_argument("source", help="AnalysisSpec JSON file path, or - for stdin")
    spec_parser.add_argument("--json", action="store_true", dest="as_json")
    schema_parser = subparsers.add_parser(
        "schema", help="Read a named packaged public JSON Schema", allow_abbrev=False,
    )
    schema_parser.add_argument("schema_name", help="Schema filename listed by capabilities")
    schema_parser.add_argument("--json", action="store_true", dest="as_json")

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a local CSV or JSON dataset",
        allow_abbrev=False,
    )
    inspect_parser.add_argument("source", help="CSV or JSON dataset path")
    inspect_parser.add_argument(
        "--profile",
        choices=(COLUMN_ALIAS_PROFILE,),
        dest="profile",
    )
    inspect_parser.add_argument("--json", action="store_true", dest="as_json")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run a local CSV or JSON analysis from an AnalysisSpec",
        allow_abbrev=False,
    )
    analyze_parser.add_argument("source", help="CSV or JSON dataset path")
    analyze_parser.add_argument(
        "--spec",
        required=True,
        dest="spec_source",
        help="AnalysisSpec JSON file path, or - for stdin",
    )
    output_group = analyze_parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", dest="as_json")
    output_group.add_argument("--format", choices=("csv", "text"), dest="table_format")
    analyze_parser.add_argument("--include-context", action="store_true",
                                help="Include complete Spec and analysis in CSV/text output")

    render_parser = subparsers.add_parser(
        "render",
        help="Render a local ranking analysis as deterministic SVG",
        allow_abbrev=False,
    )
    render_parser.add_argument("--analysis", required=True, dest="analysis_source")
    render_parser.add_argument("--overlay", dest="overlay_source")
    render_parser.add_argument("--output", required=True, dest="output_directory")
    render_parser.add_argument("--node", dest="node_executable")
    render_parser.add_argument(
        "--mark",
        dest="render_mark",
        choices=(
            "ranking-svg.v1",
            "matrix-bubble-svg.v1",
            "matrix-heatmap-svg.v1",
            "series-line-svg.v1",
            "series-stacked-bar-svg.v1",
            "composition-bar-svg.v1",
            "composition-pie-svg.v1",
            "points-bubble-svg.v1",
            *_advanced_render_marks(),
        ),
        default=argparse.SUPPRESS,
    )
    render_parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    return parser


def _usage_payload() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "ok": False,
        "error": {
            "code": "usage.invalid",
            "message": "Invalid patent-analysis command-line arguments",
            "retryable": False,
            "details": {},
        },
    }


def _write_usage_error(as_json: bool) -> int:
    if as_json:
        _write_json(_usage_payload())
    else:
        print("Invalid patent-analysis command-line arguments", file=sys.stderr)
    return EXIT_USAGE_ERROR


def _run_capabilities_cli(arguments: list[str]) -> int:
    as_json = "--json" in arguments
    if any(token in {"-h", "--help"} for token in arguments):
        if as_json:
            return _write_usage_error(as_json=True)
        print("usage: patent-analysis capabilities [--json]")
        return EXIT_OK
    if arguments not in ([], ["--json"]):
        return _write_usage_error(as_json)
    capabilities = describe_capabilities()
    if as_json:
        _write_json(capabilities)
    else:
        for analysis in capabilities["analyses"]:
            print(analysis["analysis_id"])
    return EXIT_OK


def _render_failure_payload(error: RenderError) -> dict[str, Any]:
    return {
        "render_contract_version": RENDER_CONTRACT_VERSION,
        "ok": False,
        "error": error.as_dict(),
    }


def _write_render_failure(error: RenderError) -> int:
    _write_json(_render_failure_payload(error))
    return {
        "render.invalid": EXIT_INVALID_OPERATION_PLAN,
        "input.invalid": EXIT_INPUT_ERROR,
        "usage.invalid": EXIT_USAGE_ERROR,
        "renderer.unavailable": EXIT_RENDERER_UNAVAILABLE,
        "output.conflict": EXIT_OUTPUT_CONFLICT,
    }[error.code]


def _read_render_stdin(limit: int) -> bytes:
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    content = stream.read(limit + 1)
    if isinstance(content, str):
        content = content.encode("utf-8")
    if type(content) is not bytes or len(content) > limit:
        raise ValueError
    return content


def _read_render_source(
    source: str,
    *,
    allowed_root: str | Path | None,
    limit: int,
) -> bytes:
    if source == "-":
        return _read_render_stdin(limit)
    return read_verified_bytes(
        source,
        allowed_root=allowed_root,  # type: ignore[arg-type]
        max_bytes=limit,
    )


def _run_render(args: argparse.Namespace) -> int:
    if args.analysis_source == "-" and args.overlay_source == "-":
        return _write_render_failure(_make_render_error("usage.invalid"))
    allowed_root = os.environ.get("PATENT_ANALYSIS_ALLOWED_ROOT")
    try:
        analysis = _read_render_source(
            args.analysis_source,
            allowed_root=allowed_root,
            limit=MAX_ANALYSIS_DOCUMENT_BYTES,
        )
        overlay = (
            None
            if args.overlay_source is None
            else _read_render_source(
                args.overlay_source,
                allowed_root=allowed_root,
                limit=MAX_OVERLAY_DOCUMENT_BYTES,
            )
        )
    except (DatasetInputError, OSError, UnicodeError, TypeError, ValueError):
        return _write_render_failure(_make_render_error("input.invalid"))

    try:
        receipt = render_analysis_svg(
            analysis,
            mark=getattr(args, "render_mark", None),
            overlay=overlay,
            output_directory=args.output_directory,
            node_executable=args.node_executable,
        )
    except RenderError as error:
        return _write_render_failure(error)
    except ValueError:
        return _write_render_failure(_make_render_error("render.invalid"))
    _write_json(receipt)
    return EXIT_OK


def _analysis_error_payload(error: AnalysisContractError) -> dict[str, Any]:
    return {
        "analysis_contract_version": ANALYSIS_CONTRACT_VERSION,
        "ok": False,
        "error": error.as_dict(),
    }


def _analysis_input_error_payload(
    message: str,
    *,
    contract_version: str = ANALYSIS_CONTRACT_VERSION,
) -> dict[str, Any]:
    return {
        "analysis_contract_version": contract_version,
        "ok": False,
        "error": {
            "code": "input.invalid",
            "message": message,
            "retryable": False,
            "details": {},
        },
    }


def _write_analysis_failure(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        _write_json(payload)
    else:
        print(payload["error"]["message"], file=sys.stderr)


def _run_validate_spec(source: str, *, as_json: bool) -> int:
    try:
        raw = _read_analysis_spec_bytes(
            source, allowed_root=os.environ.get("PATENT_ANALYSIS_ALLOWED_ROOT")
        )
    except (OSError, UnicodeError, ValueError):
        _write_analysis_failure(
            _analysis_input_error_payload("AnalysisSpec input could not be read or parsed"),
            as_json=as_json,
        )
        return EXIT_INPUT_ERROR
    try:
        result = validate_analysis_spec_bytes(raw)
    except AnalysisContractError as error:
        malformed = error.safe_message == "analysis spec is not legacy JSON"
        payload = (
            _analysis_input_error_payload("AnalysisSpec input could not be read or parsed")
            if malformed else _analysis_error_payload(error)
        )
        _write_analysis_failure(payload, as_json=as_json)
        return EXIT_INPUT_ERROR if malformed else EXIT_INVALID_OPERATION_PLAN
    if as_json:
        _write_json(result)
    else:
        print(f"AnalysisSpec is valid: {result['analysis_id']}")
    return EXIT_OK


def _run_schema(name: str, *, as_json: bool) -> int:
    try:
        schema = get_public_schema(name)
    except ValueError:
        _write_analysis_failure(
            _analysis_error_payload(AnalysisContractError("Public schema is unavailable")),
            as_json=as_json,
        )
        return EXIT_INVALID_OPERATION_PLAN
    _write_json({"schema_name": name, "schema": schema})
    return EXIT_OK


def _run_inspect(source: str, *, profile: str | None, as_json: bool) -> int:
    allowed_root = os.environ.get("PATENT_ANALYSIS_ALLOWED_ROOT")
    if profile is not None or Path(source).suffix.casefold() == ".json":
        try:
            dataset = read_dataset_v2(source, allowed_root=allowed_root)  # type: ignore[arg-type]
        except DatasetInputError:
            payload = _analysis_input_error_payload(
                "Dataset input could not be read or parsed",
                contract_version=DATASET_CONTRACT_VERSION,
            )
            _write_analysis_failure(payload, as_json=as_json)
            return EXIT_INPUT_ERROR
        manifest = manifest_to_public_dict(dataset.manifest)
        payload = {
            "analysis_contract_version": DATASET_CONTRACT_VERSION,
            "ok": True,
            "dataset": manifest,
            "resolution": describe_header_candidates(dataset.manifest.raw_header),
        }
        if as_json:
            _write_json(payload)
        else:
            print(f"Dataset: {manifest['row_count']} rows, {manifest['column_count']} columns")
        return EXIT_OK

    try:
        manifest = inspect_csv(source, allowed_root=allowed_root)  # type: ignore[arg-type]
    except DatasetInputError:
        payload = _analysis_input_error_payload("Dataset input could not be read or parsed")
        _write_analysis_failure(payload, as_json=as_json)
        return EXIT_INPUT_ERROR

    payload = {
        "analysis_contract_version": ANALYSIS_CONTRACT_VERSION,
        "ok": True,
        "dataset": manifest,
    }
    if as_json:
        _write_json(payload)
    else:
        print(f"Dataset: {manifest['row_count']} rows, {manifest['column_count']} columns")
    return EXIT_OK


def _run_analyze(
    source: str,
    spec_source: str,
    *,
    as_json: bool,
    table_format: str | None = None,
    include_context: bool = False,
) -> int:
    allowed_root = os.environ.get("PATENT_ANALYSIS_ALLOWED_ROOT")
    try:
        validate_allowed_root(allowed_root)  # type: ignore[arg-type]
        spec_bytes = _read_analysis_spec_bytes(spec_source, allowed_root=allowed_root)
    except (DatasetInputError, OSError, UnicodeError, ValueError, RecursionError):
        payload = _analysis_input_error_payload("AnalysisSpec input could not be read or parsed")
        _write_analysis_failure(payload, as_json=as_json)
        return EXIT_INPUT_ERROR

    try:
        if table_format is not None:
            table = run_analysis_table(
                source, spec_bytes, allowed_root=allowed_root,  # type: ignore[arg-type]
                table_format=table_format,
                include_context=include_context,
            )
        else:
            payload = run_analysis_csv(
                source, spec_bytes, allowed_root=allowed_root,  # type: ignore[arg-type]
            )
    except AnalysisContractError as exc:
        if exc.safe_message == "analysis spec is not legacy JSON":
            failure = _analysis_input_error_payload(
                "AnalysisSpec input could not be read or parsed"
            )
            _write_analysis_failure(failure, as_json=as_json)
            return EXIT_INPUT_ERROR
        failure = _analysis_error_payload(exc)
        _write_analysis_failure(failure, as_json=as_json)
        return EXIT_INVALID_OPERATION_PLAN
    except DatasetInputError:
        failure = _analysis_input_error_payload("Dataset input could not be read or parsed")
        _write_analysis_failure(failure, as_json=as_json)
        return EXIT_INPUT_ERROR

    if table_format is not None:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(table.encode("utf-8"))
        else:
            sys.stdout.write(table)
    elif as_json:
        _write_json(payload)
    else:
        legacy_result = payload.get("result")
        if isinstance(legacy_result, dict) and isinstance(legacy_result.get("rows"), list):
            print(f"Analysis complete: {len(legacy_result['rows'])} result rows")
        else:
            print(f"Analysis complete: {payload['analysis_id']} ({payload['result_variant']})")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parse_argv = list(sys.argv[1:] if argv is None else argv)
    if parse_argv and parse_argv[0] == "capabilities":
        return _run_capabilities_cli(parse_argv[1:])
    requested_as_json = "--json" in parse_argv
    requested_render = bool(parse_argv and parse_argv[0] == "render")
    if any(token in {"-h", "--help"} for token in parse_argv):
        if requested_render:
            return _write_render_failure(_make_render_error("usage.invalid"))
        if requested_as_json:
            return _write_usage_error(as_json=True)
    try:
        args = _build_parser().parse_args(parse_argv)
    except (argparse.ArgumentError, UsageError):
        if requested_render:
            return _write_render_failure(_make_render_error("usage.invalid"))
        return _write_usage_error(requested_as_json)
    except SystemExit as exc:
        if exc.code == 0:
            return EXIT_OK
        return _write_usage_error(requested_as_json)

    if args.command == "contract":
        contract = describe_contract()
        if args.as_json:
            _write_json(contract)
        else:
            print(f"OperationPlan contract {contract['contract_version']}")
            for operation in contract["operations"]:
                print(operation)
        return EXIT_OK

    if args.command == "validate-spec":
        return _run_validate_spec(args.source, as_json=args.as_json)

    if args.command == "schema":
        return _run_schema(args.schema_name, as_json=args.as_json)

    if args.command == "inspect":
        return _run_inspect(args.source, profile=args.profile, as_json=args.as_json)

    if args.command == "analyze":
        if args.include_context and args.table_format is None:
            return _write_usage_error(args.as_json)
        return _run_analyze(
            args.source,
            args.spec_source,
            as_json=args.as_json,
            table_format=args.table_format,
            include_context=args.include_context,
        )

    if args.command == "render":
        return _run_render(args)

    try:
        plan = _read_plan(
            args.source,
            allowed_root=os.environ.get("PATENT_ANALYSIS_ALLOWED_ROOT"),
        )
    except (OSError, UnicodeError, ValueError, RecursionError):
        payload = {
            "contract_version": CONTRACT_VERSION,
            "ok": False,
            "error": {
                "code": "input.invalid",
                "message": "OperationPlan input could not be read or parsed",
                "retryable": False,
                "details": {},
            },
        }
        if args.as_json:
            _write_json(payload)
        else:
            print(payload["error"]["message"], file=sys.stderr)
        return EXIT_INPUT_ERROR

    try:
        validate_operation_plan(plan)
    except OperationContractError as exc:
        payload = {
            "contract_version": CONTRACT_VERSION,
            "ok": False,
            "error": exc.as_dict(),
        }
        if args.as_json:
            _write_json(payload)
        else:
            print(payload["error"]["message"], file=sys.stderr)
        return EXIT_INVALID_OPERATION_PLAN

    payload = {"contract_version": CONTRACT_VERSION, "ok": True}
    if args.as_json:
        _write_json(payload)
    else:
        print("OperationPlan is valid")
    return EXIT_OK
