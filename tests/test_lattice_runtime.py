from __future__ import annotations

import pytest

from lstp.errors import CompilationError, LatticeSyntaxError
from lstp.packet.compiler import CompilerOptions, compile_lattice
from lstp.text.ast import MainClause
from lstp.text.parser import parse
from lstp.text.tokenizer import tokenize


def test_tokenizer_prefers_longest_operators() -> None:
    kinds = [token.kind.value for token in tokenize("!!alert -> NL") if token.value]
    assert kinds[:3] == ["URGENT_DIRECTIVE", "IDENTIFIER", "ARROW"]


def test_parser_builds_main_clause() -> None:
    document = parse("!request @door -> NL %0.8")
    clause = document.clauses[0]
    assert isinstance(clause, MainClause)
    assert clause.action == "request"
    assert clause.confidence is not None


def test_parser_rejects_reserved_undefined_operator() -> None:
    with pytest.raises(LatticeSyntaxError):
        parse("!state @x <= y")


def test_compiler_produces_typed_canonical_packet() -> None:
    packet = compile_lattice(
        '!open @front_door {mode=COMMIT, scope=["urn:door:front"], confirm=true} -> NL %0.95\n'
        'because[user("urn:user:request")]',
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    assert packet.protocol_version == "0.1"
    assert packet.octad.pragmatics.type == "request"
    assert packet.octad.pragmatics.speech_act == "command"
    assert packet.octad.pragmatics.goal == "open"
    assert packet.octad.permissions.mode == "COMMIT"
    assert packet.octad.permissions.scope == ("urn:door:front",)
    assert packet.octad.permissions.require_confirmation is True
    assert packet.octad.evidence[0].source_type == "user"


def test_relative_context_must_resolve_before_canonical_compile() -> None:
    with pytest.raises(CompilationError, match="context_resolver"):
        compile_lattice("?risk ↑2 -> NL", options=CompilerOptions(packet_id="p1", thread_id="t1"))


def test_relative_context_resolution_is_stable_packet_id() -> None:
    packet = compile_lattice(
        "?risk ↑2 -> NL",
        options=CompilerOptions(
            packet_id="p1", thread_id="t1",
            context_resolver=lambda depth, agent: f"history-{depth}",
        ),
    )
    assert packet.octad.context.references[0].packet_id == "history-2"


def test_october_candidate_permission_fields_fail_closed() -> None:
    with pytest.raises(CompilationError, match="not canonical"):
        compile_lattice(
            "!open @door {capabilities=[commit]} -> NL",
            options=CompilerOptions(packet_id="p1", thread_id="t1"),
        )
