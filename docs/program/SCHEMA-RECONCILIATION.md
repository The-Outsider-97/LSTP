# Canonical Octad schema reconciliation

Status: **resolved by the 4 October 2026 canonical-contract pass**.

The 30 September record documented unresolved drift between the Whitepaper, the subordinate specification, and `spec/octad_schema.json`. That drift is no longer the implementation contract on this branch.

The authoritative reconciliation is recorded in:

- `spec/CANONICAL-v0.1.md`;
- `spec/octad_schema.json`;
- `spec/permissions-safety.md`;
- `spec/vocabulary.md`;
- `docs/program/CANONICAL-RECONCILIATION-2026-10-04.md`.

## Resolved decisions

| Domain | Canonical v0.1 decision |
|---|---|
| Envelope | `id`, `version`, `carrier`, `audit`, and optional `extensions` are envelope metadata outside Octad semantic equality. |
| Pragmatics | Required `act`; optional goal/modifiers/register; numeric urgency `[0,1]`. |
| Atoms | Ordered typed `aN` array with closed core atom-kind vocabulary. |
| Relations | Typed relation plus ordered `arguments`; legacy SPO is migration-only. |
| Context | Required `thread_id`; canonical references require stable `packet_id`. |
| Confidence | Required packet-level numeric value `[0,1]`; optional relation confidence. |
| Permissions | Orthogonal capabilities + typed resources + constraints; named profiles are non-ordered bundles. |
| Evidence | Ordered provenance records with source types `user/sensor/model/tool/retrieved/inferred`. |
| Output | Closed core format vocabulary plus explicit optional output constraints. |
| Extensions | Namespaced object payloads; cannot override core semantics or permissions. |

## Legacy artifacts

The former subordinate shapes (`intent/action/force/tone`, atom maps, SPO relations, lowercase scalar permission modes, `provided/needed/assumptions/challenges`) are no longer canonical v0.1. Migration tooling may ingest them only as explicitly legacy input and must surface ambiguous/lossy mappings.

## Remaining blockers

Schema reconciliation being resolved does **not** make LSTP ready. Remaining work includes parser/compiler implementation, semantic/reference validation, permission-aware validation, canonical byte serialization, conformance vectors, interoperability evidence, SLAI integration, publication synchronization, and final release/pre-training audit.
