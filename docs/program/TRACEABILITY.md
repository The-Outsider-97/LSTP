# Initial requirements traceability

This is an initial index, not completed conformance. `normative-candidates.json`
records 193 uppercase-keyword candidate lines from the three technical Markdown
specs with source/text-based IDs. They require manual splitting, PDF authority
review, and implementation/test/example links. Definitions and explanatory lines
may be false positives. Schema constraints, EBNF productions, and PDF requirements
also need complete individual coverage; this line inventory does not replace it.

| ID | PDF requirement | Technical artifact | Implementation / tests | Documentation / status |
|---|---|---|---|---|
| WP-3.1 | Canonical eight fields | schema; spec §3 | None | README; SPEC-002 blocks |
| WP-3.2 | Inspectable fields and deterministic diagnostics | spec §34 | errors.py, json_input.py; test_json_input diagnostics | README; partial (JSON only) |
| WP-3.3 | Defined canonical round-trip equality | spec §§35–36 | None | SPEC-001/002 block |
| WP-3.4 | Authority never silently broadened | permissions; schema | No execution code; no conformance proof | SPEC-003 blocks |
| WP-3.5 | Referential context owned by host | spec §11 | None | SPEC-004 blocks |
| WP-3.6 | No invented extension semantics | EBNF; operator table | No compiler | Audit; open |
| WP-5.2 | Canonical Lattice forms | EBNF | None | SPEC-001 blocks |
| WP-5.3 | Machine-readable JSON Schema | octad_schema.json | test_artifacts meta-schema check | JSON syntax fixed, conformance blocked |
| WP-5.5 | No semantic invention in compilation | spec §§21–29 | None | Open |
| WP-5.6 | Explicit serialization ordering/numbers/Unicode | spec §35 | None | Open; JSON decoding isn't serialization |
| WP-6.1 | Pragmatic type; numeric urgency | schema pragmatics | None | SPEC-002 blocks |
| WP-6.2 | Typed aN atoms | schema atoms | None | SPEC-002 blocks |
| WP-6.3 | Typed relations and resolvable arguments | schema relations | None | SPEC-002 blocks |
| WP-6.4 | Required thread_id and context links | schema context | None | SPEC-002/004 block |
| WP-6.5 | Numeric confidence [0,1] | schema confidence | None | SPEC-002 blocks |
| WP-6.6 | Modes/scope/forbids/limits/confirm/review/log | permissions; schema | None | SPEC-003 blocks |
| WP-6.7 | Evidence constructors/provenance | schema evidence | None | SPEC-002 blocks |
| WP-6.8 | Output format and constraints | schema output | None | SPEC-002 blocks |
| WP-6.9 | References, permission preservation, extensions | spec semantic validation | None | Open |
| WP-7.9 | Unresolved macros not guessed | EBNF; operators | None | Open |
| WP-8.3 | Each carrier has mapping, codecs, tests, failures | spec carriers | None | Open |
| WP-8.4 | Version/profile negotiation outside Octad | spec version | None | Open |
| WP-9.4 | Resolver verifies existence/version/access | spec context | None | Open; host contract needed |
| WP-10 | Requested ∩ policy ∩ capability | permissions | None | Audit; SPEC-003 blocks |
| WP-11.2 | SLAI/model/LSTP and root launcher | corrected spec layout | No adapter | README; unimplemented |
| WP-13.3 | Negative, hostile and positive input fixtures | spec §43.3 | test_json_input property/adversarial tests | Partial; JSON substrate only |
| WP-13.8 | Independent implementation interoperability | conformance corpus absent | None | Open |
| WP-13.9 | Measure only after correctness | benchmarks absent | None | No performance claims |
| WP-16.5 | Working packaging/CLI commands | pyproject.toml | test_cli; wheel smoke | README; foundation only |
| WP-16.6 | Conformance corpus and CI | .github/workflows/ci.yml | engineering suite; readiness gate | Partial, gate intentionally fails |

For future links, use actual test node IDs and fixture paths. Never mark a
requirement verified merely because a test bearing its name exists. Requirements
must be checked against independent expected semantics and negative examples.
