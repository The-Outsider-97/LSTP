"""Replay/idempotency storage interfaces and reference implementations."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock
from typing import Protocol, runtime_checkable


@runtime_checkable
class ReplayStore(Protocol):
    """Atomic operation-id reservation interface used by host authorization."""

    def reserve(self, operation_id: str, action_digest: str) -> str | None:
        """Reserve *operation_id* for *action_digest*.

        Return ``None`` when reservation succeeds. If already reserved, return
        the previously stored digest. Implementations MUST make this operation
        atomic across their advertised concurrency boundary.
        """
        ...

    def release(self, operation_id: str) -> None:
        """Release a reservation when host policy explicitly permits retry."""
        ...

    def digest_for(self, operation_id: str) -> str | None:
        """Return the stored digest for *operation_id*, if present."""
        ...


class ReplayGuard:
    """Thread-safe in-process replay store."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._reserved: dict[str, str] = {}

    @staticmethod
    def _validate(operation_id: str, action_digest: str | None = None) -> None:
        if not operation_id:
            raise ValueError("operation_id must be non-empty")
        if action_digest is not None and not action_digest:
            raise ValueError("action_digest must be non-empty")

    def reserve(self, operation_id: str, action_digest: str) -> str | None:
        self._validate(operation_id, action_digest)
        with self._lock:
            existing = self._reserved.get(operation_id)
            if existing is not None:
                return existing
            self._reserved[operation_id] = action_digest
            return None

    def release(self, operation_id: str) -> None:
        self._validate(operation_id)
        with self._lock:
            self._reserved.pop(operation_id, None)

    def digest_for(self, operation_id: str) -> str | None:
        self._validate(operation_id)
        with self._lock:
            return self._reserved.get(operation_id)


class SQLiteReplayStore:
    """Durable SQLite replay store with atomic unique-key reservation.

    Every operation uses a short-lived connection. ``reserve`` acquires an
    immediate write transaction before checking/inserting the primary key, so
    competing processes sharing one database file cannot both reserve the same
    operation id.
    """

    def __init__(self, path: str | Path, *, timeout: float = 5.0) -> None:
        self.path = str(path)
        self.timeout = timeout
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=self.timeout,
            isolation_level=None,
        )
        connection.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)}")
        return connection

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS lstp_replay_reservations (
                    operation_id TEXT PRIMARY KEY NOT NULL,
                    action_digest TEXT NOT NULL
                )
                """
            )
        finally:
            connection.close()

    @staticmethod
    def _validate(operation_id: str, action_digest: str | None = None) -> None:
        if not operation_id:
            raise ValueError("operation_id must be non-empty")
        if action_digest is not None and not action_digest:
            raise ValueError("action_digest must be non-empty")

    def reserve(self, operation_id: str, action_digest: str) -> str | None:
        self._validate(operation_id, action_digest)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT action_digest FROM lstp_replay_reservations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if row is not None:
                connection.execute("ROLLBACK")
                return str(row[0])
            connection.execute(
                "INSERT INTO lstp_replay_reservations(operation_id, action_digest) VALUES (?, ?)",
                (operation_id, action_digest),
            )
            connection.execute("COMMIT")
            return None
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def release(self, operation_id: str) -> None:
        self._validate(operation_id)
        connection = self._connect()
        try:
            connection.execute(
                "DELETE FROM lstp_replay_reservations WHERE operation_id = ?",
                (operation_id,),
            )
        finally:
            connection.close()

    def digest_for(self, operation_id: str) -> str | None:
        self._validate(operation_id)
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT action_digest FROM lstp_replay_reservations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
        finally:
            connection.close()
        return None if row is None else str(row[0])


__all__ = ["ReplayGuard", "ReplayStore", "SQLiteReplayStore"]
