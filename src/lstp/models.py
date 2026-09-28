"""Canonical semantic containers for LSTP v0.1.

This module intentionally models only the protocol boundary that is unambiguous in
the authoritative Whitepaper: an Octad has exactly eight semantic domains. It does
not guess unresolved carrier grammar, permission subfields, or canonical byte
serialization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

JSONValue = None | bool | int | float | str | tuple["JSONValue", ...] | Mapping[str, "JSONValue"]


def _freeze(value: Any, *, path: str = "$") -> JSONValue:
    """Return a strict immutable JSON-value snapshot for semantic comparison.

    Canonical semantic containers must not silently coerce host-language values.
    In particular, JSON object keys are strings and JSON numbers exclude NaN and
    infinities. Rejecting those values here keeps the model boundary deterministic
    without claiming a byte-canonical serialization profile.
    """
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite number at {path}")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non-string object key at {path}: {type(key).__name__}")
            frozen[key] = _freeze(item, path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, path=f"{path}[{index}]") for index, item in enumerate(value))
    raise TypeError(f"unsupported canonical value type at {path}: {type(value).__name__}")


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
            object.__setattr__(self, name, _freeze(getattr(self, name), path=f"$.{name}"))

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

    The envelope is deliberately minimal. Carrier/audit structures remain opaque
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
            object.__setattr__(self, name, _freeze(getattr(self, name), path=f"$.{name}"))

    def semantically_equals(self, other: object) -> bool:
        """Compare semantic Octad content only, excluding envelope metadata."""
        return isinstance(other, PacketEnvelope) and self.octad == other.octad
