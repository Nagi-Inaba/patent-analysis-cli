from __future__ import annotations

from typing import Any

_FALLBACK_MESSAGE = "input is invalid"
_SAFE_MESSAGES = frozenset(
    {
        _FALLBACK_MESSAGE,
        "input path is not permitted",
        "csv input exceeds published limits",
        "dataset input exceeds published limits",
        "dataset cannot be read",
        "dataset encoding is invalid",
        "dataset header is invalid",
        "dataset CSV format is invalid",
        "dataset exceeds row limit",
        "ranking expansion exceeds published limits",
    }
)


class DatasetInputError(ValueError):
    """Bounded public error for rejected or unreadable local input."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "input.invalid",
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        del code, retryable, details
        safe_message = message if message in _SAFE_MESSAGES else _FALLBACK_MESSAGE
        super().__init__(safe_message)
        self.code = "input.invalid"
        self.safe_message = safe_message
        self.retryable = False
        self.details: dict[str, Any] = {}
        self.__suppress_context__ = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.safe_message,
            "retryable": self.retryable,
            "details": self.details,
        }
