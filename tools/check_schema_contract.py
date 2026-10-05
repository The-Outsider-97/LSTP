"""Check the reconciled LSTP v0.1 canonical JSON schema.

This is a structural drift gate, not semantic-conformance proof. Cross-field
reference integrity, permission authorization, canonical bytes, and carrier
round trips require separate validators/tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "spec" / "octad_schema.json"

OCTAD_FIELDS = {
    "pragmatics",
    "atoms",
    "relations",
    "context",
    "confidence",
    "permissions",
    "evidence",
    "output",
}
ATOM_KINDS = {
    "entity", "concept", "value", "event", "time", "location",
    "resource", "proposition", "unknown",
}
CAPABILITIES = {"read", "suggest", "prepare", "write", "execute", "commit"}
PROFILES = {"RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT"}
EVIDENCE_TYPES = {"user", "sensor", "model", "tool", "retrieved", "inferred"}
OUTPUT_FORMATS = {"NL", "LATTICE", "JSON", "YAML", "TABLE", "CODE", "FILE", "NONE"}
ACTS = {"assert", "request", "question", "inform", "correct", "acknowledge", "refuse", "respond"}


def _defs(schema: dict[str, Any]) -> dict[str, Any]:
    value = schema.get("$defs")
    return value if isinstance(value, dict) else {}


def _properties(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    value = value.get("properties")
    return value if isinstance(value, dict) else {}


def _required(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()
    value = value.get("required")
    return {item for item in value if isinstance(item, str)} if isinstance(value, list) else set()


def _enum(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()
    enum = value.get("enum")
    return {item for item in enum if isinstance(item, str)} if isinstance(enum, list) else set()


def contract_failures(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = _defs(schema)

    missing = OCTAD_FIELDS - _required(schema)
    if missing:
        failures.append(f"OCTAD_REQUIRED: missing {sorted(missing)!r}")

    if schema.get("additionalProperties") is not False:
        failures.append("TOP_LEVEL_CLOSED: canonical packet must reject unknown top-level fields")

    pragmatics = defs.get("pragmatics", {})
    pprops = _properties(pragmatics)
    if "act" not in _required(pragmatics) or _enum(pprops.get("act")) != ACTS:
        failures.append("PRAGMATICS_ACT: canonical act field/vocabulary drift")

    confidence = defs.get("confidence", {})
    if not (
        isinstance(confidence, dict)
        and confidence.get("type") == "number"
        and confidence.get("minimum") == 0
        and confidence.get("maximum") == 1
    ):
        failures.append("CONFIDENCE: packet confidence must be numeric [0,1]")

    atom = defs.get("atom", {})
    aprops = _properties(atom)
    if not {"id", "kind"}.issubset(_required(atom)):
        failures.append("ATOM_REQUIRED: atom.id and atom.kind must be required")
    if _enum(aprops.get("kind")) != ATOM_KINDS:
        failures.append("ATOM_KIND: canonical atom-kind vocabulary drift")
    if not (isinstance(defs.get("atoms"), dict) and defs["atoms"].get("type") == "array"):
        failures.append("ATOMS_SHAPE: atoms must be an array")

    relation = defs.get("relation", {})
    rprops = _properties(relation)
    if not {"type", "arguments"}.issubset(_required(relation)):
        failures.append("RELATION_REQUIRED: relation.type and relation.arguments must be required")
    if {"subject", "predicate", "object"} & set(rprops):
        failures.append("RELATION_SPO: legacy SPO fields are not canonical")

    context = defs.get("context", {})
    if not {"thread_id", "references"}.issubset(_required(context)):
        failures.append("CONTEXT_REQUIRED: context.thread_id and references must be required")
    context_ref = defs.get("contextReference", {})
    if "packet_id" not in _required(context_ref):
        failures.append("CONTEXT_STABLE_REF: canonical context references require packet_id")

    permissions = defs.get("permissions", {})
    per_props = _properties(permissions)
    if not {"capabilities", "resources"}.issubset(_required(permissions)):
        failures.append("PERMISSION_REQUIRED: capabilities and resources must be required")
    capability_ref = defs.get("capability", {})
    if _enum(capability_ref) != CAPABILITIES:
        failures.append("PERMISSION_CAPABILITIES: capability vocabulary drift")
    if _enum(per_props.get("profile")) != PROFILES:
        failures.append("PERMISSION_PROFILES: profile vocabulary drift")
    for field in ("forbid", "require_confirmation", "require_review", "require_logging"):
        if field not in per_props:
            failures.append(f"PERMISSION_FIELD: missing {field!r}")
    if "mode" in per_props:
        failures.append("PERMISSION_MODE: legacy scalar mode must not be canonical")

    evidence_item = defs.get("evidenceItem", {})
    eprops = _properties(evidence_item)
    if not {"id", "source_type"}.issubset(_required(evidence_item)):
        failures.append("EVIDENCE_REQUIRED: evidence id/source_type must be required")
    if _enum(eprops.get("source_type")) != EVIDENCE_TYPES:
        failures.append("EVIDENCE_TYPES: provenance vocabulary drift")
    if not (isinstance(defs.get("evidence"), dict) and defs["evidence"].get("type") == "array"):
        failures.append("EVIDENCE_SHAPE: evidence must be an array")

    output = defs.get("output", {})
    oprops = _properties(output)
    if "format" not in _required(output) or _enum(oprops.get("format")) != OUTPUT_FORMATS:
        failures.append("OUTPUT_FORMAT: canonical output format drift")

    extensions = defs.get("extensions", {})
    if not isinstance(extensions, dict) or extensions.get("type") != "object":
        failures.append("EXTENSIONS_SHAPE: extensions must be namespaced objects")

    return failures


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    failures = contract_failures(schema)
    for failure in failures:
        print(failure)
    if failures:
        print(f"Schema contract drift: {len(failures)} blocking finding(s).")
        return 1
    print("Reconciled v0.1 schema contract checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
