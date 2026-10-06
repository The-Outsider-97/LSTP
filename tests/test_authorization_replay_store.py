from __future__ import annotations

from lstp.models import Context, Octad, Output, PacketEnvelope, Permissions, Pragmatics, Resource
from lstp.packet.authorization import Authority, HostPolicy, OperationRequest, PrincipalContext, authorize_operation
from lstp.packet.replay import SQLiteReplayStore

RESOURCE = "urn:test:document:1"


def _packet() -> PacketEnvelope:
    return PacketEnvelope(
        Octad(
            Pragmatics("request", goal="test.commit"),
            (),
            (),
            Context("thread-1"),
            1.0,
            Permissions(("commit",), (Resource(RESOURCE),)),
            (),
            Output("NONE"),
        ),
        "packet-1",
        "0.1",
    )


def test_authorization_uses_durable_replay_store_without_store_specific_logic(tmp_path) -> None:
    first_store = SQLiteReplayStore(tmp_path / "replay.sqlite3")
    second_store = SQLiteReplayStore(tmp_path / "replay.sqlite3")
    authority = Authority(frozenset({"commit"}), frozenset({RESOURCE}))
    principal = PrincipalContext("agent.child", authority)
    policy = HostPolicy(
        capabilities=frozenset({"commit"}),
        resources=frozenset({RESOURCE}),
        require_confirmation_for=frozenset(),
        require_logging_for=frozenset(),
    )
    operation = OperationRequest(
        "commit",
        RESOURCE,
        "op-1",
        "sha256:action-1",
        confirmed=True,
        reviewed=True,
        logging_ready=True,
    )

    first = authorize_operation(
        _packet(),
        operation,
        principal=principal,
        policy=policy,
        runtime=authority,
        replay_guard=first_store,
    )
    second = authorize_operation(
        _packet(),
        operation,
        principal=principal,
        policy=policy,
        runtime=authority,
        replay_guard=second_store,
    )

    assert first.allowed is True
    assert second.allowed is False
    assert second.diagnostics[0].code == "replay_detected"
