# Lattice Semantic Transport Protocol (LSTP) v0.1

**Status:** Draft normative specification — Phase 1  
**Protocol name:** Lattice Semantic Transport Protocol  
**Short name:** LSTP  
**Project vision:** Lattice-Holo OS  
**Version:** 0.1  
**Core principle:** One meaning. Many carriers. Always inspectable.

---

## Abstract

The Lattice Semantic Transport Protocol (LSTP) is a semantic communication protocol for human-AI and AI-AI interaction. It represents a message as a canonical semantic packet before that message is rendered or transported through text, JSON, graph structures, visual interfaces, audio/haptic signals, or AI-native references.

LSTP v0.1 formalizes the architecture described by the project whitepaper into an implementable Phase 1 contract. The canonical semantic model is the **Octad**, consisting of:

1. pragmatics;
2. atoms;
3. relations;
4. context;
5. confidence;
6. permissions;
7. evidence; and
8. output.

The canonical packet also carries envelope metadata: packet identity, protocol version, carrier information, audit information, and optional namespaced extensions.

This specification is intentionally text-first and schema-first. It establishes the semantic contract required by the Phase 2 parser while keeping context-stack resolution, macro expansion, semantic graph compilation, radial interfaces, audio/haptic signaling, AI-native vector attachments, and natural-language bridging in their later roadmap phases.

LSTP v0.1 does not claim to eliminate ambiguity, hallucination, ontology mismatch, or unsafe execution. Its narrower goal is to make intent, references, relations, context, uncertainty, permission state, evidence state, and requested output more explicit, inspectable, and testable.

---

## 1. Status and scope

This document is the normative Phase 1 protocol specification for LSTP v0.1.

It defines:

- the canonical Octad packet model;
- top-level envelope metadata;
- structural and semantic conformance requirements;
- Lattice text-to-packet interpretation rules at the level needed to build a parser;
- carrier categories;
- confidence, evidence, and output semantics;
- extension rules;
- permission and safety boundaries;
- version and validation behavior;
- the host-integration boundary required for later use with SLAI.

It does **not** define:

- a production parser implementation;
- context-stack storage or resolution;
- macro expansion;
- a semantic graph compiler;
- radial or spatial UI behavior;
- audio/haptic encoding;
- embedding interchange;
- cryptographic semantic fingerprints;
- a natural-language translator;
- authentication, signatures, or transport encryption;
- SLAI-specific runtime code.

Those are intentionally separated from the Phase 1 protocol contract.

---

## 2. Normative language

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 (RFC 2119 and RFC 8174) when, and only when, they appear in all capitals.

JSON terms follow RFC 8259.

The canonical packet schema uses JSON Schema Draft 2020-12.

Timestamps, when present in protocol-defined timestamp fields, use RFC 3339 date-time form.

---

## 3. Design invariants

A conforming implementation MUST preserve the following invariants.

### 3.1 Canonical meaning is packet-first

The canonical semantic packet is the authoritative protocol representation of the message's encoded meaning.

A carrier may render, author, serialize, summarize, or point to the packet. A carrier is not automatically equivalent to the full packet.

### 3.2 The Octad is semantic; envelope fields are not Octad members

The Octad contains exactly eight semantic components:

```text
pragmatics
atoms
relations
context
confidence
permissions
evidence
output
```

The following top-level fields are envelope metadata:

```text
id
version
carrier
audit
extensions
```

This distinction prevents transport/audit metadata from being confused with the semantic model.

### 3.3 Inspectability

Every core semantic field MUST be representable in an inspectable symbolic form.

Optional vectors, embeddings, latent pointers, or learned representations MUST NOT become the sole authoritative representation of the packet.

### 3.4 Recoverable compression

Lattice text may be compact, but a conforming parser MUST preserve the semantic distinctions represented by the source.

Compression MUST NOT silently erase permission state, confidence, evidence status, context references, or requested output semantics.

### 3.5 Safety is not inferred from syntax

A valid packet may request an action but cannot grant itself authority.

`permissions.mode` communicates requested permission semantics. A host MUST independently enforce identity, authorization, safety, and execution policy.

### 3.6 Semantic equivalence does not require textual identity

Round-tripping:

```text
Lattice text -> Octad packet -> Lattice text
```

SHOULD preserve meaning, but it does not need to reproduce whitespace, ordering of equivalent constraint entries, or the exact original shorthand.

---

## 4. Terminology

### 4.1 Packet

A complete LSTP JSON object containing the Octad plus required envelope fields.

### 4.2 Octad

The eight semantic fields: pragmatics, atoms, relations, context, confidence, permissions, evidence, and output.

### 4.3 Lattice text

The human-readable symbolic carrier defined by `spec/grammar.ebnf` and `spec/operator-table.md`.

### 4.4 Carrier

A representation, authoring surface, rendering, signal, or pointer associated with a packet.

### 4.5 Full encoding carrier

A carrier capable of preserving the full semantic packet. In the current architecture these include Lattice text, JSON packet representation, and semantic graph representation when the graph compiler is implemented.

### 4.6 Structured rendering carrier

A visual or spatial representation that can expose most packet structure but may hide detail behind interaction or zoom.

### 4.7 Signal carrier

A compact attention/status signal, such as audio or haptic output, that generally does not preserve the entire packet.

### 4.8 Host

The runtime that parses, validates, stores, routes, renders, reasons over, or acts on LSTP packets.

SLAI may later be one such host.

### 4.9 Producer

A component that emits LSTP text or canonical packets.

### 4.10 Consumer

A component that accepts and interprets LSTP text or packets.

### 4.11 Semantic validation

Validation beyond JSON shape: reference resolution, permission requirements, known vocabulary semantics, context availability, and host constraints.

### 4.12 Extension

Namespaced data outside the core vocabulary that does not alter the meaning of core fields.

---

## 5. Architecture

LSTP retains the seven-layer architecture established by the whitepaper:

```text
Layer 0: Semantic Kernel
Layer 1: Lattice Text
Layer 2: Semantic Graph
Layer 3: Context Stack
Layer 4: Multimodal Interface
Layer 5: AI-Native Compression
Layer 6: Safety and Permissions
```

Phase 1 fully specifies the semantic kernel, the text grammar contract, and the permission semantics required for later implementation.

The remaining layers are intentionally staged:

```text
Phase 1  specification + schema
Phase 2  tokenizer + parser + packet compiler + validation + CLI
Phase 3  context stack + macros
Phase 4  semantic graph compiler
Phase 5  radial UI
Phase 6  audio/haptic signaling
Phase 7  AI-native exchange + vector attachments + fingerprints
Phase 8  natural-language bridge
```

A Phase 1 decision MUST NOT unnecessarily couple the core packet to a later rendering or host implementation.

---

## 6. Canonical packet structure

A complete v0.1 packet has the following shape:

```json
{
  "id": "pkt_example_001",
  "version": "0.1",
  "pragmatics": {},
  "atoms": {},
  "relations": [],
  "context": {},
  "confidence": {},
  "permissions": {},
  "evidence": {},
  "output": {},
  "carrier": {},
  "audit": {},
  "extensions": {}
}
```

`extensions` is optional. Every other top-level field shown above is REQUIRED by `spec/octad-schema.json`.

The structural schema is authoritative for JSON shape. This document is authoritative for semantic requirements that JSON Schema cannot fully express.

---

## 7. Packet identity and version

### 7.1 `id`

`id` is an opaque packet identifier.

Requirements:

- MUST be a non-empty string;
- SHOULD be stable for the lifetime of that logical packet revision chain;
- MUST NOT be assumed to be a UUID;
- MUST NOT be interpreted as authorization;
- SHOULD be recorded in host audit logs where packets can trigger actions.

Examples:

```text
pkt_example_001
pkt_correct_message_001
```

LSTP v0.1 does not standardize global uniqueness generation.

### 7.2 `version`

For this specification:

```json
"version": "0.1"
```

is REQUIRED.

A v0.1 consumer MUST reject or explicitly route an unsupported version rather than guessing compatibility.

Future version-negotiation rules are outside the scope of v0.1.

---

# Part I — The Octad

## 8. Pragmatics

`pragmatics` describes why the packet exists and what communicative act it performs.

Example:

```json
{
  "pragmatics": {
    "intent": "question",
    "action": "request_reason",
    "force": [
      "correction",
      "accusation",
      "question"
    ],
    "tone": "frustrated_direct",
    "urgency": "high"
  }
}
```

### 8.1 Core fields

| Field | Meaning |
|---|---|
| `intent` | Primary communicative intent or class of message |
| `action` | Symbolic action/request identifier |
| `force` | One or more communicative-force labels |
| `tone` | Optional interactional tone metadata |
| `urgency` | Optional urgency label |
| `extensions` | Namespaced pragmatics extensions |

The core schema intentionally does not close `intent`, `action`, `force`, `tone`, or `urgency` to a fixed ontology in v0.1. The project does not yet have a versioned ontology registry, and pretending otherwise would create false interoperability.

A producer SHOULD use stable, documented identifiers within its vocabulary.

### 8.2 Lattice force mapping

The text prefixes have the following core interpretation:

```text
!   directive
!!  urgent directive
?   interrogative
.   declarative/contextual
```

The parser MUST preserve the action identifier that follows the prefix.

`!!` MAY affect host prioritization, but MUST NOT elevate permissions.

### 8.3 Multiple main clauses

A Lattice document may contain more than one communicative clause.

When multiple clauses form one packet, the compiler SHOULD preserve all meaningful forces in `pragmatics.force`. If no single intent faithfully describes the packet, a producer MAY use a neutral value such as `mixed` while retaining the individual forces.

The exact application ontology remains inspectable rather than hidden in parser heuristics.

---

## 9. Atoms

`atoms` contains the entities, concepts, documents, data, people, claims, objects, or symbolic values referred to by the packet.

Example compatible with the whitepaper shorthand:

```json
{
  "atoms": {
    "message": "@message",
    "dog": "@dog",
    "claim": "dog_color"
  }
}
```

Structured form:

```json
{
  "atoms": {
    "sales": {
      "kind": "dataset",
      "label": "sales",
      "ref": "host://dataset/sales",
      "attributes": {
        "period": "-4Q"
      }
    }
  }
}
```

### 9.1 Atom keys

Atom map keys use core identifiers:

```text
[A-Za-z_][A-Za-z0-9_-]*
```

The key is local to the packet unless an external ontology or host explicitly provides broader identity semantics.

### 9.2 Atom values

v0.1 permits scalar shorthand and structured atom objects.

Structured atoms may carry:

- `kind`;
- `label`;
- `value`;
- `ref`;
- `attributes`;
- `extensions`.

The schema does not dereference `ref`. URI schemes such as `host://` are examples of host data and are not standardized LSTP schemes.

### 9.3 Reference form

Lattice text uses:

```lattice
@name
@qualified.path
```

as symbolic references.

A semantic validator SHOULD verify references that are required for execution or reasoning. JSON Schema cannot guarantee referential integrity between relation endpoints and the `atoms` map.

---

## 10. Relations

`relations` is an ordered array of typed semantic links.

Example:

```json
{
  "relations": [
    {
      "type": "corrective_claim",
      "subject": "@dog",
      "predicate": "color",
      "object": "blue"
    }
  ]
}
```

Each relation requires:

- `type`;
- `subject`.

It may also include:

- `id`;
- `predicate`;
- `object`;
- `arguments`;
- `qualifiers`;
- `extensions`.

### 10.1 Why `type` and `predicate` are separate

The whitepaper examples use both high-level relation categories and predicates. v0.1 preserves that distinction:

- `type` classifies the relation itself;
- `predicate` names the property or semantic predicate where useful.

Example:

```json
{
  "type": "assert",
  "subject": "@message",
  "predicate": "is_incorrect"
}
```

### 10.2 Relation endpoint semantics

A relation endpoint may be an atom reference or explicit literal.

A consumer MUST NOT assume that a string beginning with `@` resolves successfully merely because it matches the lexical form.

### 10.3 No invented semantics for undefined glyphs

The draft whitepaper includes notation such as `<=` without defining it in the operator table.

Core v0.1 therefore does not assign `<=` a causal, ordering, implication, or comparison meaning.

Strict Lattice parsers SHOULD reject undefined core glyphs. Extension parsers MAY preserve them only when an explicit vocabulary defines their semantics.

This rule protects later SLAI reasoning components from receiving relationships whose meaning was guessed by the parser.

---

## 11. Context

`context` carries references to prior semantic frames and context variables.

Example:

```json
{
  "context": {
    "refs": [
      {
        "depth": 2,
        "agent": "agent_risk"
      }
    ]
  }
}
```

The draft compatibility form:

```json
{
  "context": {
    "prior_message_ref": "ctx↑1"
  }
}
```

is accepted by the schema, but canonical producers SHOULD prefer structured `refs`.

### 11.1 Context reference

Lattice:

```lattice
↑0
↑2
↑2@agent_risk
```

Canonical structured representation:

```json
{
  "depth": 2,
  "agent": "agent_risk"
}
```

A context reference identifies a requested stack location. It does not contain the referenced content.

### 11.2 Phase boundary

The syntax of context references is v0.1.

Resolution of:

- `ctx.push`;
- `ctx.pop`;
- `↑n`;
- `↑n@agent`;

is a Phase 3 runtime responsibility.

A Phase 2 parser MUST be able to preserve the reference without inventing the missing context.

### 11.3 Permissions are not inherited from context

Context may recover semantic information. It MUST NOT silently recover or strengthen action authority.

A new side-effecting packet still requires an explicit effective permission mode and host authorization.

---

## 12. Confidence

`confidence` makes explicit a packet-level certainty, uncertainty, or required-confidence signal.

Example:

```json
{
  "confidence": {
    "type": "speaker",
    "value": 0.95
  }
}
```

### 12.1 Value range

Numerical confidence values MUST be in:

```text
0.0 <= confidence <= 1.0
```

### 12.2 Fields

| Field | Meaning |
|---|---|
| `type` | Label identifying the confidence interpretation/source |
| `value` | Stated packet-level confidence |
| `required` | Required threshold when the packet expresses one |
| `approximate` | Whether approximation is explicitly signaled |
| `extensions` | Namespaced specialized confidence data |

The schema does not force a closed `type` vocabulary because the whitepaper does not yet define one.

### 12.3 `%` text marker

At packet level:

```lattice
%0.82
```

maps to:

```json
{
  "confidence": {
    "value": 0.82
  }
}
```

### 12.4 `~`

A suffix:

```lattice
cause~
```

marks the immediately preceding term as approximate/uncertain.

The compiler MUST preserve that distinction. It MUST NOT fabricate a numeric probability from `~`.

### 12.5 Claim-specific confidence

The whitepaper includes claim-level confidence examples, but the canonical relation-level confidence vocabulary is not yet standardized.

v0.1 therefore permits a producer to retain more specific confidence data in an appropriate namespaced extension rather than pretending a universal attachment model exists.

---

## 13. Permissions

`permissions` states the requested action mode.

Core modes:

```text
readonly
preview
sandbox
confirm
commit
auto
advisory
reply_or_explain_only
```

Normative behavior is defined in `spec/permissions-safety.md`.

### 13.1 Critical invariant

A permission mode is a semantic request, not proof of authorization.

A packet containing:

```json
{
  "permissions": {
    "mode": "commit"
  }
}
```

MUST NOT cause execution solely because the packet is syntactically, structurally, or semantically valid.

### 13.2 Side-effecting packets

If a packet can plausibly cause an external or authoritative-state side effect, semantic validation MUST require an explicit `permissions.mode`.

Structural JSON Schema validation cannot always infer whether an arbitrary symbolic action is side-effecting. That check therefore belongs to the consumer or host policy layer.

### 13.3 `auto`

The v0.1 schema requires `authorization_ref` when `mode` is `auto`.

The host MUST independently resolve and validate that reference.

---

## 14. Evidence

`evidence` makes support, missing support, assumptions, and challenge paths inspectable.

Example:

```json
{
  "evidence": {
    "provided": [
      "support_tickets",
      "funnel_drop",
      "user_interviews"
    ],
    "needed": [],
    "assumptions": [
      "pricing_constant"
    ],
    "challenges": [
      "check cohort_by_channel"
    ]
  }
}
```

### 14.1 Evidence does not equal truth

A packet can contain false, incomplete, irrelevant, or misinterpreted evidence.

LSTP does not certify evidence validity. It provides structure in which evidence status can be inspected.

### 14.2 Evidence item

v0.1 accepts either a concise string or a structured item carrying fields such as:

- `id`;
- `type`;
- `source`;
- `ref`;
- `description`;
- `supports`;
- `extensions`.

The protocol does not standardize citation formats or source-quality metrics in v0.1.

### 14.3 Assumptions

Assumptions SHOULD be explicit when they materially affect interpretation.

Example:

```lattice
{assume:market_stable}
```

### 14.4 Challenges

Challenge paths identify checks that could falsify, weaken, or refine the current interpretation.

Example:

```lattice
challenge[check_cohort_by_channel]
```

A challenge is not automatically executed. Permission rules still apply.

---

## 15. Output

`output` describes the requested response representation and semantic detail.

Example:

```json
{
  "output": {
    "format": "brief",
    "zoom": 2
  }
}
```

### 15.1 Format

`format` is a symbolic requested format such as:

```text
brief
memo
recommendation
explanation
action_items
draft
```

v0.1 intentionally does not define a closed registry of output formats.

### 15.2 Zoom

Canonical values:

```text
0, 1, 2, 3, 4, 5, "max"
```

Text mapping:

```text
@z0   -> 0
@z1   -> 1
@z2   -> 2
@z3   -> 3
@z4   -> 4
@z5   -> 5
@zmax -> "max"
```

Semantics:

| Zoom | Meaning |
|---|---|
| `0` | Signal only |
| `1` | Minimal answer |
| `2` | Concise useful answer |
| `3` | Working detail |
| `4` | Deep analysis |
| `5` | Full reasoning structure |
| `"max"` | Maximum available expansion |

Zoom is a semantic-depth request, not a guaranteed number of tokens, sentences, graph nodes, or reasoning steps.

### 15.3 Requirements

Additional response requirements MAY be represented in `output.requirements`.

Permission constraints MUST NOT be placed there as a way to bypass the `permissions` field.

---

# Part II — Envelope Metadata

## 16. Carrier

`carrier` identifies how the packet was authored, received, or preferably rendered.

Core carrier identifiers in the v0.1 schema are:

```text
lattice_text
json_packet
semantic_graph
radial
spatial
audio_signal
haptic_signal
vector_pointer
other
```

### 16.1 Carrier categories

The project architecture distinguishes:

#### Full encoding carriers

- Lattice text;
- JSON packet;
- semantic graph.

#### Structured rendering carriers

- radial UI;
- spatial interfaces.

#### Signal carriers

- audio signal;
- haptic signal.

#### Assistive/pointer carriers

- vector pointers and later semantic fingerprints.

A signal or vector pointer MUST NOT be treated as if it independently preserves the entire Octad.

### 16.2 `source`

Identifies the observed input carrier where known.

### 16.3 `preferred`

Identifies a requested rendering carrier.

Example:

```json
{
  "carrier": {
    "source": "lattice_text",
    "preferred": "radial"
  }
}
```

### 16.4 Carrier conversion

Conversion MUST preserve core semantic fields.

Permission state, confidence, evidence state, and context references MUST NOT silently disappear during carrier conversion.

---

## 17. Audit

`audit` contains packet-level provenance and validation metadata.

Example:

```json
{
  "audit": {
    "created_by": "user",
    "created_at": "2026-08-28T16:46:00+02:00",
    "source_carrier": "lattice_text",
    "validated": true,
    "schema_version": "0.1",
    "revision": 1
  }
}
```

Fields are metadata, not authority.

In particular:

```json
"validated": true
```

is only a claim carried by the packet. A consumer that depends on validation MUST validate locally.

### 17.1 Timestamps

When `created_at` is present, it MUST be an RFC 3339 date-time.

### 17.2 Revisions

`revision` is a positive integer.

v0.1 does not standardize merge semantics, distributed revision control, or cryptographic provenance.

---

## 18. Extensions

`extensions` provides explicit namespace space for host- and domain-specific data.

Example:

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

Rules:

1. extension keys SHOULD identify their owning implementation, project, organization, or domain;
2. extensions MUST NOT redefine or override a core field;
3. a core consumer MAY preserve an unknown extension without understanding it;
4. an unknown extension MUST NOT be treated as granting permission;
5. removing an unknown extension MUST NOT change the meaning of already-present core fields;
6. extension data required for safe execution MUST be understood and validated by the host before execution.

The example namespace `slai` is illustrative. It does not make SLAI metadata part of LSTP core.

---

# Part III — Lattice Text

## 19. Text carrier overview

Lattice text is the primary human-auditable serialization targeted by the first parser.

General form:

```lattice
<intent><action> @<target>[<scope>] :: <operations>
{constraints}
-> <output>@z<n>
%<confidence>
; metadata
```

Example:

```lattice
!analyze @sales[-4Q] :: cmp(region) + detect(anomaly) + infer(cause~)
{mode=readonly, assume:market_stable}
-> brief@z2
%0.82
; ctx↑0
```

The exact syntax is defined by `spec/grammar.ebnf`; operator meaning is defined by `spec/operator-table.md`.

---

## 20. Text encoding and lexical rules

Lattice source MUST be UTF-8.

Core unquoted identifiers are deliberately restricted to:

```text
[A-Za-z_][A-Za-z0-9_-]*
```

Qualified identifiers are dot-separated core identifiers.

This restriction keeps the first tokenizer deterministic across Python environments and platforms while still allowing arbitrary Unicode content inside strings and external atom data.

The restriction is lexical, not linguistic: it does not imply that LSTP is English-only.

---

## 21. Main clause mapping

### 21.1 Directive

```lattice
!analyze @sales :: detect(anomaly)
```

maps conceptually to:

```json
{
  "pragmatics": {
    "intent": "directive",
    "action": "analyze"
  },
  "atoms": {
    "sales": "@sales"
  }
}
```

and relations/operation structure representing `detect(anomaly)`.

The exact operation ontology is not standardized in v0.1. The parser/compiler MUST preserve the symbolic operation rather than map it to arbitrary executable code.

### 21.2 Question

```lattice
?risk @strategy
```

expresses interrogative force.

### 21.3 Declarative form

```lattice
.note @experiment :: result(valid)
```

expresses declarative/contextual force.

### 21.4 Urgent directive

```lattice
!!alert @operator :: inspect(sensor_fault)
```

expresses urgency but does not bypass permissions.

---

## 22. Operation expressions

`::` begins an operation expression.

Function-like forms are symbolic:

```lattice
cmp(region)
detect(anomaly)
infer(cause~)
```

A parser MUST NOT directly dispatch arbitrary function names to host code.

A host adapter MAY map known symbolic operations to registered capabilities after validation and authorization.

`+` composes sibling terms.

`|` expresses alternatives.

Unary `-` expresses exclusion outside signed scope literals.

Parentheses group expressions.

---

## 23. Scope

Target scope follows a target:

```lattice
@sales[-4Q]
@product_launch[next_Q]
```

The grammar preserves signed period-like values and filters, but v0.1 does not claim a universal calendar or domain interpretation for every unit.

A domain vocabulary SHOULD define the meaning of scope units it uses.

---

## 24. Constraints

Constraint blocks use braces:

```lattice
{mode=readonly, assume:market_stable}
```

Recognized core mappings include:

- `mode` -> `permissions.mode`;
- `tone` -> `pragmatics.tone`;
- `assume` -> `evidence.assumptions`.

Other keys may become output requirements, host constraints, or extensions according to the registered vocabulary.

Unknown keys MUST NOT be interpreted as permission aliases.

---

## 25. Output

Text:

```lattice
-> brief@z2
```

canonicalizes to:

```json
{
  "output": {
    "format": "brief",
    "zoom": 2
  }
}
```

---

## 26. Confidence

Text:

```lattice
%0.82
```

canonicalizes to packet-level confidence.

The value MUST be within `[0,1]`.

The `~` postfix marks approximation of the immediately preceding term and MUST remain inspectable.

---

## 27. Context and macros

### 27.1 Context

The grammar recognizes:

```lattice
ctx.push{domain=startup, metric=activation, period=-3M}
?bottleneck ↑0 -> answer@z2
```

and:

```lattice
?risk ↑2@agent_risk -> summary@z2
```

Phase 2 is responsible for parsing these forms into an AST/packet representation.

Phase 3 is responsible for the actual stack behavior.

### 27.2 Macros

The grammar recognizes:

```lattice
def #Decision = {
  options + criteria + tradeoffs + reversibility + risks + recommendation
}
```

and:

```lattice
!decide @job_offer :: #Decision -> answer@z3
```

Expansion is Phase 3.

An unresolved macro MUST remain unresolved or produce a clear error. It MUST NOT be replaced by guessed content.

---

## 28. Ambiguity

Explicit ambiguity may be represented as:

```lattice
ambig{
  "bank": finance%0.62 | river_edge%0.38
}
```

The alternatives are inspectable.

A parser MUST NOT silently select one alternative merely to make parsing easier.

The protocol does not guarantee that the confidence distribution is calibrated.

---

## 29. Draft syntax corrected by Phase 1

The whitepaper is explicitly a design draft, and several examples use symbols whose semantics were not defined.

Phase 1 resolves this conservatively.

### 29.1 Postfix `↑`

`↑n` is defined as context reference.

A bare postfix form such as:

```text
churn↑
```

is not assigned a trend meaning in strict core v0.1.

Use an explicit named relation such as:

```lattice
trend(churn, up)
```

when that is the intended domain meaning.

### 29.2 `<=`

The draft evidence example uses `<=` without defining whether it means:

- less-than-or-equal;
- implication;
- causal influence;
- dependence;
- support;
- something else.

Core v0.1 therefore reserves but does not define it.

A strict parser SHOULD reject it until a vocabulary defines the operator.

### 29.3 Suffix `!`

A draft worked example includes a suffix exclamation in `incorrect!`, while `!` is otherwise a clause prefix.

Core v0.1 does not define suffix `!` as a semantic operator. Writers SHOULD represent emphasis through pragmatics or literal content rather than ambiguous punctuation.

These corrections intentionally prefer explicit meaning over speculative compression.

---

# Part IV — Canonical JSON and Validation

## 30. JSON Schema

`spec/octad-schema.json` uses JSON Schema Draft 2020-12.

Its responsibilities are structural:

- required top-level fields;
- JSON types;
- core permission enumeration;
- confidence bounds;
- zoom bounds;
- identifier patterns;
- `auto` requirement for `authorization_ref`;
- known carrier names;
- closed core objects with explicit extension points.

JSON Schema does not prove semantic correctness.

---

## 31. Structural validation

A packet is **structurally valid** when it validates against `spec/octad-schema.json` using Draft 2020-12 semantics.

Implementations SHOULD enable date-time format checking for protocol timestamp fields.

A validator MUST NOT report semantic or authorization validity merely because schema validation succeeded.

---

## 32. Semantic validation

A packet is **semantically valid for a consumer** only when the consumer can establish all applicable invariants, including:

- supported protocol version;
- required atom/reference resolution;
- supported relation/operation vocabulary;
- context availability where needed;
- macro availability where needed;
- permission-mode requirement for side-effecting operations;
- valid host authorization;
- output constraints the consumer claims to support;
- no extension conflict with core semantics.

Some semantic checks are host-dependent.

---

## 33. Conformance classes

### 33.1 Packet producer

A conforming v0.1 packet producer:

- emits schema-valid canonical packets;
- uses `version="0.1"`;
- does not put core data only in opaque extensions;
- does not claim stronger permission than intended;
- preserves uncertainty/evidence distinctions it knows.

### 33.2 Packet consumer

A conforming v0.1 packet consumer:

- validates version before relying on fields;
- validates packet structure;
- does not silently reinterpret unknown core values;
- preserves unsupported extensions if round-tripping them;
- performs required semantic validation before acting.

### 33.3 Lattice producer

A conforming strict Lattice producer emits text accepted by `grammar.ebnf` and does not rely on reserved undefined operators.

### 33.4 Lattice parser

A conforming strict parser:

- uses deterministic tokenization;
- follows `grammar.ebnf`;
- preserves syntax needed for the Octad;
- does not execute symbolic operation names during parsing;
- rejects undefined core glyph semantics;
- does not strengthen permissions;
- produces explicit errors for unresolved constructs when resolution is required.

### 33.5 Action-capable host

A conforming action-capable host additionally follows `permissions-safety.md`.

---

## 34. Error categories

Phase 2 implementations SHOULD distinguish at least:

```text
syntax_error
schema_error
semantic_error
unsupported_version
unresolved_reference
unresolved_context
unresolved_macro
permission_error
unsupported_vocabulary
```

These are recommended error categories, not mandatory wire-level error packet types in v0.1.

Errors SHOULD contain enough location/context information to be actionable without exposing secrets.

---

## 35. Serialization and ordering

JSON objects are unordered by the JSON data model.

A producer MAY use a stable human-readable field order, such as the order shown in this specification, but consumers MUST NOT assign meaning based on JSON property order.

v0.1 does not define byte-level canonical JSON for hashing or signatures.

Therefore:

- semantic equality MUST NOT depend on whitespace;
- cryptographic fingerprints MUST NOT be computed from arbitrary JSON serialization and called an LSTP semantic fingerprint;
- semantic fingerprinting remains a later roadmap item.

---

## 36. Round-trip expectations

A conforming text-to-packet-to-text pipeline SHOULD preserve:

- communicative force;
- symbolic action;
- targets;
- scopes;
- operations;
- constraints;
- permission mode;
- context references;
- confidence;
- evidence/assumption/challenge content;
- output format;
- zoom;
- extension data where supported.

It MAY normalize:

- whitespace;
- line breaks;
- quote escaping;
- ordering of map entries;
- scalar shorthand into structured atom form;
- equivalent representation details.

Permission or evidence semantics MUST NOT be dropped as "formatting."

---

# Part V — Safety, Carriers, and Host Integration

## 37. Permission safety

The normative permission model is defined separately in `spec/permissions-safety.md`.

The minimum invariant is:

> No irreversible or externally authoritative action may occur solely because LSTP text or JSON requested it.

LSTP is a semantic transport protocol, not an authorization protocol.

---

## 38. Evidence and unsupported certainty

LSTP cannot prevent a model or user from writing a false claim with high confidence.

It can, however, make the following independently inspectable:

- what is being claimed;
- how confident the sender says it is;
- what evidence is attached;
- what evidence is missing;
- what assumptions are being used;
- what checks could challenge the claim.

A consumer SHOULD avoid converting absence of evidence into positive confidence.

---

## 39. AI-native representations

The whitepaper permits optional vector references in later phases while requiring symbolic structure to remain authoritative.

v0.1 therefore does not define embedding payloads inside the Octad.

A future vector attachment SHOULD point to or accompany symbolic atoms/relations rather than replace them.

This is important for later SLAI perception integration because learned embeddings may be useful for similarity and multimodal alignment, but they are model-dependent and not inherently interoperable semantic identities.

---

## 40. Multimodal input

LSTP may later receive semantic content derived from text, images, audio, sensors, or other perception systems.

The core rule is source separation:

- perceived/derived content may populate atoms, relations, confidence, evidence, and carrier metadata;
- untrusted content inside a modality MUST NOT be allowed to rewrite permissions merely because it resembles Lattice syntax;
- source uncertainty SHOULD remain explicit;
- a perception embedding does not become the canonical packet meaning by itself.

---

## 41. SLAI integration

LSTP is intended to remain usable independently and later be installable alongside SLAI:

```text
SLAI/
├── LSTP/
├── src/
├── data/
├── logs/
└── .github/
```

### 41.1 Dependency direction

The protocol core MUST remain host-neutral.

The preferred dependency direction is:

```text
SLAI integration/adapters  --->  LSTP public parser/schema/types
```

rather than:

```text
LSTP core  --->  SLAI agents/internal modules
```

This avoids circular coupling and allows LSTP conformance tests to run independently.

### 41.2 Language Agent boundary

A future SLAI Language Agent integration can map language-analysis structures into:

```text
intent / communicative force -> pragmatics
entities                     -> atoms
semantic links               -> relations
dialogue frame               -> context
confidence                   -> confidence
```

That mapping belongs in an adapter or later natural-language bridge, not in the core v0.1 schema.

The core protocol MUST NOT assume a particular NLU model, tokenizer, grammar processor, or response generator.

### 41.3 Perception boundary

A future Perception integration can contribute:

- modality-derived atoms;
- relation hypotheses;
- confidence;
- evidence/source references;
- carrier metadata.

Learned encodings and embeddings SHOULD remain optional attachments or host references until the AI-native exchange phase defines them.

The core protocol MUST NOT assume text/vision/audio tensor shapes, model architectures, embedding dimensions, or device configuration.

### 41.4 Orchestration and execution

SLAI may route packets between agents.

LSTP permission fields MUST NOT replace SLAI's own safety, orchestration, execution, lifecycle, or authorization checks.

An agent receiving a packet MUST NOT assume the sending agent was entitled to grant the requested mode.

### 41.5 Shared memory

If SLAI later stores LSTP packets in shared memory, the packet SHOULD be treated as a versioned data contract.

Host memory keys, trace IDs, agent instance IDs, and scheduling metadata belong in host state or namespaced extensions unless a future LSTP version standardizes them.

---

## 42. Extension policy

A host MAY extend packet semantics only through an explicit namespace or registered vocabulary.

Extensions SHOULD be designed so that a core v0.1 consumer can still inspect the base packet.

An extension MUST NOT:

- redefine `mode=readonly` to permit writes;
- redefine confidence range;
- reinterpret `@z3` as an execution privilege;
- change `version` meaning;
- cause unknown extensions to execute by default.

If safe interpretation depends on an extension the consumer does not understand, the consumer MUST fail closed for action-capable use.

---

## 43. Security and privacy considerations

### 43.1 Injection

Embedded Lattice-looking text in untrusted content is data until the host deliberately parses it at an authorized protocol boundary.

### 43.2 Data leakage

Atoms, evidence, context, and audit fields may contain sensitive references. Producers SHOULD minimize unnecessary sensitive data and hosts SHOULD apply their existing access controls.

### 43.3 Denial of service

Future parsers SHOULD bound:

- nesting depth;
- macro expansion;
- context traversal;
- input size;
- relation count;
- recursion.

Macro expansion limits are especially important once Phase 3 is implemented.

### 43.4 Confused deputy

An agent or host with broader privileges MUST NOT execute a packet merely because a less-privileged sender requested `commit` or `auto`.

### 43.5 Ontology confusion

Unrecognized action/relation identifiers MUST NOT be mapped by semantic guesswork to high-impact capabilities.

---

# Part VI — Worked Examples

## 44. Read-only sales analysis

Lattice:

```lattice
!analyze @sales[-4Q] :: cmp(region) + detect(anomaly) + infer(cause~)
{mode=readonly, assume:market_stable}
-> brief@z2
%0.82
; ctx↑0
```

Representative packet:

```json
{
  "id": "pkt_sales_001",
  "version": "0.1",
  "pragmatics": {
    "intent": "directive",
    "action": "analyze",
    "force": ["directive"]
  },
  "atoms": {
    "sales": {
      "kind": "target",
      "label": "sales",
      "attributes": {
        "scope": "-4Q"
      }
    }
  },
  "relations": [
    {
      "type": "operation",
      "subject": "@sales",
      "predicate": "cmp",
      "arguments": ["region"]
    },
    {
      "type": "operation",
      "subject": "@sales",
      "predicate": "detect",
      "arguments": ["anomaly"]
    },
    {
      "type": "operation",
      "subject": "@sales",
      "predicate": "infer",
      "arguments": ["cause"],
      "qualifiers": {
        "approximate": true
      }
    }
  ],
  "context": {
    "refs": [
      {
        "depth": 0
      }
    ]
  },
  "confidence": {
    "value": 0.82
  },
  "permissions": {
    "mode": "readonly"
  },
  "evidence": {
    "provided": [],
    "needed": [],
    "assumptions": ["market_stable"],
    "challenges": []
  },
  "output": {
    "format": "brief",
    "zoom": 2
  },
  "carrier": {
    "source": "lattice_text"
  },
  "audit": {
    "schema_version": "0.1",
    "revision": 1
  }
}
```

The exact operation relation vocabulary remains implementation-defined in v0.1; the example shows an inspectable representation rather than a required ontology.

---

## 45. Preview email

Lattice:

```lattice
!email @client :: propose_meeting
{mode=preview, tone=warm+firm}
-> draft@z2
```

Safety interpretation:

- the packet may produce a draft;
- it MUST NOT send the email;
- a later send requires a distinct authorized action.

---

## 46. Context-dependent risk question

```lattice
?risk ↑2@agent_risk
-> summary@z2
```

The parser can represent the context reference in Phase 2.

If the context stack cannot resolve it, the host SHOULD return `unresolved_context` rather than guessing the missing frame.

---

## 47. Explicit correction

The draft whitepaper's emotionally loaded example can be represented without undefined postfix punctuation:

```lattice
!correct @message :: mark(incorrect)
!state @dog.color = blue
?reason @you :: lie_about(@claim)
{tone=frustrated+direct, mode=reply_or_explain_only}
-> explanation@z2
; ctx↑1
```

A packet compiler should preserve:

- correction;
- claim;
- accusation/question;
- tone;
- prior context reference;
- restricted permission mode.

It MUST NOT convert the accusation into verified fact.

---

## 48. Evidence example without undefined relational glyphs

Instead of an undefined `<=` relation:

```lattice
claim: causes(onboarding_friction, churn)
%0.74
because[evidence:support_tickets + funnel_drop + user_interviews]
assume[pricing_constant]
challenge[check_cohort_by_channel]
```

This example is valid only if the active vocabulary actually intends the named `causes` relation.

If the evidence supports correlation rather than causation, a different explicit predicate SHOULD be used.

LSTP's role is to preserve the distinction, not decide it.

---

# Part VII — Phase 1 Deliverable Contract

## 49. Required files

Phase 1 is complete only when the following repository paths are populated with real, mutually consistent content:

```text
spec/lstp-v0.1.md
spec/octad-schema.json
spec/grammar.ebnf
spec/operator-table.md
spec/permissions-safety.md
```

The roadmap also requires examples in `.lat` and `.packet.json`; those should be created after or alongside these five normative files so Phase 2 can use them as fixtures.

### 49.1 Naming

The normative Phase 1 filenames use:

```text
lstp-v0.1.md
octad-schema.json
```

not the placeholder variants:

```text
LSTP-v0.1.md
octad_schema.json
```

Keeping one canonical path prevents platform-dependent casing and tooling divergence.

---

## 50. Phase 1 acceptance criteria

Phase 1 SHOULD be considered ready for Phase 2 when:

1. `octad-schema.json` validates as a Draft 2020-12 schema;
2. all normative packet examples validate structurally;
3. invalid permission, confidence, and zoom fixtures fail as expected;
4. `grammar.ebnf` has no undefined productions;
5. every core grammar operator is documented in `operator-table.md`;
6. every core permission mode is documented in `permissions-safety.md`;
7. undefined draft glyphs are either removed from strict examples or explicitly reserved;
8. no Phase 1 file depends on SLAI imports;
9. SLAI-specific data can be carried through extensions without modifying the core Octad;
10. permission semantics cannot be strengthened by carrier conversion or extension fields;
11. text examples can be used as future Phase 2 parser fixtures;
12. the whitepaper and normative spec are clearly distinguished as design overview versus implementable contract.

---

## 51. References

Normative and technical references:

- RFC 2119 — Key words for use in RFCs to Indicate Requirement Levels.
- RFC 8174 — Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words.
- RFC 8259 — The JavaScript Object Notation (JSON) Data Interchange Format.
- JSON Schema Draft 2020-12 — Core and Validation specifications.
- RFC 3339 — Date and Time on the Internet: Timestamps.
- ISO/IEC 14977 — Syntactic metalanguage — Extended BNF. `grammar.ebnf` defines the exact EBNF conventions it uses and does not depend on parser-specific extensions being guessed.

Project reference:

- `docs/WHITEPAPER.md` — Lattice-Holo OS Whitepaper / LSTP v0.1 design whitepaper.

---

## Appendix A — Core packet field matrix

| Field | Octad? | Required top-level? | Primary role |
|---|---:|---:|---|
| `id` | No | Yes | Packet identity |
| `version` | No | Yes | Protocol version |
| `pragmatics` | Yes | Yes | Communicative purpose |
| `atoms` | Yes | Yes | Semantic entities/values |
| `relations` | Yes | Yes | Typed semantic links |
| `context` | Yes | Yes | Context references/variables |
| `confidence` | Yes | Yes | Uncertainty/confidence |
| `permissions` | Yes | Yes | Requested action mode |
| `evidence` | Yes | Yes | Support/assumptions/challenges |
| `output` | Yes | Yes | Requested response |
| `carrier` | No | Yes | Carrier metadata |
| `audit` | No | Yes | Provenance/validation metadata |
| `extensions` | No | No | Namespaced extension data |

---

## Appendix B — Core permission values

```text
readonly
preview
sandbox
confirm
commit
auto
advisory
reply_or_explain_only
```

See `spec/permissions-safety.md`.

---

## Appendix C — Core carrier values

```text
lattice_text
json_packet
semantic_graph
radial
spatial
audio_signal
haptic_signal
vector_pointer
other
```

---

## Appendix D — Non-normative integration diagram

```text
Human / AI / sensor-derived semantics
                 |
                 v
        +------------------+
        |  Lattice carrier |
        +------------------+
                 |
                 v
        +------------------+
        | parser/compiler  |   Phase 2
        +------------------+
                 |
                 v
        +------------------+
        | canonical Octad  |
        +------------------+
          |       |       |
          |       |       +------> radial / graph / later carriers
          |       |
          |       +--------------> storage / shared semantic state
          |
          v
   host adapter / policy
          |
          v
 safety + authorization + orchestration
          |
          v
      optional action
```

The canonical packet is a semantic contract. The host remains responsible for what actually happens.
