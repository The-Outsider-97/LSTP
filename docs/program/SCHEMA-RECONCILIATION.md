# Canonical Octad schema reconciliation — 30 September 2026

Status: engineering reconciliation record; it does not supersede `docs/LSTP_Whitepaper.pdf`.

Authority order: Whitepaper PDF > root README guidance > normative technical artifacts > implementation.

## Purpose

This record prevents `spec/octad_schema.json` from becoming de facto protocol law while it still conflicts with the authoritative Octad. The current schema remains a draft technical artifact until every blocking row below is reconciled and covered by positive and negative fixtures.

## Field-by-field comparison

| Domain | Authoritative contract | Current schema state | Disposition |
|---|---|---|---|
| Envelope | Identity, protocol/version, carrier/transport and audit metadata are outside the semantic Octad. | `id`, `version`, `carrier`, and `audit` are top-level siblings of Octad fields. | Structurally tolerable as a packet envelope, but the schema title/description and equality rules must keep envelope metadata distinct from Octad semantics. |
| `pragmatics` (`π`) | Requires `type`; may represent speech act, modifiers, goals, register and urgency; urgency is numeric in `[0,1]`. | Uses optional `intent`, `action`, `force`, `tone`; urgency is an arbitrary string. | **BLOCKING**. Do not coerce aliases. Replace only after canonical field names/cardinalities are fixed from the Whitepaper. |
| `atoms` (`A`) | Typed semantic units; IDs follow `aN`; kinds include entity, concept, value, event, time, location, resource, proposition and unknown; optional role/datatype/language/attributes/value. | Free identifier-keyed map with open `kind` strings and scalar shorthand. | **BLOCKING**. Current shape does not enforce canonical atom identity or kind vocabulary. |
| `relations` (`R`) | Relation has a type and arguments; arguments reference atoms or allowed special references `SELF`, `NOW`, `USER`, `SYSTEM`; optional relation confidence/attributes. | Subject/predicate/object-oriented object with optional `arguments`; arbitrary endpoints are accepted. | **BLOCKING**. Do not silently translate SPO relations into canonical argument relations. |
| `context` (`C`) | Requires `thread_id`; may include packet/parent/conversation IDs, turn, temporal/location data, bindings, references, speaker and audience. | `thread_id` is absent; `refs`, `prior_message_ref`, `variables`, and `frame` are optional. | **BLOCKING**. A packet cannot be certified canonical without the required thread anchor. |
| `confidence` (`κ`) | Packet-level number in `[0,1]`. | Object with optional `type`, `value`, `required`, `approximate`. | **BLOCKING**. Wrapper-object compatibility must not be treated as canonical v0.1. |
| `permissions` (`Π`) | Requested authority only. Modes: `RO`, `SUGGEST`, `PREVIEW`, `RW`, `EXEC`, `COMMIT`; may express scope, forbids, cost/time limits, confirmation, review and logging requirements. | Draft lower-case modes include `readonly`, `sandbox`, `confirm`, `auto`, `advisory`, and `reply_or_explain_only`; canonical forbid/review/log fields are absent. | **CRITICAL BLOCKER**. No aliases or privilege-order coercion. Unknown/noncanonical modes fail closed. |
| `evidence` (`E`) | Provenance-like support; Lattice identifies user, sensor, model, tool, retrieved and inferred source constructors. | Uses `provided`, `needed`, `assumptions`, `challenges`; source vocabulary is open. | **BLOCKING / FAIL-CLOSED DISPOSITION RECORDED (D-014)**. The authoritative source vocabulary is known, but canonical JSON cardinality/object shape is not uniquely specified. Do not translate the subordinate shape into canonical evidence. Evidence conformance remains blocked until authority is clarified. |
| `output` (`Ω`) | Formats: `NL`, `LATTICE`, `JSON`, `YAML`, `TABLE`, `CODE`, `FILE`, `NONE`; optional schema/channel/target/language/max-byte constraints. | Arbitrary string `format`, zoom, requirements. | **BLOCKING**. Canonical format vocabulary is not enforced and several authoritative constraints are absent. |

## Safety rules for reconciliation

1. Do not accept a draft field merely because it can be mapped heuristically to an authoritative field.
2. Do not add compatibility aliases to permission modes. Permission conversion is security-sensitive and must be explicit and fail closed.
3. Do not claim JSON Schema conformance as semantic conformance. Reference resolution, permission policy, extension ownership and carrier equivalence require additional validation.
4. Do not generate training corpora from packets certified by the current draft schema.
5. Do not implement evidence JSON details that the authoritative source does not actually define. D-014 makes this an explicit conformance blocker rather than an invitation to choose an implementation-specific shape.
6. Any future schema replacement must arrive with positive and negative fixtures and tests derived from this matrix rather than from the implementation alone.

## Machine-checkable drift gate

`tools/check_schema_contract.py` checks high-confidence authoritative invariants that can be established without inventing missing mappings. It intentionally fails against the current schema until the blocking drift is removed. This is a readiness gate, not a general JSON Schema validator.

The checker intentionally does not assert a canonical evidence JSON shape. D-014 records why: a test for an invented evidence representation would merely encode implementation preference as protocol law.

## Open decisions before schema replacement

- **Evidence:** exact JSON cardinality and object shape for the authoritative evidence constructors remains an authority-level blocker under D-014; implementation must fail closed meanwhile.
- Exact JSON representation/cardinality of pragmatics modifiers/goals where the PDF does not fully constrain them.
- Whether envelope metadata is represented by this schema as a wrapper object or split into an envelope schema plus a pure-Octad schema. Semantic equality must remain Octad-only either way.
- Canonical extension behavior and whether unknown extension data is preserved or rejected by each carrier profile.

Until these are resolved from authoritative text or a deliberate protocol decision, the schema remains non-canonical and pre-training readiness remains blocked.
