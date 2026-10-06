# Whitepaper-first authority audit — 6 October 2026

## Purpose

This audit restores the active project hierarchy: Whitepaper first, then README,
then technical specifications, then implementation.

The October reconciliation temporarily inverted that hierarchy. This document
records the resulting contract differences before any additional core protocol
features are added.


## Executive finding

The implementation is materially more complete than it was at the Whitepaper's
analyzed commit, but the October reconciliation changed several Level-1 protocol
decisions instead of merely implementing them.

The current runtime is therefore an engineering candidate, not a frozen LSTP
v0.1 reference implementation, until the conflicts below are resolved
Whitepaper-first.

## Compatibility matrix

| Area | Whitepaper Level-1 requirement | Current repository | Status |
|---|---|---|---|
| Octad | Eight domains: pragmatics, atoms, relations, context, confidence, permissions, evidence, output | Same eight domains | ALIGNED |
| Envelope | Identity/version/carrier/audit outside Octad semantics | Outside semantic equality | ALIGNED |
| Atoms | Typed aN atoms and core kinds | Same model | ALIGNED |
| Relations | Type plus ordered arguments; atom/special refs | Same model | ALIGNED |
| Confidence | Scalar in [0,1] | Same model | ALIGNED |
| Evidence | user/sensor/model/tool/retrieved/inferred constructors | Same source vocabulary in typed records | SUBSTANTIALLY ALIGNED |
| Output | NL/LATTICE/JSON/YAML/TABLE/CODE/FILE/NONE | Same formats | ALIGNED |
| Context thread | thread_id required | Same | ALIGNED |
| Relative context | upward-depth refs require host resolution | Compiler fails closed until stable packet ID is resolved | ALIGNED |
| Canonical equality | Semantic comparator required; bytes are separate | Semantic equality plus canonical byte profile | COMPATIBLE ADDITION |
| Pragmatics | Required type; permits speech_act, modifiers, goal, register, urgency | Required act; no core speech_act | CONFLICT |
| Permissions | Canonical six MODE values with scope/forbid/limits/confirm/review/log | Canonical capabilities/resources plus non-ordered profiles | CONFLICT |
| Permission order | RO <= SUGGEST <= PREVIEW <= RW <= EXEC <= COMMIT | Profiles explicitly non-ordered | CONFLICT |
| Canonical Lattice | Ordered Octad core plus atomic/framed/named/stream packet forms | Compact directive/operator grammar only | CONFLICT / MISSING |
| Context fields | Includes parent packet, timezone and window concepts | Uses parent_id; timezone/window absent | PARTIAL CONFLICT |
| Host authorization | Requested permission intersected with host authority | Stronger principal/policy/runtime/resource intersection | COMPATIBLE HOST HARDENING |
| Replay storage | Host-side operational concern | ReplayStore, ReplayGuard, SQLite adapter | COMPATIBLE HOST HARDENING |


## Blocking conflicts

### GOV-PRAG — canonical pragmatics changed

Whitepaper section 6.1 requires a pragmatic `type` and permits a separate
speech act, modifiers, goal, register and urgency. Section 7.3 names canonical
Lattice entries including `TYPE` and `SPEECH_ACT`.

The current canonical contract instead requires `act` and has no core
`speech_act` field.

This is not a spelling-only difference. The Whitepaper treats TYPE and
SPEECH_ACT as distinct semantic entries. Any migration from the October
candidate representation must therefore be explicit and may be lossy.

Freeze consequence: training data must not be generated against the current
act-only shape as though it were authoritative v0.1.

### GOV-PERM — canonical permission protocol was replaced

Whitepaper sections 6.6 and 10 define requested authority using six modes:
RO, SUGGEST, PREVIEW, RW, EXEC and COMMIT. They are conceptually ordered by
increasing operational authority while scope remains independent.

The October reconciliation replaced this wire representation with orthogonal
capability arrays and explicitly declared the six profile names non-ordered.

The capability-intersection engine is useful host-security machinery, but it is
not the same canonical wire protocol.

Resolution direction: retain the authorization engine internally where safe,
but derive concrete host capabilities from Whitepaper mode, scope and forbids
under one documented mapping.

### GOV-GRAM — canonical Lattice packet grammar was dropped

Whitepaper section 7 defines canonical Lattice as an ordered Octad text form and
explicitly identifies atomic, framed, named and streamed packet forms.

The current `spec/grammar.ebnf` instead defines the compact directive/operator
surface and contains no canonical Octad packet productions.

Compact syntax remains useful, but under the Whitepaper it must be a separate
carrier/profile compiled deterministically into canonical semantics.

Resolution direction: restore the canonical ordered-Octad grammar and preserve
the compact grammar as a separately named profile.

### GOV-CTX — context field drift

The Whitepaper names packet relationship/context concepts including parent
packet identity, timezone and window. The current canonical artifacts use
`parent_id` and omit timezone/window.

The exact Level-1 field names and semantics must be restored or explicitly
revised; aliases must not hide the conflict.

### GOV-EXT — additive security fields promoted into core

The implementation added authorization references, expiry, delegation metadata
and typed resource structures. These are defensible security features, but the
Whitepaper does not establish all of them as core v0.1 permission fields.

They may remain host mechanisms, namespaced extensions or a future revision.
They must not silently redefine Level-1 v0.1.


## Engineering work that can be retained

This audit does not recommend discarding the current implementation wholesale.
The following components can largely survive the Whitepaper reconciliation:

- bounded JSON input and canonical Unicode/number handling;
- typed atom, relation, evidence and output implementations;
- diagnostics infrastructure;
- semantic reference validation;
- context-resolution fail-closed behavior;
- canonical byte serializer architecture;
- host authorization intersection, after adapting its protocol input mapping;
- delegation/replay implementations as host/security profiles;
- ReplayStore abstraction and SQLite implementation;
- RFC3339 and BCP47 validation;
- test, CI, property-testing and adversarial-testing infrastructure.

The principal rewrite is concentrated at the semantic contract boundary:
pragmatics, permissions, canonical Lattice grammar and selected context fields.

## Ordered remediation plan

### Phase A — governance lock

1. Restore Whitepaper > README > spec > implementation authority in normative
   headers.
2. Mark October canonical/schema/grammar/permission artifacts as candidate
   artifacts under reconciliation.
3. Keep `training_ready=false` and `contract_reconciled=false`.

### Phase B — canonical semantic repair

1. Define the Whitepaper-compliant pragmatics shape and vocabulary.
2. Restore the Whitepaper permission mode/scope representation.
3. Define a deterministic mode-to-host-capabilities mapping without changing
   the wire contract.
4. Restore missing Whitepaper context fields/names.
5. Update schema, typed model, serializer/deserializer and semantic validator
   together.

### Phase C — grammar repair

1. Restore canonical ordered-Octad Lattice grammar.
2. Preserve compact operator syntax as a separately named profile.
3. Implement canonical parsing plus compact-to-canonical compilation.
4. Add atomic/framed/named/stream fixtures and round-trip tests.

### Phase D — migration and conformance

1. Define explicit migration handling for October candidate packets that use
   act/capabilities/resources.
2. Surface loss or ambiguity; never silently coerce.
3. Expand positive, negative and hostile vectors.
4. Re-run all permission-preservation and authorization tests against the
   restored Whitepaper contract.

### Phase E — freeze evidence

1. Independent second implementation.
2. Shared canonical-byte and semantic round-trip vectors.
3. SLAI integration.
4. Whitepaper/README/spec/runtime synchronization audit.
5. Clean CI/release evidence.
6. Only then set `contract_reconciled=true` and evaluate
   `training_ready=true`.

## Immediate readiness judgment

The repository has a strong engineering core, but the contract boundary is not
currently freeze-safe. Pre-training remains blocked until GOV-PRAG, GOV-PERM,
GOV-GRAM and GOV-CTX are resolved and the resulting contract passes the
conformance suite.

Production hardening may continue only where it is protocol-neutral. New core
semantic features should not be added until the authority conflict is closed.


## Phase B implementation status — 6 October 2026

The Whitepaper semantic repair has now been implemented as a candidate across the
schema, typed model, canonical serializer/decoder, semantic validator, compact
Lattice compiler, host authorization boundary, tests, conformance vectors, and
Level-3 permission/vocabulary documentation.

Implemented repairs:

- **GOV-PRAG:** canonical pragmatics now uses required `type` and distinct
  optional `speech_act`; the October `act` field fails closed.
- **GOV-PERM:** canonical packet permissions now use the six Whitepaper modes,
  explicit `scope`, subtractive `forbid`, limits and
  confirmation/review/logging constraints. `capabilities`, `resources`, and
  `profile` are no longer canonical packet fields.
- **Host enforcement:** the six wire modes are translated deterministically into
  concrete capabilities only at the authorization boundary; principal, policy,
  runtime and resource intersections remain intact.
- **GOV-CTX:** canonical context now restores `parent_packet_id`, `timezone`,
  and `window` while retaining stable packet-reference resolution.
- October candidate semantic fields are rejected rather than silently aliased or
  migrated by the canonical decoder/model boundary.

Still open:

- **GOV-GRAM:** the canonical ordered-Octad atomic/framed/named/stream Lattice
  grammar remains to be restored. The current parser/compiler covers the compact
  operator carrier only.
- **GOV-EXT:** final core-vs-extension/revision status for
  `authorization_ref`, `expires_at`, and delegation metadata remains open.
- **PHASEB-VERIFY:** the repaired candidate requires successful engineering and
  conformance evidence before these repairs are treated as merged/verified.

Accordingly, `contract_reconciled` and `training_ready` remain false.


## Phase C implementation status — 6 October 2026

The Whitepaper canonical Lattice grammar has now been restored as a candidate
without deleting or overloading the existing compact operator carrier.

Implemented:

- `spec/grammar.ebnf` now defines the ordered
  `π | A | R | C | κ | Π | E | Ω` canonical carrier;
- atomic, framed, named, and named-stream packet productions are explicit;
- `spec/compact-grammar.ebnf` preserves the operator-oriented authoring carrier
  as a separate profile;
- `parse_canonical_lattice()` parses canonical packets directly into typed
  Octads while preserving named-packet labels only as carrier metadata;
- the exact Whitepaper example is covered by executable parser tests;
- canonical field order, duplicate fields, obsolete October permission fields,
  stream separators, and compact/canonical profile separation have negative
  regression coverage.

Phase C deliberately does not invent envelope identifiers from Lattice packet
labels, does not assign undocumented atom-constructor aliases, and does not
silently accept compact syntax as canonical syntax.

**PHASEC-VERIFY** remains open until executable engineering/conformance evidence
is available. **GOV-EXT** remains independent and unresolved.

Accordingly, `contract_reconciled` and `training_ready` remain false.
