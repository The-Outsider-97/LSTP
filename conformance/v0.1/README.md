# LSTP v0.1 conformance vectors

These fixtures are executable evidence for the reconciled v0.1 contract.

- `positive/` contains canonical byte representations that MUST decode, validate, and re-encode byte-for-byte identically.
- `negative/` contains packets that MUST be rejected structurally or semantically.

The suite is intentionally small in this increment. It establishes the harness and covers canonical byte stability, unknown-field rejection, unresolved semantic references, and permission profile widening. Additional vectors should be added for every fixed regression and every normative cross-field rule.

A vector passing JSON syntax alone is not conformance. Positive vectors must pass typed construction and semantic validation. Negative vectors must fail closed and must not be silently migrated or normalized into a different protocol meaning.
