"""One verified patent read, one read per sidecar, aliases before population filters."""

from __future__ import annotations

import ntpath
from dataclasses import dataclass
from pathlib import PurePosixPath

from patent_analysis.analysis_inputs import records_population_spec
from patent_analysis.dataset_v2 import read_dataset_v2
from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_inputs import PreparedInventorInputs, prepare_inventor_dataset
from patent_analysis.inventor_models import PatentObservation
from patent_analysis.inventor_sidecars import (
    SidecarSnapshot,
    _relative,
    read_inventor_sidecar,
    read_inventor_sidecar_csv,
    validate_observation_references,
)
from patent_analysis.inventor_units import form_units


@dataclass(frozen=True, slots=True)
class InventorExecutionInputs:
    prepared: PreparedInventorInputs
    snapshot: SidecarSnapshot | None
    full_observations: tuple[PatentObservation, ...]


def prepare_execution(source, spec, parameters, *, allowed_root):
    if spec["population"].get("family_mode") != "records":
        raise DatasetInputError("input is invalid")
    population, _ = records_population_spec(spec["population"])
    auxiliary = parameters.get("auxiliary")
    if auxiliary:
        paths = (
            [auxiliary["path"]] if auxiliary["format"] == "json" else auxiliary["tables"].values()
        )
        for path in paths:
            relative = _relative(path)
            if any(
                ntpath.isreserved(part) for part in PurePosixPath(relative.replace("\\", "/")).parts
            ):
                raise DatasetInputError("input path is not permitted")
    dataset = read_dataset_v2(source, allowed_root=allowed_root)
    kwargs = dict(
        bindings=spec["resolution"]["bindings"],
        date_kind=parameters.get("date_kind", "filing"),
        classification_scheme=parameters.get("classification_scheme", "IPC"),
        classification_level=parameters.get("classification_level", "full"),
    )
    # The full unfiltered registry validates citations/reviews/events even when the
    # eventual population excludes their records. This uses the same byte snapshot.
    full = prepare_inventor_dataset(dataset, **kwargs)
    records = tuple(o.record_id for o in full.observations)
    people = tuple(
        sorted({p.raw_id for o in full.observations for p in o.inventors if p.raw_id is not None})
    )
    snapshot = None
    if auxiliary:
        joins = dict(allowed_root=allowed_root, inventor_ids=people, record_ids=records)
        if auxiliary["format"] == "json":
            snapshot = read_inventor_sidecar(auxiliary["path"], **joins)
        else:
            snapshot = read_inventor_sidecar_csv(
                auxiliary["tables"], version=auxiliary["version"], **joins
            )
        kwargs["resolver"] = snapshot.identity_resolver()
        full = prepare_inventor_dataset(dataset, **kwargs)
        validate_observation_references(snapshot, full.observations, inventor_ids=people)
    # Validate complete record/publication consistency before filters can conceal
    # conflicting declarations. This is an immutable snapshot check, not aggregation.
    form_units(full.observations, unit="records")
    prepared = prepare_inventor_dataset(dataset, population=population, **kwargs)
    return InventorExecutionInputs(prepared, snapshot, full.observations)
