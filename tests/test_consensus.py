"""Contract tests of the etcd client; no real-quorum test is claimed."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from lstp.consensus import (
    ConsensusProtocolError, EtcdConsensusStore, EtcdReplayStore,
)


class MemoryGateway:
    """Deterministic fake of etcd transaction shape, NOT an independent etcd or Raft."""

    def __init__(self) -> None:
        self.revision = 1
        self.values: dict[str, tuple[str, int, int]] = {}
        self.requests: list[tuple[str, dict[str, object]]] = []

    def __call__(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.requests.append((path, dict(payload)))
        response: dict[str, object] = {"header": {"cluster_id": "42", "revision": str(self.revision)}}
        key = payload.get("key")
        if path == "/v3/kv/range":
            assert payload["serializable"] is False
            if key in self.values:
                value, rev, version = self.values[key]
                response["kvs"] = [{"value": value, "mod_revision": str(rev), "version": str(version)}]
            return response
        if path == "/v3/kv/deleterange":
            response["deleted"] = "1" if self.values.pop(key, None) else "0"
            return response
        assert path == "/v3/kv/txn"
        compare = payload["compare"][0]
        assert isinstance(compare, dict)
        key = compare["key"]
        old = self.values.get(key)
        if compare["target"] == "VERSION":
            matched = (0 if old is None else old[2]) == int(compare["version"])
        else:
            matched = old is not None and old[1] == int(compare["modRevision"])
        response["succeeded"] = matched
        if matched:
            put = payload["success"][0]["requestPut"]
            self.revision += 1
            self.values[key] = (put["value"], self.revision, (old[2] + 1 if old else 1))
        elif payload.get("failure"):
            response["responses"] = [{"response_range": {"kvs": [] if old is None else [{
                "value": old[0], "mod_revision": str(old[1]), "version": str(old[2])
            }]}}]
        return response


def store(gateway: MemoryGateway) -> EtcdConsensusStore:
    return EtcdConsensusStore("https://127.0.0.1:2379", namespace="lstp/test", expected_cluster_id="42", transport=gateway)


def test_create_update_conflict_and_linearizable_read() -> None:
    gateway = MemoryGateway()
    consensus = store(gateway)
    assert consensus.get("ontology/active") is None
    assert consensus.compare_and_swap("ontology/active", None, b"v1")
    assert not consensus.compare_and_swap("ontology/active", None, b"overwrite")
    record = consensus.get("ontology/active")
    assert record is not None and record.value == b"v1"
    assert not consensus.compare_and_swap("ontology/active", record.revision + 1, b"wrong")
    assert consensus.compare_and_swap("ontology/active", record.revision, b"v2")
    assert consensus.get("ontology/active").value == b"v2"  # type: ignore[union-attr]
    assert all(req["serializable"] is False for path, req in gateway.requests if path == "/v3/kv/range")


def test_ontology_digest_pointer_is_exact() -> None:
    gateway = MemoryGateway()
    consensus = store(gateway)
    assert consensus.propose_ontology_digest(None, version="0.1", digest="a" * 64)
    entry = consensus.get("ontology/active")
    assert entry is not None and b'"version":"0.1"' in entry.value
    with pytest.raises(ValueError, match="digest"):
        consensus.propose_ontology_digest(None, version="0.1", digest="not-a-digest")


def test_distributed_replay_adapter_reserves_atomically() -> None:
    gateway = MemoryGateway()
    first = EtcdReplayStore(store(gateway))
    second = EtcdReplayStore(store(gateway))
    assert first.reserve("operation-1", "sha256:one") is None
    assert second.reserve("operation-1", "sha256:one") == "sha256:one"
    assert second.reserve("operation-1", "sha256:two") == "sha256:one"
    assert first.digest_for("operation-1") == "sha256:one"
    assert len(gateway.values) == 1
    assert "operation-1" not in str(gateway.requests)  # hashed key, not raw identity
    first.release("operation-1")
    assert second.digest_for("operation-1") is None


def test_untrusted_endpoints_and_invalid_keys_rejected() -> None:
    for endpoint in ("http://example.com:2379", "https://u:p@example.com", "https://example.com/v3"):
        with pytest.raises(ValueError):
            EtcdConsensusStore(endpoint)
    c = store(MemoryGateway())
    with pytest.raises(ValueError):
        c.get("../escape")
    with pytest.raises(ValueError):
        c.compare_and_swap("ok", 0, b"value")
    with pytest.raises(ValueError):
        c.compare_and_swap("ok", None, b"v" * 1_048_577)
    with pytest.raises(ValueError):
        EtcdReplayStore(c).reserve("", "digest")


def test_wrong_cluster_id_and_missing_conflict_are_fail_closed() -> None:
    gateway = MemoryGateway()
    c = EtcdConsensusStore("https://127.0.0.1:2379", expected_cluster_id="99", transport=gateway)
    with pytest.raises(ConsensusProtocolError, match="cluster ID"):
        c.get("key")

    def bad_gateway(path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        return {"header": {"cluster_id": "42", "revision": "1"}, "succeeded": False, "responses": []}
    replay = EtcdReplayStore(EtcdConsensusStore("https://127.0.0.1:2379", transport=bad_gateway))
    with pytest.raises(ConsensusProtocolError, match="replay conflict"):
        replay.reserve("op", "digest")
