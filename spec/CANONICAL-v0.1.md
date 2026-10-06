# LSTP v0.1 Canonical Contract

Status: implementation candidate under Whitepaper-first reconciliation.

This document records the October 2026 implementation candidate. It is not higher authority than the Level-1 Whitepaper. Where this file conflicts with `docs/LSTP_Whitepaper.pdf`, the Whitepaper governs until the conflict is explicitly reconciled and the project readiness gate records that decision.

BCP 14 terms (`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`) are used normatively.

## 1. Authority

The active project hierarchy is:

1. `docs/LSTP_Whitepaper.pdf` — Level 1 authoritative conceptual/protocol reference;
2. root `README.md` — Level 2 project guidance;
3. `spec/` — Level 3 technical artifacts;
4. `src/lstp/` — Level 4 reference implementation.

Conformance fixtures and tests are executable evidence. They do not override a higher-authority source.

This October candidate MUST NOT be used to redefine Whitepaper semantics. Known conflicts are tracked in `docs/program/WHITEPAPER-AUTHORITY-AUDIT-2026-10-06.md`. Until those conflicts are closed, this file is an implementation candidate rather than a frozen v0.1 authority.

## 2. Core model

An LSTP packet contains:

- an **envelope**, which identifies and transports the packet; and
- an **Octad**, which contains exactly eight semantic domains.

The Octad domains are, in canonical order:

1. `pragmatics`
2. `atoms`
3. `relations`
4. `context`
5. `confidence`
6. `permissions`
7. `evidence`
8. `output`

All eight Octad domains are REQUIRED in canonical JSON, even when a domain is empty. This makes omission distinguishable from an explicit empty/default state during carrier compilation.

Envelope fields are not part of semantic Octad equality.

## 3. Canonical packet shape

A canonical packet has the following top-level structure:

```json
{
  "id": "pkt_example_001",
  "version": "0.1",
  "pragmatics": {"act": "request", "urgency": 0.25},
  "atoms": {},
  "relations": [],
  "context": {"thread_id": "thread_example", "references": []},
  "confidence": 1.0,
  "permissions": {"capabilities": [], "resources": []},
  "evidence": [],
  "output": {"format": "NL"},
  "carrier": {},
  "audit": {},
  "extensions": {}
}
```

Required top-level fields are `id`, `version`, all eight Octad fields, `carrier`, and `audit`. `extensions` is OPTIONAL and defaults to an empty object when a host materializes a canonical in-memory envelope.

Unknown top-level fields MUST be rejected by canonical JSON validation.

## 4. Identity and version

### 4.1 `id`

`id` is a non-empty opaque packet identifier. It MUST NOT be interpreted as authentication, authorization, or proof of provenance.

A host SHOULD keep an identifier stable across the lifetime of one logical packet revision chain and SHOULD create a new identifier when a semantically distinct packet is produced.

### 4.2 `version`

Canonical v0.1 packets MUST contain:

```json
"version": "0.1"
```

A v0.1 consumer MUST reject or explicitly route unsupported versions. It MUST NOT guess compatibility.

## 5. Pragmatics (`π`)

`pragmatics` describes the communicative function of the packet.

Canonical fields:

- `act` — REQUIRED core communicative act;
- `goal` — OPTIONAL application/domain goal identifier;
- `modifiers` — OPTIONAL set of additional pragmatic labels;
- `register` — OPTIONAL register/style identifier;
- `urgency` — OPTIONAL number in `[0,1]`;
- `extensions` — OPTIONAL namespaced data.

Core `act` values are defined in `spec/vocabulary.md` and include at least:

- `assert`
- `request`
- `question`
- `inform`
- `correct`
- `acknowledge`
- `refuse`
- `respond`

The old subordinate fields `intent`, `action`, `force`, and `tone` are not canonical aliases. A migration tool MAY translate them only under an explicit non-conformance migration profile and MUST surface any lossy mapping.

Urgency affects priority semantics only. It MUST NOT increase execution authority.

## 6. Atoms (`A`)

`atoms` is an ordered array of typed semantic units.

Each atom MUST contain:

- `id` — packet-local atom identifier matching `a0`, `a1`, `a2`, ...;
- `kind` — one core atom kind.

An atom MAY also contain:

- `value`;
- `role`;
- `datatype`;
- `language`;
- `attributes`;
- `extensions`.

Core atom kinds are:

- `entity`
- `concept`
- `value`
- `event`
- `time`
- `location`
- `resource`
- `proposition`
- `unknown`

Atom IDs MUST be unique within one packet.

Free identifier-keyed atom maps and scalar atom shorthand are not canonical v0.1 JSON.

## 7. Relations (`R`)

`relations` is an ordered array of typed semantic relations.

Each relation MUST contain:

- `type` — relation identifier;
- `arguments` — ordered array with at least one argument.

A relation MAY contain:

- `id`;
- `confidence` in `[0,1]`;
- `attributes`;
- `extensions`.

Relation arguments MUST be one of:

- an atom reference such as `a0`;
- `SELF`;
- `NOW`;
- `USER`;
- `SYSTEM`.

Literal values that participate in relations SHOULD be represented as atoms so that they can be referenced, evidenced, and compared deterministically.

The previous subject/predicate/object shape is not canonical v0.1 JSON. It MAY be accepted only by an explicit migration adapter.

Core relation identifiers are defined in `spec/vocabulary.md`. Domain-specific relations MUST use a namespaced identifier.

## 8. Context (`C`)

`context` anchors the packet in a conversation or execution thread.

`thread_id` is REQUIRED and MUST be a non-empty string.

Optional fields are:

- `packet_id` — semantic reference to another packet where needed;
- `parent_id`;
- `conversation_id`;
- `turn` — non-negative integer;
- `speaker`;
- `audience` — array of identifiers;
- `time` — RFC 3339 date-time;
- `location` — structured or symbolic application value;
- `bindings` — application bindings;
- `references` — stable context references;
- `extensions`.

A canonical context reference MUST contain a stable `packet_id`. It MAY also preserve authoring metadata such as `depth` or `agent`.

Relative Lattice syntax such as `↑2` is authoring sugar. Before a packet is serialized as canonical JSON for storage, replay, signing, hashing, or inter-agent transport, the reference MUST be resolved to a stable packet identifier or compilation MUST fail with an unresolved-context diagnostic.

Context MUST NOT implicitly grant or strengthen permissions.

## 9. Confidence (`κ`)

Canonical packet-level confidence is a JSON number in `[0,1]`.

It is REQUIRED. Producers that do not have a meaningful confidence estimate MUST use `1.0` only when confidence represents certainty of faithful encoding rather than certainty of truth; otherwise they SHOULD use a documented conservative value and record interpretation in evidence or extensions.

Relation-specific confidence MAY be expressed on an individual relation.

Canonical serialization rules for numeric bytes are specified separately from semantic shape; semantic validators MUST reject values outside `[0,1]`.

## 10. Permissions (`Π`)

Permissions represent **requested authority**, never authority itself.

The canonical representation uses orthogonal capabilities and constraints rather than a total privilege ladder.

Canonical fields:

- `capabilities` — REQUIRED set drawn from the core capability vocabulary;
- `resources` — REQUIRED array of typed resource identifiers/references;
- `profile` — OPTIONAL convenience profile;
- `forbid` — OPTIONAL set of explicitly forbidden capabilities;
- `require_confirmation` — OPTIONAL boolean;
- `require_review` — OPTIONAL boolean;
- `require_logging` — OPTIONAL boolean;
- `limits` — OPTIONAL object for bounded cost/time/count constraints;
- `authorization_ref` — OPTIONAL opaque host authorization reference;
- `expires_at` — OPTIONAL RFC 3339 date-time;
- `delegation` — OPTIONAL attenuation metadata;
- `extensions` — OPTIONAL namespaced data.

Core capabilities are:

- `read`
- `suggest`
- `prepare`
- `write`
- `execute`
- `commit`

`forbid` always narrows the request. No capability name implies another unless a profile explicitly expands to a capability set.

Convenience profiles are defined in `spec/permissions-safety.md`. Core profiles include `RO`, `SUGGEST`, `PREVIEW`, `RW`, `EXEC`, and `COMMIT`, but profiles are **named bundles**, not ordered privilege levels. Implementations MUST NOT compare them numerically.

A packet requesting side effects without the required explicit capability MUST fail closed at the action-capable host boundary.

Effective authority is always computed by the host from at least:

```text
requested LSTP capabilities
INTERSECT host policy
INTERSECT authenticated principal authority
INTERSECT runtime capability
INTERSECT current resource scope
```

LSTP does not authenticate principals and does not provide a bearer capability token.

## 11. Evidence (`E`)

`evidence` is an ordered array of provenance/support records.

Each evidence item MUST contain:

- `id` — packet-local evidence identifier;
- `source_type` — one of the core provenance constructors.

Core source types are:

- `user`
- `sensor`
- `model`
- `tool`
- `retrieved`
- `inferred`

An evidence item MAY contain:

- `source_ref` — stable source or host reference;
- `input_hash` — content digest when available;
- `span` — source range/location descriptor;
- `supports` — relation IDs or proposition atom IDs supported by this evidence;
- `description` — human-readable note;
- `confidence` in `[0,1]`;
- `extensions`.

Evidence does not prove truth. It records declared support/provenance so that a consumer can inspect and validate it.

The previous `provided`/`needed`/`assumptions`/`challenges` object is not canonical v0.1 JSON.

## 12. Output (`Ω`)

`output` expresses requested response/representation constraints.

`format` is REQUIRED and MUST be one of:

- `NL`
- `LATTICE`
- `JSON`
- `YAML`
- `TABLE`
- `CODE`
- `FILE`
- `NONE`

Optional fields are:

- `schema` — schema/profile identifier;
- `channel` — requested output channel;
- `target` — recipient/consumer/output target identifier;
- `language` — BCP 47 language tag where applicable;
- `max_bytes` — positive integer;
- `requirements` — ordered list of additional declarative constraints;
- `extensions`.

Output target does not grant access to that target. Host policy remains authoritative.

## 13. Envelope metadata

### 13.1 `carrier`

`carrier` is an object describing how the packet was authored, transported, or rendered. Core semantics MUST NOT depend on carrier metadata.

### 13.2 `audit`

`audit` is an object containing transport/validation metadata. A packet's own audit claim MUST NOT substitute for local validation or authorization.

### 13.3 `extensions`

Extensions are optional namespaced objects. A namespace key MUST be explicit and non-empty. Extension payloads MUST be objects.

Extensions MUST NOT override, replace, widen, or reinterpret core fields. In particular, permission-like data in an extension cannot grant authority.

## 14. Vocabulary and namespacing

Core identifiers are ASCII identifiers defined by `spec/vocabulary.md`.

Domain-specific identifiers MUST be namespaced, for example:

```text
slai.route
finance.position
robotics.move
```

A consumer that does not understand a non-core namespaced semantic identifier MAY preserve it but MUST NOT invent semantics for it.

Unknown capability names MUST fail closed.

## 15. Response and outcome semantics

LSTP does not add a ninth Octad field for responses or errors. Responses use the same Octad and the core vocabulary.

`pragmatics.act = "respond"` SHOULD be used for direct protocol responses.

Core outcome relations include:

- `outcome.success`
- `outcome.failure`
- `outcome.partial`
- `outcome.refused`
- `outcome.unsupported`
- `outcome.needs_confirmation`
- `outcome.needs_context`

A response SHOULD reference the originating packet through context and SHOULD identify the request/relation it answers when that is available.

## 16. Compact Lattice carrier

Lattice compact syntax is a carrier/authoring surface. It is not a second semantic contract.

A conforming Lattice compiler MUST produce the canonical Octad shape in this document and the JSON Schema. Any compact construct without one deterministic canonical mapping MUST be rejected rather than guessed.

Macros and unresolved relative context references MAY exist in an authoring phase, but canonical packet serialization MUST contain their resolved semantic result. Macro expansion and relative reference resolution MUST NOT grant permissions.

## 17. Canonicalization and deterministic bytes

Semantic conformance and byte canonicalization are distinct.

v0.1 canonical JSON serialization MUST use a separately testable canonicalization profile before hashes, signatures, or byte-level equality are standardized. The intended baseline is RFC 8785-compatible object/string ordering and escaping with an LSTP numeric profile that avoids cross-language binary floating-point ambiguity.

Until that profile and fixtures are implemented, implementations MUST NOT claim canonical byte equality, semantic fingerprints, or signature interoperability.

## 18. Unicode and identifiers

Protocol identifiers are ASCII. Human-readable string values MAY contain Unicode.

Canonicalization work MUST define NFC treatment for normalized text fields and MUST define rendering/validation behavior for bidirectional control characters and invisible format characters. Implementations MUST reject invalid UTF-8 and unpaired Unicode surrogates.

## 19. Security invariants

A conforming action-capable host MUST:

1. treat permissions as requests, not proof;
2. authenticate principals outside LSTP;
3. fail closed on unknown capabilities or unsupported protocol versions;
4. prevent extensions, evidence, retrieved content, and context from becoming alternate authority channels;
5. prevent delegation from widening authority;
6. revalidate scope and authorization immediately before side effects;
7. apply replay/idempotency/expiry controls appropriate to the host;
8. retain enough audit information to reconstruct the effective authorization decision.

## 20. Conformance levels

A component MAY claim only the levels it actually implements:

- **JSON-structural** — validates the canonical JSON Schema;
- **semantic** — validates references, vocabularies, capability rules, context requirements, and cross-field invariants;
- **Lattice-compiler** — maps supported compact Lattice to canonical Octad deterministically;
- **serialization** — emits and accepts canonical byte representation;
- **permission-aware host** — enforces permission semantics and fail-closed execution boundaries;
- **interoperable implementation** — passes shared conformance vectors against at least one independent implementation.

Passing one level MUST NOT be reported as passing a stronger level.

## 21. v0.1 non-goals

v0.1 does not standardize:

- authentication or identity issuance;
- cryptographic signatures;
- transport encryption;
- a universal ontology;
- a general-purpose logic language;
- model reasoning internals;
- model training procedures;
- a safety policy engine;
- a distributed consensus mechanism.

## 22. Training and release gate

LSTP-derived training data MUST NOT be described as protocol-frozen until:

1. the canonical schema and semantic validator agree with this contract;
2. Lattice compilation is deterministic for the supported subset;
3. canonicalization/numeric rules are frozen;
4. positive and negative conformance vectors exist;
5. permission and evidence validation are implemented;
6. release/readiness tooling reports no unresolved protocol blocker.

The project MAY continue engineering before that point, but MUST keep the distinction between implemented foundation, protocol conformance, and production readiness explicit.
