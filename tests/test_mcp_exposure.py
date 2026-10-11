from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

from advanced_inventory import ADVANCED_IDS, INVENTOR_IDS, MCP_IDS, MCP_MARKS


def test_mcp_dependencies_are_exact_and_core_import_stays_independent() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["optional-dependencies"]["mcp"] == ["mcp==2.0.0", "pyjwt==2.15.1"]
    assert project["scripts"]["patent-analysis-mcp"] == "patent_analysis_mcp.server:main"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import patent_analysis; "
            "assert 'mcp' not in sys.modules; assert 'mcp_types' not in sys.modules",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_mcp_exposure_is_derived_only_from_completed_public_registry_entries() -> None:
    from patent_analysis.analysis_registry import list_analysis_definitions
    from patent_analysis_mcp.exposure import (
        describe_mcp_capabilities,
        visible_analysis_ids,
    )

    expected = tuple(
        definition.analysis_id
        for definition in list_analysis_definitions()
        if definition.mcp_public
    )
    capabilities = describe_mcp_capabilities()

    assert visible_analysis_ids() == expected == MCP_IDS
    assert tuple(item["analysis_id"] for item in capabilities["analyses"]) == expected
    assert capabilities["render_marks"] == list(MCP_MARKS)
    assert set(capabilities["schemas"]) == {
        "analysis-result.schema.json",
        "analysis-spec.schema.json",
        *(
            f"{name}-{kind}-v1.schema.json"
            for name in ("matrix", "timeline", "composition")
            for kind in ("parameters", "result")
        ),
        "growth-parameters-v1.schema.json",
        "growth-result-v1.schema.json",
        "concentration-parameters-v1.schema.json",
        "concentration-result-v1.schema.json",
        "lifecycle-parameters-v1.schema.json",
        "lifecycle-result-v1.schema.json",
        *(
            f"{name[:-3]}-{kind}-v1.schema.json"
            for name in (*ADVANCED_IDS, *INVENTOR_IDS)
            for kind in ("parameters", "result")
        ),
        "inventor-sidecar-v1.schema.json",
    }
