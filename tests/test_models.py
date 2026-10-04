from __future__ import annotations

import math

import pytest

from lstp.models import Octad, PacketEnvelope


def make_octad() -> Octad:
    return Octad(
        pragmatics={"type": "QUERY"},
        atoms=[{"id": "a0", "kind": "concept", "value": "mars"}],
        relations=[],
        context={"thread_id": "t-1"},
        confidence=0.8,
        permissions={"mode": "RO"},
        evidence=[],
        output={"format": "JSON"},
    )


def test_octad_preserves_authoritative_field_order() -> None:
    assert tuple(name for name, _ in make_octad().semantic_items()) == (
        "pragmatics",
        "atoms",
        "relations",
        "context",
        "confidence",
        "permissions",
        "evidence",
        "output",
    )


def test_octad_takes_immutable_snapshot() -> None:
    source = {"type": "QUERY", "nested": ["a"]}
    octad = make_octad()
    octad = Octad(**{**dict(octad.semantic_items()), "pragmatics": source})
    source["type"] = "COMMAND"
    source["nested"].append("b")
    assert octad.pragmatics["type"] == "QUERY"  # type: ignore[index]
    assert octad.pragmatics["nested"] == ("a",)  # type: ignore[index]


def test_envelope_metadata_is_not_semantic_equality() -> None:
    octad = make_octad()
    left = PacketEnvelope(octad, "p-1", "0.1", carrier={"source": "json"})
    right = PacketEnvelope(octad, "p-2", "0.1", carrier={"source": "lattice"})
    assert left != right
    assert left.semantically_equals(right)


def test_envelope_rejects_empty_identity() -> None:
    with pytest.raises(ValueError, match="packet_id"):
        PacketEnvelope(make_octad(), "", "0.1")


@pytest.mark.parametrize("version", ["", "0.0", "0.2", "1.0", "latest"])
def test_envelope_rejects_unknown_protocol_versions(version: str) -> None:
    with pytest.raises(ValueError, match="unsupported protocol_version"):
        PacketEnvelope(make_octad(), "p-1", version)


def test_model_rejects_non_json_like_runtime_objects() -> None:
    with pytest.raises(TypeError, match=r"unsupported canonical value type at \$\.output"):
        Octad({}, {}, [], {}, 1.0, {}, [], object())


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_model_rejects_non_finite_numbers(value: float) -> None:
    with pytest.raises(ValueError, match=r"non-finite number at \$\.confidence"):
        Octad({}, {}, [], {}, value, {}, [], {})


def test_model_rejects_non_string_mapping_keys_instead_of_coercing() -> None:
    with pytest.raises(TypeError, match=r"non-string object key at \$\.context: int"):
        Octad({}, {}, [], {1: "one", "1": "string-one"}, 1.0, {}, [], {})  # type: ignore[dict-item]


def test_envelope_applies_same_strict_json_boundary() -> None:
    with pytest.raises(ValueError, match=r"non-finite number at \$\.audit\.duration"):
        PacketEnvelope(make_octad(), "p-1", "0.1", audit={"duration": math.inf})


@pytest.mark.parametrize(
    ("field", "value"),
    [("carrier", "json"), ("audit", []), ("extensions", ["slai"])],
)
def test_envelope_structures_must_be_objects(field: str, value: object) -> None:
    kwargs = {field: value}
    with pytest.raises(TypeError, match=rf"expected object at \$\.{field}"):
        PacketEnvelope(make_octad(), "p-1", "0.1", **kwargs)  # type: ignore[arg-type]


def test_namespaced_extensions_are_preserved_without_interpretation() -> None:
    packet = PacketEnvelope(
        make_octad(),
        "p-1",
        "0.1",
        extensions={"slai": {"trace_id": "trace-1", "requested_mode": "EXEC"}},
    )
    assert packet.extensions["slai"]["trace_id"] == "trace-1"  # type: ignore[index]
    assert packet.octad.permissions == {"mode": "RO"}


@pytest.mark.parametrize("namespace", ["", " ", "\t"])
def test_empty_extension_namespace_is_rejected(namespace: str) -> None:
    with pytest.raises(ValueError, match="extension namespace"):
        PacketEnvelope(make_octad(), "p-1", "0.1", extensions={namespace: {}})


def test_extension_namespace_payload_must_be_object() -> None:
    with pytest.raises(TypeError, match="must contain an object"):
        PacketEnvelope(make_octad(), "p-1", "0.1", extensions={"slai": "EXEC"})
