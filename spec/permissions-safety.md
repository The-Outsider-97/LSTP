# LSTP v0.1 Permissions and Safety

Status: Whitepaper-aligned Level-3 permission profile. Host-security additions
that are not yet established as Level-1 v0.1 core semantics remain provisional
under GOV-EXT.

## 1. Principle

The `permissions` Octad field expresses **requested authority** only. It is not
authentication, authorization, consent, or a bearer capability.

A consuming host MUST independently evaluate the request against authenticated
principal authority, local policy, runtime capability, resource scope, current
state, and safety policy before any side effect occurs.

## 2. Canonical Whitepaper wire fields

A canonical permission request uses the Whitepaper mode/scope representation:

```json
{
  "permissions": {
    "mode": "PREVIEW",
    "scope": ["urn:example:document:1"],
    "forbid": ["urn:example:document:archive"],
    "require_confirmation": false,
    "require_review": false,
    "require_logging": true,
    "limits": {}
  }
}
```

Core fields:

- `mode` — requested operational mode;
- `scope` — explicit resource/target identifiers;
- `forbid` — explicit exclusions that narrow the request;
- `require_confirmation` — explicit trusted confirmation requirement;
- `require_review` — explicit host review requirement;
- `require_logging` — explicit audit logging requirement;
- `limits` — declared cost/time/count/application constraints;
- `extensions` — namespaced extension data.

The current engineering candidate also accepts `authorization_ref`,
`expires_at`, and `delegation` for host-security hardening. These fields do
not become frozen v0.1 core semantics merely because the reference
implementation supports them. GOV-EXT must resolve their final status before
training/release freeze.

## 3. Core modes

LSTP v0.1 defines exactly six Whitepaper modes:

- `RO`
- `SUGGEST`
- `PREVIEW`
- `RW`
- `EXEC`
- `COMMIT`

Their conceptual order is:

```text
RO <= SUGGEST <= PREVIEW <= RW <= EXEC <= COMMIT
```

The order expresses increasing operational authority. It MUST NOT be interpreted
as widening resource scope, removing forbids, bypassing limits, or satisfying
confirmation/review/logging requirements.

### RO

Read/inspect/transform already-authorized information without authoritative
mutation.

### SUGGEST

May produce advice, recommendations, judgments, plans, or proposed responses.
It does not authorize preparation of an executable/committable mutation unless
the host explicitly treats the produced object as non-authoritative advice.

### PREVIEW

May prepare a draft, patch, command preview, event preview, transaction preview,
or other non-committed artifact. The preview MUST remain distinguishable from
authoritative state.

### RW

May request authoritative read/write behavior within explicit scope. It does not
remove host confirmation, review, logging, or policy requirements.

### EXEC

May request execution within explicit scope and an explicitly authorized runtime
environment. Execution does not imply unrestricted external commit.

### COMMIT

May request an externally observable or authoritative effect, including send,
publish, deploy, purchase, merge, schedule, delete, or physical actuation. A
COMMIT packet still requires independent host authorization.

## 4. Scope and forbids

`scope` is the packet's explicit requested resource/target boundary. Core LSTP
does not infer wildcard, prefix, URI hierarchy, regular-expression, or glob
semantics.

The reference authorization layer performs exact matching unless an explicitly
named host profile defines additional semantics.

`forbid` always narrows. At minimum, an exact item that appears in both
`scope` and `forbid` MUST be treated as denied. Carrier conversion MUST NOT
remove or weaken forbids.

An empty scope MUST NOT be interpreted as a wildcard. For side-effect-capable
modes (`RW`, `EXEC`, `COMMIT`), the reference semantic validator requires
explicit scope.

## 5. Host-internal capability mapping

Concrete capabilities are an implementation mechanism used by an action-capable
host. They are not canonical packet fields.

The reference host uses this monotonic mapping:

| Wire mode | Internal capabilities |
|---|---|
| `RO` | `read` |
| `SUGGEST` | `read`, `suggest` |
| `PREVIEW` | `read`, `suggest`, `prepare` |
| `RW` | `read`, `suggest`, `prepare`, `write` |
| `EXEC` | `read`, `suggest`, `prepare`, `write`, `execute` |
| `COMMIT` | `read`, `suggest`, `prepare`, `write`, `execute`, `commit` |

This mapping exists only at the host authorization boundary. Serializers,
parsers, model classes, and canonical JSON MUST NOT expose
`capabilities`, `resources`, or `profile` as v0.1 permission fields.

## 6. Effective authorization

The reference host computes effective authority as an exact intersection:

```text
mode-derived internal capabilities
INTERSECT authenticated principal capabilities
INTERSECT host-policy capabilities
INTERSECT runtime capabilities
```

and independently:

```text
(requested scope MINUS exact forbids)
INTERSECT authenticated principal resources
INTERSECT host-policy resources
INTERSECT runtime resources
```

Application limits and host-specific scope semantics may only narrow these
results.

## 7. Side effects

A side effect is a change to persistent, shared, external, authoritative,
financial, communicative, scheduled, deployed, or physical state beyond the
ephemeral computation needed to evaluate a packet.

Examples include sending messages, modifying files/records, committing code,
creating calendar/task records, submitting transactions, purchasing, publishing,
deploying, invoking a downstream action-capable agent, or physical actuation.

A host MUST classify an operation by actual behavior, not by function name.

## 8. Confirmation, review, and logging

These constraints are independent.

If `require_confirmation` is true, execution MUST NOT occur until a trusted
host interaction obtains affirmative confirmation for the concrete action and
target.

If `require_review` is true, the host MUST complete the configured review step
before the operation becomes eligible.

If `require_logging` is true, logging MUST be ready before execution.

Silence, timeout, continued conversation, parser success, schema success, model
confidence, or a matching permission mode MUST NOT count as confirmation.

## 9. Provisional host-security fields

### Authorization reference

`authorization_ref`, when present in the current engineering candidate, is an
opaque trusted-host reference. It grants no authority by itself and MUST be
resolved against host-controlled authorization state.

### Expiry

`expires_at` narrows the candidate authorization lifetime and is interpreted as
RFC 3339. A host MAY apply a shorter lifetime.

### Delegation

Delegation MUST be attenuating. The child request's derived capabilities and
effective scope MUST NOT exceed authenticated parent authority.

These mechanisms are retained as security hardening while GOV-EXT decides
whether they become v0.1 extensions, a named host profile, or a later protocol
revision.

## 10. Replay and idempotency

Packet identity and expiry do not themselves provide replay protection.

Action-capable hosts SHOULD use an atomic replay/idempotency store. The reference
implementation exposes a `ReplayStore` contract with in-process and SQLite
implementations. Multi-node deployments require a store with equivalent atomic
reservation semantics.

Replay infrastructure is host security machinery and does not change packet
permission semantics.

## 11. Prompt and packet injection

Untrusted content may contain strings that resemble LSTP syntax. Such content
MUST NOT populate or alter canonical permissions unless it passes through the
designated LSTP construction/parsing boundary.

Evidence, context, carrier metadata, output targets, and extensions MUST NOT act
as alternate permission channels.

## 12. Fail-closed conditions

An action-capable consumer MUST produce no authoritative side effect when:

- the protocol version is unsupported;
- the permission mode is missing or insufficient for the requested operation;
- scope is empty for a side-effect-capable request;
- the target falls outside effective scope;
- a forbid excludes the target;
- authenticated principal authority is insufficient;
- host policy or runtime capability is insufficient;
- required confirmation/review/logging is incomplete;
- expiry or replay policy rejects the request;
- delegation would widen authority;
- required context is unresolved;
- an extension attempts to override core permission semantics;
- the concrete action materially changed after authorization.

## 13. Carrier conversion

Carrier conversion MUST preserve or narrow requested authority.

It MUST NOT:

- add a stronger mode by inference;
- expand scope;
- remove forbids;
- remove limits or confirmation/review/logging requirements;
- convert missing permissions into executable authority;
- infer authority from urgency, confidence, evidence, context, or output target;
- promote extension values into core permissions.

## 14. Conformance

A permission-aware v0.1 host is conforming only if it:

- recognizes exactly the six Whitepaper modes;
- preserves their conceptual order without widening scope;
- keeps concrete capabilities internal to host authorization;
- performs explicit scope validation;
- treats forbids as subtractive;
- independently authorizes side effects;
- enforces confirmation/review/logging;
- prevents delegation widening;
- fails closed when authority cannot be established.
