"""Decode the single packaged advanced bundle within fixed byte and digest bounds."""
from __future__ import annotations

import hashlib
import re
import zlib

MAX_BUNDLE_BYTES = 4 * 1024 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}", re.ASCII)


def decode_advanced_bundle(archive: bytes, expected_sha256: str) -> bytes:
    """Reject bombs, extra members, trailing bytes and any changed JavaScript.

    Compression is a distribution format only. The existing renderer receives
    the same fully verified, bounded JavaScript bytes through its framed protocol.
    """
    if (
        type(archive) is not bytes
        or not archive
        or len(archive) > MAX_BUNDLE_BYTES
        or not isinstance(expected_sha256, str)
        or _DIGEST.fullmatch(expected_sha256) is None
    ):
        raise ValueError("advanced bundle is invalid")
    try:
        decoder = zlib.decompressobj(wbits=31)
        source = decoder.decompress(archive, MAX_BUNDLE_BYTES + 1)
        if (
            not source
            or len(source) > MAX_BUNDLE_BYTES
            or not decoder.eof
            or decoder.unconsumed_tail
            or decoder.unused_data
            or hashlib.sha256(source).hexdigest() != expected_sha256
        ):
            raise ValueError("advanced bundle is invalid")
        source.decode("utf-8", errors="strict")
    except (zlib.error, UnicodeError, ValueError):
        raise ValueError("advanced bundle is invalid") from None
    return source
