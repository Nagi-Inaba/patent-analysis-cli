"""Immutable startup-approved roots for the local stdio adapter."""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType

from patent_analysis.access import validate_allowed_root

_ROOT_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_REPARSE_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)


class RootError(ValueError):
    def __init__(self, code: str = "input.invalid") -> None:
        self.code = code
        super().__init__("approved root or relative path is invalid")


@dataclass(frozen=True, slots=True)
class ApprovedRoot:
    root_id: str
    path: Path

    def __post_init__(self) -> None:
        if not isinstance(self.root_id, str) or not _ROOT_ID.fullmatch(self.root_id):
            raise RootError()
        try:
            path = Path(self.path)
        except TypeError:
            raise RootError() from None
        object.__setattr__(self, "path", path)


def _is_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(
        _REPARSE_ATTRIBUTE and attributes & _REPARSE_ATTRIBUTE
    )


def _validated_root(value: ApprovedRoot) -> Path:
    try:
        validate_allowed_root(value.path)
        resolved = value.path.resolve(strict=True)
    except (OSError, TypeError, ValueError):
        raise RootError() from None
    if not resolved.is_dir() or _is_reparse(resolved):
        raise RootError()
    return resolved


def _relative_segments(value: object) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise RootError()
    if len(value.encode("utf-8")) > 4096:
        raise RootError()
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive or windows.root:
        raise RootError()
    segments = tuple(value.replace("\\", "/").split("/"))
    if not segments or len(segments) > 128:
        raise RootError()
    for segment in segments:
        if (
            not segment
            or segment in {".", ".."}
            or len(segment) > 255
            or segment.endswith((".", " "))
            or ":" in segment
            or any(ord(character) < 32 or ord(character) == 127 for character in segment)
        ):
            raise RootError()
    return segments


def _is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _root_map(values: Iterable[ApprovedRoot]) -> Mapping[str, Path]:
    result: dict[str, Path] = {}
    try:
        declarations = tuple(values)
    except TypeError:
        raise RootError() from None
    for declaration in declarations:
        if not isinstance(declaration, ApprovedRoot) or declaration.root_id in result:
            raise RootError()
        root = _validated_root(declaration)
        if any(
            _is_within(existing, root) or _is_within(root, existing)
            for existing in result.values()
        ):
            raise RootError()
        result[declaration.root_id] = root
    if not result:
        raise RootError()
    return MappingProxyType(result)


class RootRegistry:
    __slots__ = ("input_roots", "output_roots")

    def __init__(
        self,
        *,
        input_roots: Iterable[ApprovedRoot],
        output_roots: Iterable[ApprovedRoot],
    ) -> None:
        inputs = _root_map(input_roots)
        outputs = _root_map(output_roots)
        if set(inputs) & set(outputs):
            raise RootError()
        if any(
            _is_within(input_path, output_path) or _is_within(output_path, input_path)
            for input_path in inputs.values()
            for output_path in outputs.values()
        ):
            raise RootError()
        self.input_roots = inputs
        self.output_roots = outputs

    @staticmethod
    def _get_root(roots: Mapping[str, Path], root_id: object) -> Path:
        if not isinstance(root_id, str) or root_id not in roots:
            raise RootError()
        return roots[root_id]

    @staticmethod
    def _walk(root: Path, segments: tuple[str, ...], *, create: bool) -> Path:
        # Startup approval is not evidence that the path is still link-free.
        # Reject a replaced root or ancestor before any output side effect.
        try:
            validate_allowed_root(root)
        except (OSError, TypeError, ValueError):
            raise RootError() from None
        current = root
        for segment in segments:
            current = current / segment
            if not os.path.lexists(current):
                if not create:
                    raise RootError()
                try:
                    validate_allowed_root(current.parent)
                    current.mkdir()
                except (OSError, TypeError, ValueError):
                    raise RootError() from None
            if _is_reparse(current):
                raise RootError()
        try:
            resolved = current.resolve(strict=True)
        except OSError:
            raise RootError() from None
        if not _is_within(root, resolved):
            raise RootError()
        return resolved

    def resolve_input(self, root_id: object, relative_path: object) -> Path:
        root = self._get_root(self.input_roots, root_id)
        resolved = self._walk(root, _relative_segments(relative_path), create=False)
        try:
            metadata = resolved.stat(follow_symlinks=False)
        except OSError:
            raise RootError() from None
        if not stat.S_ISREG(metadata.st_mode) or _is_reparse(resolved):
            raise RootError()
        return resolved

    def resolve_output_directory(self, root_id: object, relative_path: object) -> Path:
        root = self._get_root(self.output_roots, root_id)
        resolved = self._walk(root, _relative_segments(relative_path), create=True)
        if not resolved.is_dir() or _is_reparse(resolved):
            raise RootError()
        return resolved


__all__ = ("ApprovedRoot", "RootError", "RootRegistry")
