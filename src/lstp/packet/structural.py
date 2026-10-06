"""Strict JSON-type checks used before canonical model construction."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from lstp.errors import CanonicalizationError, Diagnostic

_JSON_NUMBER = (int, float, Decimal)


def _error(code: str, message: str, path: str) -> CanonicalizationError:
    return CanonicalizationError(Diagnostic(code, message, path=path))


def _object(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _error("expected_object", "expected JSON object", path)
    return value


def _array(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise _error("expected_array", "expected JSON array", path)
    return value


def _string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise _error("expected_string", "expected JSON string", path)
    return value


def _bool(value: object, path: str) -> bool:
    if not isinstance(value, bool):
        raise _error("expected_boolean", "expected JSON boolean", path)
    return value


def _integer(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise _error("expected_integer", "expected JSON integer", path)
    return value


def _number(value: object, path: str) -> object:
    if isinstance(value, bool) or not isinstance(value, _JSON_NUMBER):
        raise _error("expected_number", "expected JSON number", path)
    return value


def _string_array(value: object, path: str) -> None:
    for index, item in enumerate(_array(value, path)):
        _string(item, f"{path}[{index}]")


def _optional_string(data: Mapping[str, object], key: str, path: str) -> None:
    if key in data:
        _string(data[key], f"{path}.{key}")


def _optional_bool(data: Mapping[str, object], key: str, path: str) -> None:
    if key in data:
        _bool(data[key], f"{path}.{key}")


def validate_canonical_json_types(root: Mapping[str, object]) -> None:
    """Reject schema-relevant JSON type mismatches before typed construction."""
    _string(root["id"], "$.id")
    _string(root["version"], "$.version")
    _number(root["confidence"], "$.confidence")
    _object(root["carrier"], "$.carrier")
    _object(root["audit"], "$.audit")

    pragmatics = _object(root["pragmatics"], "$.pragmatics")
    _string(pragmatics["type"], "$.pragmatics.type")
    _optional_string(pragmatics, "speech_act", "$.pragmatics")
    _optional_string(pragmatics, "goal", "$.pragmatics")
    _optional_string(pragmatics, "register", "$.pragmatics")
    if "urgency" in pragmatics:
        _number(pragmatics["urgency"], "$.pragmatics.urgency")
    if "modifiers" in pragmatics:
        _string_array(pragmatics["modifiers"], "$.pragmatics.modifiers")
    if "extensions" in pragmatics:
        _object(pragmatics["extensions"], "$.pragmatics.extensions")

    for index, raw in enumerate(_array(root["atoms"], "$.atoms")):
        path = f"$.atoms[{index}]"
        atom = _object(raw, path)
        _string(atom["id"], f"{path}.id")
        _string(atom["kind"], f"{path}.kind")
        for key in ("role", "datatype", "language"):
            _optional_string(atom, key, path)
        if "attributes" in atom:
            _object(atom["attributes"], f"{path}.attributes")
        if "extensions" in atom:
            _object(atom["extensions"], f"{path}.extensions")

    for index, raw in enumerate(_array(root["relations"], "$.relations")):
        path = f"$.relations[{index}]"
        relation = _object(raw, path)
        _string(relation["type"], f"{path}.type")
        _string_array(relation["arguments"], f"{path}.arguments")
        _optional_string(relation, "id", path)
        if "confidence" in relation:
            _number(relation["confidence"], f"{path}.confidence")
        if "attributes" in relation:
            _object(relation["attributes"], f"{path}.attributes")
        if "extensions" in relation:
            _object(relation["extensions"], f"{path}.extensions")

    context = _object(root["context"], "$.context")
    _string(context["thread_id"], "$.context.thread_id")
    for key in (
        "packet_id",
        "parent_packet_id",
        "conversation_id",
        "speaker",
        "time",
        "timezone",
    ):
        _optional_string(context, key, "$.context")
    if "turn" in context:
        _integer(context["turn"], "$.context.turn")
    if "audience" in context:
        _string_array(context["audience"], "$.context.audience")
    if "bindings" in context:
        _object(context["bindings"], "$.context.bindings")
    if "extensions" in context:
        _object(context["extensions"], "$.context.extensions")
    for index, raw in enumerate(_array(context["references"], "$.context.references")):
        path = f"$.context.references[{index}]"
        reference = _object(raw, path)
        _string(reference["packet_id"], f"{path}.packet_id")
        if "depth" in reference:
            _integer(reference["depth"], f"{path}.depth")
        for key in ("agent", "label"):
            _optional_string(reference, key, path)
        if "extensions" in reference:
            _object(reference["extensions"], f"{path}.extensions")

    permissions = _object(root["permissions"], "$.permissions")
    _optional_string(permissions, "mode", "$.permissions")
    if "scope" in permissions:
        _string_array(permissions["scope"], "$.permissions.scope")
    if "forbid" in permissions:
        _string_array(permissions["forbid"], "$.permissions.forbid")
    for key in ("require_confirmation", "require_review", "require_logging"):
        _optional_bool(permissions, key, "$.permissions")
    if "limits" in permissions:
        _object(permissions["limits"], "$.permissions.limits")
    if "extensions" in permissions:
        _object(permissions["extensions"], "$.permissions.extensions")
    for index, raw in enumerate(_array(root["evidence"], "$.evidence")):
        path = f"$.evidence[{index}]"
        evidence = _object(raw, path)
        _string(evidence["id"], f"{path}.id")
        _string(evidence["source_type"], f"{path}.source_type")
        for key in ("source_ref", "input_hash", "description"):
            _optional_string(evidence, key, path)
        if "supports" in evidence:
            _string_array(evidence["supports"], f"{path}.supports")
        if "confidence" in evidence:
            _number(evidence["confidence"], f"{path}.confidence")
        if "extensions" in evidence:
            _object(evidence["extensions"], f"{path}.extensions")

    output = _object(root["output"], "$.output")
    _string(output["format"], "$.output.format")
    for key in ("schema", "channel", "target", "language"):
        _optional_string(output, key, "$.output")
    if "max_bytes" in output:
        _integer(output["max_bytes"], "$.output.max_bytes")
    if "requirements" in output:
        _string_array(output["requirements"], "$.output.requirements")
    if "extensions" in output:
        _object(output["extensions"], "$.output.extensions")

    if "extensions" in root:
        _object(root["extensions"], "$.extensions")
