"""Check high-confidence Whitepaper invariants against the Octad JSON schema.

This is a drift/readiness gate, not a JSON Schema validator and not proof of
semantic conformance. It deliberately checks only requirements whose canonical
meaning is sufficiently explicit in the authoritative Whitepaper.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "spec" / "octad_schema.json"

CANONICAL_PERMISSION_MODES = {"RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT"}
CANONICAL_ATOM_KINDS = {
    "entity",
    "concept",
    "value",
    "event",
    "time",
    "location",
    "resource",
    "proposition",
    "unknown",
}
CANONICAL_OUTPUT_FORMATS = {
    "NL",
    "LATTICE",
    "JSON",
    "YAML",
    "TABLE",
    "CODE",
    "FILE",
    "NONE",
}


def _defs(schema: dict[str, Any]) -> dict[str, Any]:
    value = schema.get("$defs")
    return value if isinstance(value, dict) else {}


def _properties(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    properties = value.get("properties")
    return properties if isinstance(properties, dict) else {}


def _required(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()
    required = value.get("required")
    if not isinstance(required, list):
        return set()
    return {item for item in required if isinstance(item, str)}


def contract_failures(schema: dict[str, Any]) -> list[str]:
    """Return deterministic descriptions of authoritative contract drift."""
    failures: list[str] = []
    defs = _defs(schema)

    top_required = _required(schema)
    for field in (
        "pragmatics",
        "atoms",
        "relations",
        "context",
        "confidence",
        "permissions",
        "evidence",
        "output",
    ):
        if field not in top_required:
            failures.append(f"OCTAD_REQUIRED: top-level field {field!r} is not required")

    pragmatics = defs.get("pragmatics", {})
    pragmatics_props = _properties(pragmatics)
    if "type" not in _required(pragmatics):
        failures.append("PRAGMATICS_TYPE: pragmatics.type is not required")
    urgency = pragmatics_props.get("urgency", {})
    if not (
        isinstance(urgency, dict)
        and urgency.get("type") == "number"
        and urgency.get("minimum") == 0
        and urgency.get("maximum") == 1
    ):
        failures.append("PRAGMATICS_URGENCY: urgency is not a number constrained to [0,1]")

    atoms = defs.get("atoms", {})
    atom = defs.get("atom", {})
    atom_props = _properties(atom)
    if not (isinstance(atoms, dict) and atoms.get("type") == "array"):
        failures.append("ATOMS_SHAPE: atoms is not the canonical typed-atom array")
    atom_id = atom_props.get("id", {})
    if not (isinstance(atom_id, dict) and atom_id.get("pattern") == "^a(?:0|[1-9][0-9]*)$"):
        failures.append("ATOM_ID: canonical aN atom identifiers are not enforced")
    atom_kind = atom_props.get("kind", {})
    atom_kind_enum = atom_kind.get("enum") if isinstance(atom_kind, dict) else None
    if not isinstance(atom_kind_enum, list) or set(atom_kind_enum) != CANONICAL_ATOM_KINDS:
        failures.append("ATOM_KIND: canonical atom-kind vocabulary is not enforced")

    relation = defs.get("relation", {})
    relation_props = _properties(relation)
    if not {"type", "arguments"}.issubset(_required(relation)):
        failures.append("RELATION_SHAPE: relation.type and relation.arguments are not both required")
    if "subject" in relation_props or "predicate" in relation_props or "object" in relation_props:
        failures.append("RELATION_SPO: draft subject/predicate/object fields remain canonical")

    context = defs.get("context", {})
    if "thread_id" not in _required(context):
        failures.append("CONTEXT_THREAD: context.thread_id is not required")

    confidence = defs.get("confidence", {})
    if not (
        isinstance(confidence, dict)
        and confidence.get("type") == "number"
        and confidence.get("minimum") == 0
        and confidence.get("maximum") == 1
    ):
        failures.append("CONFIDENCE_SHAPE: confidence is not a number constrained to [0,1]")

    permissions = defs.get("permissions", {})
    permission_props = _properties(permissions)
    mode = permission_props.get("mode", {})
    modes = mode.get("enum") if isinstance(mode, dict) else None
    if not isinstance(modes, list) or set(modes) != CANONICAL_PERMISSION_MODES:
        failures.append("PERMISSION_MODES: permission mode vocabulary differs from the Whitepaper")
    for field in ("forbid", "require_confirm", "require_review", "log"):
        if field not in permission_props:
            failures.append(f"PERMISSION_FIELD: canonical permission field {field!r} is absent")

    output = defs.get("output", {})
    output_props = _properties(output)
    output_format = output_props.get("format", {})
    formats = output_format.get("enum") if isinstance(output_format, dict) else None
    if not isinstance(formats, list) or set(formats) != CANONICAL_OUTPUT_FORMATS:
        failures.append("OUTPUT_FORMATS: canonical output-format vocabulary is not enforced")

    return failures


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    failures = contract_failures(schema)
    for failure in failures:
        print(failure)
    if failures:
        print(f"Schema contract drift: {len(failures)} blocking finding(s).")
        return 1
    print("High-confidence schema contract checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
