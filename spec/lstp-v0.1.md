# Lattice Semantic Transport Protocol (LSTP) v0.1

Status: normative companion index.

The canonical v0.1 protocol contract is now defined in:

- `spec/CANONICAL-v0.1.md` — semantic and behavioral contract;
- `spec/octad_schema.json` — canonical JSON shape;
- `spec/grammar.ebnf` — compact Lattice carrier grammar;
- `spec/operator-table.md` — operator semantics;
- `spec/permissions-safety.md` — permission/safety profile;
- `spec/vocabulary.md` — core vocabulary.

This file intentionally no longer carries an independent packet model. The previous version of this document conflicted with the Whitepaper and JSON Schema and was one of the causes of the split v0.1 contract recorded in the 22 September 2026 audit.

## Normative rules

1. The semantic Octad has exactly eight required canonical domains: `pragmatics`, `atoms`, `relations`, `context`, `confidence`, `permissions`, `evidence`, and `output`.
2. Envelope identity/version/carrier/audit/extensions are outside Octad semantic equality.
3. Canonical JSON MUST satisfy `spec/octad_schema.json`.
4. Compact Lattice is an authoring/carrier syntax. It MUST compile deterministically to the canonical Octad or fail with a diagnostic.
5. Permission declarations request authority only; the host independently authorizes effects.
6. Extensions MUST NOT override core semantics or become alternate authority channels.
7. Relative context authoring references MUST resolve to stable packet IDs before canonical storage/replay/inter-agent transport.
8. Unsupported protocol versions and unknown permission capabilities fail closed.
9. No implementation may claim canonical byte equality until the serialization/numeric profile and conformance vectors are frozen.
10. Training data MUST NOT be called protocol-frozen until the readiness gate defined by `spec/CANONICAL-v0.1.md` is satisfied.

## Conformance

Conformance claims are scoped. A component may claim JSON-structural, semantic, Lattice-compiler, serialization, permission-aware-host, or interoperable-implementation conformance only for levels it actually passes.

The reference implementation is not normative by itself. Where code and this specification disagree, the specification and machine-readable normative artifacts win and the code must be corrected.

## Historical note

Earlier revisions used a competing schema based on fields such as `intent`, `action`, free identifier-keyed atoms, subject/predicate/object relations, lowercase scalar permission modes, and a `provided`/`needed` evidence object. Those shapes are legacy draft material and are not canonical v0.1 after the 4 October 2026 reconciliation pass.

Migration tools MAY read such packets, but they MUST label the operation as migration rather than v0.1 conformance and MUST surface lossy or ambiguous mappings.
