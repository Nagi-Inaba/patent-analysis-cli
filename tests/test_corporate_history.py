from types import MappingProxyType

import pytest

from patent_analysis.corporate_history import (
    corporate_aliases,
    corporate_relations,
    match_corporate_events,
)
from patent_analysis.inventor_models import parse_observation_date
from patent_analysis.inventor_sidecars import TABLE_IDS, SidecarSnapshot


def snapshot(**tables):
    tables.setdefault("sources", [dict(source_id="s", kind="local_document")])
    tables.setdefault(
        "entities",
        [dict(entity_id=i, display_name=i, source_ids=("s",)) for i in ("A", "B", "C", "P", "Q")],
    )
    rows = {k: tuple(MappingProxyType(r) for r in tables.get(k, ())) for k in TABLE_IDS}
    return SidecarSnapshot("1.0.0", MappingProxyType(rows), (), ())


def group(start="2010-01-01", end="2030-12-31", relation="subsidiary"):
    return dict(
        group_id="g",
        child_id="A",
        parent_id="P",
        relation=relation,
        valid_from=start,
        valid_to=end,
        source_ids=("s",),
    )


def test_full_interval_known_boundaries_are_definite_not_current_backfill():
    s = snapshot(groups=[group()])
    result = corporate_relations(s, "A", parse_observation_date("2020", kind="filing"))
    assert result[0]["strength"] == "definite"
    assert result[0]["parent_id"] == "P"
    assert result[0]["group_id"] == "g"
    assert result[0]["source_ids"] == ["s"]
    assert corporate_relations(s, "A", parse_observation_date("2009", kind="filing")) == []


def event(**changes):
    row = dict(
        event_id="e",
        type="acquisition",
        entity_ids=("A", "B"),
        record_ids=(),
        announcement_date="2020-02",
        effective_date="2020-06",
        status="completed",
        scope="whole_entity",
        source_ids=("s",),
    )
    row.update(changes)
    return row


def test_completed_whole_entity_matches_are_context_not_employment():
    rows = match_corporate_events(
        snapshot(events=[event()]), ("A",), ("B",), ("r1", "r2"), "2020-01-01", "2020-12-31"
    )
    assert rows[0]["organizational_transfer_support"] is True
    assert rows[0]["employment_confirmation"] is False
    assert rows[0]["effective_date"]["precision"] == "month"
    assert rows[0]["strength"] == "possible"


def test_scoped_business_transfer_requires_referenced_patent():
    def supports(records):
        return match_corporate_events(
            snapshot(
                events=[
                    event(type="business_transfer", scope="partial_business", record_ids=records)
                ]
            ),
            ("A",),
            ("B",),
            ("r1", "r2"),
            "2020-01-01",
            "2020-12-31",
        )[0]

    assert supports(("r2",))["organizational_transfer_support"] is True
    assert supports(())["organizational_transfer_support"] is False


@pytest.mark.parametrize(
    "status,scope,kind",
    [
        ("announced", "whole_entity", "acquisition"),
        ("withdrawn", "whole_entity", "merger"),
        ("unknown", "whole_entity", "acquisition"),
        ("completed", "patents_only", "patent_rights_transfer"),
        ("completed", "minority_interest", "minority_investment"),
        ("completed", "partial_business", "acquisition"),
    ],
)
def test_non_completed_rights_minority_or_unscoped_partial_never_support(status, scope, kind):
    row = match_corporate_events(
        snapshot(events=[event(status=status, scope=scope, type=kind)]),
        ("A",),
        ("B",),
        ("r1",),
        "2020-01-01",
        "2020-12-31",
    )[0]
    assert row["status"] == status
    assert not row["organizational_transfer_support"]
    assert not row["employment_confirmation"]


@pytest.mark.parametrize(
    "start,end", [(None, None), ("2010", "2030"), ("2020-06-01", "2030-01-01")]
)
def test_coarse_unknown_or_partial_boundaries_are_possible(start, end):
    rows = corporate_relations(
        snapshot(groups=[group(start, end)]), "A", parse_observation_date("2020", kind="filing")
    )
    assert rows[0]["strength"] == "possible"
    assert rows[0]["uncertainty"]


def test_minority_context_is_not_a_controlling_parent():
    row = corporate_relations(
        snapshot(groups=[group(relation="minority_interest")]),
        "A",
        parse_observation_date("2020", kind="filing"),
    )[0]
    assert row["controlling"] is False


def test_aliases_are_interval_display_hints_not_opaque_id_mapping():
    alias = dict(
        alias_id="a",
        raw_alias="Old Name",
        entity_id="A",
        valid_from="2010-01-01",
        valid_to="2020-12-31",
        source_ids=("s",),
    )
    s = snapshot(entity_aliases=[alias])
    when = parse_observation_date("2020", kind="filing")
    rows = corporate_aliases(s, "A", when)
    assert rows[0]["raw_alias"] == "Old Name"
    assert rows[0]["display_hint_only"] is True
    assert rows[0]["strength"] == "definite"
    assert corporate_aliases(s, "Old Name", when) == []
    assert corporate_aliases(s, "A", parse_observation_date("2021", kind="filing")) == []


def test_explicit_unmatched_record_scope_is_not_organizational_support():
    row = match_corporate_events(
        snapshot(events=[event(record_ids=("other",))]),
        ("A",),
        ("B",),
        ("r1", "r2"),
        "2020-01-01",
        "2020-12-31",
    )[0]
    assert not row["organizational_transfer_support"]
    assert row["record_ids"] == ["other"]
    assert "record_scope_not_matched" in row["uncertainty"]
