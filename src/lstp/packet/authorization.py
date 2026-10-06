"""Host-side authorization, delegation attenuation, expiry, and replay controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from lstp.errors import AuthorizationError, Diagnostic
from lstp.formats import parse_rfc3339
from lstp.models import PacketEnvelope, Permissions
from lstp.packet.replay import ReplayGuard, ReplayStore
from lstp.packet.validator import MODE_CAPABILITIES, require_semantic_validity

CAPABILITIES = frozenset().union(*MODE_CAPABILITIES.values())
_SIDE_EFFECTS = frozenset({"write", "execute", "commit"})


def _diag(code: str, message: str, path: str | None = None) -> Diagnostic:
    return Diagnostic(code=code, message=message, path=path)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Authority:
    """Capabilities/resources granted by a trusted host boundary."""

    capabilities: frozenset[str]
    resources: frozenset[str]

    def __post_init__(self) -> None:
        unknown = self.capabilities - CAPABILITIES
        if unknown:
            raise ValueError(f"unknown authority capabilities: {sorted(unknown)!r}")
        if any(not item for item in self.resources):
            raise ValueError("authority resource ids must be non-empty")


@dataclass(frozen=True, slots=True)
class PrincipalContext:
    """Authenticated principal identity and its current host authority."""

    principal_id: str
    authority: Authority

    def __post_init__(self) -> None:
        if not self.principal_id:
            raise ValueError("principal_id must be non-empty")


@dataclass(frozen=True, slots=True)
class DelegationContext:
    """Trusted parent identity and authority for one delegated packet."""

    packet_id: str
    principal_id: str
    authority: Authority

    def __post_init__(self) -> None:
        if not self.packet_id or not self.principal_id:
            raise ValueError("delegation packet_id and principal_id must be non-empty")


@dataclass(frozen=True, slots=True)
class HostPolicy:
    """Host policy that can only narrow principal/runtime authority."""

    capabilities: frozenset[str] = field(default_factory=lambda: CAPABILITIES)
    resources: frozenset[str] = field(default_factory=frozenset)
    trusted_authorization_refs: frozenset[str] = field(default_factory=frozenset)
    require_confirmation_for: frozenset[str] = field(default_factory=lambda: _SIDE_EFFECTS)
    require_review_for: frozenset[str] = field(default_factory=frozenset)
    require_logging_for: frozenset[str] = field(default_factory=lambda: _SIDE_EFFECTS)

    def __post_init__(self) -> None:
        for name, values in (
            ("capabilities", self.capabilities),
            ("require_confirmation_for", self.require_confirmation_for),
            ("require_review_for", self.require_review_for),
            ("require_logging_for", self.require_logging_for),
        ):
            unknown = values - CAPABILITIES
            if unknown:
                raise ValueError(f"unknown {name} capabilities: {sorted(unknown)!r}")
        if any(not item for item in self.resources):
            raise ValueError("policy resource ids must be non-empty")
        if any(not item for item in self.trusted_authorization_refs):
            raise ValueError("trusted authorization references must be non-empty")


@dataclass(frozen=True, slots=True)
class OperationRequest:
    """Concrete operation evaluated immediately before a host side effect."""

    capability: str
    resource_id: str
    operation_id: str
    action_digest: str
    confirmed: bool = False
    reviewed: bool = False
    logging_ready: bool = False

    def __post_init__(self) -> None:
        if self.capability not in CAPABILITIES:
            raise ValueError(f"unknown operation capability: {self.capability!r}")
        if not self.resource_id:
            raise ValueError("operation resource_id must be non-empty")
        if not self.operation_id:
            raise ValueError("operation_id must be non-empty")
        if not self.action_digest:
            raise ValueError("action_digest must be non-empty")


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    diagnostics: tuple[Diagnostic, ...]
    effective_capabilities: frozenset[str]
    effective_resources: frozenset[str]

    def raise_for_denial(self) -> None:
        if not self.allowed:
            raise AuthorizationError(self.diagnostics)


def _requested_authority(permissions: Permissions) -> Authority:
    """Translate Whitepaper wire semantics into host-internal authority.

    The packet transports one requested permission mode plus explicit scope.
    Concrete capabilities exist only at the host boundary. Forbid removes
    exact scope entries; it never grants or widens authority.
    """
    capabilities = (
        frozenset()
        if permissions.mode is None
        else MODE_CAPABILITIES[permissions.mode]
    )
    resources = frozenset(permissions.scope) - frozenset(permissions.forbid)
    return Authority(capabilities, resources)


def effective_authority(
    packet: PacketEnvelope,
    *,
    principal: PrincipalContext,
    policy: HostPolicy,
    runtime: Authority,
) -> Authority:
    """Compute requested ∩ principal ∩ policy ∩ runtime authority."""
    require_semantic_validity(packet)
    requested = _requested_authority(packet.octad.permissions)
    capabilities = (
        requested.capabilities
        & principal.authority.capabilities
        & policy.capabilities
        & runtime.capabilities
    )
    resources = (
        requested.resources
        & principal.authority.resources
        & policy.resources
        & runtime.resources
    )
    return Authority(capabilities, resources)


def validate_delegation(
    packet: PacketEnvelope,
    *,
    child: PrincipalContext,
    parent: DelegationContext,
) -> tuple[Diagnostic, ...]:
    """Verify identity binding and monotonic attenuation for delegation."""
    delegation = packet.octad.permissions.delegation
    if delegation is None:
        return ()
    requested = _requested_authority(packet.octad.permissions)
    diagnostics: list[Diagnostic] = []

    if delegation.parent_packet is not None and delegation.parent_packet != parent.packet_id:
        diagnostics.append(_diag(
            "delegation_parent_mismatch",
            "delegation parent_packet does not match authenticated parent packet",
            "$.permissions.delegation.parent_packet",
        ))
    if delegation.delegator is not None and delegation.delegator != parent.principal_id:
        diagnostics.append(_diag(
            "delegator_mismatch",
            "delegation delegator does not match authenticated parent principal",
            "$.permissions.delegation.delegator",
        ))
    if delegation.principal is not None and delegation.principal != child.principal_id:
        diagnostics.append(_diag(
            "delegated_principal_mismatch",
            "delegation principal does not match authenticated child principal",
            "$.permissions.delegation.principal",
        ))

    extra_capabilities = requested.capabilities - parent.authority.capabilities
    if extra_capabilities:
        diagnostics.append(_diag(
            "delegation_capability_widening",
            f"delegation requests capabilities outside parent authority: {sorted(extra_capabilities)!r}",
            "$.permissions.mode",
        ))
    extra_resources = requested.resources - parent.authority.resources
    if extra_resources:
        diagnostics.append(_diag(
            "delegation_resource_widening",
            "delegation requests resources outside parent authority",
            "$.permissions.scope",
        ))
    return tuple(diagnostics)


def authorize_operation(
    packet: PacketEnvelope,
    operation: OperationRequest,
    *,
    principal: PrincipalContext,
    policy: HostPolicy,
    runtime: Authority,
    parent: DelegationContext | None = None,
    replay_guard: ReplayStore | None = None,
    now: datetime | None = None,
) -> AuthorizationDecision:
    """Authorize one concrete operation without performing it.

    Callers MUST invoke this immediately before a side effect. If a replay store
    is supplied, side-effect identity is atomically reserved only after every
    other authorization check succeeds.
    """
    require_semantic_validity(packet)
    permissions = packet.octad.permissions
    diagnostics: list[Diagnostic] = []

    if permissions.expires_at is not None:
        expiry = parse_rfc3339(permissions.expires_at)
        current = now or _utc_now()
        if current.tzinfo is None:
            diagnostics.append(_diag(
                "invalid_authorization_clock",
                "authorization clock must be timezone-aware",
            ))
        elif current.astimezone(timezone.utc) >= expiry:
            diagnostics.append(_diag(
                "authorization_expired",
                "permission request has expired",
                "$.permissions.expires_at",
            ))

    if permissions.authorization_ref is not None:
        if permissions.authorization_ref not in policy.trusted_authorization_refs:
            diagnostics.append(_diag(
                "authorization_ref_untrusted",
                "authorization_ref is not recognized by the trusted host policy",
                "$.permissions.authorization_ref",
            ))

    if permissions.delegation is not None:
        if parent is None:
            diagnostics.append(_diag(
                "delegation_parent_authority_missing",
                "delegated packet requires authenticated parent authority",
                "$.permissions.delegation",
            ))
        else:
            diagnostics.extend(validate_delegation(packet, child=principal, parent=parent))

    effective = effective_authority(packet, principal=principal, policy=policy, runtime=runtime)
    if operation.capability not in effective.capabilities:
        diagnostics.append(_diag(
            "capability_denied",
            f"operation capability {operation.capability!r} is not effectively authorized",
            "$.permissions.mode",
        ))
    if operation.resource_id not in effective.resources:
        diagnostics.append(_diag(
            "resource_denied",
            "operation resource is outside effective scope",
            "$.permissions.scope",
        ))

    confirmation_required = (
        permissions.require_confirmation
        or operation.capability in policy.require_confirmation_for
    )
    review_required = permissions.require_review or operation.capability in policy.require_review_for
    logging_required = permissions.require_logging or operation.capability in policy.require_logging_for

    if confirmation_required and not operation.confirmed:
        diagnostics.append(_diag(
            "confirmation_required",
            "trusted confirmation is required for this operation",
        ))
    if review_required and not operation.reviewed:
        diagnostics.append(_diag("review_required", "host review is required for this operation"))
    if logging_required and not operation.logging_ready:
        diagnostics.append(_diag("logging_required", "audit logging must be ready before execution"))

    if diagnostics:
        return AuthorizationDecision(False, tuple(diagnostics), effective.capabilities, effective.resources)

    if replay_guard is not None and operation.capability in _SIDE_EFFECTS:
        existing_digest = replay_guard.reserve(operation.operation_id, operation.action_digest)
        if existing_digest is not None:
            code = "operation_changed" if existing_digest != operation.action_digest else "replay_detected"
            message = (
                "operation id was already bound to different action content"
                if code == "operation_changed"
                else "operation id has already been reserved or executed"
            )
            return AuthorizationDecision(
                False,
                (_diag(code, message),),
                effective.capabilities,
                effective.resources,
            )

    return AuthorizationDecision(True, (), effective.capabilities, effective.resources)


def require_authorized_operation(
    packet: PacketEnvelope,
    operation: OperationRequest,
    *,
    principal: PrincipalContext,
    policy: HostPolicy,
    runtime: Authority,
    parent: DelegationContext | None = None,
    replay_guard: ReplayStore | None = None,
    now: datetime | None = None,
) -> AuthorizationDecision:
    decision = authorize_operation(
        packet,
        operation,
        principal=principal,
        policy=policy,
        runtime=runtime,
        parent=parent,
        replay_guard=replay_guard,
        now=now,
    )
    decision.raise_for_denial()
    return decision


__all__ = [
    "Authority",
    "AuthorizationDecision",
    "DelegationContext",
    "HostPolicy",
    "OperationRequest",
    "PrincipalContext",
    "ReplayGuard",
    "ReplayStore",
    "authorize_operation",
    "effective_authority",
    "require_authorized_operation",
    "validate_delegation",
]
