"""Canonical semantic containers for LSTP v0.1.

This module intentionally models only the protocol boundary that is unambiguous in
the authoritative Whitepaper: an Octad has exactly eight semantic domains.  It does
not guess unresolved carrier grammar, permission subfields, or canonical byte
serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

JSONValue = None | bool | int | float | str | tuple["JSONValue", ...] | Mapping[str, "JSONValue"]


def _freeze(value: Any) -> JSONValue:
    """Return an immutable snapshot suitable for deterministic semantic equality."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        frozen = {str(key): _freeze(item) for key, item in value.items()}
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    raise TypeError(f"unsupported canonical value type: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class Octad:
    """The eight canonical semantic domains, independent of transport envelope."""

    pragmatics: JSONValue
    atoms: JSONValue
    relations: JSONValue
    context: JSONValue
    confidence: JSONValue
    permissions: JSONValue
    evidence: JSONValue
    output: JSONValue

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            object.__setattr__(self, name, _freeze(getattr(self, name)))

    def semantic_items(self) -> tuple[tuple[str, JSONValue], ...]:
        """Return fields in the authoritative Octad order."""
        return (
            ("pragmatics", self.pragmatics),
            ("atoms", self.atoms),
            ("relations", self.relations),
            ("context", self.context),
            ("confidence", self.confidence),
            ("permissions", self.permissions),
            ("evidence", self.evidence),
            ("output", self.output),
        )


@dataclass(frozen=True, slots=True)
class PacketEnvelope:
    """Non-Octad packet metadata kept separate from semantic equality.

    The envelope is deliberately minimal.  Carrier/audit structures remain opaque
    until their normative contracts are reconciled; no field here grants authority.
    """

    octad: Octad
    packet_id: str
    protocol_version: str
    carrier: JSONValue = field(default_factory=dict)
    audit: JSONValue = field(default_factory=dict)
    extensions: JSONValue = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.packet_id:
            raise ValueError("packet_id must not be empty")
        if not self.protocol_version:
            raise ValueError("protocol_version must not be empty")
        for name in ("carrier", "audit", "extensions"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))

    def semantically_equals(self, other: object) -> bool:
        """Compare semantic Octad content only, excluding envelope metadata."""
        return isinstance(other, PacketEnvelope) and self.octad == other.octad
