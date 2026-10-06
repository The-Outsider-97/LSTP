# Protocol decision register

This register records hardening decisions that affect conformance work. It is not a substitute for the authoritative `docs/LSTP_Whitepaper.pdf`. Decisions that would change authoritative semantics remain blocked pending an explicit Whitepaper revision.

## D-007 — Two Lattice surfaces must not be conflated

**Status:** resolved and implemented in v0.1.

**Authority:** Whitepaper §§5.2 and 7.1–7.10.

The Whitepaper describes both (a) an ordered canonical Octad text form and
(b) compact operator notation. v0.1 now keeps these as separate carrier
profiles: `spec/grammar.ebnf` defines canonical ordered-Octad Lattice and
`spec/compact-grammar.ebnf` defines the compact operator surface.

Canonical and compact parsing/compilation have separate APIs and tests. Compact
input does not prove canonical acceptance, and unmappable syntax fails rather
than inventing Octad semantics.

## D-008 — Signed numeric ambiguity is a grammar defect, not an AST choice

**Status:** accepted defect classification; strict-core grammar corrected, parser conformance still pending.

**Authority:** Whitepaper §7.10 and operator-table distinction between unary exclusion and signed scope values.

The original EBNF allowed `unary_expression` to consume `-` while `primary_expression` could also consume a `signed_number` or `signed_period`. Inputs such as `-1` therefore admitted competing structural interpretations. The strict-core grammar now keeps signed numeric/period values in scope syntax and reserves general-expression `-` for unary exclusion. Parser work must preserve that ownership rather than reintroducing lexical ambiguity.

## D-009 — Confidence attachment requires one owner

**Status:** accepted defect classification; strict-core grammar corrected, compiler conflict rules still pending.

The original compact grammar permitted confidence on a `postfix_expression`, while `claim_clause` also permitted a trailing confidence clause. This made constructs such as `claim: x %0.5` structurally ambiguous. Strict v0.1 now exposes numerical confidence only at packet level. The compiler must not duplicate, merge, or infer term/relation/claim confidence. Duplicate packet-level confidence declarations still require a deterministic conflict rule before compilation is enabled.

## D-010 — Envelope metadata remains outside the Octad

**Status:** accepted from authority.

Whitepaper Figure 2 and §§6/8 distinguish semantic Octad content from protocol/version, carrier/transport, identity, and audit-envelope metadata. Python convenience must not add envelope fields to Octad equality. `thread_id` and other context semantics remain inside `C` where the Whitepaper requires them; transport metadata remains outside.

The reference model therefore keeps separate `Octad` and `PacketEnvelope` types. Round-trip tests must state whether they compare semantic Octad equality, envelope equality, normalized carrier syntax, or bytes.

## D-011 — Permission modes have conceptual order without widening scope

**Status:** accepted from Level-1 authority; October capability-wire replacement is superseded.

**Authority:** Whitepaper §§6.6 and 10.1–10.4.

The canonical modes are `RO`, `SUGGEST`, `PREVIEW`, `RW`, `EXEC`, and
`COMMIT`. The Whitepaper explicitly presents the conceptual order:

```text
RO <= SUGGEST <= PREVIEW <= RW <= EXEC <= COMMIT
```

The order expresses increasing operational authority. It does **not** widen
resource scope, remove forbids, bypass limits, or satisfy confirmation/review/
logging requirements.

The host may translate a requested mode into concrete internal capabilities for
authorization, but that translation is an implementation mechanism rather than
a replacement wire representation.

Effective authority remains the intersection of the requested Whitepaper
permission, scope/constraints, authenticated/local policy and runtime capability.
Unsupported or conflicting declarations fail closed.

## D-012 — Training freeze requires a reconciled contract plus independent evidence

**Status:** contract conflict resolved; release evidence gate remains active.

The Whitepaper-first v0.1 contract is now reconciled across Octad shape,
canonical/compact Lattice, permission modes, context, envelope placement, and
canonical serialization. `docs/program/readiness.json` records
`contract_reconciled=true`.

Training readiness still requires executable engineering checks, adversarial
conformance evidence, independent interoperability, SLAI integration,
publication synchronization, and final release sign-off. Code existence alone
is not sufficient.

## D-013 — Canonical model values use a strict JSON-value boundary

**Status:** accepted implementation hardening; no byte-canonical serialization claim.

The canonical Python containers accept only values representable by the JSON data model: null, booleans, finite numbers, strings, arrays, and objects with string keys. Host-language mappings with non-string keys are rejected rather than coerced because coercion can collapse distinct keys (for example `1` and `"1"`). NaN and positive/negative infinity are rejected because they are outside the JSON number model and make cross-carrier equality non-portable.

This decision constrains the implementation boundary only. It does not define number precision, Unicode normalization, member ordering, textual formatting, or canonical bytes; those remain part of the unresolved serialization profile. Diagnostics include the value path so malformed nested data can be rejected deterministically without echoing payload content.

## D-014 — Evidence constructors are normative vocabulary with Level-3 structural refinement

**Status:** resolved for v0.1.

**Authority:** Whitepaper evidence/provenance requirements and the canonical
JSON Schema.

The Whitepaper establishes evidence as an Octad domain and the source types
`user`, `sensor`, `model`, `tool`, `retrieved`, and `inferred`.
The Level-3 schema supplies the concrete JSON item structure
(`id`, `source_type`, optional provenance/support metadata) as a technical
refinement that does not contradict the Level-1 semantics.

Carrier mappings MUST preserve source type and supported metadata when the
carrier defines syntax for it. Canonical Lattice currently fails closed on rich
evidence metadata whose text syntax is not frozen rather than dropping it.

## D-015 — Envelope versions and extensions fail closed

**Status:** accepted implementation hardening; no new semantic vocabulary introduced.

**Authority:** Whitepaper envelope/version boundary and extension rules; subordinate version rule is consistent with the authoritative fail-closed compatibility principle.

The v0.1 reference model accepts protocol version `0.1` only. Empty, future, alias, or convenience labels such as `latest` are rejected rather than interpreted as compatible. Version negotiation is not inferred by the model.

Envelope `carrier`, `audit`, and `extensions` values are required to be JSON objects at the Python model boundary. Extension entries must use explicit non-empty top-level namespace keys, and each namespace maps to an object. The model preserves such data without assigning semantic meaning to it.

Extensions are never an alternate permission channel. An extension payload containing action-like or permission-like data does not modify `Octad.permissions`, does not grant authority, and is not promoted into a core field. Unknown extension meaning remains opaque to the core implementation; execution that depends on it requires separate host understanding and validation.

This decision deliberately does not define a namespace registry, extension naming ontology, carrier-specific preservation policy, or canonical extension bytes. Those remain specification/serialization work rather than assumptions in the model.


## D-016 — GOV-EXT security metadata remains outside canonical v0.1

**Status:** accepted and implemented.

**Authority:** Whitepaper §§6.6 and 10; Whitepaper-first hierarchy.

`authorization_ref`, permission expiry, and delegation identity bindings are
useful production security controls but are not Level-1 canonical permission
fields. Canonical v0.1 therefore rejects them inside `permissions`.

The reference host preserves the safeguards through trusted
`HostAuthorizationContext` and `HostDelegationBinding` inputs supplied
outside the packet. This prevents sender-controlled packet data from becoming a
trusted authorization channel while retaining expiry, authorization-reference,
and delegation-attenuation enforcement.

A future protocol version may standardize additional wire fields only through an
explicit versioned change. v0.1 training data MUST use only the Whitepaper core
permission fields.
