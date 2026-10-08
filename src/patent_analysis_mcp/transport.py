"""Bounded local stdio transport using the MCP 2.0 low-level server."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import BinaryIO

import anyio
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from patent_analysis_mcp.contracts import MAX_STDIO_MESSAGE_BYTES

_INVALID_FRAME = "{\n"


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
            return raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return _INVALID_FRAME


@asynccontextmanager
async def bounded_stdio_server() -> AsyncIterator[tuple[object, object]]:
    bounded_stdin = _BoundedStdin(sys.stdin.buffer, MAX_STDIO_MESSAGE_BYTES)
    async with stdio_server(stdin=bounded_stdin) as streams:
        yield streams


async def run_stdio_server(server: Server[object]) -> None:
    async with bounded_stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
            raise_exceptions=False,
        )


__all__ = ("bounded_stdio_server", "run_stdio_server")
