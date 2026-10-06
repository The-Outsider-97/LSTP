"""Semantic validation for the canonical LSTP v0.1 model."""

from __future__ import annotations

from dataclasses import dataclass

from lstp.errors import Diagnostic, SemanticValidationError
from lstp.formats import is_well_formed_bcp47, parse_rfc3339
from lstp.models import Atom, Octad, PacketEnvelope, SPECIAL_ARGUMENTS

CORE_RELATIONS = frozenset({
    "is", "has", "part_of", "located_at", "causes", "requires", "references",
    "produces", "requests", "answers", "outcome.success", "outcome.failure",
    "outcome.partial", "outcome.refused", "outcome.unsupported",
    "outcome.needs_confirmation", "outcome.needs_context",
})

MODE_CAPABILITIES: dict[str, frozenset[str]] = {
    "RO": frozenset({"read"}),
    "SUGGEST": frozenset({"read", "suggest"}),
    "PREVIEW": frozenset({"read", "suggest", "prepare"}),
    "RW": frozenset({"read", "suggest", "prepare", "write"}),
    "EXEC": frozenset({"read", "suggest", "prepare", "write", "execute"}),
    "COMMIT": frozenset({"read", "suggest", "prepare", "write", "execute", "commit"}),
}
SIDE_EFFECT_MODES = frozenset({"RW", "EXEC", "COMMIT"})


@dataclass(frozen=True, slots=True)
class ValidationResult:
    diagnostics: tuple[Diagnostic, ...]

    @property
    def valid(self) -> bool:
        return not self.diagnostics

    def raise_for_errors(self) -> None:
        if self.diagnostics:
            raise SemanticValidationError(self.diagnostics)


def _diag(code: str, message: str, path: str) -> Diagnostic:
    return Diagnostic(code=code, message=message, path=path)


def _duplicates(values: tuple[str, ...], *, code: str, label: str, path: str) -> list[Diagnostic]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        if value in seen:
            duplicate.add(value)
        seen.add(value)
    return [_diag(code, f"duplicate {label} {value!r}", path) for value in sorted(duplicate)]


def _validate_relation_vocabulary(octad: Octad) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for index, relation in enumerate(octad.relations):
        if relation.type not in CORE_RELATIONS and "." not in relation.type:
            diagnostics.append(_diag(
                "unknown_relation",
                "non-core relation identifiers must be namespaced",
                f"$.relations[{index}].type",
            ))
    return diagnostics


def _validate_references(octad: Octad) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    atoms_by_id: dict[str, Atom] = {atom.id: atom for atom in octad.atoms}
    relation_ids = {relation.id for relation in octad.relations if relation.id is not None}
    for index, relation in enumerate(octad.relations):
        for arg_index, argument in enumerate(relation.arguments):
            if argument not in SPECIAL_ARGUMENTS and argument not in atoms_by_id:
                diagnostics.append(_diag(
                    "unresolved_atom",
                    f"relation argument references missing atom {argument!r}",
                    f"$.relations[{index}].arguments[{arg_index}]",
                ))
    for evidence_index, evidence in enumerate(octad.evidence):
        for support_index, support in enumerate(evidence.supports):
            path = f"$.evidence[{evidence_index}].supports[{support_index}]"
            if support.startswith("r"):
                if support not in relation_ids:
                    diagnostics.append(_diag("unresolved_evidence_support", f"evidence references missing relation {support!r}", path))
            else:
                atom = atoms_by_id.get(support)
                if atom is None:
                    diagnostics.append(_diag("unresolved_evidence_support", f"evidence references missing atom {support!r}", path))
                elif atom.kind != "proposition":
                    diagnostics.append(_diag("nonproposition_evidence_support", "evidence atom support must reference a proposition atom", path))
    return diagnostics


def _validate_formats(octad: Octad) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if octad.context.time is not None:
        try:
            parse_rfc3339(octad.context.time)
        except (TypeError, ValueError):
            diagnostics.append(_diag(
                "invalid_context_time",
                "context.time must be an RFC 3339 date-time",
                "$.context.time",
            ))
    if octad.permissions.expires_at is not None:
        try:
            parse_rfc3339(octad.permissions.expires_at)
        except (TypeError, ValueError):
            diagnostics.append(_diag(
                "invalid_permission_expiry",
                "permissions.expires_at must be an RFC 3339 date-time",
                "$.permissions.expires_at",
            ))
    for index, atom in enumerate(octad.atoms):
        if atom.language is not None and not is_well_formed_bcp47(atom.language):
            diagnostics.append(_diag(
                "invalid_atom_language",
                "atom language must be a well-formed BCP 47 language tag",
                f"$.atoms[{index}].language",
            ))
    if octad.output.language is not None and not is_well_formed_bcp47(octad.output.language):
        diagnostics.append(_diag(
            "invalid_output_language",
            "output language must be a well-formed BCP 47 language tag",
            "$.output.language",
        ))
    return diagnostics


def _validate_permissions(octad: Octad) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    permissions = octad.permissions

    diagnostics.extend(
        _duplicates(
            permissions.scope,
            code="duplicate_permission_scope",
            label="permission scope",
            path="$.permissions.scope",
        )
    )
    diagnostics.extend(
        _duplicates(
            permissions.forbid,
            code="duplicate_permission_forbid",
            label="permission forbid",
            path="$.permissions.forbid",
        )
    )

    for item in sorted(set(permissions.scope) & set(permissions.forbid)):
        diagnostics.append(
            _diag(
                "permission_scope_forbidden",
                f"scope item {item!r} is both allowed and forbidden; forbid wins",
                "$.permissions",
            )
        )

    if permissions.mode in SIDE_EFFECT_MODES and not permissions.scope:
        diagnostics.append(
            _diag(
                "missing_permission_scope",
                "side-effect-capable permission modes require explicit scope",
                "$.permissions.scope",
            )
        )

    if permissions.delegation is not None:
        delegation = permissions.delegation
        if (
            delegation.parent_packet is None
            and delegation.delegator is None
            and delegation.principal is None
        ):
            diagnostics.append(
                _diag(
                    "empty_delegation",
                    "delegation metadata must identify at least one delegation link",
                    "$.permissions.delegation",
                )
            )
    return diagnostics


def validate_octad(octad: Octad) -> ValidationResult:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_duplicates(tuple(atom.id for atom in octad.atoms), code="duplicate_atom_id", label="atom id", path="$.atoms"))
    diagnostics.extend(_duplicates(tuple(r.id for r in octad.relations if r.id is not None), code="duplicate_relation_id", label="relation id", path="$.relations"))
    diagnostics.extend(_duplicates(tuple(e.id for e in octad.evidence), code="duplicate_evidence_id", label="evidence id", path="$.evidence"))
    diagnostics.extend(_validate_relation_vocabulary(octad))
    diagnostics.extend(_validate_references(octad))
    diagnostics.extend(_validate_formats(octad))
    diagnostics.extend(_validate_permissions(octad))
    return ValidationResult(tuple(diagnostics))


def validate_packet(packet: PacketEnvelope) -> ValidationResult:
    diagnostics = list(validate_octad(packet.octad).diagnostics)
    if packet.octad.context.packet_id is not None and packet.octad.context.packet_id != packet.packet_id:
        diagnostics.append(_diag(
            "packet_context_identity_mismatch",
            "context.packet_id must match envelope id when it identifies the current packet",
            "$.context.packet_id",
        ))
    delegation = packet.octad.permissions.delegation
    if delegation is not None and delegation.parent_packet == packet.packet_id:
        diagnostics.append(_diag(
            "self_delegation",
            "delegation parent_packet must not equal the current packet id",
            "$.permissions.delegation.parent_packet",
        ))
    return ValidationResult(tuple(diagnostics))


def require_semantic_validity(packet: PacketEnvelope) -> PacketEnvelope:
    validate_packet(packet).raise_for_errors()
    return packet
