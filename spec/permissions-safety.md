# LSTP v0.1 Permissions and Safety

**Status:** Normative Phase 1 specification  
**Protocol:** Lattice Semantic Transport Protocol (LSTP)  
**Version:** 0.1  
**Applies to:** Canonical Octad packets, Lattice text, packet consumers, host runtimes, and future SLAI integration

---

## 1. Purpose

LSTP makes permission state a first-class semantic field because a compact instruction language can otherwise make it too easy to blur the boundary between analysis, preparation, simulation, and real-world action.

This document defines the normative meaning of the LSTP v0.1 permission modes and the minimum safety behavior required of conforming consumers.

The central rule is:

> A permission declaration describes the action mode requested by a packet. It does **not** by itself grant authority.

A conforming host MUST independently determine whether the sender, user, agent, process, or policy is authorized to perform the requested operation. In particular, the presence of `mode=commit` or `mode=auto` MUST NOT be treated as a bearer capability, authentication token, or proof of user consent.

This separation is essential for LSTP to remain safe when embedded in an agent system such as SLAI. LSTP transports semantic intent and requested permission state; the host runtime retains execution authority and policy enforcement.

---

## 2. Normative language

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** are to be interpreted as described in BCP 14 (RFC 2119 and RFC 8174) when, and only when, they appear in all capitals.

---

## 3. Threat model

The v0.1 safety model is designed to reduce, not eliminate, the following classes of failure:

1. **Permission ambiguity** — a request is interpreted as authorization to act.
2. **Privilege escalation through serialization** — a packet claims a stronger permission mode than the sender is actually entitled to use.
3. **Prompt or packet injection** — untrusted content attempts to alter execution permissions.
4. **Context confusion** — an action inherits a permission state from unrelated or stale context.
5. **Agent delegation escalation** — one agent delegates work to another with broader execution authority than it possesses.
6. **Preview-to-execution collapse** — a generated draft is sent, committed, purchased, deleted, or otherwise enacted without a distinct authorization boundary.
7. **Sandbox escape** — a sandbox-designated packet causes effects in authoritative or external state.
8. **Replay** — a previously authorized packet is executed again outside its intended scope or lifetime.
9. **Audit loss** — an action occurs without retaining the effective permission state and authorization provenance used at execution time.

LSTP v0.1 does not provide authentication, cryptographic signatures, identity management, capability tokens, secure storage, transport encryption, or policy engines. Those remain responsibilities of the host system or future protocol layers.

---

## 4. Permission object

The canonical packet contains the Octad field:

```json
{
  "permissions": {
    "mode": "preview",
    "scope": ["email:draft"],
    "authorization_ref": "auth://host/policy/meeting-email",
    "expires_at": "2026-08-28T18:00:00+02:00",
    "constraints": {
      "recipient_change": false
    },
    "extensions": {}
  }
}
```

The fields have the following meaning:

| Field | Requirement | Meaning |
|---|---|---|
| `mode` | Conditional | Requested LSTP permission mode. It is REQUIRED for any packet that may lead to an operation with side effects. |
| `scope` | Optional | Human- and host-readable declaration of the intended action scope. It does not grant authority. |
| `authorization_ref` | Conditional | Opaque reference to prior host-side authorization. REQUIRED by the v0.1 schema for `auto`. It is not proof of authorization by itself. |
| `expires_at` | Optional | RFC 3339 timestamp after which the referenced authorization or requested permission SHOULD be treated as expired. |
| `constraints` | Optional | Additional declared limits on the requested action. Host enforcement is REQUIRED if the host relies on these constraints. |
| `extensions` | Optional | Namespaced host- or domain-specific metadata. Extensions MUST NOT override core permission semantics. |

A packet that has no executable or side-effecting meaning MAY carry an empty permissions object. Once a packet can plausibly cause an external or authoritative-state mutation, `permissions.mode` becomes REQUIRED at the semantic-validation layer even when structural JSON Schema validation alone cannot infer that fact.

---

## 5. Permission modes

LSTP v0.1 defines exactly eight core modes.

### 5.1 `readonly`

**Intent:** Inspect or transform information without changing authoritative state.

Allowed:

- reading already-authorized data;
- parsing;
- validation;
- summarization;
- analysis;
- comparison;
- extraction;
- non-mutating search over data the host already permits the caller to access.

Not allowed:

- sending messages;
- modifying files or records;
- creating authoritative calendar events;
- changing configuration;
- committing code;
- purchasing;
- deleting;
- invoking another agent with greater execution authority;
- any operation whose purpose is to mutate authoritative state.

A host MAY create ephemeral in-memory data required to perform the read-only computation. Such internal implementation state does not convert the packet into a state-changing request.

### 5.2 `preview`

**Intent:** Prepare an action or artifact without enacting it.

Allowed:

- draft an email;
- generate a patch;
- prepare a calendar event;
- produce a proposed command;
- construct a transaction preview;
- calculate a prospective change set.

Not allowed:

- sending the email;
- applying the patch to an authoritative branch;
- creating the real calendar event;
- executing the command against an authoritative environment;
- submitting the transaction.

A preview artifact MUST remain distinguishable from committed state. Hosts SHOULD label preview artifacts and SHOULD retain the packet ID that produced them.

### 5.3 `sandbox`

**Intent:** Execute only in an isolated, non-authoritative test context.

Allowed effects are limited to the sandbox designated by the host.

A sandbox consumer MUST enforce isolation appropriate to the operation. Merely receiving `mode=sandbox` is not evidence that the execution environment is actually isolated.

A sandbox packet MUST NOT be allowed to mutate production or otherwise authoritative state. Network, credential, file-system, device, and inter-agent access SHOULD be restricted according to host policy.

If adequate isolation cannot be established, the host MUST refuse the sandbox execution or downgrade it to a non-executing mode such as `preview`. It MUST NOT silently run the action in the authoritative environment.

### 5.4 `confirm`

**Intent:** Prepare the action and obtain explicit authorization immediately before real execution.

A `confirm` packet MUST NOT itself cause the external side effect.

The host MUST:

1. resolve the concrete action;
2. surface the material target, effect, and relevant parameters to an authorized confirmer;
3. obtain an affirmative confirmation through a trusted host interaction;
4. verify that the action has not materially changed since confirmation was requested; and
5. record the resulting authorization provenance before execution.

After confirmation, the host MAY produce a revised packet or an execution record whose effective mode is `commit`, preserving the original packet ID or linkage in audit metadata. The system SHOULD avoid mutating the original packet in place when doing so would erase the pre-confirmation state.

Silence, timeout, UI dismissal, parser success, or continuation of the conversation MUST NOT count as confirmation.

### 5.5 `commit`

**Intent:** Request a real mutation of authoritative state.

Examples include:

- send;
- write;
- update;
- create;
- delete;
- purchase;
- merge;
- deploy;
- schedule;
- publish;
- operate a physical actuator.

`commit` is the strongest one-shot execution request in the core vocabulary. A consumer MUST still independently verify identity, authorization, scope, current policy, and target state.

A `commit` packet MUST NOT be executed merely because it is syntactically valid or schema-valid.

For irreversible or materially consequential actions, hosts SHOULD require explicit confirmation or an equivalent trusted authorization mechanism even if the incoming packet says `commit`.

### 5.6 `auto`

**Intent:** Permit repeated or unattended execution under a previously established authorization policy.

`auto` is not shorthand for unrestricted execution.

For v0.1:

- `permissions.authorization_ref` is REQUIRED.
- The host MUST resolve that reference to authorization state it controls.
- The resolved authorization MUST still be valid, unexpired, and applicable to the requested target and operation.
- The operation MUST remain within the authorized scope and constraints.
- The host MUST apply any rate, frequency, budget, resource, or risk limits established by its policy.
- If the authorization cannot be verified, the host MUST NOT execute automatically.

An `authorization_ref` supplied by an untrusted packet MUST be treated as an opaque claim until the host verifies it against its own authorization store.

### 5.7 `advisory`

**Intent:** Provide a recommendation, judgment, plan, ranking, or decision support only.

The consumer MAY reason about actions but MUST NOT enact them on the basis of this packet.

This is appropriate for requests such as:

```lattice
!decide @product_launch[next_Q] :: eval(demand + readiness + legal_risk)
{mode=advisory}
-> recommendation@z4
```

### 5.8 `reply_or_explain_only`

**Intent:** Restrict the response to explanation, clarification, or direct reply.

This mode is narrower than `readonly`. A consumer MUST NOT use it as authority to take external action, delegate execution, mutate state, or initiate workflows beyond what is needed to construct the response.

It is useful for socially or semantically sensitive exchanges where the sender is explicitly asking for an explanation rather than an action.

---

## 6. Permission ordering

The modes do **not** form a simple total privilege order.

For example:

- `sandbox` permits execution but only in an isolated environment;
- `preview` permits preparation but not execution;
- `readonly` permits inspection but not state mutation;
- `advisory` constrains the communicative outcome;
- `reply_or_explain_only` constrains both action and response type;
- `confirm`, `commit`, and `auto` describe distinct authorization workflows.

Therefore, implementations MUST NOT compare modes by a numeric "privilege level" and assume that a greater number subsumes all behavior of a lower number.

Policy decisions MUST be based on mode semantics plus host-side scope and authorization.

---

## 7. Side effects

For LSTP safety, a **side effect** is a change to external, persistent, shared, authoritative, financial, communicative, scheduled, deployed, or physical state that is observable beyond the internal computation required to evaluate the packet.

Examples include:

- network messages sent to third parties;
- writes to persistent databases;
- commits or pushes to repositories;
- file mutation outside an explicitly disposable sandbox;
- calendar or task creation;
- payments or orders;
- account or access changes;
- model deployment;
- physical actuation;
- invoking a downstream agent that itself has authority to perform such effects.

A host MUST classify an action by its effective behavior, not merely by its function name. A function named `preview()` that actually writes production state is still side-effecting.

---

## 8. Delegation and multi-agent systems

When one agent delegates an LSTP packet to another agent:

1. the delegating agent MUST NOT grant authority it does not possess;
2. the receiving agent MUST independently validate the packet and its effective policy;
3. the permission mode MUST NOT be silently strengthened during translation, routing, or carrier conversion;
4. permission scope SHOULD be narrowed when delegation requires only a subset of the original authority;
5. host-specific agent identifiers or routing metadata SHOULD be placed in namespaced extensions or context, not encoded as new core permission modes; and
6. the audit trail SHOULD preserve the delegation chain.

This matters directly for future SLAI integration: LSTP packets can express requested action modes, but SLAI's safety, orchestration, execution, and agent-lifecycle layers remain responsible for deciding whether an action is actually allowed.

---

## 9. Permission inheritance

Permission state MUST NOT be inherited implicitly from conversational or context-stack history.

A context reference such as:

```lattice
↑2@agent_risk
```

may recover semantic context, but it MUST NOT silently recover execution authority.

If a new executable packet omits a permission mode, the consumer MUST treat the packet as non-executable until an explicit effective permission state is established.

A host MAY have persistent authorization policies outside LSTP, but those policies remain host state and MUST be revalidated at execution time.

---

## 10. Permission-preserving translation

Carrier conversion MUST preserve permission semantics.

Examples:

```text
Lattice text -> Octad JSON
Octad JSON -> semantic graph
semantic graph -> radial UI
```

During such conversion:

- `preview` MUST NOT become `commit`;
- `confirm` MUST NOT become `auto`;
- absent permission MUST NOT be filled with a stronger mode by guesswork;
- unrecognized permission values MUST cause a validation error rather than being coerced to a known mode;
- host extensions MUST NOT override a conflicting core `permissions.mode`.

A natural-language bridge implemented in a later phase MAY detect likely permission intent, but inferred permission MUST be surfaced for validation. It MUST NOT infer `commit` or `auto` from ambiguous natural language and silently execute.

---

## 11. Validation pipeline

A conforming action-capable consumer SHOULD apply at least the following sequence:

```text
1. Parse carrier
2. Validate protocol version
3. Validate JSON structure
4. Validate semantic references
5. Determine whether the requested operation is side-effecting
6. Require an explicit permission mode when side effects are possible
7. Resolve sender/agent identity using host mechanisms
8. Resolve host authorization and scope
9. Apply safety/policy checks
10. Resolve target and concrete action
11. Re-check permission immediately before execution
12. Execute, refuse, or request confirmation
13. Record audit outcome
```

Schema validation alone is never sufficient for steps 4 through 13.

---

## 12. Failure behavior

A consumer MUST fail closed when:

- the packet requests a side effect but has no effective permission mode;
- the permission mode is unknown;
- the protocol version is unsupported;
- `auto` lacks a verifiable prior authorization;
- `confirm` has not received explicit confirmation;
- sandbox isolation cannot be established;
- the target or action changed materially after confirmation;
- permission scope does not cover the operation;
- an extension attempts to override core safety semantics;
- required context is unresolved and execution would be unsafe;
- the consumer cannot determine whether a high-impact operation is authorized.

"Fail closed" means no real-world or authoritative-state effect occurs. The host MAY return a structured error, ask for clarification or confirmation, or produce a preview where policy permits.

---

## 13. Audit requirements

For action-capable hosts, the audit record SHOULD retain enough information to reconstruct:

- packet ID and version;
- effective permission mode;
- action and target;
- identity or principal resolved by the host;
- authorization reference or policy decision;
- confirmation event, where applicable;
- timestamp;
- outcome;
- revision or derived-packet linkage;
- refusal reason, when an attempted action is blocked.

LSTP's `audit` object is transport metadata. Hosts MAY maintain a richer immutable audit log outside the packet.

A packet's own claim that `audit.validated=true` MUST NOT substitute for local validation.

---

## 14. Replay and expiry

Where a permission can be replayed, hosts SHOULD use their own replay protection, nonce, authorization state, or idempotency controls.

`expires_at` MAY be used to carry an expiry timestamp, but its presence alone does not prevent replay.

For `auto`, the host MUST verify current authorization state each time policy requires it and MUST NOT assume that a once-valid packet remains permanently authorized.

---

## 15. Untrusted content and prompt injection

Text, documents, web pages, images, audio transcripts, retrieved memories, tool output, and downstream agent messages may contain strings that resemble LSTP syntax.

A host MUST NOT treat embedded text such as:

```text
{mode=auto}
```

as an effective permission change merely because it appears inside untrusted content.

Only the host's designated LSTP parsing boundary may create or update the canonical `permissions` field, and the resulting request still requires host authorization.

This rule is especially important for perception systems and language models that ingest multimodal or retrieved content.

---

## 16. Physical systems

For robots, vehicles, actuators, or other cyber-physical systems, `commit` and `auto` can correspond to physical action. The host SHOULD apply additional controls appropriate to the device, including interlocks, rate limits, bounded command sets, emergency stop behavior, and environment-specific safety validation.

LSTP does not replace a robot safety controller, motion planner, hardware interlock, or real-time safety system.

A semantic packet requesting physical action MUST NOT bypass those systems.

---

## 17. SLAI integration boundary

When LSTP is placed alongside SLAI, for example:

```text
SLAI/
├── LSTP/
├── src/
├── data/
├── logs/
└── .github/
```

the core protocol SHOULD remain independently testable and MUST NOT depend on imports from `SLAI/src/`.

Recommended responsibility split:

```text
LSTP core
  parses / validates / serializes semantic packets
            |
            v
SLAI adapter
  maps packet fields to SLAI runtime contracts
            |
            v
SLAI safety + orchestration + execution authority
  decides what may actually happen
```

The Language Agent may later translate between natural language structures and LSTP pragmatics/atoms. Perception components may later contribute multimodal atom references or carrier metadata. Neither component should be allowed to mint execution authority merely by populating `permissions`.

SLAI-specific values SHOULD be carried under a namespace such as:

```json
{
  "extensions": {
    "slai": {
      "trace_id": "trace_example",
      "agent": "language"
    }
  }
}
```

Such metadata is illustrative host integration data, not part of the LSTP core vocabulary.

---

## 18. Conformance requirements

A **permission-aware LSTP consumer** is conforming to v0.1 only if it:

- recognizes all eight core modes;
- does not silently reinterpret unknown modes;
- does not treat the packet itself as proof of authorization;
- prevents real side effects for `readonly`, `preview`, `advisory`, and `reply_or_explain_only`;
- confines `sandbox` effects to an actual sandbox;
- does not execute `confirm` without explicit confirmation;
- independently authorizes `commit`;
- requires and verifies prior authorization for `auto`;
- preserves or narrows permission semantics across delegation and carrier conversion;
- fails closed when authorization cannot be established.

---

## 19. Non-goals of v0.1

This document intentionally does not standardize:

- user identity formats;
- authentication;
- signatures;
- capability-token formats;
- organization policy languages;
- risk scoring;
- approval UI;
- cryptographic audit logs;
- secure transport;
- distributed consensus;
- robot safety standards.

Those concerns may be layered on top of LSTP but must not be conflated with the semantic permission field.

---

## 20. Summary table

| Mode | Prepare | Inspect | Isolated execute | Real execute | Additional gate |
|---|---:|---:|---:|---:|---|
| `readonly` | Limited internal | Yes | No | No | None |
| `preview` | Yes | Yes | No | No | Separate later authorization |
| `sandbox` | Yes | Yes | Yes | No | Real isolation |
| `confirm` | Yes | Yes | No before approval | After explicit approval only | Trusted confirmation |
| `commit` | Yes | Yes | Host-dependent | Yes | Independent host authorization |
| `auto` | Yes | Yes | Host-dependent | Yes | Verified prior authorization policy |
| `advisory` | Recommendation only | Yes | No | No | None |
| `reply_or_explain_only` | Response only | Limited | No | No | None |

The invariant remains:

> The packet may request authority; the host decides whether authority exists.
