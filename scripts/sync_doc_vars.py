"""Keep counts quoted in the docs in sync with the implementation.

A documented number is wrapped as ``<!--var:NAME-->VALUE<!--/var-->``. Each NAME is
computed from the registries below, so adding an analysis or mark updates every
document with one command:

    python scripts/sync_doc_vars.py           # rewrite the numbers
    python scripts/sync_doc_vars.py --check   # exit 1 if any number is stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

LEGACY_ANALYSIS_ID = "ranking.v1"
SHARED_EXAMPLE_CSV = "advanced/patents.csv"
MARKER = re.compile(r"<!--var:(\w+)-->(.*?)<!--/var-->")


def variables() -> dict[str, int]:
    from patent_analysis.analyses._inventor_registration import MODULE_BY_ID
    from patent_analysis.analysis_registry import list_analysis_definitions
    from patent_analysis.contracts import list_operations
    from patent_analysis.renderer_registry import list_renderer_definitions
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    definitions = list_analysis_definitions()
    v2 = [d for d in definitions if d.analysis_id != LEGACY_ANALYSIS_ID]
    catalog = ROOT / "examples" / "analysis-catalog.json"
    cases = json.loads(catalog.read_text(encoding="utf-8"))["cases"]
    return {
        "analysis_count": len(definitions),
        "v2_analysis_count": len(v2),
        # Family-representative selection excludes legacy ranking.v1 and the
        # native inventor analyses, which accept only family_mode "records".
        "population_analysis_count": sum(d.analysis_id not in MODULE_BY_ID for d in v2),
        "inventor_analysis_count": len(MODULE_BY_ID),
        "mark_count": len(list_renderer_definitions()),
        "mcp_analysis_count": sum(d.mcp_public for d in definitions),
        "mcp_tool_count": len(ToolHandlers.tool_names()),
        "operation_count": len(list_operations()),
        "catalog_case_count": len(cases),
        "shared_example_count": sum(c["csv"] == SHARED_EXAMPLE_CSV for c in cases),
    }


def doc_files(root: Path = ROOT) -> list[Path]:
    names = ("README.md", "SECURITY.md", "CONTRIBUTING.md")
    top = [root / name for name in names if (root / name).is_file()]
    return top + sorted((root / "docs").glob("*.md"))


def render(text: str, values: Mapping[str, int]) -> str:
    def substitute(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise ValueError(f"unknown doc variable: {name}")
        return f"<!--var:{name}-->{values[name]}<!--/var-->"

    return MARKER.sub(substitute, text)


def sync(values: Mapping[str, int], *, write: bool, root: Path = ROOT) -> list[Path]:
    """Return the files whose numbers differ from ``values``; rewrite them if ``write``."""
    changed = []
    for path in doc_files(root):
        # Bytes in and out so the repository's LF line endings are never touched.
        old = path.read_bytes().decode("utf-8")
        new = render(old, values)
        if new != old:
            changed.append(path)
            if write:
                path.write_bytes(new.encode("utf-8"))
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report stale numbers only")
    args = parser.parse_args(argv)
    try:
        changed = sync(variables(), write=not args.check)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    for path in changed:
        print(path.relative_to(ROOT).as_posix())
    if args.check and changed:
        print("stale doc numbers; run: python scripts/sync_doc_vars.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
