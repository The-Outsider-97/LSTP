# Initial requirements traceability

> **6 October 2026 audit note:** Phase B restored Whitepaper pragmatics, permissions, and context semantics. Phase C restores canonical ordered-Octad Lattice syntax and keeps compact Lattice as a separate carrier profile. Verification, GOV-EXT, interoperability, and release/training gates remain open.

This is an initial index, not completed conformance. `normative-candidates.json`
records 193 uppercase-keyword candidate lines from the three technical Markdown
specs with source/text-based IDs. They require manual splitting, PDF authority
review, and implementation/test/example links. Definitions and explanatory lines
may be false positives. Schema constraints, EBNF productions, and PDF requirements
also need complete individual coverage; this line inventory does not replace it.

Protocol-level interpretations are recorded in `DECISIONS.md`. A decision record
can unblock architecture or identify a required change, but it is not conformance
evidence by itself.

| ID | PDF requirement | Technical artifact | Implementation / tests | Documentation / status |
|---|---|---|---|---|
| WP-3.1 | Canonical eight fields | schema; spec §3 | models.Octad; test_models field order | D-010; field container implemented, field semantics still SPEC-002-blocked |
| WP-3.2 | Inspectable fields and deterministic diagnostics | spec §34 | errors.py, json_input.py; test_json_input diagnostics | README; partial (JSON only) |
| WP-3.3 | Defined canonical round-trip equality | canonical JSON profile; candidate model | semantic equality plus canonical JSON round-trip tests implemented | Engineering mechanism implemented; canonical semantics still governance-blocked |
| WP-3.4 | Authority never silently broadened | Whitepaper permissions; host authorization | Whitepaper mode is translated only at host boundary; exact scope/forbid plus principal/policy/runtime intersection, delegation attenuation, extension isolation and replay controls implemented | Phase B implemented; GOV-EXT/verification remain |
| WP-3.5 | Referential context owned by host | spec §11 | None | D-010; SPEC-004 blocks |
| WP-3.6 | No invented extension semantics | EBNF; operator table; spec extensions | PacketEnvelope namespace preservation; test_models extension cases | D-007/D-015; partial model boundary only |
| WP-5.2 | Canonical Lattice forms | Whitepaper §7; `spec/grammar.ebnf`; `spec/compact-grammar.ebnf` | canonical ordered-Octad parser implements atomic/framed/named/stream forms; compact parser/compiler remains separate | Phase C implemented; PHASEC-VERIFY pending |
| WP-5.3 | Machine-readable JSON Schema | octad_schema.json | test_artifacts meta-schema check | JSON syntax fixed, conformance blocked |
| WP-5.5 | No semantic invention in compilation | spec §§21–29 | None | D-007/D-009; open |
| WP-5.6 | Explicit serialization ordering/numbers/Unicode | canonical JSON byte profile | deterministic serializer/deserializer and Unicode/number tests implemented | Engineering profile implemented; must be revalidated after contract repair |
| WP-6.1 | Pragmatic type; numeric urgency | Whitepaper §§6.1, 7.3; schema | typed model, canonical serializer/decoder and compact compiler now preserve separate type/speech_act plus urgency | Phase B implemented; PHASEB-VERIFY pending |
| WP-6.2 | Typed aN atoms | schema atoms | typed Atom model and reference tests | Substantially aligned; revalidate after contract repair |
| WP-6.3 | Typed relations and resolvable arguments | schema relations | typed Relation model plus semantic reference validation | Substantially aligned |
| WP-6.4 | Required thread_id and context links | Whitepaper §6.4/7.5; schema | thread_id/reference resolution plus parent_packet_id/timezone/window implemented and round-trip covered | Phase B implemented; PHASEB-VERIFY pending |
| WP-6.5 | Numeric confidence [0,1] | schema confidence | bounded packet/relation confidence validation implemented | Aligned |
| WP-6.6 | Modes/scope/forbids/limits/confirm/review/log | Whitepaper §§6.6,10; permission profile; schema | six-mode mode/scope wire model implemented; forbids are preserved and narrow authority; unknown forbid expressions fail closed at action authorization; confirmation/review/logging retained | Phase B implemented; GOV-EXT and PHASEB-VERIFY remain |
| WP-6.7 | Evidence constructors/provenance | candidate evidence schema/model | typed evidence source constructors and support-reference validation implemented | Source vocabulary aligned; exact canonical shape remains under audit |
| WP-6.8 | Output format and constraints | schema output | typed output model plus BCP47/max-bytes validation | Substantially aligned |
| WP-6.9 | References, permission preservation, extensions | spec semantic validation | Extension namespace structural checks only | D-007/D-011/D-015; partial |
| WP-7.9 | Unresolved macros not guessed | EBNF; operators | None | D-007; open |
| WP-8.3 | Each carrier has mapping, codecs, tests, failures | canonical + compact grammar profiles | canonical parser/compiler/fail-closed encoder plus compact parser/compiler have separate APIs/tests; governed canonical surface has semantic round-trip tests | Partial; PHASEC-VERIFY/TEST-001 and independent interoperability remain |
| WP-8.4 | Version/profile negotiation outside Octad | spec version | PacketEnvelope rejects versions other than 0.1; test_models unknown-version cases | D-010/D-015; v0.1 fail-closed boundary implemented, negotiation absent |
| WP-9.4 | Resolver verifies existence/version/access | spec context | None | Open; host contract needed |
| WP-10 | Requested ∩ policy ∩ capability | Whitepaper permissions; host authorization | six-mode wire request is deterministically mapped to host-internal capabilities then intersected with principal/policy/runtime authority and scope; confirmation/review/logging, expiry and replay retained | Phase B implemented; GOV-EXT/verification remain |
| WP-11.2 | SLAI/model/LSTP and root launcher | corrected spec layout | No adapter | README; unimplemented |
| WP-13.3 | Negative, hostile and positive input fixtures | spec §43.3 | test_json_input property/adversarial tests; test_models malformed envelope/extension tests | Partial; D-008/D-009 require blocked grammar cases |
| WP-13.8 | Independent implementation interoperability | initial conformance corpus exists | no independent second implementation | Open hard blocker |
| WP-13.9 | Measure only after correctness | benchmarks absent | None | No performance claims |
| WP-16.5 | Working packaging/CLI commands | pyproject.toml | test_cli; wheel smoke | README; foundation only |
| WP-16.6 | Conformance corpus and CI | .github/workflows/ci.yml | engineering suite; readiness gate | Partial, gate intentionally fails |
| WP-training-freeze | Stable/versioned training contract | grammar/schema/vocabulary/serialization | None | D-012; explicitly blocked |

For future links, use actual test node IDs and fixture paths. Never mark a
requirement verified merely because a test bearing its name exists. Requirements
must be checked against independent expected semantics and negative examples.
