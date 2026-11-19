# Changelog

## Unreleased - compatibility and efficiency refinement (2026-11-19)

- Repair the package import failure introduced when two compact implementations merged; retain both published wire profiles and the incremental API.
- Share strict canonical decoding and parse input JSON once, while preserving numeric, Unicode, structural and semantic checks.
- Reuse validated snapshots during model request preparation and replace repeated projection reserialization with exact normalized-state comparison.
- Retain a normalized source copy and digest for projections; caller-owned mutable sequences cannot change an accepted view.
- Make schema-heavy model input opt-in, retain the measured extraction tuple prompt, and expose the selected output contract.
- Add regression coverage and a reproducible CPU benchmark; record live-model evidence separately from new local timing results.


## 0.1.0a1 — engineering foundation (2026-09-22)

- Audit baseline and record conflicting Whitepaper/spec/schema/permission contracts.
- Add package metadata, bounded JSON inspection, payload-free diagnostics and CLI.
- Add input/CLI/property/adversarial tests and engineering CI matrix.
- Add explicit failing protocol readiness gate, initial traceability and program plan.
- Repair schema JSON syntax, schema filename references and subordinate SLAI layout.
- Reject trailing controls in schema identifier patterns; preserve declared lexical rules.
- Correct README authority order and remove inaccurate operational claims.

No canonical model, Lattice parser, compiler, permission engine or serialization
is released. No protocol freeze, migration compatibility, production readiness or
model-training readiness is claimed. The authoritative PDF is unchanged.
