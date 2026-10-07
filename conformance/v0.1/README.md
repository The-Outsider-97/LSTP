# LSTP v0.1 conformance vectors

These fixtures are executable evidence for the reconciled and frozen v0.1
contract. Both the Python reference implementation and the independent
JavaScript verifier consume `manifest.json`.

## Vector classes

- `positive/` — canonical JSON bytes that MUST decode, validate, and re-encode
  byte-for-byte identically.
- `negative/` — structural or semantic failures that MUST fail closed.
- `lattice/canonical/positive/` — canonical ordered-Octad Lattice that MUST
  parse and validate.
- `lattice/canonical/negative/` — canonical Lattice syntax/ordering failures.
- `lattice/canonical/unrepresentable/` — valid semantics that MUST NOT be
  silently dropped when a canonical-Lattice syntax is not governed.

The manifest also freezes the non-core permission fields that canonical v0.1
must reject.

A vector passing JSON syntax alone is not conformance. Positive vectors must
pass typed construction and semantic validation. Negative vectors must fail at
their intended layer and must not be silently migrated.

## Property/adversarial coverage

The release suite supplements static fixtures with deterministic Hypothesis and
resource-limit tests covering:

- compact permission mode/scope preservation;
- forbid attenuation;
- unknown-field mutation at packet and permission boundaries;
- legacy candidate-field rejection;
- strict canonical-byte mutation;
- compact-to-canonical round trips;
- byte/depth/string/collection/node/number resource limits;
- arbitrary byte fuzz and pathological numeric inputs.

## Independent implementation

`interop/js/verify.mjs` is dependency-free and does not import, spawn, or
invoke the Python implementation. It consumes the same manifest, reproduces
canonical JSON bytes, validates the frozen permission boundary and core
reference rules, and checks canonical-Lattice Octad ordering.

Run:

```bash
node interop/js/verify.mjs
```

Recorded execution evidence is stored under `docs/program/evidence/`.

## Release responsibility

Corpus completeness is tracked separately from execution. TEST-001 covers the
breadth and review of the conformance corpus; VERIFY-001 requires the full suite
to execute successfully from a clean checkout before the release/training
freeze is approved.
