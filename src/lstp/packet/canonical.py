"""Public canonical API, backed by one strict validation/serialization pipeline."""

from lstp.packet.serializer import (
    _preflight as _preflight,
)
from lstp.packet.serializer import (
    _validated_mapping as _validated_mapping,
)
from lstp.packet.serializer import (
    canonical_dumps,
    canonical_loads,
    packet_to_mapping,
)

__all__ = ["canonical_dumps", "canonical_loads", "packet_to_mapping"]
