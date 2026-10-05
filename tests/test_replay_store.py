from __future__ import annotations

import pytest

from lstp.packet.replay import ReplayGuard, ReplayStore, SQLiteReplayStore


def test_in_memory_guard_conforms_to_protocol() -> None:
    store = ReplayGuard()
    assert isinstance(store, ReplayStore)
    assert store.reserve("op-1", "sha256:a") is None
    assert store.digest_for("op-1") == "sha256:a"
    assert store.reserve("op-1", "sha256:a") == "sha256:a"
    assert store.reserve("op-1", "sha256:b") == "sha256:a"
    store.release("op-1")
    assert store.digest_for("op-1") is None


def test_sqlite_store_persists_across_instances(tmp_path) -> None:
    path = tmp_path / "replay.sqlite3"
    first = SQLiteReplayStore(path)
    second = SQLiteReplayStore(path)

    assert isinstance(first, ReplayStore)
    assert first.reserve("op-1", "sha256:a") is None
    assert second.digest_for("op-1") == "sha256:a"
    assert second.reserve("op-1", "sha256:a") == "sha256:a"
    assert second.reserve("op-1", "sha256:b") == "sha256:a"


def test_sqlite_release_allows_explicit_retry(tmp_path) -> None:
    store = SQLiteReplayStore(tmp_path / "replay.sqlite3")
    assert store.reserve("op-1", "sha256:a") is None
    store.release("op-1")
    assert store.reserve("op-1", "sha256:b") is None
    assert store.digest_for("op-1") == "sha256:b"


def test_sqlite_rejects_invalid_configuration_and_identity(tmp_path) -> None:
    with pytest.raises(ValueError, match="file-backed"):
        SQLiteReplayStore(":memory:")
    with pytest.raises(ValueError, match="timeout"):
        SQLiteReplayStore(tmp_path / "x.sqlite3", timeout=0)

    store = SQLiteReplayStore(tmp_path / "y.sqlite3")
    with pytest.raises(ValueError, match="operation_id"):
        store.reserve("", "sha256:a")
    with pytest.raises(ValueError, match="action_digest"):
        store.reserve("op-1", "")
