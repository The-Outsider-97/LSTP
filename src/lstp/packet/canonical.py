"""Public strict canonical packet encoding API."""

from __future__ import annotations

from collections.abc import Mapping

from lstp.errors import CanonicalizationError, Diagnostic
from lstp.json_input import InputLimits, loads_json
from lstp.models import PacketEnvelope
from lstp.packet.serializer import (
    canonical_dumps,
    canonical_loads as _canonical_loads,
    packet_to_mapping,
)
from lstp.packet.structural import validate_canonical_json_types


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
        require_canonical_bytes=require_canonical_bytes,
    )
    decoded = loads_json(data) if limits is None else loads_json(data, limits=limits)
    if not isinstance(decoded, Mapping):
        raise CanonicalizationError(
            Diagnostic("expected_object", "canonical packet must be a JSON object", path="$")
        )
    validate_canonical_json_types(decoded)
    return packet


__all__ = ["canonical_dumps", "canonical_loads", "packet_to_mapping"]
