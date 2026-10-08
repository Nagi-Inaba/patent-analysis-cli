from __future__ import annotations

import hashlib

import pytest

from patent_analysis import DatasetInputError
from patent_analysis.data import read_csv_rows
from patent_analysis.dataset_v2 import read_dataset_v2


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16"])
def test_multibyte_and_quoted_newline_cross_decoder_chunks(encoding, tmp_path):
    source = tmp_path / "input.csv"
    value = "特許😀" * 3000 + "\r\n末尾"
    raw = ('group,text\r\nA,"' + value + '"\r\n').encode(encoding)
    source.write_bytes(raw)
    legacy, manifest = read_csv_rows(source, allowed_root=tmp_path)
    current = read_dataset_v2(source, allowed_root=tmp_path)
    assert legacy == [{"group": "A", "text": value}]
    assert current.rows[0].values == ("A", value)
    expected_hash = hashlib.sha256(raw).hexdigest()
    assert manifest["content_sha256"] == current.manifest.source_input_sha256 == expected_hash
    assert source.read_bytes() == raw


@pytest.mark.parametrize("encoding,tail", [("utf-8", b"\xf0"), ("utf-16", b"\x00")])
def test_invalid_encoding_after_decoder_boundary_returns_safe_error(encoding, tail, tmp_path):
    source = tmp_path / "PRIVATE.csv"
    source.write_bytes(("group,text\n" + "A,PRIVATE\n" * 2000).encode(encoding) + tail)
    for reader in (read_csv_rows, read_dataset_v2):
        with pytest.raises(DatasetInputError) as caught:
            reader(source, allowed_root=tmp_path)
        assert caught.value.code == "input.invalid"
        assert "PRIVATE" not in str(caught.value)
