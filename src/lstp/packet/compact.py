"""Lossless, explicitly versioned tuple carrier; canonical bytes remain authoritative.

L1 is a carrier for canonical v0.1, not a new semantic protocol version. D1 is
an optional content-addressed transport delta. Neither representation grants
authority; authorization and signing operate on the restored canonical packet.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from lstp.errors import CanonicalizationError, Diagnostic
from lstp.json_input import InputLimits, loads_json
from lstp.models import PacketEnvelope
from lstp.packet.canonical import _preflight, canonical_dumps, canonical_loads, packet_to_mapping
from lstp.packet.serializer import _encode

# Order is part of the L1 contract. Application maps, extensions, attributes,
# bindings, limits, spans and literal atom values are opaque JSON values here.
FIELDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "packet": (
            "id",
            "pragmatics",
            "atoms",
            "context",
            "permissions",
            "output",
            "evidence",
            "relations",
            "confidence",
            "carrier",
            "audit",
            "extensions",
        ),
        "pragmatics": (
            "type",
            "speech_act",
            "goal",
            "modifiers",
            "register",
            "urgency",
            "extensions",
        ),
        "atom": ("id", "kind", "value", "role", "datatype", "language", "attributes", "extensions"),
        "relation": ("type", "arguments", "id", "confidence", "attributes", "extensions"),
        "context": (
            "thread_id",
            "bindings",
            "references",
            "packet_id",
            "parent_packet_id",
            "conversation_id",
            "turn",
            "speaker",
            "audience",
            "time",
            "timezone",
            "window",
            "location",
            "extensions",
        ),
        "reference": ("packet_id", "depth", "agent", "label", "extensions"),
        "permissions": (
            "mode",
            "scope",
            "forbid",
            "require_confirmation",
            "require_review",
            "require_logging",
            "limits",
            "extensions",
        ),
        "evidence": (
            "id",
            "source_type",
            "source_ref",
            "input_hash",
            "span",
            "supports",
            "description",
            "confidence",
            "extensions",
        ),
        "output": (
            "format",
            "schema",
            "channel",
            "target",
            "language",
            "max_bytes",
            "requirements",
            "extensions",
        ),
    }
)
_REQUIRED = {
    "packet": 6,
    "pragmatics": 1,
    "atom": 2,
    "relation": 2,
    "context": 1,
    "reference": 1,
    "permissions": 0,
    "evidence": 2,
    "output": 1,
}
_DEFAULTS: dict[str, dict[str, Any]] = {
    "packet": {
        "evidence": [],
        "relations": [],
        "confidence": 1,
        "carrier": {},
        "audit": {},
    },
    "context": {"references": []},
}
_CHILDREN = {
    ("packet", "pragmatics"): ("pragmatics", False),
    ("packet", "atoms"): ("atom", True),
    ("packet", "relations"): ("relation", True),
    ("packet", "context"): ("context", False),
    ("packet", "permissions"): ("permissions", False),
    ("packet", "evidence"): ("evidence", True),
    ("packet", "output"): ("output", False),
    ("context", "references"): ("reference", True),
}


def _error(code: str, message: str) -> CanonicalizationError:
    return CanonicalizationError(Diagnostic(code, message, path="$"))


def _pack(data: Mapping[str, Any], shape: str) -> list[Any]:
    defaults = _DEFAULTS.get(shape, {})
    fields = FIELDS[shape]
    values = [data.get(name, defaults.get(name)) for name in fields]
    while len(values) > _REQUIRED[shape]:
        index = len(values) - 1
        if values[index] != defaults.get(fields[index]):
            break
        values.pop()
    for index, value in enumerate(values):
        child = _CHILDREN.get((shape, fields[index]))
        if child is not None and value is not None:
            name, many = child
            values[index] = [_pack(item, name) for item in value] if many else _pack(value, name)
    return values


def _unpack(values: object, shape: str) -> dict[str, Any]:
    fields = FIELDS[shape]
    if not isinstance(values, list) or not _REQUIRED[shape] <= len(values) <= len(fields):
        raise _error("compact_shape", "invalid compact tuple length or type")
    data = dict(_DEFAULTS.get(shape, {}))
    for index, value in enumerate(values):
        name = fields[index]
        # Null is an absent optional slot, except for literal atom values.
        if value is None and index >= _REQUIRED[shape]:
            continue
        child = _CHILDREN.get((shape, name))
        if child is not None:
            child_name, many = child
            if many:
                if not isinstance(value, list):
                    raise _error("compact_shape", "compact collection must be an array")
                value = [_unpack(item, child_name) for item in value]
            else:
                value = _unpack(value, child_name)
        data[name] = value
    return data


def _slots(packet: PacketEnvelope) -> list[Any]:
    canonical_dumps(packet)  # Validate semantics, Unicode and numbers before packing.
    return _pack(packet_to_mapping(packet), "packet")


def compact_dumps(packet: PacketEnvelope) -> bytes:
    """Encode every canonical field, including evidence, constraints and metadata."""
    return _encode(["L1", _slots(packet)]).encode("utf-8")


def compact_loads(
    source: str | bytes,
    *,
    limits: InputLimits | None = None,
    require_compact_bytes: bool = False,
) -> PacketEnvelope:
    """Restore and validate canonical v0.1; never guess a carrier or protocol version."""
    value = loads_json(source) if limits is None else loads_json(source, limits=limits)
    _preflight(value)
    if not isinstance(value, list) or len(value) != 2 or value[0] != "L1":
        raise _error("compact_profile", "expected the L1 compact carrier")
    mapping = _unpack(value[1], "packet")
    mapping["version"] = "0.1"
    # Bound the expanded representation as well as the supplied representation.
    packet = canonical_loads(_encode(mapping).encode("utf-8"), limits=limits)
    if require_compact_bytes:
        supplied = source.encode("utf-8") if isinstance(source, str) else source
        if supplied != compact_dumps(packet):
            raise _error("non_compact_bytes", "input is not deterministic L1 byte form")
    return packet


def incremental_dumps(packet: PacketEnvelope, *, base: PacketEnvelope | None = None) -> bytes:
    """Use a D1 transport delta only when its complete byte cost beats L1.

    This is network/storage compression, not a promise of model-token savings.
    The receiver must already possess the exact, explicitly supplied base.
    """
    full = compact_dumps(packet)
    if base is None:
        return full
    old, new = _slots(base), _slots(packet)
    changes = [
        [index, item]
        for index, item in enumerate(new)
        if index >= len(old) or _encode(item) != _encode(old[index])
    ]
    delta = _encode(
        [
            "D1",
            hashlib.sha256(canonical_dumps(base)).hexdigest(),
            hashlib.sha256(canonical_dumps(packet)).hexdigest(),
            len(new),
            changes,
        ]
    ).encode("utf-8")
    return delta if len(delta) < len(full) else full


def incremental_loads(
    source: str | bytes,
    *,
    base: PacketEnvelope | None = None,
    limits: InputLimits | None = None,
) -> PacketEnvelope:
    """Fail closed on missing, stale, wrong or corrupted bases; accept full L1 fallback."""
    value = loads_json(source) if limits is None else loads_json(source, limits=limits)
    _preflight(value)
    if isinstance(value, list) and len(value) == 2 and value[0] == "L1":
        return compact_loads(source, limits=limits)
    if not isinstance(value, list) or len(value) != 5 or value[0] != "D1":
        raise _error("compact_profile", "expected an L1 or D1 carrier")
    if base is None or value[1] != hashlib.sha256(canonical_dumps(base)).hexdigest():
        raise _error("delta_base", "exact delta base is unavailable")
    size, changes = value[3:]
    if type(size) is not int or not 6 <= size <= len(FIELDS["packet"]):
        raise _error("delta_shape", "invalid delta target length")
    if not isinstance(changes, list):
        raise _error("delta_shape", "delta changes must be an array")
    slots = _slots(base)[:size]
    slots.extend([None] * (size - len(slots)))
    previous = -1
    for change in changes:
        if not isinstance(change, list) or len(change) != 2:
            raise _error("delta_shape", "invalid delta change")
        index, item = change
        if type(index) is not int or not previous < index < size:
            raise _error("delta_shape", "delta slots must be unique, ordered and in range")
        previous = index
        slots[index] = item
    packet = compact_loads(_encode(["L1", slots]).encode("utf-8"), limits=limits)
    if value[2] != hashlib.sha256(canonical_dumps(packet)).hexdigest():
        raise _error("delta_integrity", "restored packet does not match target digest")
    return packet
