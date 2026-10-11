"""M07 snapshot-specific patent citation observations, not personal ability.

Citation rows are immutable sidecar evidence mappings, not datasets/adapters.
Unknown counts differ from zero; family counts never silently sum publications.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from fractions import Fraction

from patent_analysis.inventor_graph import eligible, person_json, prepare
from patent_analysis.inventor_identity import text_ok
from patent_analysis.inventor_models import parse_observation_date
from patent_analysis.inventor_numeric import checked, exact, finish, invalid
from patent_analysis.inventor_profiles import MAX_COLUMNS
from patent_analysis.inventor_units import aggregate_contributions

_CITATION_FIELDS = {
    "citation_id",
    "record_id",
    "count",
    "snapshot_date",
    "citing_ids",
    "source_ids",
}


def _citations(citations, records, snapshot):
    if not isinstance(citations, tuple) or len(citations) > 5000:
        invalid()
    selected = {}
    seen = {}
    primary = {}
    for row in citations:
        if not isinstance(row, Mapping) or set(row) != _CITATION_FIELDS:
            invalid()
        if (
            not text_ok(row["citation_id"])
            or not text_ok(row["record_id"])
            or row["record_id"] not in records
            or not isinstance(row["source_ids"], (tuple, list))
            or not row["source_ids"]
            or len(row["source_ids"]) > 64
            or not all(text_ok(s) for s in row["source_ids"])
            or len(set(row["source_ids"])) != len(row["source_ids"])
        ):
            invalid()
        date = parse_observation_date(row["snapshot_date"], kind="citation_snapshot")
        if date.start is None:
            invalid()
        count = row["count"]
        ids = row["citing_ids"]
        if count is not None and (type(count) is not int or not 0 <= count <= 9007199254740991):
            invalid()
        if ids is not None:
            if (
                not isinstance(ids, (tuple, list))
                or len(ids) > 64
                or not all(text_ok(i) for i in ids)
                or len(set(ids)) != len(ids)
                or count != len(ids)
            ):
                invalid()
            ids = tuple(sorted(ids))
        signature = (count, ids)
        key = (row["record_id"], row["snapshot_date"])
        if seen.setdefault(key, signature) != signature:
            invalid()
        if primary.setdefault(row["citation_id"], (key, signature)) != (key, signature):
            invalid()
        if row["snapshot_date"] == snapshot:
            selected[row["record_id"]] = signature
    return selected, sum(date != snapshot for _, date in seen)


def _unit_values(units, selected, basis, representatives):
    if basis not in {"unique_citing_ids", "record_counts", "representative_record"}:
        invalid()
    if basis == "representative_record":
        if (
            not isinstance(representatives, Mapping)
            or set(representatives) != {u.unit_id for u in units}
            or any(representatives[u.unit_id] not in u.observation_ids for u in units)
        ):
            invalid()
    elif representatives is not None:
        invalid()
    if basis == "record_counts" and any(u.unit in {"family", "application"} for u in units):
        invalid()
    result = {}
    for unit in units:
        ids = unit.observation_ids
        if basis == "representative_record":
            count = selected.get(representatives[unit.unit_id], (None, None))[0]
            reason = "missing_citations" if count is None else None
        elif basis == "unique_citing_ids":
            evidence = [selected.get(r, (None, None))[1] for r in ids]
            count = (
                len({i for group in evidence for i in group})
                if all(v is not None for v in evidence)
                else None
            )
            reason = "missing_citing_ids" if count is None else None
        else:
            known = {selected[r][0] for r in ids if r in selected and selected[r][0] is not None}
            if len(known) > 1:
                invalid()
            count = next(iter(known)) if known else None
            reason = "missing_citations" if count is None else None
        result[unit.unit_id] = (count, reason)
    return result


def citation_metrics(
    units,
    observations,
    citations,
    *,
    snapshot_date,
    citation_basis="record_counts",
    representative_records=None,
    person_weight="full",
    min_cohort_units=5,
    recent_start_year=None,
):
    """Full-population metrics, unit evidence, same-snapshot filing-field baselines.

    Field reference weights are 1/number of unit observed codes. Baseline mean is
    sum(weight*citations)/sum(weight), with minimum DISTINCT units per field/year.
    Unit adjustment is the classification-weighted mean of count/baseline. Any
    missing field baseline makes unit adjustment undefined. Raw sums/means cover
    known citations only and explicitly flag partial coverage; adjusted person
    sums/means require complete adjustment coverage of that person's units.
    Recent activity requires known membership for every own witnessed unit; a
    recent dated witness proves presence even when that unit has missing dates.
    """
    records, identities = prepare(units, observations)
    contributions = aggregate_contributions(units, person_weight=person_weight)
    if (
        type(min_cohort_units) is not int
        or not 1 <= min_cohort_units <= 5000
        or (
            recent_start_year is not None
            and (type(recent_start_year) is not int or not 1 <= recent_start_year <= 9999)
        )
    ):
        invalid()
    snapshot = parse_observation_date(snapshot_date, kind="citation_snapshot")
    if snapshot.start is None:
        invalid()
    columns = {c for row in records.values() for c in row.classifications}
    if len(columns) > MAX_COLUMNS or len({c[0] for c in columns}) > 1:
        invalid()
    selected, ignored = _citations(citations, records, snapshot_date)
    values = _unit_values(units, selected, citation_basis, representative_records)
    years = [r.observed_date.start.year for r in records.values() if r.observed_date.start]
    recent_start = (
        recent_start_year
        if recent_start_year is not None
        else (max(1, max(years) - 2) if years else None)
    )
    cohorts = defaultdict(dict)
    unit_cohort = {}
    cohort_reasons = {}
    for unit in sorted(units, key=lambda u: u.unit_id):
        dates = [records[r].observed_date for r in unit.observation_ids]
        reason = None
        year = None
        if any(d.kind != "filing" for d in dates):
            reason = "not_filing_date"
        elif any(d.start is None for d in dates):
            reason = "missing_filing_date"
        elif len({d.start.year for d in dates}) > 1:
            reason = "multiple_filing_years"
        else:
            year = dates[0].start.year
        if not unit.classifications:
            reason = reason or "missing_classification"
        cohort_reasons[unit.unit_id] = reason
        unit_cohort[unit.unit_id] = year
        count, _ = values[unit.unit_id]
        if count is not None and reason is None:
            for c in unit.classifications:
                cohorts[year, c][unit.unit_id] = (Fraction(1, len(unit.classifications)), count)
    baselines = {}
    baseline_rows = []
    for (year, code), evidence in sorted(cohorts.items()):
        denominator = checked(sum((w for w, _ in evidence.values()), Fraction(0)))
        numerator = checked(sum((w * count for w, count in evidence.values()), Fraction(0)))
        mean = checked(numerator / denominator)
        reason = (
            "insufficient_cohort_units"
            if len(evidence) < min_cohort_units
            else ("zero_cohort_mean" if not mean else None)
        )
        baselines[year, code] = (mean, reason)
        baseline_rows.append(
            {
                "filing_year": year,
                "classification": list(code),
                "distinct_units": len(evidence),
                "reference_weight": exact(denominator),
                "raw_mean": exact(mean),
                "undefined_reason": reason,
            }
        )
    adjusted = {}
    unit_rows = []
    for unit in sorted(units, key=lambda u: u.unit_id):
        count, citation_reason = values[unit.unit_id]
        reasons = set()
        if citation_reason:
            reasons.add(citation_reason)
        if cohort_reasons[unit.unit_id]:
            reasons.add(cohort_reasons[unit.unit_id])
        value = Fraction(0)
        if not reasons:
            for code in unit.classifications:
                baseline, reason = baselines.get(
                    (unit_cohort[unit.unit_id], code), (None, "insufficient_cohort_units")
                )
                if reason:
                    reasons.add(reason)
                else:
                    value = checked(
                        value + Fraction(count, 1) / baseline / len(unit.classifications)
                    )
        adjusted[unit.unit_id] = value if not reasons else None
        unit_rows.append(
            {
                "unit_id": unit.unit_id,
                "record_ids": list(unit.observation_ids),
                "citation_count": count,
                "filing_year": unit_cohort[unit.unit_id],
                "adjusted_value": exact(value) if not reasons else None,
                "undefined_reasons": sorted(reasons),
            }
        )
    activities = dict(contributions.people)
    reasons_by_unit = {u["unit_id"]: u["undefined_reasons"] for u in unit_rows}
    people = []
    unplottable = []
    allocated = Fraction(0)
    reserved = Fraction(0)
    for p in sorted(identities):
        activity = activities[p]
        member_units = [u for u in units if p in u.inventor_keys]
        known_activity = Fraction(0)
        raw_sum = Fraction(0)
        adjusted_sum = Fraction(0)
        recent = Fraction(0)
        recent_complete = recent_start is not None
        reasons = set()
        if not eligible(p):
            reasons.add("ambiguous_identity")
        complete = True
        for unit in member_units:
            weight = (
                Fraction(1, len(unit.inventor_keys))
                if person_weight == "fractional"
                else Fraction(1)
            )
            count, citation_reason = values[unit.unit_id]
            if count is None:
                reasons.add("missing_citations")
                if citation_reason:
                    reasons.add(citation_reason)
            else:
                known_activity += weight
                raw_sum = checked(raw_sum + weight * count)
            adjustment = adjusted[unit.unit_id]
            if adjustment is None:
                complete = False
                reasons.update(reasons_by_unit[unit.unit_id])
            else:
                adjusted_sum = checked(adjusted_sum + weight * adjustment)
            person_dates = [
                records[r].observed_date.start
                for r in unit.observation_ids
                if p in records[r].inventor_keys
            ]
            missing_person_date = any(date is None for date in person_dates)
            if missing_person_date:
                reasons.add("missing_activity_date")
            if recent_start is not None and any(
                d is not None and d.year >= recent_start for d in person_dates
            ):
                recent += weight
            elif missing_person_date:
                recent_complete = False
        allocated = checked(allocated + raw_sum)
        if not eligible(p):
            reserved = checked(reserved + raw_sum)
        metrics = {
            **person_json(p, identities),
            "activity": exact(activity),
            "known_citation_activity": exact(known_activity),
            "raw_sum": exact(raw_sum) if known_activity else None,
            "raw_mean": exact(raw_sum / known_activity) if known_activity else None,
            "adjusted_sum": exact(adjusted_sum) if complete else None,
            "adjusted_mean": exact(adjusted_sum / activity) if complete else None,
            "recent_activity": exact(recent) if recent_complete else None,
            "partial_citation_coverage": known_activity != activity,
            "unplottable_reasons": sorted(reasons),
        }
        people.append(metrics)
        if reasons:
            unplottable.append(
                {"person_token": metrics["person_token"], "reasons": sorted(reasons)}
            )
    return finish(
        {
            "people": people,
            "units": unit_rows,
            "cohorts": baseline_rows,
            "unplottable": unplottable,
            "basis": {
                "unit": units[0].unit if units else None,
                "snapshot_date": snapshot_date,
                "citation_basis": citation_basis,
                "person_weight": person_weight,
                "representative_records": [
                    {"unit_id": u, "record_id": r}
                    for u, r in sorted((representative_records or {}).items())
                ],
                "min_cohort_units": min_cohort_units,
                "recent_start_year": recent_start,
                "cohort": "same_snapshot_filing_year_observed_unit_classifications",
                "classification_reference_weight": "fractional_unit_codes",
                "raw_mean_denominator": "known_citation_activity",
                "self_citation_information": "unknown",
                "precision": 12,
                "interpretation": "patent_citations_not_personal_ability_or_employment_quality",
            },
            "coverage": {
                "units": len(units),
                "known_citation_units": sum(v[0] is not None for v in values.values()),
                "missing_citation_units": sum(v[0] is None for v in values.values()),
                "known_zero_units": sum(v[0] == 0 for v in values.values()),
                "other_snapshot_record_entries": ignored,
                "selected_source_ids": sorted(
                    {
                        s
                        for row in citations
                        if row["snapshot_date"] == snapshot_date
                        for s in row["source_ids"]
                    }
                ),
                "ambiguous_people": sum(not eligible(p) for p in identities),
                "unit_citation_sum": exact(
                    sum((v[0] for v in values.values() if v[0] is not None), 0)
                ),
                "allocated_citation_sum": exact(allocated),
                "reserved_ambiguous_citations": exact(reserved),
                "unallocated_missing_person_citations": exact(
                    sum((values[u.unit_id][0] or 0 for u in units if not u.inventor_keys), 0)
                ),
            },
        }
    )
