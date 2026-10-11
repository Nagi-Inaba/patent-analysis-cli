"""M06 neutral technology features and similarities, never MDS coordinates."""

from patent_analysis.inventor_profiles import technology_similarity

from . import _inventor_common as c

ANALYSIS_ID = "inventor-similarity.v1"
VARIANT = "points"


def validate_parameters(value):
    return c.validate_parameters(
        value,
        choices=c.PROFILE_CHOICES,
        extras={
            "feature": ("composition", lambda v: v in ("composition", "count", "tfidf")),
            "co_inventor_overlay": (False, lambda v: type(v) is bool),
        },
    )


def required_roles(value):
    return c.unit_roles(validate_parameters(value), "classification")


def _compute(units, observations, p, inputs):
    return technology_similarity(
        units,
        observations,
        person_weight=p["person_weight"],
        classification_weight=p["classification_weight"],
        feature=p["feature"],
        co_inventor_overlay=p["co_inventor_overlay"],
    )


def analyze_inventor_similarity_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        compute=_compute,
    )
