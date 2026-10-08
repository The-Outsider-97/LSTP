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


@pytest.mark.parametrize(
    ("factory", "payload"),
    [
        (Atom.from_mapping, {"id": "a0", "kind": "entity", "role": None}),
        (Atom.from_mapping, {"id": "a0", "kind": "entity", "language": None}),
        (Relation.from_mapping, {"type": "is", "arguments": ["a0"], "id": None}),
        (Relation.from_mapping, {"type": "is", "arguments": ["a0"], "confidence": None}),
        (ContextReference.from_mapping, {"packet_id": "p1", "depth": None}),
        (ContextReference.from_mapping, {"packet_id": "p1", "agent": None}),
        (EvidenceItem.from_mapping, {"id": "e0", "source_type": "tool", "source_ref": None}),
        (EvidenceItem.from_mapping, {"id": "e0", "source_type": "tool", "confidence": None}),
        (Output.from_mapping, {"format": "JSON", "target": None}),
        (Output.from_mapping, {"format": "JSON", "max_bytes": None}),
    ],
)
def test_explicit_null_cannot_erase_optional_semantic_data(factory, payload) -> None:
    with pytest.raises((TypeError, ValueError)):
        factory(payload)


def test_omitted_optional_fields_keep_documented_defaults() -> None:
    from lstp.models import Pragmatics

    assert Atom.from_mapping({"id": "a0", "kind": "entity"}).language is None
    assert Relation.from_mapping({"type": "is", "arguments": ["a0"]}).id is None
    assert ContextReference.from_mapping({"packet_id": "p1"}).depth is None
    assert EvidenceItem.from_mapping({"id": "e0", "source_type": "tool"}).source_ref is None
    assert Output.from_mapping({"format": "JSON"}).max_bytes is None
    assert Pragmatics.from_mapping({"type": "inform"}).urgency is None


def test_present_null_urgency_is_not_silently_removed() -> None:
    from lstp.models import Pragmatics

    with pytest.raises((TypeError, ValueError)):
        Pragmatics.from_mapping({"type": "inform", "urgency": None})


def test_valid_numeric_optionals_preserved() -> None:
    from lstp.models import Pragmatics

    assert Pragmatics.from_mapping({"type": "inform", "urgency": 0.6}).urgency == 0.6
    assert Relation.from_mapping({"type": "is", "arguments": ["a0"], "confidence": 0.4}).confidence == 0.4
    assert ContextReference.from_mapping({"packet_id": "p1", "depth": 2}).depth == 2
    assert Output.from_mapping({"format": "JSON", "max_bytes": 512}).max_bytes == 512
