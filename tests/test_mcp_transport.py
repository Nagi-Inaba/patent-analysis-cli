from __future__ import annotations

import io
import json

import anyio
import mcp_types as types
import pytest
from mcp.shared.message import SessionMessage

from patent_analysis_mcp import contracts
from patent_analysis_mcp.contracts import (
    MAX_MCP_SERIALIZED_RESPONSE_BYTES,
    MAX_REQUEST_ID_BYTES,
    McpContractError,
    decode_stdio_message,
)
from patent_analysis_mcp.transport import _BoundedStdin, _BoundedWriteStream


@pytest.mark.parametrize(
    "raw",
    [
        b'{"id":1,"id":2}',
        b'{"params":{"name":"a","name":"b"}}',
        b'{"params":{"path":"a","p\\u0061th":"b"}}',
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":1e999}',
        b'{"value":9007199254740992}',
        b'{"value":"\\ud800"}',
        b'{"value":"\\u0000"}',
        b'{"value":"\xff"}',
        b'[]',
        b'{"id":true}',
        b'{"id":1.5}',
        b'{"id":[]}',
        b'{"id":"' + b'x' * (MAX_REQUEST_ID_BYTES + 1) + b'"}',
        b'{"value":' + b'[' * 64 + b'0' + b']' * 64 + b'}',
    ],
    ids=["duplicate-id", "duplicate-name", "escaped-key", "nan", "infinity", "overflow",
         "unsafe-integer", "surrogate", "nul", "utf8", "array", "bool-id", "float-id",
         "array-id", "long-id", "depth"],
)
def test_wire_rejects_ambiguous_or_unsafe_json(raw: bytes) -> None:
    with pytest.raises(McpContractError, match="^Tool input is invalid$"):
        decode_stdio_message(raw)


def test_wire_structural_limits_run_before_object_construction(monkeypatch: pytest.MonkeyPatch):
    def must_not_parse(_raw: bytes) -> object:
        pytest.fail("over-budget JSON reached the object parser")

    monkeypatch.setattr(contracts, "parse_strict_json_bytes", must_not_parse)
    payloads = [
        b'{"value":' + b'[' * 64 + b'0' + b']' * 64 + b'}',
        b'{"value":[' + b'0,' * 250_000 + b'0]}',
        b'{"value":' + b'1' * 129 + b'}',
        b'{"value":1,"v\\u0061lue":2}',
    ]
    for raw in payloads:
        with pytest.raises(McpContractError):
            decode_stdio_message(raw)


@pytest.mark.parametrize("request_id", [0, 9007199254740991, "x" * MAX_REQUEST_ID_BYTES,
                                        "界" * (MAX_REQUEST_ID_BYTES // 3)],
                         ids=["zero", "safe-integer", "ascii-limit", "unicode-limit"])
def test_wire_preserves_valid_ids_and_unicode(request_id: int | str) -> None:
    value = {"jsonrpc": "2.0", "id": request_id, "method": "ping", "params": {"label": "出願人😀"}}
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    assert decode_stdio_message(raw) == value


def test_wire_id_cap_counts_utf8_bytes() -> None:
    raw = json.dumps({"id": "界" * (MAX_REQUEST_ID_BYTES // 3 + 1)}).encode()
    with pytest.raises(McpContractError):
        decode_stdio_message(raw)


def test_bounded_input_recovers_after_rejected_frames() -> None:
    raw = b'{"x":"' + b'x' * 256 + b'"}\n{"x":1,"x":2}\n{"id":3}\n'

    async def scenario() -> None:
        frames = [frame async for frame in _BoundedStdin(io.BytesIO(raw), 64)]
        assert frames == ["{\n", "{\n", '{"id":3}\n']

    anyio.run(scenario)


def _send_message(message: types.JSONRPCMessage) -> types.JSONRPCMessage:
    async def scenario() -> types.JSONRPCMessage:
        sender, receiver = anyio.create_memory_object_stream[SessionMessage](1)
        async with _BoundedWriteStream(sender) as bounded, receiver:
            await bounded.send(SessionMessage(message))
            return (await receiver.receive()).message

    return anyio.run(scenario)


@pytest.mark.parametrize("code", [-32700, -32600, -32601, -32602, -32603, -32000])
def test_protocol_errors_do_not_echo_caller_or_exception_text(code: int) -> None:
    message = types.JSONRPCError(
        jsonrpc="2.0", id="request-1",
        error=types.ErrorData(
            code=code, message="PRIVATE_SENTINEL", data={"path": "PRIVATE_SENTINEL"}
        ),
    )
    response = _send_message(message)
    assert isinstance(response, types.JSONRPCError)
    assert response.id == "request-1"
    assert response.error.code == code
    assert "PRIVATE_SENTINEL" not in response.model_dump_json()
    assert "data" not in response.error.model_dump(exclude_unset=True)


@pytest.mark.parametrize("request_id", [7, "x" * MAX_REQUEST_ID_BYTES, "x" * 300_000],
                         ids=["integer", "capped-id", "oversized-id"])
def test_entire_jsonrpc_response_is_bounded(request_id: int | str) -> None:
    message = types.JSONRPCResponse(
        jsonrpc="2.0", id=request_id, result={"label": "x" * MAX_MCP_SERIALIZED_RESPONSE_BYTES},
    )
    response = _send_message(message)
    assert isinstance(response, types.JSONRPCError)
    assert response.error.message == "Response is too large"
    assert len(response.model_dump_json().encode()) <= MAX_MCP_SERIALIZED_RESPONSE_BYTES
    assert response.id == (None if len(str(request_id)) > MAX_REQUEST_ID_BYTES else request_id)


def test_normal_protocol_responses_are_unchanged() -> None:
    message = types.JSONRPCResponse(jsonrpc="2.0", id=3, result={"label": "出願人"})
    assert _send_message(message) == message
