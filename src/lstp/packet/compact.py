"""Lossless optional carrier for canonical LSTP 0.1 packets."""

from __future__ import annotations

import hashlib
from collections.abc import Callable

from lstp.errors import CanonicalizationError, Diagnostic
from lstp.json_input import DEFAULT_LIMITS, InputLimits, loads_json
from lstp.models import PacketEnvelope
from lstp.packet.canonical import _preflight, canonical_dumps, canonical_loads
from lstp.packet.serializer import _encode

# Frozen positions, including all mandatory envelope members. A trailing mapping
# carries optional envelope members under their original, governed names.
_FIELDS = (
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
_PROFILE = "L1"
_DELTA = "D1"


def _invalid(message: str) -> CanonicalizationError:
    return CanonicalizationError(Diagnostic("compact_profile", message, path="$"))


def _slots(canonical: bytes) -> list[object]:
    obj = loads_json(canonical)
    if obj.pop("version") != "0.1":
        raise _invalid("unsupported canonical protocol version")
    values = [obj.pop(key) for key in _FIELDS]
    if obj:
        values.append(obj)
    return values


def compact_dumps(
    packet: PacketEnvelope,
    *,
    base: PacketEnvelope | None = None,
    cost: Callable[[bytes], int] = len,
) -> bytes:
    """Encode independently or relative to an explicitly supplied immutable base."""
    full = _slots(canonical_dumps(packet))
    standalone = _encode([_PROFILE, *full]).encode()
    if base is None:
        return standalone
    base_wire = canonical_dumps(base)
    old = _slots(base_wire)
    if len(old) != len(full):
        return standalone
    # Canonical text distinguishes true from 1 inside opaque extensions.
    changes = {str(i): value for i, value in enumerate(full) if _encode(value) != _encode(old[i])}
    delta = _encode([_DELTA, hashlib.sha256(base_wire).hexdigest(), changes]).encode()
    return delta if cost(delta) < cost(standalone) else standalone


def compact_loads(
    data: bytes | str, *, base: PacketEnvelope | None = None, limits: InputLimits = DEFAULT_LIMITS
) -> PacketEnvelope:
    """Restore and validate a packet before any signing, authorization or replay decision."""
    frame = loads_json(data, limits=limits)
    if not isinstance(frame, list) or not frame:
        raise _invalid("expected compact frame")
    tag = frame[0]
    if tag == _PROFILE:
        values = frame[1:]
    elif tag == _DELTA:
        if len(frame) != 3 or not isinstance(frame[2], dict) or base is None:
            raise _invalid("delta requires a changes object and its exact base")
        base_wire = canonical_dumps(base)
        if hashlib.sha256(base_wire).hexdigest() != frame[1]:
            raise _invalid("base digest mismatch")
        values = _slots(base_wire)
        indices = {str(i): i for i in range(len(values))}
        for key, value in frame[2].items():
            if key not in indices:
                raise _invalid("unknown changed slot")
            values[indices[key]] = value
    else:
        raise _invalid("unsupported compact profile")
    if len(values) not in (len(_FIELDS), len(_FIELDS) + 1):
        raise _invalid("incorrect compact slot count")
    obj = dict(zip(_FIELDS, values[: len(_FIELDS)], strict=True))
    obj["version"] = "0.1"
    if len(values) > len(_FIELDS):
        extra = values[-1]
        if not isinstance(extra, dict) or set(extra) != {"extensions"}:
            raise _invalid("invalid envelope extension slot")
        obj.update(extra)
    _preflight(obj)
    # Expanded documents are subject to the same resource and semantic gates.
    wire = _encode(obj)
    if loads_json(wire, limits=limits) != obj:
        raise _invalid("numeric value cannot be represented exactly by the canonical encoder")
    return canonical_loads(wire, limits=limits, require_canonical_bytes=True)
