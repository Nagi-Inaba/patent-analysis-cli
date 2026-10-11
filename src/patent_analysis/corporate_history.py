"""Pure temporal legal-entity context; corporate facts never prove employment."""

from __future__ import annotations

import json
from datetime import date

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_models import ObservationDate, parse_observation_date
from patent_analysis.inventor_sidecars import SidecarSnapshot

MAX_COMPARISONS = 200000
MAX_OUTPUT_BYTES = 200 * 1024


def date_data(value: ObservationDate) -> dict:
    """Preserve raw date, kind, precision and closed uncertainty range."""
    return dict(
        raw=value.raw,
        kind=value.kind,
        precision=value.precision,
        start=value.start.isoformat() if value.start else None,
        end=value.end.isoformat() if value.end else None,
    )


def bounded_output(value: dict | list) -> dict | list:
    size = 0
    for chunk in json.JSONEncoder(ensure_ascii=False, allow_nan=False).iterencode(value):
        size += len(chunk.encode("utf-8"))
        if size > MAX_OUTPUT_BYTES:
            raise DatasetInputError("dataset input exceeds published limits")
    return value


def corporate_relations(
    snapshot: SidecarSnapshot | None, entity_id: str, observed_date: ObservationDate
) -> list[dict]:
    """Direct historical relations, with definite meaning full-interval containment."""
    if snapshot is None:
        return []
    result = []
    for row in sorted(snapshot.tables["groups"], key=lambda r: r["group_id"]):
        if row["child_id"] != entity_id:
            continue
        start = parse_observation_date(row["valid_from"], kind="valid_from")
        end = parse_observation_date(row["valid_to"], kind="valid_to")
        if (
            observed_date.start is not None
            and (start.start or date.min) > observed_date.end
            or observed_date.end is not None
            and (end.end or date.max) < observed_date.start
        ):
            continue
        definite = (
            observed_date.start is not None
            and start.precision == end.precision == "day"
            and start.start <= observed_date.start <= observed_date.end <= end.end
        )
        result.append(
            dict(
                group_id=row["group_id"],
                child_id=entity_id,
                parent_id=row["parent_id"],
                relation=row["relation"],
                controlling=row["relation"] != "minority_interest",
                strength="definite" if definite else "possible",
                valid_from=date_data(start),
                valid_to=date_data(end),
                source_ids=sorted(row["source_ids"]),
                uncertainty=[] if definite else ["incomplete_temporal_containment"],
            )
        )
    return bounded_output(result)


def corporate_aliases(
    snapshot: SidecarSnapshot | None, entity_id: str, observed_date: ObservationDate
) -> list[dict]:
    """Historical display hints only; never resolve an applicant name to a legal ID."""
    if snapshot is None:
        return []
    result = []
    for row in sorted(snapshot.tables["entity_aliases"], key=lambda r: r["alias_id"]):
        if row["entity_id"] != entity_id:
            continue
        start = parse_observation_date(row["valid_from"], kind="valid_from")
        end = parse_observation_date(row["valid_to"], kind="valid_to")
        if observed_date.start is not None and (
            (start.start or date.min) > observed_date.end
            or (end.end or date.max) < observed_date.start
        ):
            continue
        definite = (
            observed_date.start is not None
            and start.precision == end.precision == "day"
            and start.start <= observed_date.start <= observed_date.end <= end.end
        )
        result.append(
            dict(
                alias_id=row["alias_id"],
                entity_id=entity_id,
                raw_alias=row["raw_alias"],
                valid_from=date_data(start),
                valid_to=date_data(end),
                source_ids=sorted(row["source_ids"]),
                strength="definite" if definite else "possible",
                display_hint_only=True,
            )
        )
    return bounded_output(result)


def match_corporate_events(
    snapshot: SidecarSnapshot | None,
    from_ids: tuple[str, ...],
    to_ids: tuple[str, ...],
    record_ids: tuple[str, ...],
    period_start: str,
    period_end: str,
) -> list[dict]:
    """Match canonical targets and effective ranges, never infer temporal proof."""
    if snapshot is None:
        return []
    if not snapshot.tables["events"]:
        return []
    if len(snapshot.tables["events"]) > MAX_COMPARISONS:
        raise DatasetInputError("dataset input exceeds published limits")
    lower = date.fromisoformat(period_start)
    upper = date.fromisoformat(period_end)
    sources = {r["source_id"]: r["kind"] for r in snapshot.tables["sources"]}
    result = []
    for row in sorted(snapshot.tables["events"], key=lambda r: r["event_id"]):
        targets = set(row["entity_ids"])
        if not (targets & set(from_ids) and targets & set(to_ids)):
            continue
        effective = parse_observation_date(row["effective_date"], kind="effective")
        if effective.start and (effective.start > upper or effective.end < lower):
            continue
        scoped = bool(set(row["record_ids"]) & set(record_ids))
        support = row["status"] == "completed" and (
            row["scope"] == "whole_entity"
            and (not row["record_ids"] or scoped)
            and row["type"] in {"acquisition", "merger"}
            or row["scope"] == "partial_business"
            and scoped
            and row["type"] in {"acquisition", "merger", "business_transfer"}
        )
        result.append(
            dict(
                event_id=row["event_id"],
                type=row["type"],
                status=row["status"],
                scope=row["scope"],
                entity_ids=sorted(targets),
                record_ids=sorted(row["record_ids"]),
                source_ids=sorted(row["source_ids"]),
                announcement_date=date_data(
                    parse_observation_date(row["announcement_date"], kind="announcement")
                ),
                effective_date=date_data(effective),
                strength="possible",
                corporate_status="confirmed"
                if row["status"] == "completed"
                and any(sources.get(s) == "corporate_record" for s in row["source_ids"])
                else "unknown",
                organizational_transfer_support=support,
                employment_confirmation=False,
                uncertainty=["date_overlap_not_temporal_proof"]
                + ([] if effective.start else ["effective_date_missing"])
                + ([] if scoped else ["record_scope_not_matched"]),
            )
        )
    return bounded_output(result)
