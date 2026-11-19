from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lstp import (
    Atom,
    CanonicalizationError,
    Context,
    EvidenceItem,
    InputLimits,
    LSTPError,
    Octad,
    Output,
    PacketEnvelope,
    Permissions,
    Pragmatics,
    Relation,
    ResourceLimitError,
    canonical_dumps,
    canonical_loads,
    compact_dumps,
    compact_loads,
    incremental_dumps,
    incremental_loads,
)


def packet() -> PacketEnvelope:
    return PacketEnvelope(
        Octad(
            Pragmatics("request", speech_act="command", goal="slai.inspect"),
            (
                Atom("a0", "resource", "roof", role="TARGET"),
                Atom("a1", "concept", "inspect", role="ACTION"),
            ),
            (),
            Context("thread", bindings={"project": "spadra", "stage": "review"}),
            1,
            Permissions("PREVIEW", scope=("roof",)),
            (EvidenceItem("e0", "user", source_ref="urn:test:source"),),
            Output("JSON"),
        ),
        "p1",
        "0.1",
    )


def test_every_field_and_literal_dictionary_survives() -> None:
    original = packet()
    literal = {"id": "a0", "permissions": {"mode": "COMMIT"}, "L1": [None, True]}
    rich = replace(
        original,
        octad=replace(
            original.octad,
            pragmatics=replace(
                original.octad.pragmatics,
                modifiers=("polite",),
                urgency=0.2,
                extensions={"test": literal},
            ),
            atoms=(
                replace(
                    original.octad.atoms[0],
                    kind="proposition",
                    value=literal,
                    attributes=literal,
                    datatype="object",
                    language="en",
                ),
                original.octad.atoms[1],
            ),
            relations=(
                Relation(
                    "lstp.test",
                    ("a0", "a1"),
                    id="r0",
                    confidence=0.7,
                    attributes=literal,
                    extensions={"test": literal},
                ),
            ),
            confidence=0.87,
            permissions=Permissions(
                "COMMIT",
                scope=("roof",),
                forbid=("other",),
                require_confirmation=True,
                require_review=True,
                require_logging=True,
                limits={"max_calls": 2},
                extensions={"test": literal},
            ),
            evidence=(
                EvidenceItem(
                    "e0",
                    "tool",
                    source_ref="urn:source",
                    input_hash="abc",
                    span={"start": 0, "end": 1},
                    supports=("a0", "r0"),
                    description="evidence",
                    confidence=0.6,
                    extensions={"test": literal},
                ),
            ),
            output=Output(
                "JSON",
                schema="urn:schema",
                channel="test.channel",
                target="dest",
                language="en",
                max_bytes=1024,
                requirements=("compact",),
                extensions={"test": literal},
            ),
        ),
        carrier=literal,
        audit=literal,
        extensions={"test": literal},
    )
    encoded = compact_dumps(rich, profile="typed")
    assert canonical_dumps(compact_loads(encoded, require_compact_bytes=True)) == canonical_dumps(
        rich
    )


@settings(max_examples=100, derandomize=True)
@given(st.text(alphabet="abcXYZ_ 123Ã©", min_size=1, max_size=100), st.booleans())
def test_unicode_and_permission_constraints_roundtrip(value: str, confirmation: bool) -> None:
    original = packet()
    original = replace(
        original,
        octad=replace(
            original.octad,
            atoms=(replace(original.octad.atoms[0], value=value), original.octad.atoms[1]),
            permissions=replace(original.octad.permissions, require_confirmation=confirmation),
        ),
    )
    assert canonical_dumps(
        compact_loads(compact_dumps(original, profile="typed"))
    ) == canonical_dumps(original)


def test_decimal_serialization_is_independent_of_ambient_precision() -> None:
    original = packet()
    literal = Decimal("0.123456789012345678901234567890123456789000")
    original = replace(original, carrier={"precise": literal})
    with localcontext() as context:
        context.prec = 6
        wire = canonical_dumps(original)
        restored = compact_loads(compact_dumps(original, profile="typed"))
    assert b"0.123456789012345678901234567890123456789" in wire
    assert restored.carrier["precise"] == literal


@pytest.mark.parametrize("source", [b"[]", b'["L2",[]]', b'["L1",{}]', b'["L1",[1]]'])
def test_malformed_and_unknown_profiles_fail(source: bytes) -> None:
    with pytest.raises(CanonicalizationError):
        compact_loads(source)


def test_canonical_type_checks_and_duplicate_rejection_are_not_bypassed() -> None:
    encoded = json.loads(compact_dumps(packet(), profile="typed"))
    encoded[1].extend([None] * (9 - len(encoded[1])))
    encoded[1][8] = True
    with pytest.raises(CanonicalizationError):
        compact_loads(json.dumps(encoded))
    with pytest.raises(Exception, match="Duplicate JSON"):
        compact_loads('["L1",["p",["inform"],[],["t"],[],["NL"],[],[],1,{"x":1,"x":2}]]')


def test_limits_apply_to_both_carrier_and_expansion() -> None:
    encoded = compact_dumps(packet(), profile="typed")
    with pytest.raises(ResourceLimitError):
        compact_loads(encoded, limits=InputLimits(max_bytes=len(encoded) - 1))
    with pytest.raises(ResourceLimitError):
        compact_loads(encoded, limits=InputLimits(max_bytes=len(encoded) + 1))


def test_deterministic_carrier_check() -> None:
    encoded = compact_dumps(packet(), profile="typed")
    assert compact_loads(b" " + encoded) == packet()
    with pytest.raises(CanonicalizationError, match="deterministic"):
        compact_loads(b" " + encoded, require_compact_bytes=True)


def test_large_incremental_packet_restores_and_rejects_wrong_or_missing_base() -> None:
    original = replace(packet(), carrier={"shared": "context " * 1500})
    changed = replace(original, packet_id="p2", octad=replace(original.octad, confidence=0.8))
    delta = incremental_dumps(changed, base=original)
    assert json.loads(delta)[0] == "D1"
    assert incremental_loads(delta, base=original) == changed
    reloaded = canonical_loads(canonical_dumps(original))
    assert incremental_loads(delta, base=reloaded) == changed
    for base in (None, changed):
        with pytest.raises(CanonicalizationError, match="base"):
            incremental_loads(delta, base=base)
    corrupted = json.loads(delta)
    corrupted[2] = "0" * 64
    with pytest.raises(CanonicalizationError, match="digest"):
        incremental_loads(json.dumps(corrupted), base=original)


@pytest.mark.parametrize("changes", [[[0, "p2"], [0, "p3"]], [[True, "x"]], [[999, "x"]]])
def test_delta_rejects_duplicate_noninteger_and_out_of_range_slots(changes: list) -> None:
    original = replace(packet(), carrier={"shared": "x" * 2000})
    value = json.loads(incremental_dumps(replace(original, packet_id="p2"), base=original))
    value[4] = changes
    with pytest.raises(CanonicalizationError):
        incremental_loads(json.dumps(value), base=original)


def test_independent_small_messages_fall_back_to_self_contained_full_carrier() -> None:
    changed = replace(packet(), packet_id="p2")
    encoded = incremental_dumps(changed, base=packet())
    assert len(encoded) <= len(compact_dumps(changed, profile="typed"))
    assert incremental_loads(incremental_dumps(changed)) == changed


def test_shared_interoperability_fixtures_include_manually_authored_vector() -> None:
    fixture = json.loads((Path(__file__).parents[1] / "conformance/compact-v1.json").read_text())
    for row in fixture["positive"]:
        restored = compact_loads(json.dumps(row["compact"]))
        expected = canonical_loads(json.dumps(row["canonical"]))
        assert canonical_dumps(restored) == canonical_dumps(expected)
    for row in fixture["negative"]:
        with pytest.raises(LSTPError):
            compact_loads(json.dumps(row))
