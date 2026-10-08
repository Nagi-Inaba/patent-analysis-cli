"""Closed year extraction used by normalized date roles."""

from __future__ import annotations

import re

_YEAR = re.compile(r"(?<!\d)(?:18|19|20|21)\d{2}(?!\d)")


def extract_year(value: str) -> str:
    match = _YEAR.search(value)
    return match.group(0) if match is not None else ""
