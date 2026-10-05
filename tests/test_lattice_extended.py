from __future__ import annotations

import pytest

from lstp.errors import CompilationError
from lstp.packet.compiler import CompilerOptions, compile_lattice
from lstp.text.ast import AmbiguityClause, ClaimClause, MacroDefinition, MainClause
from lstp.text.parser import parse


def test_parser_handles_scope_composition_and_zoom() -> None:
    document = parse(
        "!analyze @sales[-4Q..0Q] :: "
        "lstp.eval(risk + cost | defer) -> JSON@z2"
    )
    clause = document.clauses[0]
    assert isinstance(clause, MainClause)
    assert clause.focus is not None
    assert clause.output is not None
    assert clause.output.zoom == 2


def test_compiler_preserves_scope_as_inspectable_atom_attributes() -> None:
    packet = compile_lattice(
        "!analyze @sales[-4Q..0Q] -> JSON",
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    attributes = packet.octad.atoms[0].attributes
    assert "lstp_scope" in attributes


def test_composition_alternative_exclusion_and_approximation_compile() -> None:
    packet = compile_lattice(
        "!analyze @sales :: lstp.eval((risk + cost) | -delay~) -> JSON",
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    types = {relation.type for relation in packet.octad.relations}
    assert "lstp.compose" in types
    assert "lstp.alternative" in types
    assert "lstp.exclude" in types
    assert "lstp.approximate" in types


def test_macro_definition_expands_before_compilation() -> None:
    source = (
        "def #Decision = { risk + cost }\n"
        "!analyze @sales :: lstp.eval(#Decision) -> JSON"
    )
    document = parse(source)
    assert isinstance(document.clauses[0], MacroDefinition)
    packet = compile_lattice(
        source,
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    assert any(
        relation.type == "lstp.compose" for relation in packet.octad.relations
    )


def test_claim_and_ambiguity_have_inspectable_relations() -> None:
    source = (
        "!analyze @sales -> JSON\n"
        "claim: risk\n"
        "ambig{meaning: finance | river}"
    )
    document = parse(source)
    assert isinstance(document.clauses[1], ClaimClause)
    assert isinstance(document.clauses[2], AmbiguityClause)
    packet = compile_lattice(
        source,
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    types = {relation.type for relation in packet.octad.relations}
    assert "lstp.claim" in types
    assert "lstp.ambiguity" in types


def test_relation_tail_maps_to_inspectable_relation() -> None:
    packet = compile_lattice(
        "!state @dog.color = blue -> JSON",
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    assert packet.octad.relations[0].type == "is"


def test_zoom_is_preserved_as_output_extension_not_new_core_field() -> None:
    packet = compile_lattice(
        "!summarize @report -> JSON@z3",
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    assert packet.octad.output.extensions["lstp"]["zoom"] == 3


def test_target_plus_context_focus_resolves_stable_packet_reference() -> None:
    packet = compile_lattice(
        "!analyze @sales ↑2@risk -> JSON",
        options=CompilerOptions(
            packet_id="p1",
            thread_id="t1",
            context_resolver=lambda depth, agent: f"{agent}-{depth}",
        ),
    )
    assert packet.octad.context.references[0].packet_id == "risk-2"


def test_layout_newlines_are_accepted_inside_constraint_block() -> None:
    source = (
        "!open @door {\n"
        "capabilities=[commit],\n"
        'resources=["urn:door:front"]\n'
        "} -> JSON"
    )
    packet = compile_lattice(
        source,
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    assert packet.octad.permissions.capabilities == ("commit",)


def test_runtime_context_commands_fail_canonical_compilation() -> None:
    with pytest.raises(CompilationError, match="runtime commands"):
        compile_lattice(
            "ctx.push {urgency=0.5}\n!analyze @sales -> JSON",
            options=CompilerOptions(packet_id="p1", thread_id="t1"),
        )
