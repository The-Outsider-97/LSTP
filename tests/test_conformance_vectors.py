from __future__ import annotations

import json
from pathlib import Path

import pytest

from lstp import (
    CanonicalizationError,
    LatticeSyntaxError,
    SemanticValidationError,
    canonical_dumps,
    canonical_loads,
    compile_canonical_lattice,
    parse_canonical_lattice,
)

ROOT = Path(__file__).resolve().parents[1] / "conformance" / "v0.1"
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

FAILURE_TYPES: dict[str, type[Exception]] = {
    "canonicalization": CanonicalizationError,
    "semantic": SemanticValidationError,
    "syntax": LatticeSyntaxError,
}


@pytest.mark.parametrize("relative_path", MANIFEST["positive_json"])
def test_positive_json_vectors_round_trip_byte_identically(
    relative_path: str,
) -> None:
    source = (ROOT / relative_path).read_bytes()
    packet = canonical_loads(source, require_canonical_bytes=True)
    assert canonical_dumps(packet) == source


@pytest.mark.parametrize("case", MANIFEST["negative_json"])
def test_negative_json_vectors_fail_closed(case: dict[str, str]) -> None:
    source = (ROOT / case["path"]).read_bytes()
    error_type = FAILURE_TYPES[case["failure"]]
    with pytest.raises(error_type):
        canonical_loads(source)


@pytest.mark.parametrize("relative_path", MANIFEST["positive_lattice"])
def test_positive_canonical_lattice_vectors_compile(
    relative_path: str,
) -> None:
    source = (ROOT / relative_path).read_text(encoding="utf-8")
    document = compile_canonical_lattice(source)
    assert document.packets


@pytest.mark.parametrize("case", MANIFEST["negative_lattice"])
def test_negative_canonical_lattice_vectors_fail_closed(
    case: dict[str, str],
) -> None:
    source = (ROOT / case["path"]).read_text(encoding="utf-8")
    error_type = FAILURE_TYPES[case["failure"]]
    with pytest.raises(error_type):
        parse_canonical_lattice(source)


@pytest.mark.parametrize("field", MANIFEST["noncanonical_permission_fields"])
def test_noncanonical_permission_channels_are_rejected(field: str) -> None:
    packet = json.loads((ROOT / "positive" / "minimal.json").read_text())
    values: dict[str, object] = {
        "authorization_ref": "auth-1",
        "expires_at": "2026-10-06T12:00:00Z",
        "delegation": {"parent_packet": "p0"},
        "capabilities": ["commit"],
        "resources": ["urn:test:x"],
        "profile": "COMMIT",
    }
    packet["permissions"][field] = values[field]
    with pytest.raises(CanonicalizationError, match="unknown canonical field"):
        canonical_loads(json.dumps(packet, separators=(",", ":")))
