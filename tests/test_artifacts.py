import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def test_schema_is_valid_json_and_meta_schema():
    schema = json.loads((ROOT / "spec/octad_schema.json").read_text())
    Draft202012Validator.check_schema(schema)


def test_schema_remains_explicitly_blocked_from_conformance():
    state = json.loads((ROOT / "docs/program/readiness.json").read_text())
    assert state["training_ready"] is False
    assert "SPEC-002" in [item["id"] for item in state["blockers"]]


@pytest.mark.parametrize(
    "definition, valid",
    [
        ("identifier", "sales"),
        ("qualifiedIdentifier", "sales.region"),
        ("atomRef", "@sales.region"),
    ],
)
def test_identifier_patterns_reject_trailing_controls(definition, valid):
    schema = json.loads((ROOT / "spec/octad_schema.json").read_text())
    validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"})
    assert validator.is_valid(valid)
    for suffix in ["\n", "\r", "\t", "\0"]:
        assert not validator.is_valid(valid + suffix)


def test_extension_namespace_rejects_trailing_newline():
    schema = json.loads((ROOT / "spec/octad_schema.json").read_text())
    validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/extensions"})
    assert validator.is_valid({"slai": {}})
    assert not validator.is_valid({"slai\n": {}})
