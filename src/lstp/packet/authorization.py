"""Host-side authorization, delegation attenuation, expiry, and replay controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock

from lstp.errors import AuthorizationError, Diagnostic
from lstp.models import CAPABILITIES, PacketEnvelope, Permissions
from lstp.packet.validator import require_semantic_validity

_SIDE_EFFECTS = frozenset({"write", "execute", "commit"})


def _diag(code: str, message: str, path: str | None = None) -> Diagnostic:
    return Diagnostic(code=code, message=message, path=path)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_rfc3339(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise AuthorizationError((
            _diag(
                "invalid_expiry",
                "permissions.expires_at must be an RFC 3339 date-time",
                "$.permissions.expires_at",
            ),
        )) from exc
    if parsed.tzinfo is None:
        raise AuthorizationError((
            _diag(
                "invalid_expiry",
                "permissions.expires_at must include a timezone offset",
                "$.permissions.expires_at",
            ),
        ))
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class Authority:
    """Authority granted by a trusted host boundary."""

    capabilities: frozenset[str]
    resources: frozenset[str]

    def __post_init__(self) -> None:
        unknown = self.capabilities - CAPABILITIES
        if unknown:
            raise ValueError(f"unknown authority capabilities: {sorted(unknown)!r}")
        if any(not item for item in self.resources):
            raise ValueError("authority resource ids must be non-empty")


@dataclass(frozen=True, slots=True)
class HostPolicy:
    """Host policy that can only narrow principal/runtime authority."""

    capabilities: frozenset[str] = field(default_factory=lambda: CAPABILITIES)
    resources: frozenset[str] = field(default_factory=frozenset)
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


class ReplayGuard:
    """Thread-safe in-process reservation store for idempotent side effects.

    Production hosts SHOULD use durable shared storage. Each operation id is
    bound to an action digest. Any repeated id is denied; a differing digest is
    reported as an operation-identity mutation rather than a normal replay.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._reserved: dict[str, str] = {}

    def reserve(self, operation_id: str, action_digest: str) -> str | None:
        if not operation_id or not action_digest:
            raise ValueError("operation_id and action_digest must be non-empty")
        with self._lock:
            existing = self._reserved.get(operation_id)
            if existing is not None:
                return existing
            self._reserved[operation_id] = action_digest
            return None

    def release(self, operation_id: str) -> None:
        with self._lock:
            self._reserved.pop(operation_id, None)

    def digest_for(self, operation_id: str) -> str | None:
        with self._lock:
            return self._reserved.get(operation_id)


def _requested_authority(permissions: Permissions) -> Authority:
    capabilities = frozenset(permissions.capabilities) - frozenset(permissions.forbid)
    resources = frozenset(resource.id for resource in permissions.resources)
    return Authority(capabilities, resources)


def effective_authority(
    packet: PacketEnvelope,
    *,
    principal: Authority,
    policy: HostPolicy,
    runtime: Authority,
) -> Authority:
    """Compute requested ∩ principal ∩ policy ∩ runtime authority.

    Every resource set is authoritative. An empty set therefore means no
    resource authority; it is never interpreted as a wildcard.
    """
    require_semantic_validity(packet)
    requested = _requested_authority(packet.octad.permissions)
    capabilities = (
        requested.capabilities
        & principal.capabilities
        & policy.capabilities
        & runtime.capabilities
    )
    resources = (
        requested.resources
        & principal.resources
        & policy.resources
        & runtime.resources
    )
    return Authority(capabilities, resources)


def validate_delegation(
    packet: PacketEnvelope,
    *,
    parent: Authority,
) -> tuple[Diagnostic, ...]:
    """Verify that a delegated packet does not widen authenticated parent authority."""
    delegation = packet.octad.permissions.delegation
    if delegation is None:
        return ()
    requested = _requested_authority(packet.octad.permissions)
    diagnostics: list[Diagnostic] = []
    extra_capabilities = requested.capabilities - parent.capabilities
    if extra_capabilities:
        diagnostics.append(_diag(
            "delegation_capability_widening",
            f"delegation requests capabilities outside parent authority: {sorted(extra_capabilities)!r}",
            "$.permissions.capabilities",
        ))
    extra_resources = requested.resources - parent.resources
    if extra_resources:
        diagnostics.append(_diag(
            "delegation_resource_widening",
            "delegation requests resources outside parent authority",
            "$.permissions.resources",
        ))
    return tuple(diagnostics)


def authorize_operation(
    packet: PacketEnvelope,
    operation: OperationRequest,
    *,
    principal: Authority,
    policy: HostPolicy,
    runtime: Authority,
    parent_authority: Authority | None = None,
    replay_guard: ReplayGuard | None = None,
    now: datetime | None = None,
) -> AuthorizationDecision:
    """Authorize one concrete operation without performing it.

    Callers MUST invoke this immediately before a side effect. If a replay guard
    is supplied, side-effect operation identity is atomically reserved only after
    all other authorization checks succeed.
    """
    require_semantic_validity(packet)
    permissions = packet.octad.permissions
    diagnostics: list[Diagnostic] = []

    if permissions.expires_at is not None:
        expiry = _parse_rfc3339(permissions.expires_at)
        current = (now or _utc_now()).astimezone(timezone.utc)
        if current >= expiry:
            diagnostics.append(_diag(
                "authorization_expired",
                "permission request has expired",
                "$.permissions.expires_at",
            ))

    if permissions.delegation is not None:
        if parent_authority is None:
            diagnostics.append(_diag(
                "delegation_parent_authority_missing",
                "delegated packet requires authenticated parent authority",
                "$.permissions.delegation",
            ))
        else:
            diagnostics.extend(validate_delegation(packet, parent=parent_authority))

    effective = effective_authority(packet, principal=principal, policy=policy, runtime=runtime)
    if operation.capability not in effective.capabilities:
        diagnostics.append(_diag(
            "capability_denied",
            f"operation capability {operation.capability!r} is not effectively authorized",
            "$.permissions.capabilities",
        ))
    if operation.resource_id not in effective.resources:
        diagnostics.append(_diag(
            "resource_denied",
            "operation resource is outside effective scope",
            "$.permissions.resources",
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
            if existing_digest != operation.action_digest:
                replay = _diag(
                    "operation_changed",
                    "operation id was already bound to different action content",
                )
            else:
                replay = _diag(
                    "replay_detected",
                    "operation id has already been reserved or executed",
                )
            return AuthorizationDecision(
                False,
                (replay,),
                effective.capabilities,
                effective.resources,
            )

    return AuthorizationDecision(True, (), effective.capabilities, effective.resources)


def require_authorized_operation(
    packet: PacketEnvelope,
    operation: OperationRequest,
    *,
    principal: Authority,
    policy: HostPolicy,
    runtime: Authority,
    parent_authority: Authority | None = None,
    replay_guard: ReplayGuard | None = None,
    now: datetime | None = None,
) -> AuthorizationDecision:
    decision = authorize_operation(
        packet,
        operation,
        principal=principal,
        policy=policy,
        runtime=runtime,
        parent_authority=parent_authority,
        replay_guard=replay_guard,
        now=now,
    )
    decision.raise_for_denial()
    return decision
