from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace

import pytest
from test_compact_carrier import packet

from lstp import (
    ActionProjection,
    ProjectionError,
    Relation,
    decode_action_result,
    prepare_action_input,
    project_action,
)


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
    assert prepared.representation in {"canonical", "compact"}


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
    assert len(counted) == 4
    assert all(system and user for system, user in counted)
    with pytest.raises(ValueError):
        prepare_action_input(packet(), lambda system, user: True)


def test_identifier_at_eof_cannot_hang() -> None:
    result = subprocess.run(
        [sys.executable, "-c", 'from lstp import tokenize; assert tokenize("identifier")'],
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
