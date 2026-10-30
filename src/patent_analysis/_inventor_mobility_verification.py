"""Mobility evidence entry point and authoritative audit verification."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping

from patent_analysis._inventor_mobility_candidates import build_mobility
from patent_analysis._inventor_mobility_common import _fail
from patent_analysis.corporate_history import bounded_output
from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_models import PatentObservation
from patent_analysis.inventor_sidecars import SidecarSnapshot


def build_mobility_evidence(
    observations: tuple[PatentObservation, ...],
    snapshot: SidecarSnapshot | None = None,
    *,
    minimum_observations: int = 1,
    maximum_gap_years: int = 5,
    review_bindings: Mapping[str, tuple[str, ...]] | None = None,
) -> dict:
    """M10 retains all M08 rows and histories, with identical canonical candidate IDs."""
    return build_mobility(
        observations,
        snapshot,
        minimum_observations=minimum_observations,
        maximum_gap_years=maximum_gap_years,
        review_bindings=review_bindings,
    )


def _review_component_seeds(reviews):
    """One seed per attached supersession component; original binding cap stays 64."""
    links = defaultdict(set)
    remaining = {r["review_id"] for r in reviews}
    for r in reviews:
        parent = r["supersedes_review_id"]
        if parent is not None:
            links[r["review_id"]].add(parent)
            links[parent].add(r["review_id"])
    seeds = []
    while remaining:
        seed = min(remaining)
        seeds.append(seed)
        remaining.remove(seed)
        stack = [seed]
        while stack:
            for linked in links[stack.pop()] & remaining:
                remaining.remove(linked)
                stack.append(linked)
    return tuple(seeds)


def _verified_mobility(mobility, observations, snapshot):
    """Rebuild with authoritative thresholds and the explicit review component bindings.

    The entire M08 audit must match, not just claimed statuses or candidate IDs.
    Explicit seeds can be reconstructed from their attached review components:
    rebinding the full component preserves supersession/branch semantics.
    """
    try:
        if not isinstance(mobility, dict):
            _fail()
        bounded_output(mobility)
        provenance = mobility["provenance"]
        basis = provenance["review_binding_basis"]
        if basis not in {"explicit_candidate_ids", "unambiguous_exact_scope"}:
            _fail()
        bindings = (
            {
                c["candidate_id"]: _review_component_seeds(c["reviews"])
                for c in mobility["candidates"]
            }
            if basis == "explicit_candidate_ids"
            else None
        )
        verified = build_mobility(
            observations,
            snapshot,
            minimum_observations=provenance["minimum_observations"],
            maximum_gap_years=provenance["maximum_gap_years"],
            review_bindings=bindings,
        )
        if json.dumps(mobility, sort_keys=True, allow_nan=False) != json.dumps(
            verified, sort_keys=True, allow_nan=False
        ):
            _fail()
        return verified
    except DatasetInputError:
        raise
    except (KeyError, TypeError, ValueError, RecursionError, OverflowError):
        _fail()
