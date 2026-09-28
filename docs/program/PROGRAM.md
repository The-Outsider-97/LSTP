# LSTP hardening program

Target: **15 December 2026**. The full owner mandate in the initiating conversation
governs this program. This file is its persistent engineering index, not a narrower
replacement. Initial audited baseline: `37eade2e2dcbece7b837833f546d9b8a75673a8b`.

## Authority and operating rules

1. `docs/LSTP_Whitepaper.pdf` is authoritative.
2. Root README is subordinate project guidance.
3. Spec, grammar, schema, vocabulary, permissions and operators express that contract.
4. Code and tests implement it; current behavior does not redefine it.

Use a dedicated hardening branch, coherent commits, tests, self-review and PRs.
No force-pushing shared history, main scratchpad, secrets, caches or environment
files. Routine supported changes are authorized. Escalate consequential changes
to core semantics, canonical fields, permission meanings, breaking syntax,
compatibility guarantees or the authoritative PDF. Where escalation is unavailable,
record a conservative interpretation and leave affected conformance gates blocked.

Each cycle: inspect latest state, identify weaknesses, implement, test, attempt to
break it, re-read authority, simplify/review, fix, retest, update docs, commit, report.
Never invent test outcomes, silently weaken validation, coerce permissions, hide
unsupported extensions, or label planned features as implemented.

## Work packages and completion evidence

| Work package | Mandate sections | Required evidence |
|---|---|---|
| Authority and complete audit | 1–5 | Whole-tree inventory, PDF-grounded conflicts/decisions, requirement IDs |
| Canonical model and compilation | 6–10 | Exactly eight semantic components, distinct envelope, typed invariants, syntax/semantic/reference/version validation |
| Carriers and serialization | 11,22–23 | Explicit equality, deterministic profile, version rejection, extension behavior, Lattice/JSON round trips |
| Policy and hostile inputs | 12–14 | Requested ∩ host ∩ capability boundary; forbids/scope/limits/confirm/review/log cases; resource limits and actionable errors |
| CLI and distribution | 15–16 | Installed entry points, stdin/files, exit codes, clean wheel/sdist installation |
| Verification and CI | 17–19 | Unit, grammar, schema, integration, negative, regression, property, fuzz, CLI, version/Python matrix tests; no hidden core skips |
| Maintainability/performance | 20–21 | Typed cohesive modules, no duplicated rules/cycles, measured representative workloads and pathological bounds |
| Examples and documentation | 24–25 | Executable examples, truthful statuses, PDF/Markdown/spec/code consistency |
| SLAI and pre-training | 26–27 | Standalone core, explicit adapters, SLAI/model/LSTP plus root launcher; versioned grammar/schema/vocabulary/serialization and migration guidance |
| Delivery discipline | 28–33 | Reviewable Git history, evidence-based reports, continuing falsification/hardening |
| Acceptance and final report | 34–37 | Fresh independent audit, full Definition of Done and 20-part final report; remaining risks explicit |

## Sequence (planning targets, not readiness promises)

- 22 September–6 October: authority reconciliation, complete requirement mapping,
  canonical field/grammar/permission decisions, executable fixtures and packaging.
- 7–27 October: parser/AST/compiler/canonical model, layered validation, diagnostics.
- 28 October–17 November: serializers/carriers, host boundary, CLI, reference/context
  checks, property/fuzz/adversarial coverage and executable examples.
- 18 November–1 December: interoperability fixtures, compatibility matrix,
  performance measurements, documentation/publication reconciliation, release candidate.
- 2–15 December: fresh acceptance audit, reproducibility, security review,
  pre-training freeze or explicit NOT READY report.

Do not freeze unstable semantics to meet dates. If apparently complete early,
continue hardening until fresh reviews find no material defects and all acceptance
criteria have evidence.

## Reporting and continuity

A scheduled cycle/report is configured every two days from 24 September at 09:00
Europe/Amsterdam through 15 December. The two-day recurrence's last date is
14 December; the same automation includes an additional 15 December run for the final report. Scheduled work
is execution at each run, not continuous background computation. Each run must
state any access, environment or execution blocker; never imply unseen work.

Reports include exact dates, branch/commits/PRs, completed changes, tests added/run
and outcomes, regressions/failed approaches, spec conflicts, security/reliability,
technical debt, highest risks, next cycle, and readiness per subsystem.

Read `AUDIT-2026-09-22.md`, the latest report, `readiness.json`, PR state and current
HEAD before continuing. Preserve user changes. Do not assume this branch is still
current or already merged.

## Final gates

The full owner Definition of Done applies: mutually consistent authority/specs;
all core modules functional; positive/negative/reference/round-trip/determinism
checks passing; permissions preserved and enforced at the host boundary;
hostile-input limits; comprehensive tests; clean install/build and real CI matrix;
accurate docs/examples; coherent versions/release notes; stable training contract
and migration policy. Empty scaffolds in critical paths prevent release.

The final audit must re-read the PDF/specs, use a clean environment, attack parser
and validator, review permissions, run every test/example, review metadata/CLI,
inspect dependencies/dead code/circular imports, and assess every occurrence of
TODO/FIXME/HACK/XXX/pass/NotImplemented/placeholder/temporary/stub/mock.

Final report: repository and release identifiers; architecture; conformance;
specification and implementation changes; strategy and complete test results;
security/adversarial results; performance; compatibility; installation and CLI;
limitations and risks; SLAI and training readiness; final traceability matrix;
PDF/spec changes; post-freeze recommendations. A deadline never substitutes for
passing gates. Production-critical gaps must be explicitly reported.
