"""Bounded local stdio transport using the MCP 2.x low-level server."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import BinaryIO

import anyio
import mcp_types as types
from anyio.abc import ObjectSendStream
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.shared.message import SessionMessage

from patent_analysis_mcp.contracts import (
    MAX_MCP_SERIALIZED_RESPONSE_BYTES,
    MAX_REQUEST_ID_BYTES,
    MAX_STDIO_MESSAGE_BYTES,
    McpContractError,
    decode_stdio_message,
)

_INVALID_FRAME = "{\n"
_PROTOCOL_ERRORS = {
    -32700: "Parse error",
    -32600: "Invalid Request",
    -32601: "Method not found",
    -32602: "Invalid params",
    -32603: "Internal error",
}


class _BoundedStdin:
    def __init__(self, stream: BinaryIO, maximum_bytes: int) -> None:
        self._stream = stream
        self._maximum_bytes = maximum_bytes

    def __aiter__(self) -> _BoundedStdin:
        return self

    async def _read(self) -> bytes:
        return await anyio.to_thread.run_sync(
            self._stream.readline,
            self._maximum_bytes + 1,
            abandon_on_cancel=True,
        )

    async def __anext__(self) -> str:
        raw = await self._read()
        if not raw:
            raise StopAsyncIteration
        if len(raw) > self._maximum_bytes:
            while raw and not raw.endswith(b"\n"):
                raw = await self._read()
            return _INVALID_FRAME
        try:
            decode_stdio_message(raw)
            return raw.decode("utf-8", errors="strict")
        except (McpContractError, UnicodeDecodeError):
            return _INVALID_FRAME


class _BoundedWriteStream(ObjectSendStream[SessionMessage]):
    """Apply the public privacy and byte budget to the entire JSON-RPC envelope."""

    def __init__(self, stream: ObjectSendStream[SessionMessage]) -> None:
        self._stream = stream

    async def send(self, item: SessionMessage) -> None:
        message = item.message
        if isinstance(message, types.JSONRPCError):
            code = message.error.code
            message = types.JSONRPCError(
                jsonrpc="2.0",
                id=message.id,
                error=types.ErrorData(
                    code=code, message=_PROTOCOL_ERRORS.get(code, "Protocol error")
                ),
            )
        encoded = message.model_dump_json(by_alias=True, exclude_unset=True).encode("utf-8")
        if len(encoded) > MAX_MCP_SERIALIZED_RESPONSE_BYTES:
            # Incoming IDs are capped; also defend against oversized SDK-generated IDs.
            request_id = getattr(message, "id", None)
            if (
                isinstance(request_id, str)
                and len(request_id.encode("utf-8")) > MAX_REQUEST_ID_BYTES
            ):
                request_id = None
            message = types.JSONRPCError(
                jsonrpc="2.0",
                id=request_id,
                error=types.ErrorData(code=-32603, message="Response is too large"),
            )
        await self._stream.send(SessionMessage(message, metadata=item.metadata))

    async def aclose(self) -> None:
        await self._stream.aclose()


@asynccontextmanager
async def bounded_stdio_server() -> AsyncIterator[tuple[object, object]]:
    bounded_stdin = _BoundedStdin(sys.stdin.buffer, MAX_STDIO_MESSAGE_BYTES)
    async with stdio_server(stdin=bounded_stdin) as (read_stream, write_stream):
        yield read_stream, _BoundedWriteStream(write_stream)


async def run_stdio_server(server: Server[object]) -> None:
    async with bounded_stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
            raise_exceptions=False,
        )


__all__ = ("bounded_stdio_server", "run_stdio_server")
