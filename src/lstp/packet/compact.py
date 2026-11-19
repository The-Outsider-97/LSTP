"""Lossless, explicitly versioned tuple carrier; canonical bytes remain authoritative.

L1 is a carrier for canonical v0.1, not a new semantic protocol version. D1 is
an optional content-addressed transport delta. Neither representation grants
authority; authorization and signing operate on the restored canonical packet.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from lstp.errors import CanonicalizationError, Diagnostic
from lstp.json_input import InputLimits, loads_json
from lstp.models import PacketEnvelope
from lstp.packet.canonical import _preflight, _validated_mapping, canonical_loads
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


_FLAT_FIELDS = (
    "id",
    "pragmatics",
    "atoms",
    "relations",
    "context",
    "confidence",
    "permissions",
    "evidence",
    "output",
    "carrier",
    "audit",
)


def _slots(mapping: Mapping[str, Any], profile: str) -> list[Any]:
    if profile == "typed":
        return _pack(mapping, "packet")
    values = [mapping[key] for key in _FLAT_FIELDS]
    if "extensions" in mapping:
        values.append({"extensions": mapping["extensions"]})
    return values


def _full_frame(slots: list[Any], profile: str) -> list[Any]:
    return ["L1", slots] if profile == "typed" else ["L1", *slots]


def _mapping(slots: object, profile: str) -> dict[str, Any]:
    if profile == "typed":
        result = _unpack(slots, "packet")
    else:
        if not isinstance(slots, list) or len(slots) not in (11, 12):
            raise _error("compact_shape", "incorrect flat compact slot count")
        result = dict(zip(_FLAT_FIELDS, slots[:11], strict=True))
        if len(slots) == 12:
            extra = slots[-1]
            if not isinstance(extra, dict) or set(extra) != {"extensions"}:
                raise _error("compact_shape", "invalid envelope extension slot")
            result.update(extra)
    result["version"] = "0.1"
    return result


def _choose(full: bytes, delta: bytes, cost: Callable[[bytes], int]) -> bytes:
    full_cost, delta_cost = cost(full), cost(delta)
    if any(type(value) is not int or value < 0 for value in (full_cost, delta_cost)):
        raise ValueError("carrier cost must be a non-negative integer")
    return delta if delta_cost < full_cost else full


def compact_dumps(
    packet: PacketEnvelope,
    *,
    base: PacketEnvelope | None = None,
    cost: Callable[[bytes], int] = len,
    profile: str = "flat",
) -> bytes:
    """Encode a validated carrier; flat is the current-main default.

    The explicit typed profile retains the nested tuple mapping from the other
    merged carrier. Their standalone/delta arities are disjoint and both decode.
    Cost includes the complete frame. No tokenizer or hidden context is assumed.
    """
    if profile not in ("flat", "typed"):
        raise ValueError("profile must be flat or typed")
    mapping = _validated_mapping(packet)
    new = _slots(mapping, profile)
    full = _encode(_full_frame(new, profile)).encode("utf-8")
    if base is None:
        return full
    base_mapping = _validated_mapping(base)
    old = _slots(base_mapping, profile)
    base_hash = hashlib.sha256(_encode(base_mapping).encode("utf-8")).hexdigest()
    if profile == "flat":
        if len(old) != len(new):
            return full
        changes = {
            str(i): value for i, value in enumerate(new) if _encode(value) != _encode(old[i])
        }
        frame: list[Any] = ["D1", base_hash, changes]
    else:
        replacements = [
            [i, value]
            for i, value in enumerate(new)
            if i >= len(old) or _encode(value) != _encode(old[i])
        ]
        target_hash = hashlib.sha256(_encode(mapping).encode("utf-8")).hexdigest()
        frame = ["D1", base_hash, target_hash, len(new), replacements]
    return _choose(full, _encode(frame).encode("utf-8"), cost)


def compact_loads(
    source: str | bytes,
    *,
    base: PacketEnvelope | None = None,
    limits: InputLimits | None = None,
    require_compact_bytes: bool = False,
) -> PacketEnvelope:
    """Restore either governed arity, then apply the one strict canonical decoder."""
    frame = loads_json(source) if limits is None else loads_json(source, limits=limits)
    _preflight(frame)
    if not isinstance(frame, list) or not frame:
        raise _error("compact_profile", "expected a compact frame")
    if frame[0] == "L1":
        if len(frame) == 2:
            profile, slots = "typed", frame[1]
        elif len(frame) in (12, 13):
            profile, slots = "flat", frame[1:]
        else:
            raise _error("compact_shape", "incorrect standalone carrier arity")
    elif frame[0] == "D1":
        if len(frame) not in (3, 5):
            raise _error("compact_shape", "incorrect delta carrier arity")
        if base is None:
            raise _error("delta_base", "exact delta base is unavailable")
        base_mapping = _validated_mapping(base)
        if frame[1] != hashlib.sha256(_encode(base_mapping).encode("utf-8")).hexdigest():
            raise _error("delta_base", "exact delta base is unavailable")
        profile = "flat" if len(frame) == 3 else "typed"
        slots = _slots(base_mapping, profile)
        if profile == "flat":
            if not isinstance(frame[2], dict):
                raise _error("delta_shape", "delta changes must be an object")
            indices = {str(i): i for i in range(len(slots))}
            for key, value in frame[2].items():
                if key not in indices:
                    raise _error("delta_shape", "unknown changed slot")
                slots[indices[key]] = value
        else:
            size, changes = frame[3:]
            if type(size) is not int or not 6 <= size <= len(FIELDS["packet"]):
                raise _error("delta_shape", "invalid delta target length")
            if not isinstance(changes, list):
                raise _error("delta_shape", "delta changes must be an array")
            slots = slots[:size]
            slots.extend([None] * (size - len(slots)))
            previous = -1
            for change in changes:
                if not isinstance(change, list) or len(change) != 2:
                    raise _error("delta_shape", "invalid delta change")
                index, value = change
                if type(index) is not int or not previous < index < size:
                    raise _error("delta_shape", "delta slots must be unique, ordered and in range")
                slots[index] = value
                previous = index
    else:
        raise _error("compact_profile", "unsupported compact profile")
    mapping = _mapping(slots, profile)
    wire = _encode(mapping).encode("utf-8")
    # Expanded bytes and object nodes must satisfy exactly the same limits.
    packet = canonical_loads(wire, limits=limits)
    if frame[0] == "D1" and profile == "typed":
        if (
            frame[2]
            != hashlib.sha256(_encode(_validated_mapping(packet)).encode("utf-8")).hexdigest()
        ):
            raise _error("delta_integrity", "restored packet does not match target digest")
    if require_compact_bytes:
        supplied = source.encode("utf-8") if isinstance(source, str) else source
        expected = compact_dumps(packet, base=base if frame[0] == "D1" else None, profile=profile)
        if supplied != expected:
            raise _error("non_compact_bytes", "input is not deterministic compact byte form")
    return packet


def incremental_dumps(
    packet: PacketEnvelope,
    *,
    base: PacketEnvelope | None = None,
    cost: Callable[[bytes], int] = len,
) -> bytes:
    """Retain the typed delta API, including its target integrity digest."""
    return compact_dumps(packet, base=base, cost=cost, profile="typed")


def incremental_loads(
    source: str | bytes,
    *,
    base: PacketEnvelope | None = None,
    limits: InputLimits | None = None,
) -> PacketEnvelope:
    """Decode explicit compact context without relying on ambient state."""
    return compact_loads(source, base=base, limits=limits)
