"""Regression tests for the reconciled LSTP v0.1 schema contract."""

import json
from pathlib import Path

from tools.check_schema_contract import contract_failures

ROOT = Path(__file__).resolve().parents[1]


def _schema() -> dict[str, object]:
    return json.loads((ROOT / "spec" / "octad_schema.json").read_text(encoding="utf-8"))


def test_current_schema_matches_reconciled_contract() -> None:
    assert contract_failures(_schema()) == []


def test_legacy_permission_mode_is_rejected_by_drift_gate() -> None:
    schema = _schema()
    permissions = schema["$defs"]["permissions"]  # type: ignore[index]
    permissions["properties"]["mode"] = {"enum": ["readonly", "commit"]}  # type: ignore[index]
    failures = contract_failures(schema)
    assert any(failure.startswith("PERMISSION_MODE:") for failure in failures)


def test_permission_capability_vocabulary_is_closed() -> None:
    schema = _schema()
    schema["$defs"]["capability"]["enum"].append("auto")  # type: ignore[index]
    failures = contract_failures(schema)
    assert any(failure.startswith("PERMISSION_CAPABILITIES:") for failure in failures)


def test_relation_spo_fields_are_not_canonical() -> None:
    schema = _schema()
    relation = schema["$defs"]["relation"]  # type: ignore[index]
    relation["properties"]["subject"] = {}  # type: ignore[index]
    failures = contract_failures(schema)
    assert any(failure.startswith("RELATION_SPO:") for failure in failures)


def test_context_reference_requires_stable_packet_id() -> None:
    schema = _schema()
    context_ref = schema["$defs"]["contextReference"]  # type: ignore[index]
    context_ref["required"] = []
    failures = contract_failures(schema)
    assert any(failure.startswith("CONTEXT_STABLE_REF:") for failure in failures)


def test_evidence_is_canonical_provenance_array() -> None:
    schema = _schema()
    schema["$defs"]["evidence"]["type"] = "object"  # type: ignore[index]
    failures = contract_failures(schema)
    assert any(failure.startswith("EVIDENCE_SHAPE:") for failure in failures)
