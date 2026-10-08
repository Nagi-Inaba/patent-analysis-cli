from __future__ import annotations

from typing import Any

_TOKEN = object()
_ERROR_MESSAGES = {
    "render.invalid": "Render input was rejected",
    "input.invalid": "Render input could not be read or parsed",
    "usage.invalid": "Invalid patent-analysis render arguments",
    "renderer.unavailable": "Trusted local renderer is unavailable",
    "output.conflict": "Render output conflicts with an existing artifact",
}


class RenderError(ValueError):
    """Fixed public failure for the trusted-local render contract."""

    def __init__(self, token: object, code: str) -> None:
        if token is not _TOKEN or code not in _ERROR_MESSAGES:
            raise TypeError("RenderError is factory-only")
        safe_message = _ERROR_MESSAGES[code]
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
        self.retryable = False
        self.details: dict[str, object] = {}
        self.__suppress_context__ = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.safe_message,
            "retryable": False,
            "details": {},
        }

    def __repr__(self) -> str:
        return f"RenderError({self.code!r}, {self.safe_message!r})"


def _make_render_error(code: str) -> RenderError:
    try:
        return RenderError(_TOKEN, code)
    except (TypeError, ValueError):
        return RenderError(_TOKEN, "renderer.unavailable")
