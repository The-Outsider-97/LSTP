"""Optional etcd-backed linearizable coordination for LSTP host state.

Raft/quorum/leader election are performed by a *separately operated etcd*
cluster, NOT by this library. Only the etcd v3 JSON gRPC gateway is used.
No consensus about semantic truth, neural predictions or execution authority.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import ssl
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

_KEY_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]*")


class ConsensusUnavailable(RuntimeError):
    """Quorum, transport or server health cannot be established; fail closed."""


class ConsensusProtocolError(ConsensusUnavailable):
    """The service returned malformed or unexpected protocol data."""


@dataclass(frozen=True, slots=True)
class ConsensusValue:
    value: bytes
    revision: int


class _DenyRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


Transport = Callable[[str, Mapping[str, object]], Mapping[str, object]]


class EtcdConsensusStore:
    """Linearizable reads and atomic revisioned CAS through an external etcd cluster.

    The gateway must be protected by TLS and an authenticated/trusted network.
    Plain HTTP is restricted to loopback for local tests/development.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        namespace: str = "lstp/v1",
        timeout: float = 3.0,
        token: str | None = None,
        tls_context: ssl.SSLContext | None = None,
        expected_cluster_id: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname or (
            parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}
        ):
            raise ValueError("endpoint must be an http(s) host URL without credentials or path")
        if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("plaintext consensus endpoints are allowed only on loopback")
        if not _KEY_RE.fullmatch(namespace) or ".." in namespace.split("/") or len(namespace) > 128:
            raise ValueError("invalid consensus namespace")
        if not 0 < timeout <= 120:
            raise ValueError("timeout must be between 0 and 120 seconds")
        if token is not None and (not token or "\n" in token or "\r" in token):
            raise ValueError("invalid consensus authentication token")
        if token is not None and parsed.scheme != "https":
            raise ValueError("authentication tokens require HTTPS")
        if expected_cluster_id is not None and not expected_cluster_id.isdecimal():
            raise ValueError("expected cluster ID must be a decimal string")
        if tls_context is not None and tls_context.verify_mode == ssl.CERT_NONE:
            raise ValueError("TLS certificate verification must be enabled")
        self.endpoint = endpoint.rstrip("/")
        self.namespace = namespace
        self.timeout = timeout
        self._token = token
        self._tls_context = tls_context or ssl.create_default_context()
        self.expected_cluster_id = expected_cluster_id
        self._transport = transport
        self._opener = build_opener(_DenyRedirect(), HTTPSHandler(context=self._tls_context))

    @staticmethod
    def _b64(value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")

    @staticmethod
    def _unb64(value: object) -> bytes:
        if not isinstance(value, str):
            raise ConsensusProtocolError("etcd response value is not base64")
        try:
            return base64.b64decode(value, validate=True)
        except (ValueError, base64.binascii.Error):
            raise ConsensusProtocolError("etcd response contains invalid base64") from None

    def _key(self, key: str) -> str:
        if not isinstance(key, str) or not _KEY_RE.fullmatch(key) or ".." in key.split("/") or len(key) > 512:
            raise ValueError("invalid consensus key")
        return self._b64((self.namespace + "/" + key).encode("utf-8"))

    def _request(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        if self._transport is not None:
            response = self._transport(path, payload)
        else:
            raw = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if self._token is not None:
                headers["Authorization"] = self._token
            request = Request(self.endpoint + path, data=raw, headers=headers, method="POST")
            try:
                with self._opener.open(request, timeout=self.timeout) as stream:
                    body = stream.read(1_048_577)
                if len(body) > 1_048_576:
                    raise ConsensusProtocolError("etcd response exceeds byte limit")
                response = json.loads(body)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                # Never retry a potentially committed transaction without
                # separately verifying its outcome; callers see uncertainty.
                raise ConsensusUnavailable("etcd transaction/read unavailable") from exc
        if not isinstance(response, Mapping) or "error" in response:
            raise ConsensusProtocolError("etcd returned an error or malformed response")
        header = response.get("header")
        if not isinstance(header, Mapping):
            raise ConsensusProtocolError("etcd response lacks revision header")
        if self.expected_cluster_id is not None and str(header.get("cluster_id")) != self.expected_cluster_id:
            raise ConsensusProtocolError("etcd cluster ID does not match pinned cluster")
        return response

    @staticmethod
    def _revision(header: Mapping[str, object], name: str = "revision") -> int:
        value = header.get(name)
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ConsensusProtocolError(f"missing {name} field")
        try:
            revision = int(value)
        except ValueError:
            raise ConsensusProtocolError(f"invalid {name} field") from None
        if revision < 0:
            raise ConsensusProtocolError(f"negative {name} field")
        return revision

    def get(self, key: str) -> ConsensusValue | None:
        """Linearizable read; never request a potentially stale serializable read."""
        response = self._request("/v3/kv/range", {"key": self._key(key), "serializable": False})
        entries = response.get("kvs", [])
        if not isinstance(entries, list) or len(entries) > 1:
            raise ConsensusProtocolError("unexpected etcd range response")
        if not entries:
            return None
        item = entries[0]
        if not isinstance(item, Mapping):
            raise ConsensusProtocolError("invalid etcd key entry")
        rev = self._revision(item, "mod_revision")
        if rev == 0:
            raise ConsensusProtocolError("invalid etcd modification revision")
        return ConsensusValue(self._unb64(item.get("value")), rev)

    def compare_and_swap(self, key: str, expected_revision: int | None, value: bytes) -> bool:
        """Atomic create (None) or conditional update by etcd MOD revision."""
        if expected_revision is not None and (type(expected_revision) is not int or expected_revision <= 0):
            raise ValueError("expected_revision must be positive or None")
        if not isinstance(value, bytes) or len(value) > 1_048_576:
            raise ValueError("consensus value must be bytes <= 1 MiB")
        encoded = self._key(key)
        compare = (
            {"key": encoded, "target": "VERSION", "result": "EQUAL", "version": "0"}
            if expected_revision is None
            else {"key": encoded, "target": "MOD", "result": "EQUAL", "modRevision": str(expected_revision)}
        )
        response = self._request("/v3/kv/txn", {
            "compare": [compare],
            "success": [{"requestPut": {"key": encoded, "value": self._b64(value)}}],
            "failure": [],
        })
        if type(response.get("succeeded")) is not bool:
            raise ConsensusProtocolError("etcd transaction lacks succeeded boolean")
        return response["succeeded"] is True

    def delete(self, key: str) -> None:
        """Unconditional deletion is reserved for explicit trusted host cleanup."""
        response = self._request("/v3/kv/deleterange", {"key": self._key(key)})
        if "deleted" not in response or type(response["deleted"]) not in (int, str):
            raise ConsensusProtocolError("etcd deletion result missing")
        self._revision(response, "deleted")

    def propose_ontology_digest(
        self, expected_revision: int | None, *, version: str, digest: str
    ) -> bool:
        """Coordinate a *version pointer*, not semantic truth or authorization."""
        if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", version):
            raise ValueError("invalid ontology version")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("ontology digest must be lowercase SHA-256 hex")
        manifest = json.dumps({"digest": digest, "version": version}, sort_keys=True, separators=(",", ":"))
        return self.compare_and_swap("ontology/active", expected_revision, manifest.encode("utf-8"))


class EtcdReplayStore:
    """ReplayStore-compatible atomic reservations backed by an etcd quorum."""

    def __init__(self, consensus: EtcdConsensusStore) -> None:
        self.consensus = consensus

    @staticmethod
    def _key(operation_id: str) -> str:
        if not isinstance(operation_id, str) or not operation_id or len(operation_id) > 1024:
            raise ValueError("invalid operation_id")
        return "replay/" + hashlib.sha256(operation_id.encode("utf-8")).hexdigest()

    @staticmethod
    def _digest(action_digest: str) -> bytes:
        if not isinstance(action_digest, str) or not action_digest or len(action_digest) > 256:
            raise ValueError("invalid action_digest")
        return action_digest.encode("utf-8")

    def reserve(self, operation_id: str, action_digest: str) -> str | None:
        key = self.consensus._key(self._key(operation_id))
        value = self._digest(action_digest)
        response = self.consensus._request("/v3/kv/txn", {
            "compare": [{"key": key, "target": "VERSION", "result": "EQUAL", "version": "0"}],
            "success": [{"requestPut": {"key": key, "value": self.consensus._b64(value)}}],
            "failure": [{"requestRange": {"key": key, "serializable": False}}],
        })
        succeeded = response.get("succeeded")
        if type(succeeded) is not bool:
            raise ConsensusProtocolError("etcd replay transaction lacks result")
        if succeeded:
            return None
        responses = response.get("responses")
        if not isinstance(responses, list) or len(responses) != 1 or not isinstance(responses[0], Mapping):
            raise ConsensusProtocolError("missing replay conflict read")
        read = responses[0].get("response_range", responses[0].get("responseRange"))
        if not isinstance(read, Mapping) or not isinstance(read.get("kvs"), list) or len(read["kvs"]) != 1:
            raise ConsensusProtocolError("missing replay-conflict value")
        entry = read["kvs"][0]
        if not isinstance(entry, Mapping):
            raise ConsensusProtocolError("malformed replay-conflict value")
        try:
            return self.consensus._unb64(entry.get("value")).decode("utf-8", "strict")
        except UnicodeDecodeError:
            raise ConsensusProtocolError("invalid replay-conflict digest") from None

    def digest_for(self, operation_id: str) -> str | None:
        record = self.consensus.get(self._key(operation_id))
        if record is None:
            return None
        try:
            return record.value.decode("utf-8", "strict")
        except UnicodeDecodeError:
            raise ConsensusProtocolError("invalid stored replay digest") from None

    def release(self, operation_id: str) -> None:
        self.consensus.delete(self._key(operation_id))


__all__ = [
    "ConsensusProtocolError", "ConsensusUnavailable", "ConsensusValue",
    "EtcdConsensusStore", "EtcdReplayStore",
]
