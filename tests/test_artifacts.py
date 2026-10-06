import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def test_schema_is_valid_json_and_meta_schema() -> None:
    schema = json.loads((ROOT / "spec/octad_schema.json").read_text())
    Draft202012Validator.check_schema(schema)


def test_contract_is_reconciled_but_release_gates_remain_open() -> None:
    state = json.loads((ROOT / "docs/program/readiness.json").read_text())
    assert state["contract_reconciled"] is True
    assert state["training_ready"] is False
    ids = {item["id"] for item in state["blockers"]}
    assert ids == {
        "VERIFY-001",
        "TEST-001",
        "INTEROP-001",
        "SLAI-001",
        "DOC-001",
        "REL-001",
    }


def test_identifier_patterns_reject_trailing_controls() -> None:
    schema = json.loads((ROOT / "spec/octad_schema.json").read_text())
    for definition, valid in [
        ("identifier", "sales"),
        ("qualifiedIdentifier", "sales.region"),
        ("atomId", "a0"),
        ("relationId", "r0"),
        ("evidenceId", "e0"),
    ]:
        validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"})
        assert validator.is_valid(valid)
        for suffix in ["\n", "\r", "\t", "\0"]:
            assert not validator.is_valid(valid + suffix)


def test_extension_namespace_rejects_trailing_newline() -> None:
    schema = json.loads((ROOT / "spec/octad_schema.json").read_text())
    validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/extensions"})
    assert validator.is_valid({"slai": {}})
    assert not validator.is_valid({"slai\n": {}})
