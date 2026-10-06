from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from lstp import canonical_loads
from lstp.errors import CanonicalizationError, CompilationError
from lstp.models import EvidenceItem
from lstp.text.canonical import compile_canonical_lattice, parse_canonical_lattice
from lstp.text.canonical_serializer import (
    canonical_lattice_document_dumps,
    canonical_lattice_dumps,
)


ROOT = Path(__file__).resolve().parents[1] / "conformance" / "v0.1" / "lattice" / "canonical"


def test_governed_fixture_round_trips_semantically() -> None:
    source = (ROOT / "positive" / "whitepaper-style.lstp").read_text(
        encoding="utf-8"
    )
    original = compile_canonical_lattice(source).packets[0].octad
    encoded = canonical_lattice_dumps(original)
    decoded = compile_canonical_lattice(encoded).packets[0].octad
    assert decoded == original


def test_structured_atom_json_value_round_trips() -> None:
    source = (
        '[π=(TYPE=INFORM)|A=(a0:VALUE({"items":[1,true,null]}))|'
        'R=(is(a0))|C=(THREAD="t1")|κ=1|Π=()|E=()|Ω=(FORMAT=JSON)]'
    )
    original = compile_canonical_lattice(source).packets[0].octad
    encoded = canonical_lattice_dumps(original)
    decoded = compile_canonical_lattice(encoded).packets[0].octad
    assert decoded == original


def test_named_stream_round_trips_labels_and_semantics() -> None:
    source = (
        'one:[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]\n'
        'two:[π=(TYPE=QUESTION,SPEECH_ACT=QUESTION)|A=()|R=()|'
        'C=(THREAD="t1")|κ=0.8|Π=(MODE=RO)|E=()|Ω=(FORMAT=NL)]'
    )
    original = parse_canonical_lattice(source)
    encoded = canonical_lattice_document_dumps(original)
    decoded = compile_canonical_lattice(encoded)
    assert [packet.label for packet in decoded.packets] == ["one", "two"]
    assert [packet.octad for packet in decoded.packets] == [
        packet.octad for packet in original.packets
    ]


def test_encoder_rejects_rich_evidence_without_governed_syntax() -> None:
    source = (
        '[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=(USER("request"))|Ω=(FORMAT=NL)]'
    )
    octad = compile_canonical_lattice(source).packets[0].octad
    rich = EvidenceItem(
        "e0",
        "user",
        source_ref="request",
        description="not representable yet",
    )
    with pytest.raises(CompilationError, match="rich evidence metadata"):
        canonical_lattice_dumps(replace(octad, evidence=(rich,)))


def test_encoder_rejects_unrepresentable_context_reference_metadata() -> None:
    source = (
        '[π=(TYPE=INFORM)|A=()|R=()|'
        'C=(THREAD="t1",REFERENCES=["p0"])|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    octad = compile_canonical_lattice(source).packets[0].octad
    reference = replace(octad.context.references[0], depth=2)
    context = replace(octad.context, references=(reference,))
    with pytest.raises(CompilationError, match="stable packet IDs"):
        canonical_lattice_dumps(replace(octad, context=context))


def test_encoder_rejects_invalid_named_packet_label() -> None:
    source = (
        '[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    octad = compile_canonical_lattice(source).packets[0].octad
    with pytest.raises(CompilationError, match="canonical identifier"):
        canonical_lattice_dumps(octad, label="bad label")


def test_encoder_rejects_unrepresentable_audience_identifier() -> None:
    source = (
        '[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
        'Π=()|E=()|Ω=(FORMAT=NL)]'
    )
    octad = compile_canonical_lattice(source).packets[0].octad
    context = replace(octad.context, audience=("human user",))
    with pytest.raises(CompilationError, match="canonical identifier"):
        canonical_lattice_dumps(replace(octad, context=context))


def test_versioned_gov_ext_vector_is_not_canonical_v01() -> None:
    data = (ROOT / "unrepresentable" / "gov-ext-authorization-ref.json").read_bytes()
    with pytest.raises(CanonicalizationError, match="authorization_ref"):
        canonical_loads(data)


def test_versioned_rich_evidence_vector_fails_lattice_encoding() -> None:
    packet = canonical_loads(
        (ROOT / "unrepresentable" / "rich-evidence.json").read_bytes()
    )
    with pytest.raises(CompilationError, match="rich evidence metadata"):
        canonical_lattice_dumps(packet.octad)
