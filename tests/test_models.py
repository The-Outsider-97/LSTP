from __future__ import annotations

import pytest

from lstp.models import Octad, PacketEnvelope


def make_octad() -> Octad:
    return Octad(
        pragmatics={"type": "QUERY"},
        atoms=[{"id": "a0", "kind": "concept", "value": "mars"}],
        relations=[],
        context={"thread_id": "t-1"},
        confidence=0.8,
        permissions={"mode": "RO"},
        evidence=[],
        output={"format": "JSON"},
    )


def test_octad_preserves_authoritative_field_order() -> None:
    assert tuple(name for name, _ in make_octad().semantic_items()) == (
        "pragmatics",
        "atoms",
        "relations",
        "context",
        "confidence",
        "permissions",
        "evidence",
        "output",
    )


def test_octad_takes_immutable_snapshot() -> None:
    source = {"type": "QUERY", "nested": ["a"]}
    octad = make_octad()
    octad = Octad(**{**dict(octad.semantic_items()), "pragmatics": source})
    source["type"] = "COMMAND"
    source["nested"].append("b")
    assert octad.pragmatics["type"] == "QUERY"  # type: ignore[index]
    assert octad.pragmatics["nested"] == ("a",)  # type: ignore[index]


def test_envelope_metadata_is_not_semantic_equality() -> None:
    octad = make_octad()
    left = PacketEnvelope(octad, "p-1", "0.1", carrier={"source": "json"})
    right = PacketEnvelope(octad, "p-2", "0.1", carrier={"source": "lattice"})
    assert left != right
    assert left.semantically_equals(right)


def test_envelope_rejects_empty_identity_or_version() -> None:
    octad = make_octad()
    with pytest.raises(ValueError, match="packet_id"):
        PacketEnvelope(octad, "", "0.1")
    with pytest.raises(ValueError, match="protocol_version"):
        PacketEnvelope(octad, "p-1", "")


def test_model_rejects_non_json_like_runtime_objects() -> None:
    with pytest.raises(TypeError, match="unsupported canonical value type"):
        Octad({}, {}, [], {}, 1.0, {}, [], object())
