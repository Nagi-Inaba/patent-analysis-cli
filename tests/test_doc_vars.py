from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync_doc_vars.py"


@pytest.fixture(scope="module")
def sync_doc_vars():
    spec = importlib.util.spec_from_file_location("sync_doc_vars", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_documented_counts_match_the_implementation(sync_doc_vars):
    stale = sync_doc_vars.sync(sync_doc_vars.variables(), write=False)
    assert not stale, (
        "stale doc numbers in "
        + ", ".join(path.relative_to(ROOT).as_posix() for path in stale)
        + "; run: python scripts/sync_doc_vars.py"
    )


def test_every_variable_is_referenced_and_every_reference_is_defined(sync_doc_vars):
    defined = set(sync_doc_vars.variables())
    used = {
        match.group(1)
        for path in sync_doc_vars.doc_files()
        for match in sync_doc_vars.MARKER.finditer(path.read_text(encoding="utf-8"))
    }
    assert used == defined


def test_render_rewrites_only_marked_numbers(sync_doc_vars):
    text = "28分析 <!--var:analysis_count-->1<!--/var-->分析 <!--var:mark_count-->x<!--/var-->"
    rendered = sync_doc_vars.render(text, {"analysis_count": 28, "mark_count": 7})
    assert rendered == (
        "28分析 <!--var:analysis_count-->28<!--/var-->分析 <!--var:mark_count-->7<!--/var-->"
    )


def test_render_rejects_unknown_variable(sync_doc_vars):
    with pytest.raises(ValueError, match="unknown doc variable: nope"):
        sync_doc_vars.render("<!--var:nope-->1<!--/var-->", {"analysis_count": 28})


def test_sync_preserves_line_endings_and_reports_changes(sync_doc_vars, tmp_path):
    doc = tmp_path / "README.md"
    doc.write_bytes("a\r\n<!--var:analysis_count-->1<!--/var-->分析\n".encode())
    values = {"analysis_count": 28}

    assert sync_doc_vars.sync(values, write=False, root=tmp_path) == [doc]
    assert doc.read_bytes().endswith(b"1<!--/var-->\xe5\x88\x86\xe6\x9e\x90\n")

    assert sync_doc_vars.sync(values, write=True, root=tmp_path) == [doc]
    assert doc.read_bytes() == "a\r\n<!--var:analysis_count-->28<!--/var-->分析\n".encode()
    assert sync_doc_vars.sync(values, write=True, root=tmp_path) == []


def test_marker_pattern_does_not_span_separate_markers(sync_doc_vars):
    text = "<!--var:a-->1<!--/var--> and <!--var:b-->2<!--/var-->"
    assert [m.group(0) for m in re.finditer(sync_doc_vars.MARKER, text)] == [
        "<!--var:a-->1<!--/var-->",
        "<!--var:b-->2<!--/var-->",
    ]
