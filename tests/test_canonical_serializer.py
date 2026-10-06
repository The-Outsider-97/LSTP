from __future__ import annotations

import json
from decimal import Decimal

import pytest

from lstp import CanonicalizationError, canonical_dumps, canonical_loads
from lstp.models import Atom, Context, Octad, Output, PacketEnvelope, Permissions, Pragmatics
from lstp.packet.compiler import CompilerOptions, compile_lattice


def _packet():
    return compile_lattice(
        '!open @door {mode=COMMIT, scope=["urn:door:front"], '
        'confirm=true} -> JSON %0.50',
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )


def test_canonical_round_trip_is_byte_stable() -> None:
    packet = _packet()
    encoded = canonical_dumps(packet)
    decoded = canonical_loads(encoded, require_canonical_bytes=True)
    assert decoded == packet
    assert canonical_dumps(decoded) == encoded
    assert b" " not in encoded
    assert b"\n" not in encoded
    assert b'"confidence":0.5' in encoded


def test_noncanonical_but_valid_json_is_rejected_when_requested() -> None:
    encoded = canonical_dumps(_packet())
    pretty = json.dumps(json.loads(encoded), indent=2).encode()
    with pytest.raises(CanonicalizationError, match="not canonical byte form"):
        canonical_loads(pretty, require_canonical_bytes=True)


def test_unknown_core_field_fails_closed() -> None:
    data = json.loads(canonical_dumps(_packet()))
    data["unexpected"] = True
    with pytest.raises(CanonicalizationError, match="unknown canonical field"):
        canonical_loads(json.dumps(data))


def test_wrong_optional_type_fails_instead_of_being_coerced() -> None:
    data = json.loads(canonical_dumps(_packet()))
    data["permissions"]["require_confirmation"] = "false"
    with pytest.raises(CanonicalizationError, match="boolean"):
        canonical_loads(json.dumps(data))


def test_non_nfc_string_is_not_canonical() -> None:
    data = json.loads(canonical_dumps(_packet()))
    data["id"] = "e\u0301"
    with pytest.raises(CanonicalizationError, match="NFC"):
        canonical_loads(json.dumps(data, ensure_ascii=False))


def test_bidi_control_is_not_canonical() -> None:
    data = json.loads(canonical_dumps(_packet()))
    data["id"] = "safe\u202edanger"
    with pytest.raises(CanonicalizationError, match="bidirectional"):
        canonical_loads(json.dumps(data, ensure_ascii=False))


def test_pathological_decimal_exponent_fails_before_expansion() -> None:
    packet = PacketEnvelope(
        Octad(
            Pragmatics("inform"),
            (Atom("a0", "value", value=Decimal("1e999999")),),
            (),
            Context("t1"),
            1.0,
            Permissions(),
            (),
            Output("NL"),
        ),
        "p1",
        "0.1",
        carrier={},
        audit={},
    )
    with pytest.raises(CanonicalizationError, match="exponent"):
        canonical_dumps(packet)
