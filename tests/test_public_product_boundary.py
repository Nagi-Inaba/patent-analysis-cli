import tomllib
from pathlib import Path

PUBLIC_FILES = (
    Path("README.md"),
    Path("src/patent_analysis/capabilities.py"),
    Path("src/patent_analysis/schemas/analysis-spec-v2.schema.json"),
)

FORBIDDEN_RUNTIME_TERMS = (
    "workbench mode",
    "bubble mode",
    "matrix mode",
)

def test_public_contracts_do_not_expose_source_product_modes() -> None:
    for path in PUBLIC_FILES:
        text = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_RUNTIME_TERMS:
            assert term not in text, f"{path} exposes {term!r}"


def test_distribution_metadata_covers_bundled_renderer_licenses() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["license"] == "Apache-2.0 AND MIT AND BSD-3-Clause AND 0BSD"
    assert project["license-files"] == [
        "LICENSE",
        "src/patent_analysis/renderer/THIRD_PARTY_NOTICES.txt",
    ]
