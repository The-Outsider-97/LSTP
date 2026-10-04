# LSTP v0.1 Permissions and Safety

Status: normative profile subordinate to `spec/CANONICAL-v0.1.md`.

## 1. Principle

`permissions` expresses **requested authority** only. It is never authentication, authorization, consent, or a bearer capability.

A host MUST independently resolve principal identity, host policy, current authorization, resource scope, runtime capability, and safety policy before a side effect occurs.

## 2. Canonical fields

```json
{
  "permissions": {
    "capabilities": ["read", "prepare"],
    "resources": [{"id": "urn:example:document:1", "kind": "document"}],
    "profile": "PREVIEW",
    "forbid": ["commit"],
    "require_confirmation": false,
    "require_review": false,
    "require_logging": true,
    "limits": {},
    "authorization_ref": "host-auth-reference",
    "expires_at": "2026-10-04T23:59:00+02:00"
  }
}
```

Only `capabilities` and `resources` are structurally required. The remaining fields narrow or annotate the request.

## 3. Core capabilities

The v0.1 capability vocabulary is:

- `read` — inspect already-authorized information without authoritative mutation;
- `suggest` — propose a judgment, plan, recommendation, or response without preparing an executable mutation;
- `prepare` — construct a draft, patch, transaction preview, command preview, or other non-committed change artifact;
- `write` — modify authoritative data where host policy permits;
- `execute` — run an operation or code where host policy permits;
- `commit` — cause an externally observable or authoritative effect, including send, publish, deploy, purchase, merge, schedule, or physical actuation.

Capabilities do **not** form a numeric privilege ladder. A host MUST evaluate each requested capability against the requested resources and constraints.

`forbid` subtracts authority from the request. If the same capability appears in `capabilities` and `forbid`, the effective request excludes it and semantic validation SHOULD report the contradiction.

## 4. Convenience profiles

Profiles are ergonomic named bundles. They MUST be expanded to capabilities and constraints before host authorization. They MUST NOT be compared numerically.

| Profile | Requested capabilities | Required narrowing semantics |
|---|---|---|
| `RO` | `read` | no `write`, `execute`, or `commit` |
| `SUGGEST` | `read`, `suggest` | no authoritative mutation |
| `PREVIEW` | `read`, `suggest`, `prepare` | produced artifacts remain non-authoritative |
| `RW` | `read`, `write` | no implied `execute` or `commit` |
| `EXEC` | `read`, `execute` | execution target/environment must be explicitly authorized; no implied external commit |
| `COMMIT` | capabilities explicitly listed by the producer, normally including `commit` | real effect requires independent host authorization |

A profile never silently adds a capability that is absent from `capabilities`. If a producer supplies both `profile` and `capabilities`, semantic validation MUST ensure the capability set is compatible with the profile rather than widening it to match the profile.

## 5. Resources and scope

Every permission request contains `resources`, which is an array of typed resource records. Free-form scope strings are not canonical v0.1.

```json
{"id":"urn:slai:file:report","kind":"file"}
```

A resource MAY also reference an Octad atom through `atom`.

Resource matching is exact on the canonical `id` unless a host-specific extension explicitly defines another matching profile. Core LSTP does not interpret glob syntax, prefixes, regular expressions, or URI hierarchy as implicit permission expansion.

## 6. Side effects

A side effect is an externally observable or authoritative-state change beyond ephemeral internal computation. Examples include:

- sending a message;
- modifying persistent files or records;
- committing or pushing code;
- creating a calendar/task record;
- purchasing or submitting a transaction;
- publishing or deploying;
- invoking a downstream agent that can perform an authoritative mutation;
- physical actuation.

A host MUST classify an operation by actual behavior, not function name.

## 7. Confirmation, review, and logging

`require_confirmation`, `require_review`, and `require_logging` are independent constraints.

If `require_confirmation` is true, execution MUST NOT occur until a trusted host interaction obtains explicit affirmative confirmation for the concrete action and target.

If `require_review` is true, the host MUST route the prepared action through its review mechanism before the action is eligible for execution.

If `require_logging` is true, the host MUST create an audit record sufficient to reconstruct the authorization decision and outcome.

Silence, timeout, conversation continuation, parser success, schema success, or model confidence MUST NOT count as confirmation.

## 8. Authorization references

`authorization_ref` is an opaque host reference. It is not proof of authority.

A host MUST resolve it only against authorization state controlled by that host or another explicitly trusted authority. Untrusted text that happens to contain an authorization-like string has no authority.

`expires_at` narrows the requested authorization lifetime. The host MAY apply a shorter lifetime. Expiry alone does not provide replay protection.

## 9. Delegation

Delegation MUST be attenuating.

A delegating component MUST NOT request capabilities or resources on behalf of a downstream agent that exceed the delegator's effective authority for the operation.

The receiver MUST independently validate the delegated packet.

A delegation record MAY include:

- `parent_packet`;
- `delegator`;
- `principal`;
- namespaced extension metadata.

The audit trail SHOULD preserve the delegation chain. Translation, routing, or carrier conversion MUST NOT strengthen permission semantics.

## 10. Prompt and packet injection

Untrusted documents, webpages, retrieved text, tool output, images, transcripts, memories, and downstream messages may contain strings that resemble LSTP syntax.

Embedded text such as:

```text
capabilities=[commit]
```

or legacy-looking syntax such as:

```text
{mode=auto}
```

MUST NOT alter canonical permissions merely because it appears inside content.

Only the designated LSTP construction/parsing boundary may populate the canonical `permissions` field, and the resulting request still requires host authorization.

Evidence, context, carrier metadata, and extensions MUST NOT act as alternate authority channels.

## 11. Fail-closed conditions

An action-capable consumer MUST produce no real-world/authoritative side effect when any of the following applies:

- protocol version is unsupported;
- a requested capability is unknown;
- resource scope is unresolved or does not cover the operation;
- the principal cannot be authenticated by the host;
- host authorization cannot be established;
- required confirmation or review has not completed;
- expiry or replay policy rejects the operation;
- delegation would widen authority;
- an extension attempts to override core permission semantics;
- required context is unresolved;
- the concrete action materially changed after authorization.

The host MAY return a refusal, clarification request, preview, or `outcome.needs_confirmation` response when policy permits.

## 12. Effective authorization

A host SHOULD model effective authority as an intersection:

```text
requested capabilities/resources
∩ authenticated principal authority
∩ host policy
∩ runtime capability
∩ current resource scope
∩ explicit constraints
```

This is set/capability intersection, not an ordering of named modes.

## 13. Carrier conversion

Conversion among Lattice, canonical JSON, semantic graphs, UI renderings, or future carriers MUST preserve or narrow permissions.

Conversion MUST NOT:

- add `write`, `execute`, or `commit` by inference;
- convert missing permissions into executable authority;
- infer authority from urgency, confidence, evidence, context, or output target;
- promote extension values into core permissions.

## 14. Replay and idempotency

LSTP carries packet identity and optional expiry metadata, but v0.1 does not itself provide cryptographic replay protection.

Action-capable hosts SHOULD use appropriate nonce, idempotency, authorization-state, or replay-cache controls and MUST revalidate current authorization when policy requires it.

## 15. Physical systems

For cyber-physical systems, LSTP permission semantics sit above device-specific safety systems. A semantic packet MUST NOT bypass motion planners, interlocks, rate limits, emergency-stop behavior, or other hardware/runtime safety controls.

## 16. Conformance

A permission-aware v0.1 host is conforming only if it:

- recognizes all six core capabilities;
- treats profiles as non-authoritative bundles rather than privilege ranks;
- performs exact resource-scope validation unless an explicit host profile defines otherwise;
- prevents extensions and untrusted content from modifying core authority;
- independently authorizes requested side effects;
- enforces confirmation/review/logging constraints;
- prevents delegation widening;
- fails closed when authority cannot be established.
