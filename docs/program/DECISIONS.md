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

**Status:** accepted defect classification; resolution blocked on grammar edit/review.

**Authority:** Whitepaper §7.10 and operator-table distinction between unary exclusion and signed scope values.

In the current EBNF, `unary_expression` may consume `-` while `primary_expression` may also consume a `signed_number` or `signed_period`. Inputs such as `-1` therefore admit competing structural interpretations. A deterministic parser must not choose one silently.

The eventual grammar should make numeric sign ownership lexical/syntactic and reserve unary exclusion for operands for which exclusion is actually defined. Until that rule is explicit, parser work must retain a failing/blocked conformance case for the ambiguity.

## D-009 — Confidence attachment requires one owner

**Status:** accepted defect classification; resolution blocked on grammar edit/review.

The compact grammar permits confidence on a `postfix_expression`, while `claim_clause` also permits a trailing confidence clause. This can make constructs such as `claim: x %0.5` structurally ambiguous.

The grammar must assign confidence to exactly one syntactic owner in each position. The compiler must not duplicate, merge, or prefer confidence values without a normative rule. Duplicate packet-level confidence declarations must receive a deterministic conflict rule before compilation is enabled.

## D-010 — Envelope metadata remains outside the Octad

**Status:** accepted from authority.

Whitepaper Figure 2 and §§6/8 distinguish semantic Octad content from protocol/version, carrier/transport, identity, and audit-envelope metadata. Python convenience must not add envelope fields to Octad equality. `thread_id` and other context semantics remain inside `C` where the Whitepaper requires them; transport metadata remains outside.

A future canonical model therefore needs separate `Octad` and envelope/carrier types. Round-trip tests must state whether they compare semantic Octad equality, envelope equality, normalized carrier syntax, or bytes.

## D-011 — Permissions are requested authority and are never normalized by privilege ranking

**Status:** accepted from authority.

The canonical modes named by the Whitepaper are `RO`, `SUGGEST`, `PREVIEW`, `RW`, `EXEC`, and `COMMIT`. They are requested modes, not capability tokens and not a total privilege lattice. Case folding, aliases, or conversion from unsupported subordinate modes must not silently create a canonical mode.

Effective authority is always the intersection of requested LSTP authority, host policy, and runtime capability. `FORBID`, scope, limits, confirmation, review, and logging constraints must survive carrier conversion. Unsupported or conflicting authority declarations fail closed until a normative conflict rule exists.

## D-012 — Training freeze is blocked by canonical-contract conflicts

**Status:** active gate.

No LSTP-derived training corpus may be described as protocol-frozen while SPEC-001 through SPEC-004 remain unresolved. In particular, generated data must not depend on an implementation-specific choice for Octad field shape, compact grammar mapping, permission modes, identity placement, or serialization equality.

The readiness gate may be cleared only after the relevant authoritative requirements have implementation and independent conformance evidence, not merely after code exists.
