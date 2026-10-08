"""Closed accessibility metadata added to verified normalized drawing SVGs."""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from xml.etree import ElementTree

_ROOT = re.compile(rb"<svg(?:\s[^<>]*)?>")
_SVG = "{http://www.w3.org/2000/svg}svg"


def _text(value: str) -> str:
    cleaned = "".join(
        f"\\u{ord(char):04x}" if (unicodedata.category(char) in {"Cc", "Cf", "Cs"}
                                   or ord(char) in {0xFFFE, 0xFFFF}) else char
        for char in value)
    return html.escape(cleaned, quote=False)


def add_svg_accessibility(svg: bytes, model_bytes: bytes) -> bytes:
    """Preserve drawing bytes, adding only fixed ARIA attributes and text-only nodes."""
    if type(svg) is not bytes or type(model_bytes) is not bytes or len(model_bytes) > 2 * 1024**2:
        raise ValueError("invalid accessibility input")
    opening = _ROOT.match(svg)
    if opening is None:
        raise ValueError("invalid SVG root")
    root = ElementTree.fromstring(opening.group() + b"</svg>")
    if root.tag not in {_SVG, "svg"} or not set(root.attrib) <= {"width", "height", "viewBox"}:
        raise ValueError("unexpected SVG root attributes")
    model = json.loads(model_bytes)
    title = model["title"]
    population = model["population"]
    warnings = model["warnings"]
    if (not isinstance(title, str) or not title or len(title) > 4096
            or not isinstance(warnings, list)):
        raise ValueError("invalid accessibility metadata")
    input_rows, analyzed_rows = population["input_rows"], population["analyzed_rows"]
    if any(type(count) is not int or count < 0 for count in (input_rows, analyzed_rows)):
        raise ValueError("invalid accessibility counts")
    description = (f"入力: {input_rows}行。分析対象: {analyzed_rows}件。警告: {len(warnings)}件。"
                   "数値、分析条件、警告の詳細は対応する集計表を参照してください。")
    suffix = hashlib.sha256(model_bytes + svg).hexdigest()[:24]
    prefix = f"pa-a11y-{suffix}"
    if f'id="{prefix}-'.encode() in svg:
        raise ValueError("accessibility id collision")
    attributes = (f' role="img" aria-labelledby="{prefix}-title"'
                  f' aria-describedby="{prefix}-desc"').encode()
    metadata = (f'<title id="{prefix}-title">{_text(title)}</title>'
                f'<desc id="{prefix}-desc">{_text(description)}</desc>').encode()
    if len(metadata) > 64 * 1024:
        raise ValueError("accessibility metadata exceeds limit")
    return svg[:opening.end() - 1] + attributes + b">" + metadata + svg[opening.end():]
