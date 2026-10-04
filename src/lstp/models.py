"""Canonical semantic containers for LSTP v0.1.

This module intentionally models only protocol boundaries that are unambiguous in
the authoritative Whitepaper. An Octad has exactly eight semantic domains;
envelope metadata remains outside semantic equality. Unresolved carrier grammar,
permission subfields, evidence shape, and canonical byte serialization are not
guessed here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

JSONValue = None | bool | int | float | str | tuple["JSONValue", ...] | Mapping[str, "JSONValue"]

SUPPORTED_PROTOCOL_VERSIONS = frozenset({"0.1"})


def _freeze(value: Any, *, path: str = "$") -> JSONValue:
    """Return a strict immutable JSON-value snapshot for semantic comparison.

    Canonical semantic containers must not silently coerce host-language values.
    JSON object keys are strings and JSON numbers exclude NaN and infinities.
    Rejecting those values here keeps the model boundary deterministic without
    claiming a byte-canonical serialization profile.
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


def _freeze_object(value: Any, *, path: str) -> Mapping[str, JSONValue]:
    """Freeze a value that is required to be a JSON object."""
    frozen = _freeze(value, path=path)
    if not isinstance(frozen, Mapping):
        raise TypeError(f"expected object at {path}")
    return frozen


def _validate_extension_namespaces(extensions: Mapping[str, JSONValue]) -> None:
    """Require explicit non-empty extension namespaces.

    The Whitepaper permits namespaced host/domain extension data but does not
    define a registry. This validator therefore enforces only the safe structural
    invariant: each top-level extension key names an owner and maps to an object.
    It deliberately does not infer meaning, authorization, or namespace aliases.
    """
    for namespace, payload in extensions.items():
        if not namespace.strip():
            raise ValueError("extension namespace must not be empty")
        if not isinstance(payload, Mapping):
            raise TypeError(f"extension namespace {namespace!r} must contain an object")


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

    Carrier/audit structures remain opaque until their normative contracts are
    fully reconciled. Envelope metadata and extensions never grant authority.
    """

    octad: Octad
    packet_id: str
    protocol_version: str
    carrier: JSONValue = field(default_factory=dict)
    audit: JSONValue = field(default_factory=dict)
    extensions: JSONValue = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.packet_id, str) or not self.packet_id:
            raise ValueError("packet_id must be a non-empty string")
        if self.protocol_version not in SUPPORTED_PROTOCOL_VERSIONS:
            raise ValueError(f"unsupported protocol_version: {self.protocol_version!r}")

        carrier = _freeze_object(self.carrier, path="$.carrier")
        audit = _freeze_object(self.audit, path="$.audit")
        extensions = _freeze_object(self.extensions, path="$.extensions")
        _validate_extension_namespaces(extensions)

        object.__setattr__(self, "carrier", carrier)
        object.__setattr__(self, "audit", audit)
        object.__setattr__(self, "extensions", extensions)

    def semantically_equals(self, other: object) -> bool:
        """Compare semantic Octad content only, excluding envelope metadata."""
        return isinstance(other, PacketEnvelope) and self.octad == other.octad
