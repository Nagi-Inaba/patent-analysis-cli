"""M03 witnessed person/classification incidence and M06 neutral features.

Full/fractional classification denominators are each person's witnessed codes
within the unit, NOT the unit-wide code union. Reference includes all identities,
including reserved unresolved mass. No display cutoffs or top-N normalization.
"""

from __future__ import annotations

import math
from collections import defaultdict
from fractions import Fraction

from patent_analysis.inventor_graph import eligible, person_json, prepare
from patent_analysis.inventor_numeric import checked, exact, finish, invalid, number, person_token
from patent_analysis.inventor_units import aggregate_contributions

MAX_COLUMNS = 128


def incidence(units, records, *, person_weight, classification_weight):
    if classification_weight not in {"full", "fractional"}:
        invalid()
    aggregate_contributions(units, person_weight=person_weight)
    columns = sorted({c for row in records.values() for c in row.classifications})
    if len(columns) > MAX_COLUMNS or len({c[0] for c in columns}) > 1:
        invalid()
    values = defaultdict(Fraction)
    witnessed_units = defaultdict(set)
    missing = 0
    for unit in sorted(units, key=lambda u: u.unit_id):
        codes = defaultdict(set)
        for rid in unit.observation_ids:
            row = records[rid]
            for person in row.inventor_keys:
                codes[person].update(row.classifications)
        for person in unit.inventor_keys:
            observed = sorted(codes[person])
            if not observed:
                missing += 1
                continue
            person_value = (
                Fraction(1, len(unit.inventor_keys))
                if person_weight == "fractional"
                else Fraction(1)
            )
            value = person_value / (len(observed) if classification_weight == "fractional" else 1)
            for code in observed:
                values[person, code] = checked(values[person, code] + value)
                witnessed_units[person, code].add(unit.unit_id)
    return columns, values, witnessed_units, missing


def _profile_summaries(columns, counts, identities, activities):
    """Exact full-population summaries without materializing incidence cells."""
    person_totals = defaultdict(Fraction)
    for (person, _code), count in sorted(counts.items()):
        person_totals[person] = checked(person_totals[person] + count)
    profiles = []
    for person in sorted(identities):
        selected = [(c, counts[person, c]) for c in columns if (person, c) in counts]
        denominator = person_totals[person]
        shares = [float(count / denominator) for _, count in selected] if denominator else []
        predominant = min(selected, key=lambda v: (-v[1], v[0]))[0] if selected else None
        profiles.append(
            {
                **person_json(person, identities),
                "eligible": eligible(person),
                "activity": exact(activities[person]),
                "classification_total": exact(denominator),
                "entropy": number(-math.fsum(s * math.log2(s) for s in shares)) if shares else None,
                "hhi": number(math.fsum(s * s for s in shares)) if shares else None,
                "predominant_classification": list(predominant) if predominant else None,
                "undefined_reason": None if selected else "missing_classification",
            }
        )
    return profiles, person_totals


def technology_profiles(units, observations, *, person_weight="full", classification_weight="full"):
    records, identities = prepare(units, observations)
    columns, counts, evidence, missing = incidence(
        units, records, person_weight=person_weight, classification_weight=classification_weight
    )
    totals = defaultdict(Fraction)
    for (_person, code), count in sorted(counts.items()):
        totals[code] = checked(totals[code] + count)
    mass = checked(sum(totals.values(), Fraction(0)))
    reference = {c: totals[c] / mass if mass else None for c in columns}
    activities = dict(aggregate_contributions(units, person_weight=person_weight).people)
    profiles, person_totals = _profile_summaries(columns, counts, identities, activities)
    cells = []
    for person in sorted(identities):
        selected = [(c, counts[person, c]) for c in columns if (person, c) in counts]
        denominator = person_totals[person]
        for code, count in selected:
            share = count / denominator
            cells.append(
                {
                    "person_token": person_token(person),
                    "classification": list(code),
                    "count": exact(count),
                    "unit_count": len(evidence[person, code]),
                    "share": number(share),
                    "relative_specialization": number(share / reference[code])
                    if reference[code]
                    else None,
                }
            )
    return finish(
        {
            "profiles": profiles,
            "cells": cells,
            "classifications": [
                {
                    "classification": list(c),
                    "count": exact(totals[c]),
                    "reference_share": number(reference[c]) if reference[c] is not None else None,
                }
                for c in columns
            ],
            "basis": {
                "unit": units[0].unit if units else None,
                "person_weight": person_weight,
                "classification_weight": classification_weight,
                "reference": "all_person_witnessed_classification_contributions",
                "classification_denominator": "person_witnessed_unit_codes",
                "precision": 12,
            },
            "coverage": {
                "units": len(units),
                "records": len(records),
                "missing_classification_memberships": missing,
                "ambiguous_people": sum(not eligible(p) for p in identities),
                "classification_mass": exact(mass),
            },
        }
    )


def technology_similarity(
    units,
    observations,
    *,
    person_weight="full",
    classification_weight="full",
    feature="composition",
    co_inventor_overlay=False,
):
    """Neutral full unordered pair similarities (including diagonal), never layout.

    TF-IDF = count * (1 + ln((1 + eligible_people)/(1 + document_frequency))).
    Zero vectors and ambiguous identities have undefined cosine, not zero evidence.
    """
    if feature not in {"composition", "count", "tfidf"} or type(co_inventor_overlay) is not bool:
        invalid()
    records, identities = prepare(units, observations)
    columns, counts, _, _ = incidence(
        units, records, person_weight=person_weight, classification_weight=classification_weight
    )
    people = sorted(identities)
    n_eligible = sum(eligible(p) for p in people)
    df = {c: sum(counts.get((p, c), 0) > 0 for p in people if eligible(p)) for c in columns}
    vectors = {}
    features = []
    norms = {}
    for p in people:
        raw = [float(counts.get((p, c), 0)) for c in columns]
        total = math.fsum(raw)
        if feature == "composition":
            vector = [v / total if total else 0.0 for v in raw]
        elif feature == "tfidf":
            vector = [
                v * (1 + math.log((1 + n_eligible) / (1 + df[c])))
                for c, v in zip(columns, raw, strict=True)
            ]
        else:
            vector = raw
        norm = math.sqrt(math.fsum(v * v for v in vector))
        reason = "ambiguous_identity" if not eligible(p) else ("zero_vector" if not norm else None)
        vectors[p] = vector
        norms[p] = norm if reason is None else 0.0
        features.append(
            {
                **person_json(p, identities),
                "values": [number(v) for v in vector],
                "undefined_reason": reason,
            }
        )
    similarities = []
    # Preflight conservative minimum per-pair output before all-pair enumeration.
    if len(people) * (len(people) + 1) // 2 * 100 > 200 * 1024:
        invalid()
    for i, p in enumerate(people):
        for q in people[i:]:
            cosine = None
            reason = "undefined_profile"
            if norms[p] and norms[q]:
                cosine = math.fsum(a * b for a, b in zip(vectors[p], vectors[q], strict=True)) / (
                    norms[p] * norms[q]
                )
                if not -1e-12 <= cosine <= 1 + 1e-12:
                    invalid()
                cosine = number(min(1.0, max(0.0, cosine)))
                reason = None
            shared = [
                list(c)
                for c, a, b in zip(columns, vectors[p], vectors[q], strict=True)
                if a > 0 and b > 0
            ]
            similarities.append(
                {
                    "source": person_token(p),
                    "target": person_token(q),
                    "cosine": cosine,
                    "undefined_reason": reason,
                    "shared_classifications": shared,
                }
            )
    overlays = []
    if co_inventor_overlay:
        contributions = aggregate_contributions(units)
        overlays = [
            {"source": person_token(a), "target": person_token(b), "weight": exact(w)}
            for (a, b), w in contributions.pairs
            if eligible(a) and eligible(b)
        ]
    activities = dict(aggregate_contributions(units, person_weight=person_weight).people)
    summaries, _ = _profile_summaries(columns, counts, identities, activities)
    return finish(
        {
            "features": features,
            "profiles": summaries,
            "classifications": [list(c) for c in columns],
            "similarities": similarities,
            "co_inventor_edges": overlays,
            "basis": {
                "feature": feature,
                "person_weight": person_weight,
                "classification_weight": classification_weight,
                "precision": 12,
                "distance": "unit_vector_chord",
                "pair_storage": "upper_triangle_with_diagonal",
                "tfidf": "count_times_1_plus_ln_smoothed_eligible_document_frequency",
            },
            "coverage": {
                "people": len(people),
                "undefined_profiles": sum(not norms[p] for p in people),
            },
        }
    )
