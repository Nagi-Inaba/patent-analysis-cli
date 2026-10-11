"""The public sidecar schema rejects complete-string control/surrogate input."""

import pytest
from jsonschema import Draft202012Validator
from test_inventor_foundation_sidecars import evidence_bundle

from patent_analysis.api import get_public_schema


@pytest.mark.parametrize(
    "table,field", [("sources", "citation"), ("sources", "url"), ("reviews", "reason")]
)
@pytest.mark.parametrize("suffix", ["\n", "\ud800", "\udfff"])
def test_public_sidecar_schema_rejects_forbidden_text_suffix(table, field, suffix):
    document = evidence_bundle()
    document["tables"][table][0][field] = "private-value" + suffix
    schema = get_public_schema("inventor-sidecar-v1.schema.json")
    assert not Draft202012Validator(schema).is_valid(document)


def test_public_sidecar_schema_preserves_valid_multilingual_text():
    document = evidence_bundle()
    document["tables"]["sources"][0]["citation"] = "العربية עברית 👩‍🔬 日本語"
    schema = get_public_schema("inventor-sidecar-v1.schema.json")
    assert Draft202012Validator(schema).is_valid(document)


@pytest.mark.parametrize("value", ["2024\n", "2024-01\n"])
def test_public_sidecar_schema_rejects_trailing_newline_in_partial_dates(value):
    document = evidence_bundle()
    document["tables"]["sources"][0]["checked_date"] = value
    schema = get_public_schema("inventor-sidecar-v1.schema.json")
    assert not Draft202012Validator(schema).is_valid(document)
