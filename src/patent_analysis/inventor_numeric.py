"""Shared explicit finite/exact JSON boundary for inventor kernels.

Decimal output: 12 places, half-even. Exact integers are decimal strings to avoid
JSON/JavaScript integer loss. No automatic Fraction serialization elsewhere.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, localcontext
from fractions import Fraction

from patent_analysis.errors import DatasetInputError

PRECISION = 12
MAX_RESULT_BYTES = 200 * 1024
MAX_BITS = 128


def invalid() -> None:
    raise DatasetInputError("input is invalid")


def checked(value: Fraction) -> Fraction:
    if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > MAX_BITS:
        invalid()
    return value


def number(value: float | Fraction | int) -> float:
    if isinstance(value, Fraction):
        checked(value)
        with localcontext() as context:
            context.prec = 160
            result = float(round(Decimal(value.numerator) / Decimal(value.denominator), PRECISION))
    else:
        result = round(float(value), PRECISION)
    if not math.isfinite(result):
        invalid()
    return 0.0 if result == 0 else result


def exact(value: Fraction | int) -> dict:
    value = checked(Fraction(value))
    return {
        "value": number(value),
        "numerator": str(value.numerator),
        "denominator": str(value.denominator),
    }


def person_token(key: tuple[str, str]) -> str:
    return json.dumps(list(key), ensure_ascii=False, separators=(",", ":"))


def token_order(token: str) -> tuple[str, str]:
    """Order generated tokens by PersonKey, not JSON escape spelling."""
    return tuple(json.loads(token))


def json_size(value) -> int:
    return len(
        json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(
            "utf-8"
        )
    )


def finish(result: dict, *, reserve_bytes=0) -> dict:
    """Reject nonsemantic types and enforce the full-result byte budget."""

    def visit(value):
        if value is None or isinstance(value, (str, bool)):
            return
        if isinstance(value, int) and abs(value) <= 9007199254740991:
            return
        if isinstance(value, float) and math.isfinite(value):
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if isinstance(value, dict) and all(isinstance(k, str) for k in value):
            for item in value.values():
                visit(item)
            return
        invalid()

    visit(result)
    if json_size(result) + reserve_bytes > MAX_RESULT_BYTES:
        invalid()
    return result


def _numpy():
    try:
        import numpy as np
    except ImportError:
        raise DatasetInputError("input is invalid") from None
    return np


def _canonical_block(gram, eigenvectors, tolerance):
    """Projector pivots + twice-reorthogonalized MGS; near eigenspaces use H½."""
    np = _numpy()
    projector = eigenvectors @ eigenvectors.T
    basis = []
    basis_tolerance = 64 * len(gram) * np.finfo(float).eps
    for pivot in range(len(gram)):
        residual = projector[:, pivot].copy()
        for _ in range(2):
            for q in basis:
                residual -= np.dot(q, residual) * q
        norm = np.linalg.norm(residual)
        if norm <= basis_tolerance:
            continue
        q = residual / norm
        if q[pivot] < 0:
            q = -q
        basis.append(q)
        if len(basis) == eigenvectors.shape[1]:
            break
    if len(basis) != eigenvectors.shape[1]:
        invalid()
    canonical = np.column_stack(basis)
    if (
        np.linalg.norm(canonical.T @ canonical - np.eye(len(basis))) > basis_tolerance * 10
        or np.linalg.norm(canonical @ canonical.T - projector) > basis_tolerance * 10
    ):
        invalid()
    h = canonical.T @ gram @ canonical
    values, vectors = np.linalg.eigh((h + h.T) / 2)
    if np.min(values) < -tolerance:
        invalid()
    root = (vectors * np.sqrt(np.maximum(values, 0))) @ vectors.T
    return canonical @ root


def project_features(features: list[dict], *, duplicate_offset=0.01) -> dict:
    """Presentation-only canonical classical MDS of finite M06 feature rows.

    No change to neutral cosine. Coordinates and display-only offsets are separate.
    Requires optional NumPy; import is lazy. Fixed-env reproducible, not cross-BLAS
    bit-identical. Caller validates persisted neutral data before using this helper.
    """
    if (
        not isinstance(features, list)
        or len(features) > 200
        or not isinstance(duplicate_offset, (float, int))
        or not math.isfinite(duplicate_offset)
        or not 0 <= duplicate_offset <= 1
    ):
        invalid()
    tokens = set()
    widths = set()
    for row in features:
        key = row.get("person_key")
        values = row.get("values")
        if (
            not isinstance(key, list)
            or len(key) != 2
            or not all(isinstance(v, str) for v in key)
            or row.get("person_token") != person_token(tuple(key))
            or row["person_token"] in tokens
            or not isinstance(values, list)
            or len(values) > 128
            or not all(type(v) in {int, float} and math.isfinite(v) and v >= 0 for v in values)
        ):
            invalid()
        tokens.add(row["person_token"])
        widths.add(len(values))
    if len(widths) > 1:
        invalid()
    rows = sorted(features, key=lambda r: r["person_key"])
    valid = [r for r in rows if not r["undefined_reason"] and any(r["values"])]
    coordinates = {}
    rank = 0
    tolerance = 0.0
    stress = energy = None
    reason = "no_nonzero_profiles"
    cut_group = False
    numpy_version = None
    if valid:
        np = _numpy()
        numpy_version = np.__version__
        try:
            raw = np.array([r["values"] for r in valid], dtype=float)
            norms = np.linalg.norm(raw, axis=1)
            if not np.all(np.isfinite(norms)) or np.any(norms == 0):
                invalid()
            normalized = raw / norms[:, None]
            centered = normalized - normalized.mean(axis=0)
            gram = centered @ centered.T
            gram = (gram + gram.T) / 2
            values, vectors = np.linalg.eigh(gram)
            order = np.argsort(-values, kind="stable")
            values, vectors = values[order], vectors[:, order]
            tolerance = (
                64 * len(valid) * np.finfo(float).eps * max(1.0, float(np.max(np.abs(values))))
            )
            if np.min(values) < -tolerance:
                invalid()
            rank = int(np.sum(values > tolerance))
            blocks = []
            first = 0
            while first < rank:
                end = first + 1
                while end < rank and values[first] - values[end] <= tolerance:
                    end += 1
                blocks.append(_canonical_block(gram, vectors[:, first:end], tolerance))
                if first < 2 < end:
                    cut_group = True
                first = end
            full = np.column_stack(blocks) if blocks else np.zeros((len(valid), 0))
            xy = np.zeros((len(valid), 2))
            xy[:, : min(2, rank)] = full[:, :2]
            for row, point in zip(valid, xy, strict=True):
                coordinates[row["person_token"]] = [number(v) for v in point]
            target_squared = np.maximum(
                0, np.sum((normalized[:, None] - normalized[None, :]) ** 2, axis=2)
            )
            projected = np.linalg.norm(xy[:, None] - xy[None, :], axis=2)
            denominator = float(np.sum(np.triu(target_squared, 1)))
            numerator = float(np.sum(np.triu((projected - np.sqrt(target_squared)) ** 2, 1)))
            stress = number(math.sqrt(numerator / denominator)) if denominator > tolerance else None
            energy_denominator = float(np.sum(values[:rank]))
            energy = (
                number(float(np.sum(xy * xy)) / energy_denominator)
                if energy_denominator > tolerance
                else None
            )
            reason = (
                None if stress is not None and energy is not None else "zero_distance_and_energy"
            )
        except np.linalg.LinAlgError:
            invalid()
    coincident = {}
    for row in valid:
        xy = tuple(coordinates[row["person_token"]])
        coincident.setdefault(xy, []).append(row["person_token"])
    offsets = {}
    for members in coincident.values():
        for index, token in enumerate(members):
            offsets[token] = (
                [number(duplicate_offset * (index - (len(members) - 1) / 2)), 0.0]
                if len(members) > 1
                else [0.0, 0.0]
            )
    points = [
        {
            "person_token": r["person_token"],
            "raw_coordinates": coordinates.get(r["person_token"]),
            "display_offset": offsets.get(r["person_token"]),
            "undefined_reason": r["undefined_reason"]
            or (None if r["person_token"] in coordinates else "zero_vector"),
        }
        for r in rows
    ]
    return finish(
        {
            "points": points,
            "distortion": {"stress": stress, "retained_energy": energy, "undefined_reason": reason},
            "basis": {
                "algorithm": "canonical_projector_classical_mds.v1",
                "rank": rank,
                "eigenvalue_tolerance": format(tolerance, ".17g"),
                "numpy_version": numpy_version,
                "cut_eigenspace": cut_group,
                "distance": "unit_vector_chord",
                "precision": 12,
                "offset_basis": "coincident_rounded_projection_display_only",
            },
        }
    )
