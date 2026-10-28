"""Non-normative ontology tests; no claim of OWL-complete reasoning."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from lstp.ontology import OntologyError, OntologyRegistry, OntologyTerm, upper_ontology


def test_upper_subsumption_and_stable_snapshot() -> None:
    ontology = upper_ontology()
    assert ontology.is_a("lstp.upper.person", "lstp.upper.agent")
    assert ontology.is_a("lstp.upper.person", "lstp.upper.physical")
    assert ontology.is_a("lstp.upper.person", "lstp.upper.entity")
    assert not ontology.is_a("lstp.upper.person", "lstp.upper.information")
    restored = OntologyRegistry.from_mapping(ontology.to_mapping())
    assert restored.digest() == ontology.digest()
    assert restored.to_mapping() == ontology.to_mapping()


def test_reject_unknown_parent_and_cycles() -> None:
    with pytest.raises(OntologyError, match="parent"):
        OntologyRegistry("1.0", [OntologyTerm("test.child", "concept", ("test.absent",))])
    with pytest.raises(OntologyError, match="cycle"):
        OntologyRegistry("1.0", [
            OntologyTerm("test.a", "concept", ("test.b",)),
            OntologyTerm("test.b", "concept", ("test.a",)),
        ])


def test_no_silent_namespace_or_alias_invention() -> None:
    ontology = upper_ontology()
    with pytest.raises(OntologyError, match="unknown ontology"):
        ontology.resolve("fake.organization")
    with pytest.raises(OntologyError, match="cannot shadow"):
        OntologyRegistry("1.0", [OntologyTerm("test.a", "concept")], aliases={"test.a": "test.a"})
    aliases = OntologyRegistry(
        "1.0", [OntologyTerm("test.a", "concept")], aliases={"external.a": "test.a"}
    )
    assert aliases.resolve("external.a").identifier == "test.a"


def test_packet_relation_domain_range_checks_and_missing_types() -> None:
    ontology = upper_ontology()
    def atom(identifier: str, declared: str | None) -> SimpleNamespace:
        return SimpleNamespace(id=identifier, attributes={} if declared is None else {"ontology_type": declared})
    def packet(second: str | None, relation_name: str = "lstp.upper.located_at") -> SimpleNamespace:
        return SimpleNamespace(octad=SimpleNamespace(
            atoms=[atom("a0", "lstp.upper.person"), atom("a1", second)],
            relations=[SimpleNamespace(type=relation_name, arguments=("a0", "a1"))],
        ))
    ontology.validate_packet(packet("lstp.upper.place"))  # type: ignore[arg-type]
    with pytest.raises(OntologyError, match="type mismatch"):
        ontology.validate_packet(packet("lstp.upper.information"))  # type: ignore[arg-type]
    with pytest.raises(OntologyError, match="missing ontology type"):
        ontology.validate_packet(packet(None))  # type: ignore[arg-type]
    ontology.validate_packet(packet(None), require_types=False)  # type: ignore[arg-type]
    ontology.validate_packet(packet(None, "custom.unknown"))  # type: ignore[arg-type]


def test_snapshot_rejects_bad_term_structure() -> None:
    mapping = upper_ontology().to_mapping()
    mapping["terms"][0]["unknown"] = "bad"
    with pytest.raises(OntologyError, match="invalid ontology term shape"):
        OntologyRegistry.from_mapping(mapping)
