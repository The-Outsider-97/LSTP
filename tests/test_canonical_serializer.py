from __future__ import annotations

import json

import pytest

from lstp import CanonicalizationError, canonical_dumps, canonical_loads
from lstp.packet.compiler import CompilerOptions, compile_lattice


def _packet():
    return compile_lattice(
        '!open @door {capabilities=[commit], resources=["urn:door:front"], '
        'profile=COMMIT, confirm=true} -> JSON %0.50',
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
