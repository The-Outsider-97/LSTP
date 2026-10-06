from __future__ import annotations

import pytest

from lstp.errors import LatticeSyntaxError, SemanticValidationError
from lstp.text.canonical import compile_canonical_lattice, parse_canonical_lattice


WHITEPAPER_EXAMPLE = """[π=(TYPE=REQUEST,SPEECH_ACT=COMMAND)
 |A=(a0:ENT("door"){ROLE=TARGET})
 |R=(OPEN(a0))
 |C=(THREAD="t1")
 |κ=0.95
 |Π=(MODE=EXEC,SCOPE=["door"])
 |E=(USER("open the door"))
 |Ω=(FORMAT=NL)]"""


def test_exact_whitepaper_example_parses_to_ordered_octad() -> None:
    document = parse_canonical_lattice(WHITEPAPER_EXAMPLE)
    assert len(document.packets) == 1
    packet = document.packets[0]
    assert packet.label is None
    octad = packet.octad
    assert octad.pragmatics.type == "request"
    assert octad.pragmatics.speech_act == "command"
    assert octad.atoms[0].id == "a0"
    assert octad.atoms[0].kind == "entity"
    assert octad.atoms[0].value == "door"
    assert octad.atoms[0].role == "TARGET"
    assert octad.relations[0].type == "OPEN"
    assert octad.relations[0].arguments == ("a0",)
    assert octad.context.thread_id == "t1"
    assert octad.confidence == 0.95
    assert octad.permissions.mode == "EXEC"
    assert octad.permissions.scope == ("door",)
    assert octad.evidence[0].source_type == "user"
    assert octad.evidence[0].source_ref == "open the door"
    assert octad.output.format == "NL"


def test_atomic_packet_is_unframed_octad_core() -> None:
    source = (
        'π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=JSON)'
    )
    document = parse_canonical_lattice(source)
    assert len(document.packets) == 1
    assert document.packets[0].label is None
    assert document.packets[0].octad.output.format == "JSON"


def test_named_packet_label_is_carrier_metadata_not_octad_identity() -> None:
    source = (
        'alpha:[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    document = parse_canonical_lattice(source)
    packet = document.packets[0]
    assert packet.label == "alpha"
    assert packet.octad.context.packet_id is None


def test_stream_packet_requires_named_packets_and_line_break_separator() -> None:
    source = (
        'one:[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]\n'
        'two:[π=(TYPE=QUESTION,SPEECH_ACT=QUESTION)|A=()|R=()|'
        'C=(THREAD="t1")|κ=0.8|Π=(MODE=RO)|E=()|Ω=(FORMAT=NL)]'
    )
    document = parse_canonical_lattice(source)
    assert [item.label for item in document.packets] == ["one", "two"]
    assert document.packets[1].octad.pragmatics.type == "question"


def test_canonical_segment_order_is_strict() -> None:
    source = (
        '[π=(TYPE=INFORM)|R=()|A=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    with pytest.raises(LatticeSyntaxError):
        parse_canonical_lattice(source)


def test_duplicate_named_field_fails_closed() -> None:
    source = (
        '[π=(TYPE=INFORM,TYPE=REQUEST)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    with pytest.raises(LatticeSyntaxError, match="duplicate canonical field"):
        parse_canonical_lattice(source)


def test_unknown_canonical_permission_field_is_rejected() -> None:
    source = (
        '[π=(TYPE=REQUEST)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=(CAPABILITIES=["commit"])|E=()|Ω=(FORMAT=NL)]'
    )
    with pytest.raises(LatticeSyntaxError, match="unknown canonical permission field"):
        parse_canonical_lattice(source)


def test_context_whitepaper_fields_parse_without_aliases() -> None:
    source = (
        '[π=(TYPE=INFORM)|A=()|R=()|'
        'C=(THREAD="t1",PARENT="p0",TIMEZONE="Europe/Amsterdam",'
        'WINDOW={"turns":4})|κ=1|Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    context = parse_canonical_lattice(source).packets[0].octad.context
    assert context.parent_packet_id == "p0"
    assert context.timezone == "Europe/Amsterdam"
    assert context.window["turns"] == 4


def test_compact_syntax_is_not_accepted_by_canonical_parser() -> None:
    with pytest.raises(LatticeSyntaxError):
        parse_canonical_lattice(
            '!open @door {mode=COMMIT, scope=["door"]} -> NL %0.95'
        )


def test_parse_does_not_hide_semantic_reference_errors() -> None:
    source = (
        '[π=(TYPE=INFORM)|A=()|R=(is(a9))|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    document = parse_canonical_lattice(source)
    assert document.packets[0].octad.relations[0].arguments == ("a9",)
    with pytest.raises(SemanticValidationError):
        compile_canonical_lattice(source)


def test_compile_rejects_side_effect_mode_without_scope() -> None:
    source = (
        '[π=(TYPE=REQUEST,SPEECH_ACT=COMMAND)|A=()|R=()|C=(THREAD="t1")|'
        'κ=1|Π=(MODE=COMMIT)|E=()|Ω=(FORMAT=NONE)]'
    )
    with pytest.raises(SemanticValidationError, match="explicit scope"):
        compile_canonical_lattice(source)


def test_compile_accepts_semantically_valid_canonical_packet() -> None:
    source = (
        '[π=(TYPE=REQUEST,SPEECH_ACT=COMMAND)|'
        'A=(a0:RES("door"){ROLE=TARGET})|R=(requests(a0))|'
        'C=(THREAD="t1")|κ=1|Π=(MODE=COMMIT,SCOPE=["door"])|'
        'E=(USER("open the door"))|Ω=(FORMAT=NONE)]'
    )
    document = compile_canonical_lattice(source)
    assert document.packets[0].octad.permissions.mode == "COMMIT"


def test_atom_attributes_and_relation_metadata_are_preserved() -> None:
    source = (
        '[π=(TYPE=INFORM)|'
        'A=(a0:ENT("door"){ROLE=TARGET,ATTRIBUTES={"locked":false}})|'
        'R=(is(a0){ID=r0,CONFIDENCE=0.75,ATTRIBUTES={"source":"sensor"}})|'
        'C=(THREAD="t1")|κ=1|Π=()|E=()|Ω=(FORMAT=JSON)]'
    )
    octad = parse_canonical_lattice(source).packets[0].octad
    assert octad.atoms[0].attributes["locked"] is False
    relation = octad.relations[0]
    assert relation.id == "r0"
    assert relation.confidence == 0.75
    assert relation.attributes["source"] == "sensor"


def test_relation_metadata_unknown_field_fails_closed() -> None:
    source = (
        '[π=(TYPE=INFORM)|A=(a0:ENT("door"))|'
        'R=(is(a0){PROFILE=fast})|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    with pytest.raises(LatticeSyntaxError, match="unknown canonical relation metadata"):
        parse_canonical_lattice(source)


def test_utf8_bom_is_accepted_by_canonical_parser() -> None:
    source = (
        '\ufeff[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    document = parse_canonical_lattice(source)
    assert document.packets[0].octad.pragmatics.type == "inform"


def test_named_packet_rejects_line_break_before_frame() -> None:
    source = (
        'alpha:\n[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    with pytest.raises(LatticeSyntaxError, match="must use label"):
        parse_canonical_lattice(source)
