"""Closed set of colour palettes a caller may choose for any SVG mark."""

from __future__ import annotations

RENDER_PALETTES = ("standard", "colorblind", "monochrome", "high-contrast")
DEFAULT_RENDER_PALETTE = "standard"


def apply_render_palette(spec: dict[str, object], palette: str | None) -> dict[str, object]:
    """Record a non-default palette choice in a render spec.

    The default is left out of the spec so a default render keeps the same spec bytes (and
    hash) as before palettes existed.
    """

    if palette is None:
        return spec
    if type(palette) is not str or palette not in RENDER_PALETTES:
        raise ValueError("render palette is invalid")
    if palette != DEFAULT_RENDER_PALETTE:
        spec["palette"] = palette
    return spec


__all__ = ("DEFAULT_RENDER_PALETTE", "RENDER_PALETTES", "apply_render_palette")
