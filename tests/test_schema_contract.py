"""Regression tests for the authoritative schema-drift gate."""

import json
from pathlib import Path

from tools.check_schema_contract import contract_failures

ROOT = Path(__file__).resolve().parents[1]


def _minimal_conforming_schema() -> dict[str, object]:
    return {
        "required": [
            "pragmatics",
            "atoms",
            "relations",
            "context",
            "confidence",
            "permissions",
            "evidence",
            "output",
        ],
        "$defs": {
            "pragmatics": {
                "required": ["type"],
                "properties": {
                    "type": {"type": "string"},
                    "urgency": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
            "atoms": {"type": "array"},
            "atom": {
                "properties": {
                    "id": {"pattern": "^a(?:0|[1-9][0-9]*)$"},
                    "kind": {
                        "enum": [
                            "entity",
                            "concept",
                            "value",
                            "event",
                            "time",
                            "location",
                            "resource",
                            "proposition",
                            "unknown",
                        ]
                    },
                }
            },
            "relation": {
                "required": ["type", "arguments"],
                "properties": {"type": {}, "arguments": {}},
            },
            "context": {"required": ["thread_id"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "permissions": {
                "properties": {
                    "mode": {"enum": ["RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT"]},
                    "forbid": {},
                    "require_confirm": {},
                    "require_review": {},
                    "log": {},
                }
            },
            "output": {
                "properties": {
                    "format": {
                        "enum": ["NL", "LATTICE", "JSON", "YAML", "TABLE", "CODE", "FILE", "NONE"]
                    }
                }
            },
        },
    }


def test_gate_accepts_only_the_checked_authoritative_invariants() -> None:
    assert contract_failures(_minimal_conforming_schema()) == []


def test_current_schema_is_explicitly_blocked_from_canonical_readiness() -> None:
    schema = json.loads((ROOT / "spec" / "octad_schema.json").read_text(encoding="utf-8"))
    failures = contract_failures(schema)
    codes = {failure.split(":", 1)[0] for failure in failures}

    assert "PRAGMATICS_TYPE" in codes
    assert "PRAGMATICS_URGENCY" in codes
    assert "ATOMS_SHAPE" in codes
    assert "ATOM_ID" in codes
    assert "ATOM_KIND" in codes
    assert "RELATION_SHAPE" in codes
    assert "RELATION_SPO" in codes
    assert "CONTEXT_THREAD" in codes
    assert "CONFIDENCE_SHAPE" in codes
    assert "PERMISSION_MODES" in codes
    assert "PERMISSION_FIELD" in codes
    assert "OUTPUT_FORMATS" in codes


def test_permission_aliases_do_not_pass_as_canonical_modes() -> None:
    schema = _minimal_conforming_schema()
    permissions = schema["$defs"]["permissions"]  # type: ignore[index]
    permissions["properties"]["mode"]["enum"] = [  # type: ignore[index]
        "readonly",
        "preview",
        "sandbox",
        "confirm",
        "commit",
        "auto",
    ]
    assert any(
        failure.startswith("PERMISSION_MODES:") for failure in contract_failures(schema)
    )


def test_relation_spo_compatibility_fields_fail_closed() -> None:
    schema = _minimal_conforming_schema()
    relation = schema["$defs"]["relation"]  # type: ignore[index]
    relation["properties"]["subject"] = {}  # type: ignore[index]
    assert any(failure.startswith("RELATION_SPO:") for failure in contract_failures(schema))
