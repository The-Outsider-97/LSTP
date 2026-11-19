# L1 compact carrier and D1 transport delta

Status: optional reference-implementation profile for canonical LSTP v0.1. This document does not replace the canonical contract or the Whitepaper. Signing, replay protection and host authorization consume restored canonical packets. An inference projection is a different type and is never accepted as a protocol packet.

## L1 wire format

The JSON value is ["L1", packet_tuple]. L1 implies protocol version "0.1". Unknown profile markers and extra tuple slots fail closed. Strings, numbers and generic JSON objects obey the existing canonical Unicode and decimal rules. Deterministic bytes use the existing canonical JSON value encoder. Full canonical state is preserved; original insignificant whitespace and redundant optional defaults are not preserved.

| Shape | Ordered slots | Required prefix length |
| --- | --- | ---: |
| packet | id, pragmatics, atoms, context, permissions, output, evidence, relations, confidence, carrier, audit, extensions | 6 |
| pragmatics | type, speech_act, goal, modifiers, register, urgency, extensions | 1 |
| atom | id, kind, value, role, datatype, language, attributes, extensions | 2 |
| relation | type, arguments, id, confidence, attributes, extensions | 2 |
| context | thread_id, bindings, references, packet_id, parent_packet_id, conversation_id, turn, speaker, audience, time, timezone, window, location, extensions | 1 |
| reference | packet_id, depth, agent, label, extensions | 1 |
| permissions | mode, scope, forbid, require_confirmation, require_review, require_logging, limits, extensions | 0 |
| evidence | id, source_type, source_ref, input_hash, span, supports, description, confidence, extensions | 2 |
| output | format, schema, channel, target, language, max_bytes, requirements, extensions | 1 |

Only packet.pragmatics, packet.atoms[], packet.relations[], packet.context, packet.permissions, packet.evidence[], packet.output, and context.references[] recursively use these typed tuples. Literal atom values and application bindings, attributes, extensions, spans, windows, locations, limits, carrier and audit objects retain their JSON structure and keys. They are never interpreted as dictionaries or references by this codec.

Trailing absent/default slots are removed. Interior absent optional slots are null. The required prefix cannot be shortened. Restored packet defaults are evidence=[], relations=[], confidence=1, carrier={}, audit={}; restored context references default to []. Other absent optional fields remain unspecified. Empty/default material inside typed models is normalized by canonical serialization. In particular, atom value=null and an absent atom value have the same existing canonical typed state. No permission mode, resource scope, reference, evidence item or application extension is guessed.

A minimal hand-authored example is ["L1",["manual",["inform"],[],["thread"],[],["NL"]]]. Both the supplied carrier and its expanded canonical representation must fit InputLimits. Decoding always invokes canonical JSON type, semantic, reference, Unicode and numeric validation. require_compact_bytes additionally requires the deterministic L1 form.

## D1 transport delta

The JSON value is ["D1", base_sha256, target_sha256, target_tuple_length, changes]. Each change is [slot_index, replacement_value]. Slot indices refer only to the packet tuple, are strictly increasing unique integers, and must be within the target tuple. The receiver starts with the explicitly supplied base's L1 tuple, resizes it, fills newly available slots with null, applies replacements, restores canonical semantics, and checks the target digest.

Both digests are SHA-256 of complete canonical packet bytes, including envelope identity and metadata. They are content identifiers and integrity checks, not signatures or authority. Missing or mismatched bases, malformed changes, invalid restored packets and mismatched target digests fail closed. D1 does not depend on implicit process state. A restarted receiver can load the base from canonical storage; an out-of-order receiver must obtain the exact base or request a self-contained L1 retransmission. incremental_dumps returns L1 when no base is supplied or the complete delta is not smaller in bytes. The base and target hash overhead is included in that decision.

D1 is network/storage compression. It must be expanded before inference unless the host independently establishes that every referenced base is visible to the model and accounts for its complete context cost. The supplied model-input selector does not send D1 to a model.

## Action-extraction inference view

The explicit SLAI action-extraction profile has seven nonempty strings in this order: action, resource, project, stage, permission_mode, output_format, source. It accepts exactly one a0 resource/TARGET atom, one a1 concept/ACTION atom, request/command pragmatics with goal formed by slai. followed by the action string, no relations, confidence=1, one e0 user source reference, an output format without additional requirements, scope exactly equal to the target resource, and context containing only its thread plus project/stage bindings. Inverse reconstruction must reproduce the complete source canonical bytes. Envelope id, thread and nonsemantic carrier/audit metadata are retained by the host.

Additional permission constraints, evidence metadata, uncertainty, context, relations, output requirements or extensions reject the view. The general request preparer falls back to full canonical/L1 candidates rather than dropping these fields. ActionProjection retains its immutable source and validates its own construction. Result decoding rejects duplicate keys, invalid JSON, extra/missing fields and nonstring/empty values. validate_response also compares every extracted fact with the source. These checks do not authorize execution.

prepare_action_input requires a host-supplied token counter for the complete system and user messages. It compares each representation with its own full schema/instruction cost. It makes no byte-to-token conversion, assumes no tokenizer or pricing, and has no hidden schema state. Compact syntax can lose on total request cost; canonical JSON remains an eligible fallback. Model output can use seven-position arrays and deterministic host reconstruction without regenerating a full protocol envelope.

For pure extraction of these already structured fields, project_action(...).as_mapping() performs the task without a language model. Ordinary JSON can do the same. This is deterministic processing, not measured model inference or a protocol-specific competitive advantage.

## Interoperability and limits

conformance/compact-v1.json contains a manually authored minimal vector, canonical-fixture conversions, a constrained/contextual packet, and negative shapes. The independent JavaScript mapping is exercised by interop/js/verify.mjs without importing Python. Its evidence covers the checked finite JavaScript-representable numbers. Python preserves a wider exact Decimal profile; arbitrary-precision JavaScript interoperability is not claimed.

Canonical v0.1 remains the training representation. L1/D1 are explicit optional carrier entry points; canonical_loads does not auto-detect them. Neither aliases nor opaque compressed data are silently substituted into model prompts.
