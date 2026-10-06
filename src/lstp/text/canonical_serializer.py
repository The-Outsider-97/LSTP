"""Deterministic encoder for the governed canonical Lattice surface."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from decimal import Decimal

from lstp.errors import CompilationError, Diagnostic
from lstp.models import JSONValue, Octad
from lstp.packet.validator import validate_octad
from lstp.text.canonical import CanonicalLatticeDocument

_KIND_TO_WIRE = {
    "entity": "ENT",
    "concept": "CONCEPT",
    "value": "VALUE",
    "event": "EVENT",
    "time": "TIME",
    "location": "LOCATION",
    "resource": "RES",
    "proposition": "PROPOSITION",
    "unknown": "UNKNOWN",
}
_EVIDENCE_TO_WIRE = {
    "user": "USER",
    "sensor": "SENSOR",
    "model": "MODEL",
    "tool": "TOOL",
    "retrieved": "RETRIEVED",
    "inferred": "INFERRED",
}
_CORE_TYPE_TO_WIRE = {
    "assert": "ASSERT",
    "request": "REQUEST",
    "question": "QUESTION",
    "inform": "INFORM",
    "correct": "CORRECT",
    "acknowledge": "ACKNOWLEDGE",
    "refuse": "REFUSE",
    "respond": "RESPOND",
}
_CORE_SPEECH_TO_WIRE = {
    "command": "COMMAND",
    "question": "QUESTION",
    "statement": "STATEMENT",
}
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_QUALIFIED_IDENTIFIER_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*$"
)


def _error(message: str, path: str) -> CompilationError:
    return CompilationError(
        Diagnostic(
            "canonical_lattice_unrepresentable",
            message,
            path=path,
        )
    )


def _number_text(value: int | float | Decimal) -> str:
    if isinstance(value, bool):
        raise TypeError("boolean is not a canonical number")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical numbers must be finite")
        decimal = Decimal(str(value))
    else:
        decimal = Decimal(value)
    if not decimal.is_finite():
        raise ValueError("canonical numbers must be finite")
    if decimal == 0:
        return "0"
    text = format(decimal, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _json_text(value: JSONValue) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, (int, float, Decimal)):
        return _number_text(value)
    if isinstance(value, Mapping):
        items = [
            json.dumps(key, ensure_ascii=False, separators=(",", ":"))
            + ":"
            + _json_text(value[key])
            for key in sorted(value)
        ]
        return "{" + ",".join(items) + "}"
    if isinstance(value, Sequence):
        return "[" + ",".join(_json_text(item) for item in value) + "]"
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _string_list(values: tuple[str, ...]) -> str:
    return "[" + ",".join(_quoted(value) for value in values) + "]"


def _wire_core_identifier(
    value: str,
    mapping: Mapping[str, str],
    *,
    path: str,
) -> str:
    wire = mapping.get(value)
    if wire is not None:
        return wire
    if value.lower() in mapping:
        raise _error(
            "core identifier casing is not canonical in the typed Octad",
            path,
        )
    return value


def _require_identifier(
    value: str,
    *,
    path: str,
    qualified: bool = True,
) -> str:
    pattern = _QUALIFIED_IDENTIFIER_RE if qualified else _IDENTIFIER_RE
    if pattern.fullmatch(value) is None:
        raise _error("value cannot be represented as a canonical identifier", path)
    return value


def _no_extensions(value: Mapping[str, JSONValue], path: str) -> None:
    if value:
        raise _error(
            "canonical Lattice extension syntax is not governed in v0.1",
            path,
        )


def _pragmatics(octad: Octad) -> str:
    value = octad.pragmatics
    _no_extensions(value.extensions, "$.pragmatics.extensions")
    entries = [
        "TYPE="
        + _wire_core_identifier(
            value.type,
            _CORE_TYPE_TO_WIRE,
            path="$.pragmatics.type",
        )
    ]
    if value.speech_act is not None:
        entries.append(
            "SPEECH_ACT="
            + _wire_core_identifier(
                value.speech_act,
                _CORE_SPEECH_TO_WIRE,
                path="$.pragmatics.speech_act",
            )
        )
    if value.goal is not None:
        entries.append("GOAL=" + value.goal)
    if value.modifiers:
        entries.append("MOD=[" + ",".join(value.modifiers) + "]")
    if value.register is not None:
        entries.append("REGISTER=" + value.register)
    if value.urgency is not None:
        entries.append("URGENCY=" + _number_text(value.urgency))
    return "π=(" + ",".join(entries) + ")"


def _atoms(octad: Octad) -> str:
    encoded: list[str] = []
    for index, atom in enumerate(octad.atoms):
        _no_extensions(atom.extensions, f"$.atoms[{index}].extensions")
        kind = _KIND_TO_WIRE[atom.kind]
        inner = "" if atom.value is None else _json_text(atom.value)
        metadata: list[str] = []
        if atom.role is not None:
            metadata.append("ROLE=" + atom.role)
        if atom.datatype is not None:
            metadata.append("DATATYPE=" + _quoted(atom.datatype))
        if atom.language is not None:
            metadata.append("LANGUAGE=" + _quoted(atom.language))
        if atom.attributes:
            metadata.append("ATTRIBUTES=" + _json_text(atom.attributes))
        suffix = "{" + ",".join(metadata) + "}" if metadata else ""
        encoded.append(f"{atom.id}:{kind}({inner}){suffix}")
    return "A=(" + ",".join(encoded) + ")"


def _relations(octad: Octad) -> str:
    encoded: list[str] = []
    for index, relation in enumerate(octad.relations):
        _no_extensions(relation.extensions, f"$.relations[{index}].extensions")
        metadata: list[str] = []
        if relation.id is not None:
            metadata.append("ID=" + relation.id)
        if relation.confidence is not None:
            metadata.append("CONFIDENCE=" + _number_text(relation.confidence))
        if relation.attributes:
            metadata.append("ATTRIBUTES=" + _json_text(relation.attributes))
        suffix = "{" + ",".join(metadata) + "}" if metadata else ""
        encoded.append(
            relation.type
            + "("
            + ",".join(relation.arguments)
            + ")"
            + suffix
        )
    return "R=(" + ",".join(encoded) + ")"


def _context(octad: Octad) -> str:
    value = octad.context
    _no_extensions(value.extensions, "$.context.extensions")
    entries = ["THREAD=" + _quoted(value.thread_id)]
    if value.packet_id is not None:
        entries.append("PACKET=" + _quoted(value.packet_id))
    if value.parent_packet_id is not None:
        entries.append("PARENT=" + _quoted(value.parent_packet_id))
    if value.conversation_id is not None:
        entries.append("CONVERSATION=" + _quoted(value.conversation_id))
    if value.turn is not None:
        entries.append("TURN=" + str(value.turn))
    if value.time is not None:
        entries.append("TIME=" + _quoted(value.time))
    if value.timezone is not None:
        entries.append("TIMEZONE=" + _quoted(value.timezone))
    if value.window is not None:
        entries.append("WINDOW=" + _json_text(value.window))
    if value.location is not None:
        entries.append("LOCATION=" + _json_text(value.location))
    if value.bindings:
        entries.append("BINDINGS=" + _json_text(value.bindings))
    if value.references:
        packet_ids: list[str] = []
        for index, reference in enumerate(value.references):
            if (
                reference.depth is not None
                or reference.agent is not None
                or reference.label is not None
                or reference.extensions
            ):
                raise _error(
                    "canonical Lattice only governs stable packet IDs for context references",
                    f"$.context.references[{index}]",
                )
            packet_ids.append(reference.packet_id)
        entries.append("REFERENCES=" + _string_list(tuple(packet_ids)))
    if value.speaker is not None:
        entries.append("SPEAKER=" + value.speaker)
    if value.audience:
        audience = [
            _require_identifier(item, path=f"$.context.audience[{index}]")
            for index, item in enumerate(value.audience)
        ]
        entries.append("AUDIENCE=[" + ",".join(audience) + "]")
    return "C=(" + ",".join(entries) + ")"


def _permissions(octad: Octad) -> str:
    value = octad.permissions
    _no_extensions(value.extensions, "$.permissions.extensions")
    if value.authorization_ref is not None:
        raise _error(
            "authorization_ref has no frozen canonical Lattice syntax",
            "$.permissions.authorization_ref",
        )
    if value.expires_at is not None:
        raise _error(
            "expires_at has no frozen canonical Lattice syntax",
            "$.permissions.expires_at",
        )
    if value.delegation is not None:
        raise _error(
            "delegation has no frozen canonical Lattice syntax",
            "$.permissions.delegation",
        )
    entries: list[str] = []
    if value.mode is not None:
        entries.append("MODE=" + value.mode)
    if value.scope:
        entries.append("SCOPE=" + _string_list(value.scope))
    if value.forbid:
        entries.append("FORBID=" + _string_list(value.forbid))
    if value.limits:
        entries.append("LIMITS=" + _json_text(value.limits))
    if value.require_confirmation:
        entries.append("REQUIRE_CONFIRM=true")
    if value.require_review:
        entries.append("REQUIRE_REVIEW=true")
    if value.require_logging:
        entries.append("LOG=true")
    return "Π=(" + ",".join(entries) + ")"


def _evidence(octad: Octad) -> str:
    encoded: list[str] = []
    for index, item in enumerate(octad.evidence):
        if item.id != f"e{index}":
            raise _error(
                "canonical Lattice evidence constructors require deterministic eN ordering",
                f"$.evidence[{index}].id",
            )
        _no_extensions(item.extensions, f"$.evidence[{index}].extensions")
        if (
            item.input_hash is not None
            or item.span is not None
            or item.supports
            or item.description is not None
            or item.confidence is not None
        ):
            raise _error(
                "rich evidence metadata has no frozen canonical Lattice syntax",
                f"$.evidence[{index}]",
            )
        source = _EVIDENCE_TO_WIRE[item.source_type]
        source_ref = "" if item.source_ref is None else _quoted(item.source_ref)
        encoded.append(f"{source}({source_ref})")
    return "E=(" + ",".join(encoded) + ")"


def _output(octad: Octad) -> str:
    value = octad.output
    _no_extensions(value.extensions, "$.output.extensions")
    entries = ["FORMAT=" + value.format]
    if value.schema is not None:
        entries.append("SCHEMA=" + _quoted(value.schema))
    if value.channel is not None:
        entries.append("CHANNEL=" + value.channel)
    if value.target is not None:
        entries.append("TARGET=" + _quoted(value.target))
    if value.language is not None:
        entries.append("LANG=" + _quoted(value.language))
    if value.max_bytes is not None:
        entries.append("MAX_BYTES=" + str(value.max_bytes))
    if value.requirements:
        entries.append("REQUIREMENTS=" + _string_list(value.requirements))
    return "Ω=(" + ",".join(entries) + ")"


def canonical_lattice_dumps(
    octad: Octad,
    *,
    label: str | None = None,
) -> str:
    """Encode one semantically valid Octad into deterministic framed Lattice."""

    validate_octad(octad).raise_for_errors()
    core = "|".join(
        (
            _pragmatics(octad),
            _atoms(octad),
            _relations(octad),
            _context(octad),
            "κ=" + _number_text(octad.confidence),
            _permissions(octad),
            _evidence(octad),
            _output(octad),
        )
    )
    framed = "[" + core + "]"
    if label is None:
        return framed
    return (
        _require_identifier(label, path="$.carrier.label", qualified=False)
        + ":"
        + framed
    )


def canonical_lattice_document_dumps(
    document: CanonicalLatticeDocument,
) -> str:
    """Encode a parsed canonical document to one deterministic carrier form."""

    if not document.packets:
        raise _error("canonical document must contain at least one packet", "$")
    if len(document.packets) == 1:
        packet = document.packets[0]
        return canonical_lattice_dumps(packet.octad, label=packet.label)
    if any(packet.label is None for packet in document.packets):
        raise _error(
            "multi-packet canonical streams require labels for every packet",
            "$",
        )
    return "\n".join(
        canonical_lattice_dumps(packet.octad, label=packet.label)
        for packet in document.packets
    )


__all__ = [
    "canonical_lattice_document_dumps",
    "canonical_lattice_dumps",
]
