"""M08 patent-applicant episodes and independently reviewed move candidates."""

from collections.abc import Mapping

from patent_analysis.inventor_identity import text_ok
from patent_analysis.inventor_mobility import build_mobility

from . import _inventor_common as c

ANALYSIS_ID = "inventor-mobility.v1"
VARIANT = "network"


def validate_parameters(value):
    p = c.validate_parameters(
        value,
        choices=("date_kind", "classification_scheme", "classification_level"),
        extras={
            "minimum_observations": (1, lambda v: type(v) is int and 1 <= v <= 5000),
            "maximum_gap_years": (5, lambda v: type(v) is int and 0 <= v <= 9998),
            "review_bindings": (
                None,
                lambda v: (
                    v is None
                    or isinstance(v, Mapping)
                    and len(v) <= 5000
                    and all(
                        text_ok(k)
                        and isinstance(refs, (list, tuple))
                        and len(refs) <= 64
                        and all(text_ok(r) for r in refs)
                        and len(set(refs)) == len(refs)
                        for k, refs in v.items()
                    )
                ),
            ),
        },
    )
    p["unit"] = "records"
    if p["review_bindings"] is not None:
        p["review_bindings"] = {k: tuple(refs) for k, refs in p["review_bindings"].items()}
    return p


def required_roles(value):
    return c.unit_roles(validate_parameters(value), "date", "applicant_ids")


def _compute(units, observations, p, inputs):
    return build_mobility(
        observations,
        inputs.snapshot,
        minimum_observations=p["minimum_observations"],
        maximum_gap_years=p["maximum_gap_years"],
        review_bindings=p["review_bindings"],
    )


def analyze_inventor_mobility_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        compute=_compute,
    )
