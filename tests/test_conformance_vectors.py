from __future__ import annotations

from pathlib import Path

import pytest

from lstp import CanonicalizationError, SemanticValidationError, canonical_dumps, canonical_loads

ROOT = Path(__file__).resolve().parents[1] / "conformance" / "v0.1"


def test_positive_vectors_round_trip_byte_identically() -> None:
    for path in sorted((ROOT / "positive").glob("*.json")):
        source = path.read_bytes()
        packet = canonical_loads(source, require_canonical_bytes=True)
        assert canonical_dumps(packet) == source


@pytest.mark.parametrize(
    "name,error_type",
    [
        ("unknown-field.json", CanonicalizationError),
        ("unresolved-relation.json", SemanticValidationError),
        ("profile-widening.json", SemanticValidationError),
    ],
)
def test_negative_vectors_fail_closed(name: str, error_type: type[Exception]) -> None:
    source = (ROOT / "negative" / name).read_bytes()
    with pytest.raises(error_type):
        canonical_loads(source)
