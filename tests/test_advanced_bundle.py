"""Bounded decoding of one verified, packaged gzip renderer bundle."""

from __future__ import annotations

import gzip
import hashlib

import pytest

from patent_analysis.advanced_bundle import decode_advanced_bundle


def test_exact_compressed_bundle_round_trips_to_verified_javascript():
    source = b'"use strict";globalThis.PatentAnalysisRenderer={};'
    assert (
        decode_advanced_bundle(gzip.compress(source, mtime=0), hashlib.sha256(source).hexdigest())
        == source
    )


@pytest.mark.parametrize("suffix", [b"unexpected", gzip.compress(b"second member", mtime=0)])
def test_trailing_data_or_concatenated_members_are_rejected(suffix):
    source = b"payload"
    with pytest.raises(ValueError):
        decode_advanced_bundle(
            gzip.compress(source, mtime=0) + suffix, hashlib.sha256(source).hexdigest()
        )


@pytest.mark.parametrize("archive", [b"", b"not gzip", gzip.compress(b"payload")[:-3]])
def test_invalid_or_truncated_gzip_is_rejected(archive):
    with pytest.raises(ValueError):
        decode_advanced_bundle(archive, "a" * 64)


def test_digest_mismatch_is_rejected():
    with pytest.raises(ValueError):
        decode_advanced_bundle(gzip.compress(b"payload", mtime=0), "a" * 64)


def test_expansion_limit_is_checked_before_unbounded_decompression():
    source = b"x" * (4 * 1024 * 1024 + 1)
    with pytest.raises(ValueError):
        decode_advanced_bundle(gzip.compress(source, mtime=0), hashlib.sha256(source).hexdigest())


@pytest.mark.parametrize("digest", ["", "a" * 63, "A" * 64, None])
def test_invalid_digest_contract_is_rejected(digest):
    with pytest.raises(ValueError):
        decode_advanced_bundle(gzip.compress(b"payload", mtime=0), digest)
