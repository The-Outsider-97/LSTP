"""Optional, host-owned upper ontology and versioned domain vocabulary registry.

This is *not* a complete ontology of everything or an OWL reasoner. It provides
explicit term identity, an acyclic subclass hierarchy, controlled mappings and
packet-level domain/range checks. It never alters canonical v0.1 wire semantics.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lstp.models import PacketEnvelope

_TERM_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)+")
_VERSION_RE = re.compile(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?")


class OntologyError(ValueError):
    """An ontology definition or checked packet is inconsistent."""


@dataclass(frozen=True, slots=True)
class OntologyTerm:
    identifier: str
    kind: str  # concept or relation
    parents: tuple[str, ...] = ()
    domain: str | None = None
    range: str | None = None
    iri: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.identifier, str) or not _TERM_RE.fullmatch(self.identifier):
            raise OntologyError("term identifier must be a namespaced qualified identifier")
        if self.kind not in {"concept", "relation"}:
            raise OntologyError("term kind must be concept or relation")
        if not isinstance(self.parents, tuple) or any(
            not isinstance(parent, str) or not _TERM_RE.fullmatch(parent)
            for parent in self.parents
        ):
            raise OntologyError("invalid parent term")
        if len(self.parents) != len(set(self.parents)) or self.identifier in self.parents:
            raise OntologyError("duplicate or self-referential parents")
        if self.kind == "concept" and (self.domain is not None or self.range is not None):
            raise OntologyError("concept cannot define relation domain/range")
        if self.kind == "relation" and ((self.domain is None) != (self.range is None)):
            raise OntologyError("relation domain/range must both be present or absent")
        for value in (self.domain, self.range):
            if value is not None and (not isinstance(value, str) or not _TERM_RE.fullmatch(value)):
                raise OntologyError("invalid domain/range term")
        if self.iri is not None and (
            not isinstance(self.iri, str) or not self.iri.startswith(("https://", "http://", "urn:"))
            or any(ord(c) < 33 for c in self.iri)
        ):
            raise OntologyError("iri must be an absolute HTTP(S) or URN identifier")


class OntologyRegistry:
    """Immutable validated vocabulary, limited to asserted subclass entailment.

    Unknown terms and relationships are never inferred. A mapping between
    namespaces must be explicitly supplied by the consuming host.
    """

    def __init__(
        self,
        version: str,
        terms: Iterable[OntologyTerm],
        *,
        aliases: Mapping[str, str] | None = None,
    ) -> None:
        if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
            raise OntologyError("version must use numeric major.minor[.patch]")
        by_id: dict[str, OntologyTerm] = {}
        for index, term in enumerate(terms):
            if index >= 20_000:
                raise OntologyError("ontology exceeds 20,000 term safety limit")
            if not isinstance(term, OntologyTerm) or term.identifier in by_id:
                raise OntologyError("duplicate or malformed ontology term")
            by_id[term.identifier] = term
        if not by_id:
            raise OntologyError("ontology must contain at least one term")
        for term in by_id.values():
            for parent in term.parents:
                if parent not in by_id or by_id[parent].kind != term.kind:
                    raise OntologyError(f"unknown/incompatible parent for {term.identifier}")
            if term.kind == "relation" and term.domain is not None:
                if any(
                    ref not in by_id or by_id[ref].kind != "concept"
                    for ref in (term.domain, term.range)
                ):
                    raise OntologyError(f"unknown relation domain/range for {term.identifier}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(identifier: str) -> None:
            if identifier in visiting:
                raise OntologyError("ontology parent hierarchy contains a cycle")
            if identifier in visited:
                return
            visiting.add(identifier)
            if len(visiting) > 64:
                raise OntologyError("ontology hierarchy exceeds depth safety limit")
            for parent in by_id[identifier].parents:
                visit(parent)
            visiting.remove(identifier)
            visited.add(identifier)

        for identifier in by_id:
            visit(identifier)
        resolved_aliases: dict[str, str] = {}
        for alias, target in (aliases or {}).items():
            if not isinstance(alias, str) or not alias or alias in by_id:
                raise OntologyError("alias must be nonempty and cannot shadow a term")
            if not isinstance(target, str) or target not in by_id or alias in resolved_aliases:
                raise OntologyError("alias must refer directly to a known term")
            resolved_aliases[alias] = target
        self.version = version
        self._terms = by_id
        self._aliases = resolved_aliases

    def resolve(self, identifier: str) -> OntologyTerm:
        target = self._aliases.get(identifier, identifier)
        try:
            return self._terms[target]
        except KeyError:
            raise OntologyError(f"unknown ontology term: {identifier!r}") from None

    def is_a(self, child: str, parent: str) -> bool:
        """Reflexive/transitive subclass check; not full OWL inference."""
        child_id = self.resolve(child).identifier
        parent_id = self.resolve(parent).identifier
        if self._terms[child_id].kind != "concept" or self._terms[parent_id].kind != "concept":
            raise OntologyError("is_a applies to concepts only")
        pending = [child_id]
        seen: set[str] = set()
        while pending:
            current = pending.pop()
            if current == parent_id:
                return True
            if current not in seen:
                seen.add(current)
                pending.extend(self._terms[current].parents)
        return False

    def validate_packet(self, packet: PacketEnvelope, *, require_types: bool = True) -> None:
        """Validate explicitly mapped binary relations against typed atoms.

        Atoms use host-supplied `attributes.ontology_type`. Other relations are
        untouched; LSTP's own semantic validator remains mandatory and distinct.
        """
        types: dict[str, str] = {}
        for atom in packet.octad.atoms:
            declared = atom.attributes.get("ontology_type")
            if declared is not None:
                if not isinstance(declared, str) or self.resolve(declared).kind != "concept":
                    raise OntologyError(f"invalid ontology type for atom {atom.id}")
                types[atom.id] = declared
        for relation in packet.octad.relations:
            identifier = self._aliases.get(relation.type, relation.type)
            term = self._terms.get(identifier)
            if term is None:
                continue  # unknown domain semantics are not invented
            if term.kind != "relation":
                raise OntologyError(f"concept used as relation: {relation.type}")
            if term.domain is None:
                continue
            if len(relation.arguments) != 2:
                raise OntologyError(f"expected binary relation: {relation.type}")
            for atom_id, required in zip(relation.arguments, (term.domain, term.range)):
                actual = types.get(atom_id)
                if actual is None:
                    if require_types:
                        raise OntologyError(f"missing ontology type for relation argument: {atom_id}")
                elif not self.is_a(actual, required):
                    raise OntologyError(f"ontology type mismatch for relation argument: {atom_id}")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "terms": [
                {
                    "identifier": t.identifier,
                    "kind": t.kind,
                    "parents": list(t.parents),
                    "domain": t.domain,
                    "range": t.range,
                    "iri": t.iri,
                }
                for t in sorted(self._terms.values(), key=lambda x: x.identifier)
            ],
            "aliases": dict(sorted(self._aliases.items())),
        }

    def digest(self) -> str:
        """Registry governance fingerprint; not an LSTP packet signature."""
        snapshot = json.dumps(self.to_mapping(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(snapshot.encode("utf-8")).hexdigest()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> OntologyRegistry:
        if not isinstance(data, Mapping) or set(data) != {"version", "terms", "aliases"}:
            raise OntologyError("ontology snapshot must contain version, terms, aliases only")
        if not isinstance(data["terms"], list) or not isinstance(data["aliases"], dict):
            raise OntologyError("invalid ontology term/alias collection")
        terms: list[OntologyTerm] = []
        for entry in data["terms"]:
            if not isinstance(entry, dict) or set(entry) != {
                "identifier", "kind", "parents", "domain", "range", "iri"
            } or not isinstance(entry["parents"], list):
                raise OntologyError("invalid ontology term shape")
            terms.append(OntologyTerm(
                entry["identifier"], entry["kind"], tuple(entry["parents"]),
                entry["domain"], entry["range"], entry["iri"],
            ))
        return cls(data["version"], terms, aliases=data["aliases"])


def upper_ontology() -> OntologyRegistry:
    """A small general upper vocabulary; domain ontologies are additional packs."""
    root = "lstp.upper.entity"
    names = {
        "entity": (),
        "physical": ("entity",),
        "abstract": ("entity",),
        "agent": ("entity",),
        "person": ("agent", "physical"),
        "organization": ("agent", "abstract"),
        "artifact": ("physical",),
        "place": ("physical",),
        "event": ("entity",),
        "process": ("event",),
        "information": ("abstract",),
        "proposition": ("information",),
        "resource": ("entity",),
        "property": ("abstract",),
        "time": ("abstract",),
    }
    terms = [OntologyTerm("lstp.upper." + name, "concept", tuple("lstp.upper." + p for p in parents))
             for name, parents in names.items()]
    terms.extend([
        OntologyTerm("lstp.upper.part_of", "relation", (), root, root),
        OntologyTerm("lstp.upper.located_at", "relation", (), root, "lstp.upper.place"),
        OntologyTerm("lstp.upper.participates_in", "relation", (), "lstp.upper.agent", "lstp.upper.event"),
        OntologyTerm("lstp.upper.describes", "relation", (), "lstp.upper.information", root),
    ])
    return OntologyRegistry("0.1", terms)


__all__ = ["OntologyError", "OntologyRegistry", "OntologyTerm", "upper_ontology"]
