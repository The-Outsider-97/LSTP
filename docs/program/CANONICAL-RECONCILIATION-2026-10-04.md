# LSTP v0.1 canonical reconciliation — 4 October 2026

> **Superseded governance record.** The spec-first authority decision below was reversed by the Whitepaper-first audit of 6 October 2026. This file is retained as design history, not current authority.

## Purpose

This pass resolves the split-contract problem recorded in the 22 September 2026 audit. The project previously had two incompatible artifacts both described as v0.1: the Whitepaper model and a subordinate schema/specification model.

This reconciliation makes one implementation-facing v0.1 contract explicit and machine-checkable. It does **not** claim that the reference implementation is complete or that the protocol is training/production ready.

## Governance decision

Implementation and conformance authority is now:

1. `spec/CANONICAL-v0.1.md`;
2. `spec/octad_schema.json`;
3. grammar/operator/permission/vocabulary profiles where consistent with 1–2;
4. conformance fixtures/tests;
5. reference implementation;
6. Whitepaper as informative rationale/history/research framing.

The earlier PDF-first hierarchy is retired for implementation decisions because it made machine-readable artifacts permanently subordinate to unresolved prose contradictions. The Whitepaper SHOULD receive a publication revision documenting this governance transition.

## Canonical semantic decisions

### Octad

The Octad remains exactly eight required semantic domains:

- pragmatics;
- atoms;
- relations;
- context;
- confidence;
- permissions;
- evidence;
- output.

Envelope identity/version/carrier/audit/extensions remain outside semantic Octad equality.

### Pragmatics

Canonical pragmatics uses required `act`, optional `goal`, `modifiers`, `register`, and numeric `urgency` in `[0,1]`.

The old subordinate `intent/action/force/tone` representation is legacy migration input, not a canonical alias set.

### Atoms

Atoms are a canonical array of typed `aN` records. Scalar shorthand and free identifier-keyed atom maps are not canonical v0.1 JSON.

### Relations

Relations use `type` plus ordered `arguments`. Legacy subject/predicate/object is migration-only.

### Context

`thread_id` is required. Canonical stored/transmitted context references require a stable `packet_id`. Relative `↑N` references remain compact-authoring sugar and must resolve before canonical storage/replay/inter-agent transport.

### Confidence

Packet confidence is a required number in `[0,1]`. Relation-specific confidence may be attached to a relation.

### Permissions

The Whitepaper mode ladder and subordinate lowercase workflow modes are replaced by one orthogonal requested-capability model:

- `read`;
- `suggest`;
- `prepare`;
- `write`;
- `execute`;
- `commit`.

Named profiles `RO`, `SUGGEST`, `PREVIEW`, `RW`, `EXEC`, and `COMMIT` remain ergonomic bundles but are not numerically ordered and never grant authority by themselves.

Permissions also support typed resources, `forbid`, confirmation/review/logging requirements, limits, authorization references, expiry, delegation metadata, and extensions.

### Evidence

Evidence is an ordered provenance array. Each item has `id` and `source_type` from:

- user;
- sensor;
- model;
- tool;
- retrieved;
- inferred.

The previous `provided/needed/assumptions/challenges` object is retired from canonical v0.1.

### Output

Canonical formats are `NL`, `LATTICE`, `JSON`, `YAML`, `TABLE`, `CODE`, `FILE`, and `NONE`, with optional schema/channel/target/language/max-byte/requirements constraints.

### Responses

Responses do not add a ninth Octad field or separate packet model. `pragmatics.act=respond` and standard `outcome.*` relations represent success, failure, partial completion, refusal, unsupported requests, confirmation requirements, and missing context.

## Compact Lattice

Compact Lattice remains a carrier/authoring syntax. It is no longer allowed to function as an independent semantic contract.

A compiler must either:

- map supported syntax deterministically into the canonical Octad; or
- reject the input with a deterministic diagnostic.

Undefined or ambiguous semantics must not be guessed.

## Canonicalization

This pass intentionally separates semantic reconciliation from byte canonicalization. Canonical JSON bytes, Unicode normalization, and numeric formatting remain implementation blockers.

The intended next step is an RFC 8785-compatible serialization baseline with an LSTP numeric profile and explicit Unicode rules, covered by cross-language conformance vectors.

## Security implications

The reconciliation preserves and strengthens fail-closed boundaries:

- permissions are requests, not bearer authority;
- resources are explicit typed records rather than free-form scope strings;
- extensions cannot override core fields;
- untrusted content cannot create permission authority;
- delegation may only narrow authority;
- unresolved context cannot be used for unsafe execution;
- unsupported versions and unknown capabilities fail closed.

## Legacy compatibility

Legacy draft packets may be read by migration tooling, but migration is not canonical v0.1 validation.

Migration tooling must surface ambiguity/loss and must never silently coerce legacy permission modes into stronger canonical capabilities.

## Readiness effect

The following earlier blocker class is closed by design decision on this branch:

- competing v0.1 semantic/schema/permission/evidence contracts.

Readiness remains **false** because implementation and evidence are still missing:

- parser/AST/compiler;
- semantic validator;
- canonical serializer/numeric/Unicode profile;
- permission-aware host validator;
- conformance vectors and hostile cases;
- independent second implementation;
- SLAI adapter;
- Whitepaper publication synchronization;
- final release/pre-training audit.

## Next implementation order

1. Update semantic model classes from generic JSON-value containers to typed canonical domain objects without coupling them to SLAI.
2. Implement structural JSON packet validation against the reconciled schema.
3. Implement semantic/reference validation and deterministic diagnostics.
4. Implement Lattice lexer/parser/AST and compact-to-Octad compiler against the canonical contract.
5. Resolve/compile relative context references into stable packet IDs.
6. Implement permission/resource validation and attenuation rules.
7. Freeze canonical JSON numeric/Unicode bytes and add fixtures.
8. Add positive/negative/hostile/round-trip conformance vectors.
9. Build a small independent second implementation and run the same vectors.
10. Integrate into SLAI as a pinned independent package/submodule and make the Language Agent emit/consume canonical Octads.

## Explicit non-claims

This reconciliation does not prove:

- lower hallucination rates;
- token savings;
- latency savings;
- security superiority;
- interoperability;
- production readiness;
- model-training readiness.

Those claims require implementation and measurement.
