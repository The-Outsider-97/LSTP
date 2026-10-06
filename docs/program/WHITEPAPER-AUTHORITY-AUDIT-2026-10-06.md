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
