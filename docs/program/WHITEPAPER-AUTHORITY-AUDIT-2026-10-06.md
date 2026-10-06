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
