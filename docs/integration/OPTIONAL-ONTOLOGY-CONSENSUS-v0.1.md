# LSTP optional upper ontology and distributed coordination — engineering profile

**Status:** experimental opt-in host integration, **not** a normative change to LSTP v0.1, a complete ontology, or a production-certified distributed service.

The words "universal ontology" cannot honestly mean an exhaustively complete, universally accepted model of all entities, cultures, domains, times, and meanings. The W3C OWL/RDF/SHACL ecosystem is appropriate for large domain-specific ontologies and advanced logical inference. The implementation here offers a *small, explicitly versioned upper vocabulary* and validated host-owned extension points; it intentionally does not implement OWL 2, SHACL, RDF graph storage, or arbitrary description-logic entailment.

Likewise, distributed consensus does not cause semantic agreement or guarantee that a model's claims are true. The optional etcd adapter delegates actual Raft election, log replication, durable cluster membership, and quorum to separately operated etcd servers. LSTP itself implements only versioned compare-and-swap operations and distributed replay reservations.

## Installation and public imports

No new mandatory dependencies. Optional modules are imported explicitly:

```python
from lstp.ontology import OntologyRegistry, OntologyTerm, upper_ontology
from lstp.consensus import EtcdConsensusStore, EtcdReplayStore
```

The v0.1 wire format and all eight Octad domains are unchanged. No new fields in `permissions`, `carrier`, or semantic equality.

## Upper ontology

`upper_ontology()` provides an illustrative, non-exhaustive concept hierarchy (`entity`, `physical`, `abstract`, `agent`, `person`, `organization`, `event`, `process`, `resource`, `information`, `proposition`, `place`, `property`, `time`, `artifact`) and four typed relations (`part_of`, `located_at`, `participates_in`, `describes`) under the `lstp.upper.*` namespace.

- A term is a `concept` or `relation` with stable qualified identifier, parents, optional domain/range, and optional mapping IRI.
- Parent hierarchy must be acyclic and refer to terms of the same kind; relation domain/range require known concepts.
- `is_a` performs only reflexive/transitive asserted subclass checks, **not** open-world OWL reasoning.
- Unknown semantic namespaces remain unknown. Explicit host aliases can connect domain vocabularies without silently redefining core relation names.
- Host consumers may annotate atoms using `attributes.ontology_type` and optionally run `registry.validate_packet(packet)`. This is a host profile, not a wire requirement. Calls to normal `lstp.validate_packet(packet)` remain required.
- `to_mapping()` / `from_mapping()` provide deterministic, versioned snapshots. `digest()` hashes the registry snapshot for governance; it is **not** a signature or proof that the ontology is complete/correct.
- The registry is bounded to 20,000 terms and hierarchy depth 64. Extended domain vocabularies are supplied explicitly by the host; they are not dynamically learned from untrusted packets.

### Example

```python
ontology = upper_ontology()
assert ontology.is_a("lstp.upper.person", "lstp.upper.agent")
print(ontology.digest())
```

Building a genuinely broad ontology requires curated domain packs, provenance, mapping review, licencing, alignment tests, and either external W3C-compatible infrastructure or separate standards-based adapters. Such work is not a finite "complete universal ontology" feature.

## Distributed consensus through etcd

An externally deployed etcd cluster (typically three or five voting members, correctly networked and secured) provides actual Raft-based consensus. Configure HTTPS client access and trusted authentication **outside** LSTP. The JSON gRPC gateway uses `/v3/kv/range`, `/v3/kv/txn`, and `/v3/kv/deleterange`.

```python
import os
from lstp.consensus import EtcdConsensusStore, EtcdReplayStore

backend = EtcdConsensusStore(
    "https://etcd.internal.example:2379",
    namespace="lstp/production",
    token=os.environ["ETCD_AUTH_TOKEN"],
    expected_cluster_id=os.environ["ETCD_CLUSTER_ID"],
    timeout=3.0,
)
# Concurrent writers compete on the same key and prior revision.
assert backend.propose_ontology_digest(None, version="0.1", digest="a" * 64)
# Supply to the *existing* host authorize_operation(..., replay_guard=...).
replay_store = EtcdReplayStore(backend)
```

`EtcdConsensusStore.get()` requests a linearizable read. `compare_and_swap(key, expected_revision, bytes)` uses an atomic etcd conditional transaction (create if absent or compare modification revision). `propose_ontology_digest()` coordinates only an active ontology version/digest pointer. `EtcdReplayStore` conforms structurally to `ReplayStore` (`reserve`, `digest_for`, `release`) and atomically records the first operation digest. It never authorizes an operation; existing `authorize_operation()` is authoritative for host permissions.

### Security and failure boundary

- **Never** configure a single local `ReplayGuard` as a substitute for multi-node replay protection.
- The etcd cluster must enforce authentication, TLS, network ACLs, backups, quorum monitoring, member lifecycle, and incident recovery. The gateway does not authenticate users by TLS certificate common name; configure supported authentication separately.
- Plaintext URLs are restricted to localhost for development. TLS certificate verification is required. Redirects are rejected.
- No automatic retry occurs after an uncertain write outcome. Loss of quorum, timeouts, malformed replies, or cluster-ID mismatch raises an exception and must prevent host side effects.
- `release(operation_id)` intentionally deletes an existing replay reservation. **Only a trusted host recovery workflow** may call it; issuing releases on timeouts/restarts would destroy replay guarantees.
- Cluster configuration changes and snapshots require privileged administrative operations not exposed by this module.
- `expected_cluster_id` should be pinned to a real cluster ID after secure bootstrap. Never use illustrative hashes/IDs in production.

### Not yet verified

- The included contract tests use an in-memory fake HTTP gateway. They verify request construction and fail-closed behavior, **not** etcd quorum safety.
- A genuine three-node etcd integration test must demonstrate concurrent CAS contention, leader failure, partition/unavailability handling, restart, stable cluster-ID pinning, and replay reservation on separate processes before claiming production readiness.
- Consensus applies only to selected host operational state, not packet meaning, ontology correctness, or model decisions.
- Multi-region latency, etcd storage limits, authentication, and disaster recovery need deployment-specific testing.

## Release governance

Both modules remain **optional experimental integrations**. Do not alter `docs/program/readiness.json` to declare the protocol release or LANTRA training ready because these modules exist. They do not bypass preexisting VERIFY-001 / DOC-001 / REL-001 blockers, and LANTRA does not require a distributed cluster unless its deployment scope explicitly does.

Normative protocol semantics remain governed by `docs/LSTP_Whitepaper.pdf`, the README, and `spec/` in the existing authority order. A future wire format involving ontology identifiers or distributed membership requires separate versioned protocol governance.
