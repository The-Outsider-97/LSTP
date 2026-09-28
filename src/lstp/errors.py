"""Stable, payload-free diagnostics for the implemented input boundary."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    line: int | None = None
    column: int | None = None


class LSTPError(Exception):
    """Base for public library failures (not a wire-level protocol error)."""

    def __init__(self, diagnostic: Diagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)


class JSONInputError(LSTPError):
    """Invalid JSON or invalid Unicode at the input boundary."""


class ResourceLimitError(LSTPError):
    """Input exceeds the documented implementation resource profile."""
