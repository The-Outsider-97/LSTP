import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from lstp import (
    InputLimits,
    LSTPError,
    ResourceLimitError,
    canonical_dumps,
    canonical_loads,
    compact_dumps,
    compact_loads,
)

FIXTURES = Path(__file__).resolve().parents[1] / "conformance" / "v0.1"
VECTORS = sorted((FIXTURES / "positive").glob("*.json"))


@pytest.mark.parametrize("path", VECTORS)
def test_canonical_identity(path):
    packet = canonical_loads(path.read_bytes())
    frame = compact_dumps(packet)
    decoded = compact_loads(frame)
    assert canonical_dumps(decoded) == canonical_dumps(packet)
    assert compact_dumps(decoded) == frame


def test_exact_base_and_recovery():
    base = canonical_loads(VECTORS[-1].read_bytes())
    obj = json.loads(canonical_dumps(base))
    obj["audit"]["note"] = "reviewed"
    new = canonical_loads(json.dumps(obj))
    delta = compact_dumps(new, base=base)
    assert json.loads(delta)[:2] == ["D1", hashlib.sha256(canonical_dumps(base)).hexdigest()]
    for wrong in (None, new):
        with pytest.raises(LSTPError):
            compact_loads(delta, base=wrong)
    assert canonical_dumps(compact_loads(delta, base=base)) == canonical_dumps(new)
    assert canonical_dumps(compact_loads(compact_dumps(new))) == canonical_dumps(new)


@pytest.mark.parametrize("frame", ["{}", '["L2"]', '["L1",0]', '["D1","x",{"0":0,"0":1}]'])
def test_invalid_frame(frame):
    with pytest.raises(LSTPError):
        compact_loads(frame)


def test_unknown_fields_and_permission_types():
    frame = json.loads(compact_dumps(canonical_loads(VECTORS[0].read_bytes())))
    for key, value in (("authorization_ref", "pretend"), ("require_review", 1)):
        frame[7] = {key: value}
        with pytest.raises(LSTPError):
            compact_loads(json.dumps(frame))


@pytest.mark.parametrize("path", VECTORS)
def test_independent_fixture_and_host_signature(path):
    import hmac

    frame = (FIXTURES / "compact" / path.name).read_bytes()
    original = path.read_bytes()
    signature = hmac.digest(b"fixture-only", original, "sha256")
    restored = canonical_dumps(compact_loads(frame))
    assert hmac.compare_digest(signature, hmac.digest(b"fixture-only", restored, "sha256"))
    assert compact_dumps(canonical_loads(original)) == frame


@pytest.mark.parametrize("profile,full_arity,delta_arity", [("flat", 12, 3), ("typed", 2, 5)])
def test_both_merged_profiles_preserve_types_limits_and_explicit_context(
    profile, full_arity, delta_arity
):
    original = canonical_loads(VECTORS[0].read_bytes())
    base = replace(original, carrier={"literal": True}, audit={"shared": "context" * 1000})
    new = replace(base, carrier={"literal": 1})
    frame = compact_dumps(new, profile=profile)
    assert len(json.loads(frame)) == full_arity
    assert canonical_dumps(compact_loads(frame, require_compact_bytes=True)) == canonical_dumps(new)
    delta = compact_dumps(new, base=base, profile=profile)
    assert len(json.loads(delta)) == delta_arity
    restored_base = canonical_loads(canonical_dumps(base))
    assert canonical_dumps(compact_loads(delta, base=restored_base)) == canonical_dumps(new)
    for wrong in (None, new):
        with pytest.raises(LSTPError, match="base"):
            compact_loads(delta, base=wrong)
    with pytest.raises(ResourceLimitError):
        compact_loads(delta, base=base, limits=InputLimits(max_bytes=len(delta) + 1))


def test_all_public_exports_resolve_and_are_unique():
    import lstp

    assert len(lstp.__all__) == len(set(lstp.__all__))
    assert all(hasattr(lstp, name) for name in lstp.__all__)


@pytest.mark.parametrize("profile", ["flat", "typed"])
def test_nonminimal_optional_defaults_normalize_unless_strict_bytes_requested(profile):
    original = canonical_loads(VECTORS[0].read_bytes())
    frame = json.loads(compact_dumps(original, profile=profile))
    if profile == "typed":
        frame[1][4] = [None, None, None, False]
    else:
        frame[7]["require_confirmation"] = False
    wire = json.dumps(frame)
    assert canonical_dumps(compact_loads(wire)) == canonical_dumps(original)
    with pytest.raises(LSTPError, match="deterministic"):
        compact_loads(wire, require_compact_bytes=True)
