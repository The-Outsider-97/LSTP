from __future__ import annotations

from datetime import datetime, timezone

import pytest

from lstp.errors import AuthorizationError
from lstp.models import (
    Context,
    Delegation,
    Octad,
    Output,
    PacketEnvelope,
    Permissions,
    Pragmatics,
)
from lstp.packet.authorization import (
    Authority,
    DelegationContext,
    HostPolicy,
    OperationRequest,
    PrincipalContext,
    ReplayGuard,
    authorize_operation,
    effective_authority,
    require_authorized_operation,
)

RESOURCE = "urn:test:document:1"
OTHER_RESOURCE = "urn:test:document:2"


def _packet(
    *,
    mode: str = "COMMIT",
    scope: tuple[str, ...] = (RESOURCE,),
    confirmation: bool = False,
    review: bool = False,
    logging: bool = False,
    expires_at: str | None = None,
    authorization_ref: str | None = None,
    delegation: Delegation | None = None,
) -> PacketEnvelope:
    return PacketEnvelope(
        Octad(
            Pragmatics("request", goal="test.commit"),
            (),
            (),
            Context("thread-1"),
            1.0,
            Permissions(
                mode=mode,
                scope=scope,
                require_confirmation=confirmation,
                require_review=review,
                require_logging=logging,
                authorization_ref=authorization_ref,
                expires_at=expires_at,
                delegation=delegation,
            ),
            (),
            Output("NONE"),
        ),
        "packet-1",
        "0.1",
    )


def _authority(*capabilities: str, resources: tuple[str, ...] = (RESOURCE,)) -> Authority:
    return Authority(frozenset(capabilities), frozenset(resources))


def _principal(*capabilities: str, resources: tuple[str, ...] = (RESOURCE,)) -> PrincipalContext:
    return PrincipalContext("agent.child", _authority(*capabilities, resources=resources))


def _policy(*capabilities: str, resources: tuple[str, ...] = (RESOURCE,)) -> HostPolicy:
    return HostPolicy(
        capabilities=frozenset(capabilities),
        resources=frozenset(resources),
        require_confirmation_for=frozenset(),
        require_logging_for=frozenset(),
    )


def _operation(
    *,
    capability: str = "commit",
    resource: str = RESOURCE,
    operation_id: str = "op-1",
    digest: str = "sha256:action-1",
    confirmed: bool = True,
    reviewed: bool = True,
    logging_ready: bool = True,
) -> OperationRequest:
    return OperationRequest(
        capability,
        resource,
        operation_id,
        digest,
        confirmed,
        reviewed,
        logging_ready,
    )


def test_effective_authority_is_exact_four_way_intersection() -> None:
    packet = _packet(mode="COMMIT")
    effective = effective_authority(
        packet,
        principal=_principal("read", "commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
    )
    assert effective.capabilities == frozenset({"commit"})
    assert effective.resources == frozenset({RESOURCE})



@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("RO", {"read"}),
        ("SUGGEST", {"read", "suggest"}),
        ("PREVIEW", {"read", "suggest", "prepare"}),
        ("RW", {"read", "suggest", "prepare", "write"}),
        ("EXEC", {"read", "suggest", "prepare", "write", "execute"}),
        (
            "COMMIT",
            {"read", "suggest", "prepare", "write", "execute", "commit"},
        ),
    ],
)
def test_whitepaper_mode_maps_monotonically_to_host_capabilities(
    mode: str,
    expected: set[str],
) -> None:
    all_capabilities = ("read", "suggest", "prepare", "write", "execute", "commit")
    effective = effective_authority(
        _packet(mode=mode),
        principal=_principal(*all_capabilities),
        policy=_policy(*all_capabilities),
        runtime=_authority(*all_capabilities),
    )
    assert effective.capabilities == frozenset(expected)


def test_forbid_removes_exact_scope_before_host_intersection() -> None:
    packet = PacketEnvelope(
        Octad(
            Pragmatics("request", speech_act="command", goal="test.commit"),
            (),
            (),
            Context("thread-1"),
            1.0,
            Permissions(
                mode="COMMIT",
                scope=(RESOURCE,),
                forbid=(RESOURCE,),
            ),
            (),
            Output("NONE"),
        ),
        "packet-1",
        "0.1",
    )
    decision = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
    )
    assert decision.allowed is False
    assert "resource_denied" in {item.code for item in decision.diagnostics}

def test_unresolved_forbid_expression_fails_closed() -> None:
    packet = _packet()
    packet = PacketEnvelope(
        Octad(
            packet.octad.pragmatics,
            packet.octad.atoms,
            packet.octad.relations,
            packet.octad.context,
            packet.octad.confidence,
            Permissions(
                mode="COMMIT",
                scope=(RESOURCE,),
                forbid=("external-write",),
            ),
            packet.octad.evidence,
            packet.octad.output,
        ),
        packet.packet_id,
        packet.protocol_version,
    )
    decision = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
    )
    assert decision.allowed is False
    assert "unresolved_permission_forbid" in {
        item.code for item in decision.diagnostics
    }


def test_empty_trusted_resource_scope_is_never_wildcard() -> None:
    packet = _packet()
    decision = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit", resources=()),
        policy=_policy("commit"),
        runtime=_authority("commit"),
    )
    assert decision.allowed is False
    assert {item.code for item in decision.diagnostics} >= {"resource_denied"}


def test_capability_or_resource_missing_from_any_boundary_denies() -> None:
    packet = _packet()
    decision = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("read"),
        runtime=_authority("commit"),
    )
    assert decision.allowed is False
    assert "capability_denied" in {item.code for item in decision.diagnostics}

    resource_decision = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("commit", resources=(OTHER_RESOURCE,)),
        runtime=_authority("commit"),
    )
    assert resource_decision.allowed is False
    assert "resource_denied" in {item.code for item in resource_decision.diagnostics}


def test_packet_and_host_confirmation_review_logging_constraints_accumulate() -> None:
    packet = _packet(confirmation=True, review=True, logging=True)
    operation = _operation(confirmed=False, reviewed=False, logging_ready=False)
    decision = authorize_operation(
        packet,
        operation,
        principal=_principal("commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
    )
    assert {item.code for item in decision.diagnostics} >= {
        "confirmation_required",
        "review_required",
        "logging_required",
    }


def test_expired_permission_request_fails_closed() -> None:
    packet = _packet(expires_at="2026-10-05T12:00:00Z")
    decision = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
        now=datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc),
    )
    assert decision.allowed is False
    assert "authorization_expired" in {item.code for item in decision.diagnostics}


def test_invalid_or_untrusted_authorization_reference_fails_closed() -> None:
    packet = _packet(authorization_ref="auth-123")
    denied = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
    )
    assert "authorization_ref_untrusted" in {item.code for item in denied.diagnostics}

    policy = HostPolicy(
        capabilities=frozenset({"commit"}),
        resources=frozenset({RESOURCE}),
        trusted_authorization_refs=frozenset({"auth-123"}),
        require_confirmation_for=frozenset(),
        require_logging_for=frozenset(),
    )
    allowed = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=policy,
        runtime=_authority("commit"),
    )
    assert allowed.allowed is True


def test_delegation_requires_authenticated_parent_and_attenuation() -> None:
    packet = _packet(
        delegation=Delegation(
            parent_packet="parent-1",
            delegator="agent.parent",
            principal="agent.child",
        )
    )
    no_parent = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
    )
    assert "delegation_parent_authority_missing" in {
        item.code for item in no_parent.diagnostics
    }

    narrowed_parent = DelegationContext(
        "parent-1",
        "agent.parent",
        _authority("read"),
    )
    widened = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
        parent=narrowed_parent,
    )
    assert "delegation_capability_widening" in {item.code for item in widened.diagnostics}


def test_delegation_identity_mismatch_is_rejected() -> None:
    packet = _packet(
        delegation=Delegation(
            parent_packet="parent-1",
            delegator="agent.parent",
            principal="agent.child",
        )
    )
    wrong_parent = DelegationContext(
        "other-parent",
        "agent.other",
        _authority("commit"),
    )
    decision = authorize_operation(
        packet,
        _operation(),
        principal=_principal("commit"),
        policy=_policy("commit"),
        runtime=_authority("commit"),
        parent=wrong_parent,
    )
    codes = {item.code for item in decision.diagnostics}
    assert "delegation_parent_mismatch" in codes
    assert "delegator_mismatch" in codes


def test_replay_guard_reserves_side_effect_atomically() -> None:
    guard = ReplayGuard()
    packet = _packet()
    kwargs = {
        "principal": _principal("commit"),
        "policy": _policy("commit"),
        "runtime": _authority("commit"),
        "replay_guard": guard,
    }
    first = authorize_operation(packet, _operation(), **kwargs)
    second = authorize_operation(packet, _operation(), **kwargs)
    changed = authorize_operation(
        packet,
        _operation(digest="sha256:changed"),
        **kwargs,
    )
    assert first.allowed is True
    assert second.allowed is False
    assert second.diagnostics[0].code == "replay_detected"
    assert changed.allowed is False
    assert changed.diagnostics[0].code == "operation_changed"


def test_failed_authorization_does_not_consume_replay_identity() -> None:
    guard = ReplayGuard()
    packet = _packet(confirmation=True)
    common = {
        "principal": _principal("commit"),
        "policy": _policy("commit"),
        "runtime": _authority("commit"),
        "replay_guard": guard,
    }
    denied = authorize_operation(packet, _operation(confirmed=False), **common)
    allowed = authorize_operation(packet, _operation(confirmed=True), **common)
    assert denied.allowed is False
    assert allowed.allowed is True


def test_require_authorized_operation_raises_stable_error() -> None:
    with pytest.raises(AuthorizationError) as caught:
        require_authorized_operation(
            _packet(),
            _operation(),
            principal=_principal("read"),
            policy=_policy("commit"),
            runtime=_authority("commit"),
        )
    assert caught.value.diagnostics[0].code == "capability_denied"
