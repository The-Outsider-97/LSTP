from __future__ import annotations

import pytest

from lstp.models import Atom, Context, Octad, Output, PacketEnvelope, Permissions, Pragmatics


def make_octad() -> Octad:
    return Octad(
        pragmatics=Pragmatics(act="question"),
        atoms=(Atom(id="a0", kind="concept", value="mars"),),
        relations=(),
        context=Context(thread_id="t-1"),
        confidence=0.8,
        permissions=Permissions(),
        evidence=(),
        output=Output(format="JSON"),
    )


def test_octad_preserves_canonical_field_order() -> None:
    assert tuple(name for name, _ in make_octad().semantic_items()) == (
        "pragmatics", "atoms", "relations", "context", "confidence", "permissions", "evidence", "output"
    )


def test_typed_model_rejects_legacy_pragmatics_value() -> None:
    with pytest.raises(ValueError, match="unknown pragmatics act"):
        Pragmatics(act="QUERY")


def test_envelope_metadata_is_not_semantic_equality() -> None:
    octad = make_octad()
    left = PacketEnvelope(octad, "p-1", "0.1", carrier={"source": "json"})
    right = PacketEnvelope(octad, "p-2", "0.1", carrier={"source": "lattice"})
    assert left != right
    assert left.semantically_equals(right)


def test_envelope_rejects_unknown_protocol_version() -> None:
    with pytest.raises(ValueError, match="unsupported protocol_version"):
        PacketEnvelope(make_octad(), "p-1", "1.0")


def test_from_mapping_builds_typed_packet() -> None:
    packet = PacketEnvelope.from_mapping({
        "id": "p-1", "version": "0.1",
        "pragmatics": {"act": "question"},
        "atoms": [{"id": "a0", "kind": "concept", "value": "mars"}],
        "relations": [], "context": {"thread_id": "t-1", "references": []},
        "confidence": 0.9, "permissions": {"capabilities": [], "resources": []},
        "evidence": [], "output": {"format": "JSON"}, "carrier": {}, "audit": {},
    })
    assert packet.octad.atoms[0].id == "a0"
    assert packet.octad.permissions.capabilities == ()


def test_permission_model_rejects_unknown_capability() -> None:
    with pytest.raises(ValueError, match="unknown capability"):
        Permissions(capabilities=("admin",))


def test_extension_payload_must_be_namespaced_object() -> None:
    with pytest.raises(TypeError, match="must contain an object"):
        PacketEnvelope(make_octad(), "p-1", "0.1", extensions={"slai": "commit"})  # type: ignore[dict-item]
