"""M02 literal-focus ego extraction after full-graph metrics."""

from patent_analysis.inventor_graph import co_inventor_graph, ego_network

from . import _inventor_common as c

ANALYSIS_ID = "inventor-ego-network.v1"
VARIANT = "network"


def validate_parameters(value):
    return c.validate_parameters(
        value,
        extras={
            "focus": (
                None,
                lambda v: (
                    isinstance(v, (list, tuple))
                    and len(v) == 2
                    and v[0] in ("id", "name")
                    and isinstance(v[1], str)
                    and bool(v[1])
                ),
            ),
            "hops": (1, lambda v: type(v) is int and v in (1, 2, 3)),
        },
        required=("focus",),
    )


def required_roles(value):
    return c.unit_roles(validate_parameters(value))


def _compute(units, observations, p, inputs):
    graph = co_inventor_graph(
        units,
        observations,
        person_weight=p["person_weight"],
        pair_weight=p["pair_weight"],
        community_method=p["community_method"],
    )
    return ego_network(graph, focus=tuple(p["focus"]), hops=p["hops"])


def analyze_inventor_ego_network_csv(source, spec, *, allowed_root):
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        compute=_compute,
    )
