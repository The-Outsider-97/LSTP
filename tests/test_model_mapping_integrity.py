"""Regression tests for lossless public typed-model mapping."""
from __future__ import annotations

import pytest

from lstp.models import Atom, ContextReference, EvidenceItem, Output, PacketEnvelope, Relation


@pytest.mark.parametrize(
    ("factory", "payload"),
    [
        (Atom.from_mapping, {"id": "a0", "kind": "entity", "language": 123}),
        (Atom.from_mapping, {"id": "a0", "kind": "entity", "role": []}),
        (Relation.from_mapping, {"type": "is", "arguments": ["a0"], "id": 123}),
        (ContextReference.from_mapping, {"packet_id": "p1", "agent": []}),
        (EvidenceItem.from_mapping, {"id": "e0", "source_type": "tool", "source_ref": 42}),
        (EvidenceItem.from_mapping, {"id": "e0", "source_type": "tool", "input_hash": []}),
        (Output.from_mapping, {"format": "JSON", "target": []}),
        (Output.from_mapping, {"format": "JSON", "max_bytes": "1024"}),
    ],
)
def test_wrong_optional_types_must_not_be_silently_erased(factory, payload) -> None:
    with pytest.raises((TypeError, ValueError)):
        factory(payload)


@pytest.mark.parametrize(
    ("factory", "payload"),
    [
        (Atom.from_mapping, {"id": "a0", "kind": "entity", "unexpected": 1}),
        (Relation.from_mapping, {"type": "is", "arguments": ["a0"], "unexpected": 1}),
        (ContextReference.from_mapping, {"packet_id": "p1", "unexpected": 1}),
        (EvidenceItem.from_mapping, {"id": "e0", "source_type": "tool", "unexpected": 1}),
        (Output.from_mapping, {"format": "JSON", "unexpected": 1}),
    ],
)
def test_unknown_nested_fields_are_not_discarded(factory, payload) -> None:
    with pytest.raises(ValueError, match="unknown field"):
        factory(payload)


def test_envelope_mapping_rejects_unknown_top_level_field() -> None:
    from lstp.models import Context, Octad, Permissions, Pragmatics
    from lstp.packet.serializer import packet_to_mapping

    packet = PacketEnvelope(
        Octad(
            Pragmatics(type="inform"), (), (), Context(thread_id="t"),
            1.0, Permissions(), (), Output(format="JSON"),
        ),
        "p", "0.1",
    )
    payload = packet_to_mapping(packet)
    payload["unrecognized"] = "silently lost before fix"
    with pytest.raises(ValueError, match="unknown field"):
        PacketEnvelope.from_mapping(payload)


def test_valid_optional_identity_and_provenance_survive() -> None:
    relation = Relation.from_mapping({"type": "is", "arguments": ["a0"], "id": "r0"})
    evidence = EvidenceItem.from_mapping({
        "id": "e0", "source_type": "tool",
        "source_ref": "tool:search", "input_hash": "abc",
    })
    assert relation.id == "r0"
    assert evidence.source_ref == "tool:search"
    assert evidence.input_hash == "abc"
