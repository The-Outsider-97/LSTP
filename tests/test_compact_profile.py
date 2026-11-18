import hashlib
import json
from pathlib import Path

import pytest

from lstp import LSTPError, canonical_dumps, canonical_loads, compact_dumps, compact_loads

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
