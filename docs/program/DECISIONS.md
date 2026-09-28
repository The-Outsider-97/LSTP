# Protocol decision register

This register records hardening decisions that affect conformance work. It is not a substitute for the authoritative `docs/LSTP_Whitepaper.pdf`. Decisions that would change authoritative semantics remain blocked pending an explicit Whitepaper revision.

## D-007 — Two Lattice surfaces must not be conflated

**Status:** accepted engineering interpretation; no protocol semantics changed.

**Authority:** Whitepaper §§5.2 and 7.1–7.10.

The Whitepaper describes both (a) an ordered canonical Octad text form and (b) compact operator notation. The current `spec/grammar.ebnf` only defines the compact notation, despite its status text and documentation implying that it is the complete canonical Lattice grammar.

Until the grammar is reconciled, implementations MUST NOT claim that acceptance by the compact grammar proves acceptance of canonical LSTP v0.1, and MUST NOT infer missing Octad fields from compact syntax without an explicit normative mapping.

Required follow-up before parser conformance can be marked ready:

1. Add explicit canonical productions for the ordered eight-field Octad and the atomic/framed/named forms described by the Whitepaper.
2. Define the stream separator rather than guessing one; the Whitepaper names `packet_sep` but does not supply its terminal.
3. Define a normative compact-to-canonical mapping for every supported compact construct.
4. Give ambiguous or unmappable compact input a deterministic diagnostic instead of synthesizing semantics.
5. Test canonical and compact surfaces independently before testing their equivalence.

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

## D-011 — Permissions are requested authority and are never normalized by privilege ranking

**Status:** accepted from authority.

The canonical modes named by the Whitepaper are `RO`, `SUGGEST`, `PREVIEW`, `RW`, `EXEC`, and `COMMIT`. They are requested modes, not capability tokens and not a total privilege lattice. Case folding, aliases, or conversion from unsupported subordinate modes must not silently create a canonical mode.

Effective authority is always the intersection of requested LSTP authority, host policy, and runtime capability. `FORBID`, scope, limits, confirmation, review, and logging constraints must survive carrier conversion. Unsupported or conflicting authority declarations fail closed until a normative conflict rule exists.

## D-012 — Training freeze is blocked by canonical-contract conflicts

**Status:** active gate.

No LSTP-derived training corpus may be described as protocol-frozen while SPEC-001 through SPEC-004 remain unresolved. In particular, generated data must not depend on an implementation-specific choice for Octad field shape, compact grammar mapping, permission modes, identity placement, or serialization equality.

The readiness gate may be cleared only after the relevant authoritative requirements have implementation and independent conformance evidence, not merely after code exists.

## D-013 — Canonical model values use a strict JSON-value boundary

**Status:** accepted implementation hardening; no byte-canonical serialization claim.

The canonical Python containers accept only values representable by the JSON data model: null, booleans, finite numbers, strings, arrays, and objects with string keys. Host-language mappings with non-string keys are rejected rather than coerced because coercion can collapse distinct keys (for example `1` and `"1"`). NaN and positive/negative infinity are rejected because they are outside the JSON number model and make cross-carrier equality non-portable.

This decision constrains the implementation boundary only. It does not define number precision, Unicode normalization, member ordering, textual formatting, or canonical bytes; those remain part of the unresolved serialization profile. Diagnostics include the value path so malformed nested data can be rejected deterministically without echoing payload content.
