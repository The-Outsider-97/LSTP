"""Public strict canonical packet encoding API."""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping, Sequence
from decimal import Decimal

from lstp.errors import CanonicalizationError, Diagnostic
from lstp.json_input import InputLimits, loads_json
from lstp.models import PacketEnvelope
from lstp.packet.serializer import (
    canonical_dumps as _canonical_dumps,
    canonical_loads as _canonical_loads,
    packet_to_mapping,
)
from lstp.packet.structural import validate_canonical_json_types

_MAX_DECIMAL_EXPONENT = 1024
_BIDI_CONTROLS = {
    "\u061c",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
}


def _error(code: str, message: str, path: str) -> CanonicalizationError:
    return CanonicalizationError(Diagnostic(code, message, path=path))


def _preflight(value: object, path: str = "$") -> None:
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise _error("unicode_not_nfc", "canonical strings must already be NFC", path)
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise _error("unicode_surrogate", "unpaired surrogate is not canonical", path)
        if any(char in _BIDI_CONTROLS for char in value):
            raise _error(
                "unicode_bidi_control",
                "bidirectional formatting controls are not canonical",
                path,
            )
        return
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise _error("non_finite_number", "canonical numbers must be finite", path)
        if abs(value.as_tuple().exponent) > _MAX_DECIMAL_EXPONENT:
            raise _error(
                "number_exponent_limit",
                "canonical decimal exponent exceeds implementation safety limit",
                path,
            )
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _error("non_finite_number", "canonical numbers must be finite", path)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise _error("non_string_key", "canonical object keys must be strings", path)
            _preflight(key, f"{path}.<key>")
            _preflight(item, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _preflight(item, f"{path}[{index}]")


def canonical_dumps(packet: PacketEnvelope) -> bytes:
    """Strictly serialize a packet after Unicode/numeric safety preflight."""
    _preflight(packet_to_mapping(packet))
    return _canonical_dumps(packet)


def canonical_loads(
    data: bytes | str,
    *,
    limits: InputLimits | None = None,
    require_canonical_bytes: bool = False,
) -> PacketEnvelope:
    """Strictly decode canonical JSON, including schema-relevant JSON types."""
    packet = _canonical_loads(
        data,
        limits=limits,
        require_canonical_bytes=False,
    )
    decoded = loads_json(data) if limits is None else loads_json(data, limits=limits)
    if not isinstance(decoded, Mapping):
        raise CanonicalizationError(
            Diagnostic(
                "expected_object",
                "canonical packet must be a JSON object",
                path="$",
            )
        )
    validate_canonical_json_types(decoded)
    _preflight(decoded)
    if require_canonical_bytes:
        supplied = data.encode("utf-8") if isinstance(data, str) else data
        expected = canonical_dumps(packet)
        if supplied != expected:
            raise _error(
                "non_canonical_bytes",
                "input is valid LSTP but not canonical byte form",
                "$",
            )
    return packet


__all__ = ["canonical_dumps", "canonical_loads", "packet_to_mapping"]
