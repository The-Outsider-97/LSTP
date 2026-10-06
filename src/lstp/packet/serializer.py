"""Canonical JSON serialization/deserialization for LSTP v0.1.

The byte profile is deliberately narrower than generic JSON:
- UTF-8 without BOM;
- NFC strings only;
- bidirectional formatting controls rejected;
- object members sorted by UTF-16 code units;
- no insignificant whitespace;
- finite decimal numbers only, emitted without exponent notation;
- negative zero canonicalizes to zero.

This profile provides deterministic LSTP bytes. It is RFC 8785-inspired but uses
an explicit decimal-number profile rather than ECMAScript binary64 formatting.
"""

from __future__ import annotations

import json
import math
import unicodedata
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from lstp.errors import CanonicalizationError, Diagnostic
from lstp.json_input import InputLimits, loads_json
from lstp.models import (
    Atom,
    Context,
    ContextReference,
    Delegation,
    EvidenceItem,
    JSONValue,
    Output,
    PacketEnvelope,
    Permissions,
    Pragmatics,
    Relation,
)
from lstp.packet.validator import require_semantic_validity

_BIDI_CONTROLS = {
    "\u061c",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
}
_MAX_CANONICAL_NUMBER_CHARS = 1024


def _error(code: str, message: str, path: str = "$") -> CanonicalizationError:
    return CanonicalizationError(Diagnostic(code, message, path=path))


def _check_string(value: str, path: str) -> str:
    if unicodedata.normalize("NFC", value) != value:
        raise _error("unicode_not_nfc", "canonical strings must already be NFC", path)
    if any(char in _BIDI_CONTROLS for char in value):
        raise _error(
            "unicode_bidi_control",
            "bidirectional formatting controls are not canonical",
            path,
        )
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise _error("unicode_surrogate", "unpaired surrogate is not canonical", path)
    return value


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be")


def _decimal_text(value: int | float | Decimal, path: str) -> str:
    if isinstance(value, bool):
        raise _error("invalid_number", "boolean is not a JSON number", path)
    if isinstance(value, int):
        text = str(value)
    else:
        if isinstance(value, float):
            if not math.isfinite(value):
                raise _error(
                    "non_finite_number", "canonical numbers must be finite", path
                )
            decimal_value = Decimal(str(value))
        else:
            if not value.is_finite():
                raise _error(
                    "non_finite_number", "canonical numbers must be finite", path
                )
            decimal_value = value
        if decimal_value == 0:
            return "0"
        sign = "-" if decimal_value.is_signed() else ""
        normalized = decimal_value.copy_abs().normalize()
        digits_tuple = normalized.as_tuple().digits
        exponent = normalized.as_tuple().exponent
        digits = "".join(str(digit) for digit in digits_tuple) or "0"
        point = len(digits) + exponent
        if point <= 0:
            body = "0." + ("0" * (-point)) + digits
        elif point >= len(digits):
            body = digits + ("0" * (point - len(digits)))
        else:
            body = digits[:point] + "." + digits[point:]
        text = sign + body
    if len(text) > _MAX_CANONICAL_NUMBER_CHARS:
        raise _error(
            "number_too_large", "canonical number representation exceeds limit", path
        )
    return text


def _encode(value: Any, path: str = "$") -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        _check_string(value, path)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return _decimal_text(value, path)
    if isinstance(value, Mapping):
        items: list[str] = []
        keys = list(value.keys())
        if not all(isinstance(key, str) for key in keys):
            raise _error(
                "non_string_key", "canonical JSON object keys must be strings", path
            )
        for key in sorted(keys, key=_utf16_sort_key):
            _check_string(key, f"{path}.<key>")
            items.append(
                json.dumps(key, ensure_ascii=False, separators=(",", ":"))
                + ":"
                + _encode(value[key], f"{path}.{key}")
            )
        return "{" + ",".join(items) + "}"
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return "[" + ",".join(
            _encode(item, f"{path}[{index}]") for index, item in enumerate(value)
        ) + "]"
    raise _error(
        "unsupported_value",
        f"unsupported canonical value type: {type(value).__name__}",
        path,
    )


def _put_optional(
    target: dict[str, object], key: str, value: object, default: object = None
) -> None:
    if value != default:
        target[key] = value


def _extensions(value: Mapping[str, JSONValue]) -> dict[str, object]:
    return {key: _thaw(item) for key, item in value.items()}


def _thaw(value: JSONValue) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _pragmatics(value: Pragmatics) -> dict[str, object]:
    data: dict[str, object] = {"type": value.type}
    _put_optional(data, "speech_act", value.speech_act)
    _put_optional(data, "goal", value.goal)
    if value.modifiers:
        data["modifiers"] = list(value.modifiers)
    _put_optional(data, "register", value.register)
    _put_optional(data, "urgency", value.urgency)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def _atom(value: Atom) -> dict[str, object]:
    data: dict[str, object] = {"id": value.id, "kind": value.kind}
    if value.value is not None:
        data["value"] = _thaw(value.value)
    _put_optional(data, "role", value.role)
    _put_optional(data, "datatype", value.datatype)
    _put_optional(data, "language", value.language)
    if value.attributes:
        data["attributes"] = _thaw(value.attributes)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def _relation(value: Relation) -> dict[str, object]:
    data: dict[str, object] = {
        "type": value.type,
        "arguments": list(value.arguments),
    }
    _put_optional(data, "id", value.id)
    _put_optional(data, "confidence", value.confidence)
    if value.attributes:
        data["attributes"] = _thaw(value.attributes)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def _context_reference(value: ContextReference) -> dict[str, object]:
    data: dict[str, object] = {"packet_id": value.packet_id}
    _put_optional(data, "depth", value.depth)
    _put_optional(data, "agent", value.agent)
    _put_optional(data, "label", value.label)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def _context(value: Context) -> dict[str, object]:
    data: dict[str, object] = {
        "thread_id": value.thread_id,
        "references": [_context_reference(item) for item in value.references],
    }
    _put_optional(data, "packet_id", value.packet_id)
    _put_optional(data, "parent_packet_id", value.parent_packet_id)
    _put_optional(data, "conversation_id", value.conversation_id)
    _put_optional(data, "turn", value.turn)
    _put_optional(data, "speaker", value.speaker)
    if value.audience:
        data["audience"] = list(value.audience)
    _put_optional(data, "time", value.time)
    _put_optional(data, "timezone", value.timezone)
    if value.window is not None:
        data["window"] = _thaw(value.window)
    if value.location is not None:
        data["location"] = _thaw(value.location)
    if value.bindings:
        data["bindings"] = _thaw(value.bindings)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def _delegation(value: Delegation) -> dict[str, object]:
    data: dict[str, object] = {}
    _put_optional(data, "parent_packet", value.parent_packet)
    _put_optional(data, "delegator", value.delegator)
    _put_optional(data, "principal", value.principal)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def _permissions(value: Permissions) -> dict[str, object]:
    data: dict[str, object] = {}
    _put_optional(data, "mode", value.mode)
    if value.scope:
        data["scope"] = list(value.scope)
    if value.forbid:
        data["forbid"] = list(value.forbid)
    if value.require_confirmation:
        data["require_confirmation"] = True
    if value.require_review:
        data["require_review"] = True
    if value.require_logging:
        data["require_logging"] = True
    if value.limits:
        data["limits"] = _thaw(value.limits)
    _put_optional(data, "authorization_ref", value.authorization_ref)
    _put_optional(data, "expires_at", value.expires_at)
    if value.delegation is not None:
        data["delegation"] = _delegation(value.delegation)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def _evidence(value: EvidenceItem) -> dict[str, object]:
    data: dict[str, object] = {"id": value.id, "source_type": value.source_type}
    _put_optional(data, "source_ref", value.source_ref)
    _put_optional(data, "input_hash", value.input_hash)
    if value.span is not None:
        data["span"] = _thaw(value.span)
    if value.supports:
        data["supports"] = list(value.supports)
    _put_optional(data, "description", value.description)
    _put_optional(data, "confidence", value.confidence)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def _output(value: Output) -> dict[str, object]:
    data: dict[str, object] = {"format": value.format}
    _put_optional(data, "schema", value.schema)
    _put_optional(data, "channel", value.channel)
    _put_optional(data, "target", value.target)
    _put_optional(data, "language", value.language)
    _put_optional(data, "max_bytes", value.max_bytes)
    if value.requirements:
        data["requirements"] = list(value.requirements)
    if value.extensions:
        data["extensions"] = _extensions(value.extensions)
    return data


def packet_to_mapping(packet: PacketEnvelope) -> dict[str, object]:
    """Return the canonical JSON object model for a typed packet."""
    return {
        "id": packet.packet_id,
        "version": packet.protocol_version,
        "pragmatics": _pragmatics(packet.octad.pragmatics),
        "atoms": [_atom(item) for item in packet.octad.atoms],
        "relations": [_relation(item) for item in packet.octad.relations],
        "context": _context(packet.octad.context),
        "confidence": packet.octad.confidence,
        "permissions": _permissions(packet.octad.permissions),
        "evidence": [_evidence(item) for item in packet.octad.evidence],
        "output": _output(packet.octad.output),
        "carrier": _thaw(packet.carrier),
        "audit": _thaw(packet.audit),
        **(
            {"extensions": _extensions(packet.extensions)}
            if packet.extensions
            else {}
        ),
    }


def canonical_dumps(packet: PacketEnvelope) -> bytes:
    """Serialize a semantically valid packet to deterministic canonical UTF-8 bytes."""
    require_semantic_validity(packet)
    return _encode(packet_to_mapping(packet)).encode("utf-8")


def _expect_object(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _error("expected_object", "expected JSON object", path)
    return value


def _strict_keys(
    value: object,
    *,
    path: str,
    allowed: set[str],
    required: set[str] | frozenset[str] = frozenset(),
) -> Mapping[str, Any]:
    data = _expect_object(value, path)
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise _error(
            "unknown_field", f"unknown canonical field {unknown[0]!r}", path
        )
    missing = sorted(set(required) - set(data))
    if missing:
        raise _error(
            "missing_field", f"missing required canonical field {missing[0]!r}", path
        )
    return data


def _check_extensions(value: object, path: str) -> None:
    data = _expect_object(value, path)
    for namespace, payload in data.items():
        if not isinstance(namespace, str) or not namespace:
            raise _error(
                "extension_namespace", "extension namespace must be non-empty", path
            )
        _expect_object(payload, f"{path}.{namespace}")


def _check_structure(data: object) -> Mapping[str, Any]:
    root = _strict_keys(
        data,
        path="$",
        allowed={
            "id",
            "version",
            "pragmatics",
            "atoms",
            "relations",
            "context",
            "confidence",
            "permissions",
            "evidence",
            "output",
            "carrier",
            "audit",
            "extensions",
        },
        required={
            "id",
            "version",
            "pragmatics",
            "atoms",
            "relations",
            "context",
            "confidence",
            "permissions",
            "evidence",
            "output",
            "carrier",
            "audit",
        },
    )
    _strict_keys(
        root["pragmatics"],
        path="$.pragmatics",
        allowed={"act", "goal", "modifiers", "register", "urgency", "extensions"},
        required={"act"},
    )
    atoms = root["atoms"]
    if not isinstance(atoms, list):
        raise _error("expected_array", "atoms must be an array", "$.atoms")
    for index, item in enumerate(atoms):
        _strict_keys(
            item,
            path=f"$.atoms[{index}]",
            allowed={
                "id",
                "kind",
                "value",
                "role",
                "datatype",
                "language",
                "attributes",
                "extensions",
            },
            required={"id", "kind"},
        )
    relations = root["relations"]
    if not isinstance(relations, list):
        raise _error("expected_array", "relations must be an array", "$.relations")
    for index, item in enumerate(relations):
        _strict_keys(
            item,
            path=f"$.relations[{index}]",
            allowed={"id", "type", "arguments", "confidence", "attributes", "extensions"},
            required={"type", "arguments"},
        )
    context = _strict_keys(
        root["context"],
        path="$.context",
        allowed={
            "thread_id",
            "packet_id",
            "parent_id",
            "conversation_id",
            "turn",
            "speaker",
            "audience",
            "time",
            "location",
            "bindings",
            "references",
            "extensions",
        },
        required={"thread_id", "references"},
    )
    refs = context["references"]
    if not isinstance(refs, list):
        raise _error(
            "expected_array",
            "context.references must be an array",
            "$.context.references",
        )
    for index, item in enumerate(refs):
        _strict_keys(
            item,
            path=f"$.context.references[{index}]",
            allowed={"packet_id", "depth", "agent", "label", "extensions"},
            required={"packet_id"},
        )
    permissions = _strict_keys(
        root["permissions"],
        path="$.permissions",
        allowed={
            "capabilities",
            "resources",
            "profile",
            "forbid",
            "require_confirmation",
            "require_review",
            "require_logging",
            "limits",
            "authorization_ref",
            "expires_at",
            "delegation",
            "extensions",
        },
        required={"capabilities", "resources"},
    )
    resources = permissions["resources"]
    if not isinstance(resources, list):
        raise _error(
            "expected_array",
            "permissions.resources must be an array",
            "$.permissions.resources",
        )
    for index, item in enumerate(resources):
        _strict_keys(
            item,
            path=f"$.permissions.resources[{index}]",
            allowed={"id", "kind", "atom", "extensions"},
            required={"id"},
        )
    if "delegation" in permissions:
        _strict_keys(
            permissions["delegation"],
            path="$.permissions.delegation",
            allowed={"parent_packet", "delegator", "principal", "extensions"},
        )
    evidence = root["evidence"]
    if not isinstance(evidence, list):
        raise _error("expected_array", "evidence must be an array", "$.evidence")
    for index, item in enumerate(evidence):
        _strict_keys(
            item,
            path=f"$.evidence[{index}]",
            allowed={
                "id",
                "source_type",
                "source_ref",
                "input_hash",
                "span",
                "supports",
                "description",
                "confidence",
                "extensions",
            },
            required={"id", "source_type"},
        )
    _strict_keys(
        root["output"],
        path="$.output",
        allowed={
            "format",
            "schema",
            "channel",
            "target",
            "language",
            "max_bytes",
            "requirements",
            "extensions",
        },
        required={"format"},
    )
    _expect_object(root["carrier"], "$.carrier")
    _expect_object(root["audit"], "$.audit")
    if "extensions" in root:
        _check_extensions(root["extensions"], "$.extensions")
    return root


def _check_canonical_strings(value: object, path: str = "$") -> None:
    if isinstance(value, str):
        _check_string(value, path)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str):
                _check_string(key, f"{path}.<key>")
            _check_canonical_strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_canonical_strings(item, f"{path}[{index}]")


def canonical_loads(
    data: bytes | str,
    *,
    limits: InputLimits | None = None,
    require_canonical_bytes: bool = False,
) -> PacketEnvelope:
    """Decode, structurally check, type, and semantically validate a canonical packet."""
    decoded = loads_json(data) if limits is None else loads_json(data, limits=limits)
    root = _check_structure(decoded)
    _check_canonical_strings(root)
    try:
        packet = PacketEnvelope.from_mapping(root)
    except (TypeError, ValueError) as exc:
        raise _error("canonical_shape", str(exc)) from None
    require_semantic_validity(packet)
    if require_canonical_bytes:
        supplied = data.encode("utf-8") if isinstance(data, str) else data
        expected = canonical_dumps(packet)
        if supplied != expected:
            raise _error(
                "non_canonical_bytes", "input is valid LSTP but not canonical byte form"
            )
    return packet
