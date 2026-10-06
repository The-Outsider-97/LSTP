from __future__ import annotations

from lstp.models import Atom, Context, EvidenceItem, Octad, Output, PacketEnvelope, Permissions, Pragmatics, Relation
from lstp.packet.validator import validate_packet


def packet_with(*, atoms=(), relations=(), permissions=None, evidence=()) -> PacketEnvelope:
    return PacketEnvelope(
        Octad(
            pragmatics=Pragmatics(type="request", speech_act="command"), atoms=atoms, relations=relations,
            context=Context(thread_id="thread-1"), confidence=1.0,
            permissions=permissions or Permissions(), evidence=evidence,
            output=Output(format="NL"),
        ),
        "packet-1", "0.1",
    )


def test_validator_accepts_well_formed_references() -> None:
    packet = packet_with(
        atoms=(Atom("a0", "resource", value="door"), Atom("a1", "proposition", value="open")),
        relations=(Relation("requests", ("a0",), id="r0"),),
        evidence=(EvidenceItem("e0", "user", supports=("r0", "a1")),),
    )
    assert validate_packet(packet).valid


def test_validator_rejects_unresolved_relation_atom() -> None:
    result = validate_packet(packet_with(relations=(Relation("is", ("a9",)),)))
    assert {item.code for item in result.diagnostics} == {"unresolved_atom"}


def test_validator_requires_scope_for_side_effect_capable_mode() -> None:
    result = validate_packet(packet_with(permissions=Permissions(mode="COMMIT")))
    assert "missing_permission_scope" in {item.code for item in result.diagnostics}


def test_validator_reports_forbidden_scope_overlap() -> None:
    result = validate_packet(
        packet_with(
            permissions=Permissions(
                mode="COMMIT",
                scope=("urn:x",),
                forbid=("urn:x",),
            )
        )
    )
    assert "permission_scope_forbidden" in {
        item.code for item in result.diagnostics
    }


def test_readonly_mode_can_be_scope_free() -> None:
    result = validate_packet(packet_with(permissions=Permissions(mode="RO")))
    assert result.valid
