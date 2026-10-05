"""Stable public diagnostics and error types for LSTP tooling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    line: int | None = None
    column: int | None = None
    path: str | None = None


class LSTPError(Exception):
    """Base for public library failures (not a wire-level protocol error)."""

    def __init__(self, diagnostic: Diagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)


class JSONInputError(LSTPError):
    """Invalid JSON or invalid Unicode at the input boundary."""


class ResourceLimitError(LSTPError):
    """Input exceeds the documented implementation resource profile."""


class LatticeSyntaxError(LSTPError):
    """Lattice text cannot be tokenized or parsed deterministically."""


class CompilationError(LSTPError):
    """Parsed Lattice cannot be mapped to canonical v0.1 without guessing."""


class SemanticValidationError(LSTPError):
    """Canonical structure violates one or more semantic invariants."""

    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        if not diagnostics:
            raise ValueError("SemanticValidationError requires at least one diagnostic")
        self.diagnostics = diagnostics
        super().__init__(diagnostics[0])
