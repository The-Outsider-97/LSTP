from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from unittest.mock import patch

import pytest
from test_compact_carrier import packet

from lstp import (
    ActionProjection,
    ProjectionError,
    Relation,
    canonical_dumps,
    decode_action_result,
    prepare_action_input,
    project_action,
)
from lstp.inference import TUPLE_INPUT_INSTRUCTION, TYPED_COMPACT_INSTRUCTION
from lstp.packet import serializer


def test_projection_is_exact_and_source_bound() -> None:
    projection = project_action(packet())
    assert projection.source == packet()
    assert len(projection.source_sha256) == 64
    assert projection.validate_response(projection.dumps()) == projection.as_mapping()
    assert (
        projection.validate_response(projection.dumps(tuples=False), tuples=False)
        == projection.as_mapping()
    )
    changed = list(projection.values)
    changed[4] = "COMMIT"
    with pytest.raises(ProjectionError, match="changed"):
        projection.validate_response(json.dumps(changed))


@pytest.mark.parametrize("field", ["permissions", "evidence", "context", "confidence", "relations"])
def test_projection_refuses_additional_meaning(field: str) -> None:
    original = packet()
    octad = original.octad
    value = {
        "permissions": replace(octad.permissions, require_confirmation=True),
        "evidence": (replace(octad.evidence[0], confidence=0.8),),
        "context": replace(octad.context, speaker="agent"),
        "confidence": 0.9,
        "relations": (Relation("lstp.test", ("a0",)),),
    }[field]
    original = replace(original, octad=replace(octad, **{field: value}))
    with pytest.raises(ProjectionError):
        project_action(original)
    with pytest.raises(ProjectionError):
        ActionProjection(original)
    prepared = prepare_action_input(original, lambda system, user: len(system) + len(user))
    assert prepared.representation == "canonical"
    assert prepared.tuple_output is False
    assert "ACTION atom" in prepared.system


@pytest.mark.parametrize(
    "raw", ["[]", '["x"]', "[1,2,3,4,5,6,7]", '["","b","c","d","e","f","g"]', "{}"]
)
def test_results_require_all_seven_string_fields(raw: str) -> None:
    with pytest.raises(ProjectionError):
        decode_action_result(raw)


def test_selector_counts_full_instructions_and_uses_host_measurement() -> None:
    counted = []

    def counter(system: str, user: str) -> int:
        counted.append((system, user))
        return 1 if '"atoms"' in user else 100000

    chosen = prepare_action_input(packet(), counter)
    assert chosen.representation == "canonical"
    assert chosen.counted_input_tokens == 1
    assert len(counted) == 3
    assert all(system and user for system, user in counted)
    with pytest.raises(ValueError):
        prepare_action_input(packet(), lambda system, user: True)


def test_default_projection_uses_the_live_benchmark_contract() -> None:
    chosen = prepare_action_input(packet(), lambda system, user: len(system) + len(user))
    assert chosen.representation == "projection_tuple"
    assert chosen.system == TUPLE_INPUT_INSTRUCTION
    assert chosen.tuple_output is True
    assert project_action(packet()).validate_response(chosen.user)


def test_schema_heavy_model_input_requires_explicit_opt_in() -> None:
    def counter(system: str, user: str) -> int:
        return 0 if system.startswith(TYPED_COMPACT_INSTRUCTION) else 100

    assert prepare_action_input(packet(), counter).representation != "compact"
    chosen = prepare_action_input(packet(), counter, allow_compact=True)
    assert chosen.representation == "compact"
    assert chosen.user.startswith('["L1",[')


def test_preparation_validates_one_snapshot_and_explicit_output_override() -> None:
    with patch.object(
        serializer, "require_semantic_validity", wraps=serializer.require_semantic_validity
    ) as validate:
        prepared = prepare_action_input(
            packet(), lambda system, user: len(system) + len(user), tuple_output=False
        )
    assert validate.call_count == 1
    assert prepared.tuple_output is False
    assert "JSON object" in prepared.system


def test_projection_keeps_a_stable_source_when_caller_mutates_sequences() -> None:
    original = packet()
    atoms = list(original.octad.atoms)
    original = replace(original, octad=replace(original.octad, atoms=atoms))
    projection = project_action(original)
    source_bytes = canonical_dumps(projection.source)
    source_hash = projection.source_sha256
    atoms.clear()
    assert canonical_dumps(projection.source) == source_bytes
    assert projection.source_sha256 == source_hash
    assert projection.validate_response(projection.dumps()) == projection.as_mapping()


def test_identifier_at_eof_cannot_hang() -> None:
    result = subprocess.run(
        [sys.executable, "-c", 'from lstp import tokenize; assert tokenize("identifier")'],
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def test_default_compact_instruction_describes_the_default_wire_profile() -> None:
    from lstp import compact_dumps
    from lstp.inference import COMPACT_INSTRUCTION

    assert len(json.loads(compact_dumps(packet()))) == 12
    assert COMPACT_INSTRUCTION.startswith("Input is flat LSTP")
    assert TYPED_COMPACT_INSTRUCTION.startswith('Input is LSTP v0.1 as ["L1",packet]')
