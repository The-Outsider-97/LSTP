from __future__ import annotations

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lstp import (
    CanonicalizationError,
    InputLimits,
    LatticeSyntaxError,
    ResourceLimitError,
    SemanticValidationError,
    canonical_dumps,
    canonical_loads,
)
from lstp.packet.compiler import CompilerOptions, compile_lattice
from lstp.text.canonical import parse_canonical_lattice

MODES = ("RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT")
SIDE_EFFECT_MODES = ("RW", "EXEC", "COMMIT")
SAFE_RESOURCE = st.from_regex(r"urn:test:[a-z]{1,12}", fullmatch=True)


@settings(max_examples=150, derandomize=True)
@given(st.sampled_from(MODES), SAFE_RESOURCE)
def test_compact_permission_mode_and_scope_are_preserved_exactly(
    mode: str,
    resource: str,
) -> None:
    packet = compile_lattice(
        f'!inspect @target {{mode={mode}, scope=["{resource}"]}} -> JSON',
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    assert packet.octad.permissions.mode == mode
    assert packet.octad.permissions.scope == (resource,)


@settings(max_examples=150, derandomize=True)
@given(SAFE_RESOURCE)
def test_compact_forbid_never_widens_requested_scope(resource: str) -> None:
    packet = compile_lattice(
        (
            '!inspect @target {mode=COMMIT, '
            f'scope=["{resource}"], forbid=["{resource}"]}} -> JSON'
        ),
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    assert packet.octad.permissions.scope == (resource,)
    assert packet.octad.permissions.forbid == (resource,)


@pytest.mark.parametrize("mode", SIDE_EFFECT_MODES)
def test_side_effect_modes_without_scope_fail_semantic_validation(mode: str) -> None:
    source = json.dumps(
        {
            "id": "p1",
            "version": "0.1",
            "pragmatics": {"type": "request"},
            "atoms": [],
            "relations": [],
            "context": {"thread_id": "t1", "references": []},
            "confidence": 1,
            "permissions": {"mode": mode},
            "evidence": [],
            "output": {"format": "NONE"},
            "carrier": {},
            "audit": {},
        },
        separators=(",", ":"),
    )
    with pytest.raises(SemanticValidationError, match="explicit scope"):
        canonical_loads(source)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authorization_ref", "auth-1"),
        ("expires_at", "2026-10-06T12:00:00Z"),
        ("delegation", {"parent_packet": "p0"}),
        ("capabilities", ["commit"]),
        ("resources", ["urn:test:x"]),
        ("profile", "COMMIT"),
    ],
)
def test_noncore_permission_channels_fail_closed(field: str, value: object) -> None:
    packet = {
        "id": "p1",
        "version": "0.1",
        "pragmatics": {"type": "inform"},
        "atoms": [],
        "relations": [],
        "context": {"thread_id": "t1", "references": []},
        "confidence": 1,
        "permissions": {field: value},
        "evidence": [],
        "output": {"format": "NL"},
        "carrier": {},
        "audit": {},
    }
    with pytest.raises(CanonicalizationError, match="unknown canonical field"):
        canonical_loads(json.dumps(packet, separators=(",", ":")))


BASE_CANONICAL = (
    '[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|κ=1|'
    'Π=()|E=()|Ω=(FORMAT=NL)]'
)


@pytest.mark.parametrize(
    "mutated",
    [
        (
            '[A=()|π=(TYPE=INFORM)|R=()|C=(THREAD="t1")|κ=1|'
            'Π=()|E=()|Ω=(FORMAT=NL)]'
        ),
        (
            '[π=(TYPE=INFORM)|A=()|C=(THREAD="t1")|R=()|κ=1|'
            'Π=()|E=()|Ω=(FORMAT=NL)]'
        ),
        (
            '[π=(TYPE=INFORM)|A=()|R=()|C=(THREAD="t1")|Π=()|'
            'κ=1|E=()|Ω=(FORMAT=NL)]'
        ),
    ],
)
def test_canonical_octad_segment_reordering_is_rejected(mutated: str) -> None:
    assert parse_canonical_lattice(BASE_CANONICAL).packets
    with pytest.raises(LatticeSyntaxError):
        parse_canonical_lattice(mutated)


def _minimal_packet_mapping() -> dict[str, object]:
    return {
        "id": "p1",
        "version": "0.1",
        "pragmatics": {"type": "inform"},
        "atoms": [],
        "relations": [],
        "context": {"thread_id": "t1", "references": []},
        "confidence": 1,
        "permissions": {},
        "evidence": [],
        "output": {"format": "NL"},
        "carrier": {},
        "audit": {},
    }


UNKNOWN_FIELD = st.from_regex(
    r"x_[a-z]{1,12}",
    fullmatch=True,
)


@settings(max_examples=120, derandomize=True)
@given(UNKNOWN_FIELD, st.integers() | st.text(max_size=20))
def test_unknown_top_level_fields_always_fail_closed(
    field: str,
    value: object,
) -> None:
    packet = _minimal_packet_mapping()
    packet[field] = value
    with pytest.raises(CanonicalizationError, match="unknown canonical field"):
        canonical_loads(json.dumps(packet, separators=(",", ":")))


@settings(max_examples=120, derandomize=True)
@given(UNKNOWN_FIELD, st.integers() | st.text(max_size=20))
def test_unknown_permission_fields_always_fail_closed(
    field: str,
    value: object,
) -> None:
    packet = _minimal_packet_mapping()
    permissions = packet["permissions"]
    assert isinstance(permissions, dict)
    permissions[field] = value
    with pytest.raises(CanonicalizationError, match="unknown canonical field"):
        canonical_loads(json.dumps(packet, separators=(",", ":")))


@pytest.mark.parametrize(
    ("container", "legacy_field", "value"),
    [
        ("pragmatics", "act", "inform"),
        ("context", "parent_id", "p0"),
        ("permissions", "capabilities", ["read"]),
        ("permissions", "resources", ["urn:test:x"]),
        ("permissions", "profile", "RO"),
    ],
)
def test_legacy_candidate_fields_are_not_silently_migrated(
    container: str,
    legacy_field: str,
    value: object,
) -> None:
    packet = _minimal_packet_mapping()
    target = packet[container]
    assert isinstance(target, dict)
    target[legacy_field] = value
    with pytest.raises(CanonicalizationError, match="unknown canonical field"):
        canonical_loads(json.dumps(packet, separators=(",", ":")))


def test_canonical_decoder_enforces_resource_limits_before_acceptance() -> None:
    packet = _minimal_packet_mapping()
    source = json.dumps(packet, separators=(",", ":"))
    with pytest.raises(ResourceLimitError):
        canonical_loads(
            source,
            limits=InputLimits(max_bytes=len(source.encode("utf-8")) - 1),
        )


def test_strict_canonical_byte_mode_rejects_whitespace_mutation() -> None:
    packet = canonical_loads(
        json.dumps(_minimal_packet_mapping(), separators=(",", ":"))
    )
    canonical = canonical_dumps(packet)
    mutated = canonical.replace(b"{", b"{ ", 1)
    assert mutated != canonical
    with pytest.raises(CanonicalizationError, match="not canonical byte form"):
        canonical_loads(mutated, require_canonical_bytes=True)


@settings(max_examples=120, derandomize=True)
@given(st.sampled_from(MODES), SAFE_RESOURCE)
def test_compact_to_canonical_json_round_trip_preserves_permissions(
    mode: str,
    resource: str,
) -> None:
    packet = compile_lattice(
        f'!inspect @target {{mode={mode}, scope=["{resource}"]}} -> JSON',
        options=CompilerOptions(packet_id="p1", thread_id="t1"),
    )
    restored = canonical_loads(
        canonical_dumps(packet),
        require_canonical_bytes=True,
    )
    assert restored.octad.permissions == packet.octad.permissions
