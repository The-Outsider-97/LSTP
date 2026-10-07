# LSTP
## Lattice Semantic Transport Protocol
### An executable, specification-first protocol for inspectable semantic communication between humans and AI systems

**Protocol:** LSTP v0.1  
**Document status:** Pre-training candidate protocol publication  
**Whitepaper revision:** 3.0  
**Project attribution:** LSTP project; Phase-1 protocol specification attributed in-repository to Garrick Montgomery  
**Repository analysis date:** 7 October 2026  
**LSTP state:** reconciled v0.1 baseline on `main` @ `da804741bc34e3ff4dbe7178f022286b3f6c4893`  
**SLAI state:** `main` @ `ec55660b02db84305409cc14aa5ba230052927f5`

> **One meaning. Many carriers. Always inspectable.**
>
> This is a design objective, not an empirically established guarantee of semantic equivalence.

---


## Abstract

The Lattice Semantic Transport Protocol (LSTP) is a specification-first protocol for representing and transporting structured semantic content between humans, AI systems, and AI agents. It addresses a recurring engineering problem in AI-mediated communication: natural-language messages often entangle communicative intent, entities, relations, context, uncertainty, evidence, requested authority, and output requirements in forms that are convenient for humans but difficult to validate, replay, or audit deterministically.

LSTP v0.1 defines an eight-domain **Octad Packet** - pragmatics, atoms, relations, context, confidence, permissions, evidence, and output - while packet identity, protocol version, carrier metadata, audit metadata, and extensions remain outside Octad semantic equality. The project now includes an executable Python reference implementation with immutable typed models, semantic validation, canonical JSON serialization, canonical and compact Lattice parsing/compilation, a command-line interface, permission-aware host authorization, replay protection, versioned conformance fixtures, property/adversarial tests, and a dependency-free JavaScript interoperability verifier.

The Whitepaper-first contract reconciliation completed on 7 October 2026. Canonical requested permissions use the six Whitepaper modes `RO <= SUGGEST <= PREVIEW <= RW <= EXEC <= COMMIT` together with explicit scope, forbids, limits, confirmation, review, and logging constraints. Concrete execution capabilities, trusted authorization references, expiry, delegation identity, and replay state remain host-security concerns outside canonical v0.1 packet semantics.

SLAI v2.3 integration is also implemented. SLAI pins LSTP as a Git submodule at `SLAI/model/LSTP/` and exposes `SLAI/run_lstp.py`, which maps the real LanguageAgent `LinguisticFrame` into a validated canonical Octad without inferring execution authority from language intent.

The current evidence establishes executable protocol structure, canonical round trips, fail-closed behavior, and independent cross-language agreement on the shared v0.1 fixture corpus. It does **not** establish claims about reduced hallucination, reasoning quality, token efficiency, latency, or human usability; those remain empirical research questions. The project is therefore best described as a reconciled pre-training candidate with remaining clean-execution and final-release evidence gates, not as a finished production standard.

**Keywords:** semantic transport; semantic representation; AI-agent communication; domain-specific language; structured context; permissions; provenance; inspectability; Lattice; Octad Packet; SLAI.

## Reader's guide and status vocabulary

This paper uses four status terms deliberately:

- **Implemented** means executable repository code realizes the described behavior.
- **Verified** means the behavior has direct executable evidence such as conformance fixtures, property tests, or independent implementation output.
- **Specified** means a normative artifact defines the behavior even where broader empirical validation is still pending.
- **Future work** means the capability is outside the frozen v0.1 implementation or still requires empirical/operational evaluation.

The protocol contract and implementation are now materially aligned. Maturity claims therefore distinguish protocol correctness evidence from broader production evidence: a working reference implementation and interoperability corpus do not by themselves establish performance, usability, security assurance, or production readiness.

---

## Table of Contents

1. Introduction  
2. Problem Definition  
3. Design Requirements and Principles  
4. Conceptual Development  
5. LSTP Architecture  
6. Canonical Semantic Representation  
7. Lattice Language and Syntax  
8. Semantic Transport and Carriers  
9. Context and State  
10. Permissions, Safety, and Auditability  
11. Integration with SLAI v2.3  
12. Implementation State  
13. Evaluation and Validation  
14. Comparison and Related Work  
15. Limitations  
16. Future Work and Roadmap  
17. Discussion  
18. Conclusion  
References

---

# 1. Introduction

## 1.1 Background

Modern AI systems increasingly operate through structured interfaces even when their users communicate through natural language. Tool calls, typed APIs, schemas, state machines, agent messages, and policy objects all exist because free-form text alone does not provide deterministic structure for every downstream operation. At the same time, purely machine-oriented representations can obscure communicative intent and become difficult for human operators to inspect. LSTP is motivated by the gap between these two extremes.

The project proposes a semantic transport layer: a representation in which significant communication dimensions are made explicit before or during transport. The goal is not to prove that a single formal language can remove all ambiguity. Rather, LSTP asks whether semantic structure can be normalized enough to improve inspection, validation, replay, and system integration while retaining multiple carrier representations.

The broader idea resembles established separation patterns in protocol and knowledge-representation design. JSON separates structured data from application semantics (Bray, 2017); JSON Schema supplies a declarative vocabulary for describing valid JSON structures (Wright et al., 2022); RDF separates an abstract graph model from concrete serializations (Cyganiak et al., 2014); and agent communication languages distinguish message-level communicative acts from content languages and application behavior. LSTP does not replace these technologies. It applies a similar separation principle to a project-specific semantic packet intended for AI-mediated communication.

## 1.2 Scope

The current LSTP v0.1 scope comprises:

- an eight-part canonical semantic representation, the Octad Packet;
- a compact Lattice text syntax defined by EBNF;
- canonical JSON structure constrained by JSON Schema Draft 2020-12;
- an operator table that assigns lexical roles to core Lattice symbols;
- context and reference fields;
- evidence/provenance representation;
- requested permission semantics;
- output requirements;
- an architecture in which semantic content is conceptually separable from transport carrier.

The present repository provides a working parser/compiler/validator/serializer stack and a pinned SLAI v2.3 integration. Release readiness remains gated by clean executable verification and final release evidence.

## 1.3 Objectives

The technical objectives of LSTP are to investigate whether a compact protocol can:

1. make communicative intent and semantic structure more inspectable;
2. support a canonical representation that can be serialized into multiple carriers;
3. make context, evidence, confidence, permissions, and output requirements explicit;
4. preserve a clear boundary between permission representation and runtime enforcement;
5. enable future human-to-agent and agent-to-agent integration without binding semantics to one model architecture;
6. support executable conformance testing, semantic round-trip evaluation, and independent implementation checks.

These are objectives and hypotheses. No current benchmark demonstrates that LSTP achieves them better than alternative representations.

## 1.4 Non-goals

LSTP v0.1 is not presented as:

- a universal replacement for natural language;
- a universal ontology;
- a cryptographic security protocol;
- an authentication or authorization system;
- a guarantee of safe execution;
- a proof that ambiguity can be eliminated;
- a model-training method;
- a reasoning engine;
- a substitute for LANTRA or another language model;
- a complete network transport protocol comparable to TCP, HTTP, or QUIC.

The word *transport* in LSTP refers primarily to the structured conveyance of semantic content, not to packet routing at the network layer.

---

# 2. Problem Definition

## 2.1 Implicit intent and semantic entanglement

A natural-language request can contain several dimensions simultaneously. Consider a user who asks an agent to summarize a report, use only a particular data source, avoid making changes, explain uncertainty, and produce a concise answer. A language model may infer these conditions, but the conditions are not automatically available as independent machine-checkable fields. They may also be lost when one agent paraphrases the request to another.

LSTP therefore treats communicative force, semantic entities, relations, context, confidence, permissions, evidence, and requested output as distinct representational concerns. The purpose is not to claim that this decomposition is complete, but to make these concerns explicit enough to be inspected and validated.

## 2.2 Ambiguity

Ambiguity arises at lexical, syntactic, semantic, pragmatic, and contextual levels. Formalization can constrain some ambiguity while creating new requirements: symbols need vocabularies, references need resolvers, and relations need agreed semantics. A formal packet can still encode an ambiguous concept accurately - for example, by recording two candidate interpretations - rather than resolving the ambiguity automatically.

LSTP should therefore be evaluated on **ambiguity management**, not on the claim that ambiguity disappears. A useful protocol should make unresolved alternatives visible and avoid silently inventing specificity that the sender did not provide.

## 2.3 Context repetition and state drift

Long conversations and multi-agent workflows commonly repeat or paraphrase context. Repetition consumes space and may introduce drift. LSTP includes explicit thread, packet, parent, conversation, turn, binding, temporal, speaker, audience, and reference fields so that context can be linked rather than copied wholesale. The repository also defines compact context-reference notation such as `↑2` and `↑2@agent_risk` in the operator table.

However, a reference is not useful without a resolver. The current project specifies references but does not implement a context store or resolution algorithm. Resolution therefore remains a host/runtime responsibility.

## 2.4 Agent coordination

Multi-agent systems need messages that identify intent, content, conversation state, and sometimes authority. Established agent communication research has long separated performatives and conversation metadata from content. LSTP shares this design concern while adopting its own Octad structure. The current project does not provide empirical evidence that LSTP improves coordination relative to FIPA ACL, KQML, JSON messages, typed RPC, or framework-specific agent envelopes.

## 2.5 Permission ambiguity

A particularly consequential ambiguity is the difference between *requesting* an action and *being authorized* to perform it. The LSTP permissions specification explicitly separates these concerns. A packet may request `EXEC` or `COMMIT`, but the receiver must still evaluate local policy and runtime capability. This is a sound architectural boundary: a serialized field cannot authenticate its own authority.

## 2.6 Machine interpretability versus human inspectability

Highly compact encodings can improve regularity but become difficult to read. Rich natural language is easy for humans but comparatively difficult to validate structurally. LSTP attempts a middle position: canonical JSON favors explicit structure, while Lattice favors compact text with stable lexical roles. Whether this balance is successful is an empirical usability question that has not yet been tested.

---

# 3. Design Requirements and Principles

## 3.1 Canonical semantic representation

LSTP requires a canonical semantic structure so that carriers can be evaluated against the same logical packet. The v0.1 repository chooses the Octad Packet. A carrier should therefore encode or recover the eight canonical semantic fields without assigning contradictory semantics.

## 3.2 Inspectability

The project principle “One meaning. Many carriers. Always inspectable.” is best interpreted as a normative target. Inspectability requires:

- named semantic fields;
- explicit confidence rather than only rhetorical hedging;
- explicit evidence objects where provenance matters;
- explicit requested authority;
- explicit context relationships;
- deterministic diagnostics when a packet is invalid;
- preservation of unsupported extensions rather than silent semantic guessing.

Inspectability is not equivalent to correctness. A packet can be perfectly inspectable and still contain false evidence, a poor semantic mapping, or an unauthorized request.

## 3.3 Recoverability and round-trip integrity

Carrier separation is meaningful only if semantic structure can survive encoding and decoding. This motivates a future invariant:

```text
canonical(packet) = canonical(decode(encode(packet)))
```

The equality must be defined carefully. Byte identity may be unnecessary if semantically irrelevant ordering or formatting changes. A reference implementation should therefore specify a canonical comparison model before claiming deterministic serialization or round-trip fidelity.

## 3.4 Explicit permission semantics

Authority is represented as data and evaluated by the host. Permissions should narrow, never silently broaden, an operation. Forbidden scope should override allowed scope, and unsupported modes should fail closed.

## 3.5 Structured context

Context should be referential where possible, with explicit identity and lifecycle metadata. This supports replay and audit but requires resolvers and retention policies outside the protocol.

## 3.6 Extensibility without accidental semantics

The operator table states that undefined draft glyphs must not acquire invented semantics. This is a strong principle for protocol evolution. Extension namespaces, version negotiation, and compatibility rules should eventually make this principle enforceable.

## 3.7 Carrier independence

LSTP separates semantic content from carrier representation. Carrier independence should not be interpreted as “all carriers are equivalent by definition.” Equivalence must be demonstrated by conformance and round-trip tests.

## 3.8 Evidence before performance claims

A technically credible LSTP project should report measured results only after benchmarks exist. Claims such as lower token use, lower latency, fewer hallucinations, better reasoning, or improved interoperability require comparative experimental designs rather than architectural intuition.

---

# 4. Conceptual Development

Earlier LSTP documentation describes a conceptual lineage involving **Lattice**, **HoloSemantics**, and **LΩ**. These terms should be preserved only as design history unless a current normative artifact assigns them executable semantics.

## 4.1 Lattice

Lattice is the current compact text notation associated with LSTP. Unlike the historical concept alone, it now has concrete Phase-1 artifacts: an EBNF grammar and operator table. This makes Lattice part of the current specification surface, although no repository parser implements the grammar yet.

## 4.2 HoloSemantics

HoloSemantics is best treated as a historical/conceptual influence: the idea that a compact semantic representation should remain expandable into richer contextual meaning. No current executable module named HoloSemantics establishes a runtime contract. The concept may motivate semantic zoom and structured context, but it should not be described as an implemented subsystem.

## 4.3 LΩ

LΩ likewise belongs to the conceptual lineage of compact semantic expression and output-oriented structure. In the current canonical model, `Ω` has a concrete, narrower meaning: the **output** field of the Octad. Historical LΩ concepts should not be conflated with the v0.1 `output` object.

## 4.4 From concept to protocol

The current repository represents a useful transition from exploratory notation toward protocol engineering. The EBNF grammar, JSON Schema, operator table, and permission specification are materially stronger foundations than informal examples. The next transition must be from specification to executable conformance, not additional unvalidated syntax expansion.

---

# 5. LSTP Architecture

![Figure 1. Current LSTP v0.1 specification architecture.](figures/fig01_architecture.svg)

**Figure 1. Current LSTP v0.1 architecture.** The specification, canonical/compact carrier profiles, typed reference implementation, validation layer, host authorization boundary, and conformance evidence are all present; external policy and execution remain host responsibilities.

## 5.1 Semantic layer

The semantic layer is the Octad. It defines the project-specific dimensions that LSTP considers canonical for a message. This is the primary conceptual contract.


## 5.2 Lattice carriers

LSTP v0.1 distinguishes two explicit textual surfaces with one semantic Octad.

The **canonical Lattice** profile is defined by `spec/grammar.ebnf` and encodes the fixed ordered core:

```text
pragmatics | atoms | relations | context | confidence | permissions | evidence | output
```

It supports atomic, framed, named, and named-stream packet forms. The reference implementation exposes `parse_canonical_lattice()`, `compile_canonical_lattice()`, `canonical_lattice_dumps()`, and `canonical_lattice_document_dumps()`.

The **compact Lattice** profile is defined separately by `spec/compact-grammar.ebnf` and the operator table. It provides directive, interrogative, target, output, confidence, macro, zoom, and context-reference shorthand. `compile_lattice()` maps supported compact syntax deterministically into the canonical Octad and fails on ambiguous or unmappable input rather than inventing authority or context.

## 5.3 JSON representation

`spec/octad_schema.json` defines the canonical JSON shape using JSON Schema Draft 2020-12. The Python typed model and strict canonical decoder enforce the same frozen field boundary, including rejection of obsolete candidate fields and non-core permission channels.

The canonical JSON byte profile additionally defines UTF-8 encoding, recursive UTF-16 code-unit key ordering, NFC string requirements, forbidden bidirectional controls, deterministic number formatting, and duplicate-key rejection. Canonical positive fixtures must decode and re-encode byte-for-byte identically.

## 5.4 Validation and diagnostics

The reference implementation performs layered validation:

1. bounded UTF-8/JSON input validation;
2. structural/canonical field checks;
3. typed model construction;
4. semantic reference and vocabulary validation;
5. RFC 3339 and structural BCP 47 validation where applicable;
6. permission invariants such as explicit scope for side-effect-capable modes;
7. host-side authorization immediately before concrete operations.

Diagnostics use stable codes and fail closed where the implementation cannot safely infer meaning.

## 5.5 Compilation and normalization

Compact Lattice compiles into the typed canonical Octad. Relative context syntax must resolve to a stable packet identifier before canonical transport, storage, replay, or hashing. Unresolved references are rejected rather than serialized as ambiguous canonical state.

Canonical Lattice parsing and semantic validation are intentionally separable: syntactically valid packets can be inspected, while `compile_canonical_lattice()` additionally enforces semantic validity.

## 5.6 Serialization

LSTP v0.1 defines deterministic canonical JSON bytes through `spec/canonical-json-v0.1.md` and the Python serializer/deserializer. The governed canonical-Lattice surface also has a deterministic encoder and semantic round-trip tests.

The canonical-Lattice encoder fails closed on semantic fields for which v0.1 has no frozen textual representation instead of silently dropping information. This distinction is important for richer evidence metadata and extensions.

---

# 6. Canonical Semantic Representation

![Figure 2. The eight canonical semantic fields of the Octad Packet.](figures/fig02_octad.svg)

**Figure 2. The Octad Packet.** Identity, protocol/version, carrier/transport, and audit-envelope information sit outside the eight semantic fields in the v0.1 design.

## 6.1 Pragmatics (`π` / `pragmatics`)

The pragmatics field represents how the message should be understood as a communicative act. The schema requires a `type` and permits speech act, modifiers, goals, register, and urgency. Urgency is bounded from zero to one. Pragmatics should describe communication semantics; it should not be used to smuggle authorization into the packet.

## 6.2 Atoms (`A` / `atoms`)

Atoms are typed semantic units. The schema recognizes entity, concept, value, event, time, location, resource, proposition, and unknown kinds. Atom IDs follow an `aN` pattern such as `a0`. Optional role, datatype, language, attributes, and values provide additional structure.

Atoms are intentionally generic. Domain-specific interpretation still depends on shared vocabulary. This is analogous to the broader ontology problem: portability of syntax does not automatically provide portability of conceptual meaning (Gruber, 1993).

## 6.3 Relations (`R` / `relations`)

Relations connect atoms or special references such as `SELF`, `NOW`, `USER`, and `SYSTEM`. A relation has a type and arguments, and may include relation-level confidence and attributes. The relation vocabulary is not fully standardized by the current repository, so interoperability depends on agreed relation names or extension vocabularies.

## 6.4 Context (`C` / `context`)

Context is anchored by a required `thread_id`. The schema can also represent packet and parent IDs, conversation ID, turn, temporal data, location, bindings, references, speaker, and audience. These fields support replay and continuity but depend on host systems to assign identities and resolve references.

## 6.5 Confidence (`κ` / `confidence`)

The packet-level confidence value is a number from zero to one. The specification does not establish that this value is statistically calibrated. Consumers should therefore treat it as represented confidence unless calibration methodology is supplied by the producer. Future evaluation should distinguish syntactic preservation of confidence from predictive calibration.

## 6.6 Permissions (`Π` / `permissions`)

Permissions represent requested authority. The current modes are `RO`, `RW`, `EXEC`, `PREVIEW`, `COMMIT`, and `SUGGEST`. The permissions object can also express scope, forbids, cost/time limits, confirmation, review, and logging requirements.

The mode is not a capability token. A receiving runtime must intersect the request with local policy and available capabilities.

## 6.7 Evidence (`E` / `evidence`)

Evidence provides provenance-like support for claims or requests. The Lattice grammar includes evidence constructors for user, sensor, model, tool, retrieved, and inferred sources. This is compatible with the broader principle that provenance records should support assessment of how information was produced, while LSTP remains substantially simpler than W3C PROV-DM (Moreau & Missier, 2013).

## 6.8 Output (`Ω` / `output`)

Output describes requested response representation. The grammar supports `NL`, `LATTICE`, `JSON`, `YAML`, `TABLE`, `CODE`, `FILE`, and `NONE`, with optional schema, channel, target, language, and maximum byte constraints. A requested format does not guarantee that the receiver can or should satisfy it; inability should be surfaced rather than silently changing semantics.

## 6.9 Invariants

The JSON Schema requires all eight Octad fields and disallows unspecified top-level properties. The reference implementation enforces or tests the following key invariants:

- every relation argument referring to an atom must resolve to an existing atom ID unless it is an allowed special reference;
- context parent links must not create invalid cycles where a host forbids them;
- permissions must not be widened during serialization or translation;
- unknown extension data must not override core permission fields;
- confidence values must remain in the allowed range;
- decode/encode paths must preserve semantic equality under a defined canonicalization function.

Several are semantic invariants and are therefore enforced by typed/semantic validation rather than JSON Schema alone.

---

# 7. Lattice Language and Syntax

## 7.1 Canonical Octad syntax

The current EBNF defines the canonical text representation. The following example is derived directly from that grammar:

```lattice
[π=(TYPE=REQUEST,SPEECH_ACT=COMMAND)
 |A=(a0:ENT("door"){ROLE=TARGET})
 |R=(OPEN(a0))
 |C=(THREAD="t1")
 |κ=0.95
 |Π=(MODE=EXEC,SCOPE=["door"])
 |E=(USER("open the door"))
 |Ω=(FORMAT=NL)]
```

This is a **grammar-level example**, not a parser-verified execution trace, because the repository parser is not implemented.

## 7.2 Framing and naming

The grammar recognizes:

```text
atomic_packet = octad_core
framed_packet = "[" octad_core "]"
named_packet  = IDENT ":" framed_packet
stream_packet = named_packet { packet_sep named_packet }
```

This design supports individual packets and named streams while keeping the Octad core ordered.

## 7.3 Pragmatics syntax

The canonical pragmatics segment uses named entries such as `TYPE`, `SPEECH_ACT`, `MOD`, `GOAL`, `REGISTER`, and `URGENCY`. The operator table also defines compact communicative prefixes such as `!`, `!!`, `?`, and a leading `.`. These compact forms require a compiler mapping into canonical pragmatics before they can be treated as equivalent representations.

## 7.4 Atoms and relations

Atoms use typed constructors such as:

```lattice
a0:ENT("report"){ROLE=TARGET}
a1:CONCEPT("risk")
```

Relations use function-like relation names:

```lattice
R=(SUMMARIZE(a0), EVALUATE(a1))
```

The syntax does not imply that arbitrary relation identifiers execute host functions. A host must map known semantic operations to capabilities explicitly.

## 7.5 Context

Canonical context fields include thread, packet, parent, conversation, turn, time, timezone, window, location, bindings, references, speaker, and audience. Compact context references such as `↑2` are defined by the operator table but require a runtime resolver.

## 7.6 Confidence and approximation

Canonical packet confidence is represented by `κ=number`. The compact operator table additionally assigns `%0.82` as a confidence marker and `~` as an approximation marker. The two are not equivalent: `~` denotes qualitative uncertainty while `%` carries an explicit numeric value.

## 7.7 Permissions

Canonical permission syntax includes:

```lattice
Π=(MODE=PREVIEW,
   SCOPE=["report"],
   FORBID=["external-write"],
   REQUIRE_CONFIRM=true,
   LOG=true)
```

Permission syntax must be preserved through carrier transformations because accidental widening is a safety-relevant semantic error.

## 7.8 Output

Canonical output fields specify format and related constraints. The compact operator table defines `->` and semantic zoom markers such as `@z2`. Zoom expresses desired semantic depth, not a guaranteed token count.

## 7.9 Macros and extensions

Macro reference syntax exists, but macro expansion is deferred. The operator table is explicit that unresolved macros must not be silently replaced with guessed content. This principle should generalize to all unsupported extensions.

## 7.10 Syntax discipline

Earlier illustrative LSTP prose used overloaded or undefined symbols. The current operator table is intentionally stricter: undefined postfix trend glyphs, for example, should not acquire invented meanings. This improves protocol discipline and should be retained in the implementation.

---

# 8. Semantic Transport and Carriers

## 8.1 Meaning versus carrier

The central architectural claim of LSTP is a separation:

```text
semantic packet != carrier representation
```

A semantic packet describes meaning as represented by the Octad. A carrier determines how that structure is encoded for transport or inspection. In the present repository, Lattice and canonical JSON are the meaningful specification targets.

## 8.2 Current carriers

### Lattice text

Canonical and compact Lattice are specified by separate EBNF profiles and implemented by separate parser/compiler paths. Versioned positive/negative fixtures and semantic round-trip tests provide executable conformance evidence.

### Canonical JSON

Canonical JSON is constrained by JSON Schema and a deterministic byte profile. The Python implementation and independent JavaScript verifier reproduce shared canonical bytes for the current v0.1 fixtures. JSON itself remains only a carrier; generic JSON systems do not automatically understand LSTP semantics.

## 8.3 Conceptual carriers

Earlier project material discusses broader carrier possibilities, including natural-language or multimodal representations. At the analyzed commit these are **conceptual/future**. A carrier should not be described as supported until it has:

- a formal mapping to the Octad;
- encoder/decoder implementations;
- positive and negative fixtures;
- semantic round-trip tests;
- extension/version behavior;
- documented failure modes.

## 8.4 Carrier negotiation

The current repository does not implement carrier negotiation. A future protocol envelope should identify protocol version, carrier profile, canonicalization rules, and extension namespaces. Negotiation must remain outside the Octad because these are transport/envelope concerns rather than semantic fields.

---

# 9. Context and State

## 9.1 Packet relationships

`thread_id`, `packet_id`, `parent_packet_id`, and `conversation_id` can express message relationships. This allows a host to construct conversation graphs rather than relying only on chronological text concatenation.

## 9.2 Context references

The operator table defines stack-depth references such as `↑0`, `↑2`, and `↑2@agent_risk`. These are parseable references whose meaning depends on a host-managed context namespace. The compact compiler may accept these authoring references only when a host resolver can convert them to stable packet identifiers; canonical compilation fails closed when resolution is unavailable.

## 9.3 State ownership

LSTP should not own all conversation state. A protocol packet can reference state, but the authoritative lifecycle, retention, privacy, and mutation rules belong to the consuming environment. This is especially important in SLAI integration, where agent/task context already has its own runtime semantics.

## 9.4 Context drift

Structured references reduce repetition but can make stale references dangerous. A host resolver should verify existence, version, namespace, and access rights. For mutable context, references may require snapshot IDs or content hashes if deterministic replay is a requirement.

---

# 10. Permissions, Safety, and Auditability

![Figure 3. LSTP permission representation and the external enforcement boundary.](figures/fig03_permissions.svg)

**Figure 3. Permission representation versus enforcement.** LSTP can represent a sender's requested authority, but effective authority is determined by the consuming system.

## 10.1 Permission modes

The permissions specification defines an ordered conceptual lattice:

```text
RO <= SUGGEST <= PREVIEW <= RW <= EXEC <= COMMIT
```

The ordering expresses increasing operational authority, but a higher mode does not widen scope. `COMMIT` should therefore never be interpreted as “permission to do anything.”

## 10.2 Scope and forbids

Scope restricts the requested authority to declared resources. Forbids override allowed scope. A consuming runtime should treat ambiguity conservatively and reject requests whose target cannot be resolved safely.

## 10.3 Limits, confirmation, review, and logging

Cost/time limits and review/confirmation/logging flags are valuable because they turn operational expectations into inspectable data. They still require enforcement mechanisms. A `REQUIRE_CONFIRM=true` field has no protective effect if the runtime ignores it.

## 10.4 Effective authority

The permission specification's defensible model is:

```text
requested permission ∩ local policy ∩ runtime capability
```

This is aligned with least-privilege thinking: the packet expresses no more than a request, while the host remains authoritative.

## 10.5 Auditability

Auditability requires more than packet logging. A serious implementation should preserve:

- the original carrier representation where policy allows;
- the canonical packet after parsing/compilation;
- validation diagnostics;
- the policy decision and resolved effective authority;
- tool/action requests and results;
- relevant context identifiers;
- version/schema identifiers;
- timestamps and actor identities supplied by the host.

Cryptographic signing, tamper-evident logs, identity assurance, and non-repudiation are separate security capabilities and should not be implied by the word *audit*.

## 10.6 Evidence and provenance

The `evidence` field can improve traceability if producers populate it accurately. W3C PROV-DM demonstrates that provenance can be modeled around entities, activities, agents, and derivations (Moreau & Missier, 2013). LSTP's evidence representation is not equivalent to PROV-DM, but a future profile could define mappings for systems that need richer provenance.

## 10.7 Safety claims

The project should avoid claiming that structured permissions make an AI system safe. Safety outcomes depend on identity, policy, isolation, tool design, verification, monitoring, human oversight, and organizational controls. NIST's AI RMF similarly treats AI risk management as a socio-technical lifecycle concern rather than a single data-field problem (Tabassi, 2023).

---


# 11. Integration with SLAI v2.3

![Figure 4. Implemented LSTP integration in SLAI v2.3.](figures/fig04_slai.svg)

**Figure 4. Implemented SLAI integration boundary.** SLAI pins LSTP as an independently versioned Git submodule and maps LanguageAgent semantic output into a validated Octad without granting action authority.

## 11.1 Repository-grounded current state

SLAI `main` was integrated through PR #31 and merge commit `ec55660b02db84305409cc14aa5ba230052927f5`. The repository now contains:

```text
SLAI/
├── run_lstp.py
└── model/
    └── LSTP/    # Git submodule
```

The gitlink is pinned to LSTP commit `7f4c1dab1255d3b36364adc7227e7743679087fb`. LSTP is therefore versioned independently rather than copied into SLAI or imported by mutating `sys.path`.

## 11.2 Implemented installation architecture

SLAI declares the LSTP submodule in `.gitmodules` and installs the pinned local package through `-e ./model/LSTP`. Clones intended to use LSTP must initialize submodules, for example through `git clone --recurse-submodules` or `git submodule update --init --recursive`.

Moving the gitlink is an explicit compatibility change and should be accompanied by the integration smoke tests.

## 11.3 Human-to-LSTP flow

The implemented adapter uses SLAI's existing language stack rather than replacing it:

```text
human natural language
   -> SLAI LanguageAgent.process()
   -> LinguisticFrame
   -> deterministic frame_to_lstp()
   -> typed LSTP Octad
   -> LSTP semantic validation
   -> canonical LSTP JSON
```

The mapping uses frame intent, entities, propositional content, speech-act class, confidence, and session identity. Entity ordering is deterministic.

## 11.4 Permission boundary

Language interpretation never grants execution authority. The adapter emits empty `Permissions()`, including for directive speech acts. Write, execute, and commit authority must be established separately by a trusted host through LSTP's authorization boundary.

This prevents a linguistic classification such as "command" from being confused with permission to act.

## 11.5 Relationship with the SLAI language stack

LSTP is an interchange/validation boundary, not a replacement for `LanguageAgent`, NLU/NLG, or model training. The current SLAI repository does not expose a separate module literally named LANTRA at this boundary; the integration therefore uses the actual v2.3 public `LanguageAgent.process()` / `LinguisticFrame` interface.

Future language-model implementations may help derive or render Octads, but model output must still pass canonical validation and independent authorization.

## 11.6 Agent-to-agent use

The current merged integration demonstrates the language-to-LSTP boundary. Broader agent-to-agent adoption remains an application integration task: receivers should validate protocol version and semantics, preserve packet identity/context, and apply their own local policy before interpreting requested authority.

## 11.7 Integration evidence

SLAI includes tests for:

- deterministic frame-to-Octad mapping;
- zero-authority behavior for directives;
- strict canonical JSON round trip;
- entity-order determinism;
- a real `LanguageAgent -> LSTP` smoke path.

The final release gate still requires clean executable cross-repository evidence; the integration architecture itself is implemented and merged.

---


# 12. Implementation State

## 12.1 Normative artifacts

The reconciled v0.1 repository contains:

- `spec/CANONICAL-v0.1.md`;
- `spec/octad_schema.json`;
- `spec/grammar.ebnf` for canonical Lattice;
- `spec/compact-grammar.ebnf` for compact Lattice;
- `spec/operator-table.md`;
- `spec/permissions-safety.md`;
- `spec/vocabulary.md`;
- `spec/canonical-json-v0.1.md`.

The Whitepaper remains Level 1 authority; the technical artifacts refine it without overriding it.

## 12.2 Reference implementation

`src/lstp/` contains executable implementations for:

- immutable typed Octad and packet-envelope models;
- bounded JSON input;
- canonical JSON serialization/deserialization;
- canonical and compact Lattice parsing/compilation;
- structural and semantic validation;
- RFC 3339 and BCP 47 format checks;
- host authorization and permission attenuation;
- replay/idempotency storage with in-process and SQLite implementations;
- public package exports and CLI.

The runtime deliberately separates semantic packet validity from host authorization. Sender-controlled fields cannot authenticate themselves or become bearer capabilities.

## 12.3 Packaging and release checks

`pyproject.toml` defines package `lstp` version `0.1.0a1`, Python support from 3.11 through 3.14, a `lstp` console script, and development dependencies for pytest, Hypothesis, JSON Schema, build, Ruff, and mypy.

`tools/run_release_checks.py` provides the single release/pre-training verification entry point. It runs schema drift checks, Ruff, format checks, strict mypy, the full pytest/property/conformance suite, package build, independent JavaScript interoperability verification, and wheel/sdist installation smoke checks.

At the publication baseline, GitHub-hosted Actions jobs are being created but terminate before executing step 1 (`steps:null`), so the project does not claim a complete clean-run release result yet.

## 12.4 Conformance and tests

The repository contains a shared v0.1 conformance manifest used by both Python and the independent JavaScript verifier. Positive and negative fixtures cover canonical JSON and canonical Lattice, while deterministic property/adversarial tests cover field mutation, permission preservation, migration-field rejection, resource limits, arbitrary byte fuzz, pathological depth/numbers, and canonical round trips.

Independent JavaScript execution on Node.js v22.16.0 passed the current shared manifest with 2 positive JSON cases, 8 negative JSON semantic cases, 1 positive and 1 negative canonical-Lattice case, exact reproduction of 1,078 canonical bytes, and rejection of all 6 non-core permission channels.

## 12.5 Current maturity

The protocol contract is reconciled (`contract_reconciled=true`). The remaining blockers are not unresolved core semantics. They are:

1. clean executable release verification;
2. Whitepaper/publication synchronization;
3. final release/pre-training audit and sign-off.

This distinction is important: LSTP is no longer a scaffold-only specification, but it is also not yet a production-ready released standard.

---

# 13. Evaluation and Validation


## 13.1 Current evidence

The repository now contains executable correctness evidence but still reports no performance or human-usability result.

Current protocol evidence includes:

- canonical JSON byte-stability fixtures;
- canonical and compact Lattice parser/compiler tests;
- typed semantic round trips;
- negative semantic/reference/permission fixtures;
- deterministic property and mutation tests;
- bounded-resource and arbitrary-byte adversarial tests;
- host-authorization and replay tests;
- one independent dependency-free JavaScript verifier consuming the same conformance manifest;
- a pinned SLAI v2.3 integration and smoke-test path.

The independent JavaScript run recorded on 7 October 2026 passed the shared manifest. GitHub-hosted Python release jobs have not supplied usable execution evidence because the jobs terminate before their first step.

No benchmark currently establishes improved reasoning, hallucination rate, model quality, token efficiency, end-to-end latency, or human inspectability.

## 13.2 Evaluation framework

Validation remains separated into protocol correctness, interoperability, usability, security-relevant behavior, and computational cost.

| Dimension | Method | Current result |
|---|---|---|
| Parsing | Versioned canonical/compact fixture corpus | Implemented; clean full-suite release run pending |
| Rejection | Negative + mutation/property corpus | Implemented |
| Schema | Draft 2020-12 + structural drift gate | Implemented |
| Round trip | JSON byte equality and Lattice semantic equality | Implemented |
| Permissions | Property tests + host authorization fixtures | Implemented |
| Context | Stable-reference and fail-closed resolution tests | Implemented for protocol boundary |
| Interoperability | Independent JavaScript implementation | Passed shared v0.1 manifest |
| SLAI integration | Pinned submodule + real LanguageAgent smoke path | Implemented; clean release execution pending |
| Inspectability | Controlled user study | Not measured |
| Ambiguity | Comparative annotation study | Not measured |
| Performance | Reproducible benchmarks | Not measured |

## 13.3 Parse, schema, and adversarial validation

The v0.1 fixture corpus includes positive canonical bytes and negative cases for unknown fields, unresolved references, missing side-effect scope, duplicate identifiers, vocabulary violations, packet/context identity mismatch, and evidence-reference failures. Property tests mutate top-level and permission fields, reject obsolete candidate representations, exercise compact-to-canonical permission preservation, and enforce bounded decoding.

These tests are release evidence only when executed successfully from a clean checkout; `VERIFY-001` remains the gate for that complete run.

## 13.4 Semantic round-trip and interoperability

The implementation tests:

```text
Octad -> canonical JSON -> Octad
Octad -> canonical Lattice -> Octad
compact Lattice -> Octad -> canonical JSON -> Octad
```

Canonical JSON byte equality is stronger than semantic equality and is governed by the canonical byte profile.

The independent JavaScript verifier does not import or invoke the Python package. It independently checks canonical JSON bytes, frozen packet shape, permission boundaries, semantic references, and canonical-Lattice Octad ordering against the same manifest. Its successful shared-vector run is the current interoperability evidence.

---

## 13.5 Ambiguity evaluation

A useful experiment would compare natural-language-only messages with LSTP-mediated representations for a fixed task set. Independent annotators could measure whether intent, scope, evidence, and output requirements are recovered consistently. The experiment should also count cases where formalization introduces incorrect specificity.

## 13.6 Permission preservation

Property-based tests should attempt transformations across carriers while asserting that mode, scope, forbids, limits, confirmation, review, and logging requirements never become more permissive. Mutation testing can deliberately remove or alter permission fields to ensure validators and policy adapters fail safely.

## 13.7 Human inspectability

Inspectability should be tested rather than assumed. Participants with different technical backgrounds could identify errors in natural language, JSON Octads, and Lattice packets. Measures might include task completion time, error-detection rate, subjective workload, and confidence. Results may show that JSON is more inspectable for some users and Lattice for others.

## 13.8 Interoperability

True protocol interoperability requires at least two independent implementations. Both should consume the same fixtures and produce semantically equivalent canonical packets. A single reference implementation cannot establish interoperability by itself.

## 13.9 Performance

Only after correctness should the project measure size, parse time, serialization time, memory use, and model-facing tokenization. Token counts should be reported per tokenizer/model because there is no universal mapping from Lattice characters to model tokens.

---

# 14. Comparison and Related Work

## 14.1 JSON and JSON Schema

JSON is a general-purpose data interchange format, while LSTP defines a domain-specific semantic model that can use JSON as a carrier. JSON Schema provides structural validation but does not supply LSTP semantics. LSTP's schema correctly declares Draft 2020-12, whose specification separates core and validation vocabularies (Wright et al., 2022).

## 14.2 RDF and semantic-web representations

RDF provides an abstract graph model based on subject-predicate-object triples and supports multiple serializations (Cyganiak et al., 2014). LSTP shares the idea that abstract semantics can be separated from serialization, but the Octad is not an RDF graph model. LSTP includes pragmatic, permission, confidence, context, evidence, and output structures that reflect its AI-message focus. Conversely, RDF has mature global identifier and semantic-web ecosystems that LSTP does not currently provide.

## 14.3 Ontologies

Ontology research emphasizes explicit shared conceptualization and portable vocabularies (Gruber, 1993). LSTP's atoms and relations do not eliminate the ontology problem. Two agents can parse the same packet yet disagree about what a relation type means. Domain vocabularies or mappings remain necessary for strong semantic interoperability.

## 14.4 Agent communication languages

FIPA ACL and KQML are important precedents for representing communicative acts in agent systems. They separate message-level intent/performative from content and conversation metadata. LSTP's pragmatics and context fields address related concerns, while the Octad additionally elevates confidence, permissions, evidence, and output structure. No evidence currently establishes that LSTP is superior; the appropriate claim is that it explores a different packet decomposition.

## 14.5 Domain-specific languages

Lattice is a domain-specific language for semantic messaging. DSL research notes that specialized languages can improve domain expressiveness but impose design, tooling, maintenance, and user-learning costs (Mernik et al., 2005). LSTP must therefore justify its compact syntax through measurable benefits rather than compactness alone.

## 14.6 Structured prompting and tool/function calling

Modern AI APIs frequently use JSON-like schemas for tool calls and structured output. These mechanisms are typically application- or vendor-specific and focus on invoking functions or constraining output. LSTP's intended scope is broader: communicative pragmatics, context, confidence, evidence, permissions, and output are represented in one canonical packet. That broader scope also increases standardization difficulty.

## 14.7 RPC and message protocols

Typed RPC and event systems provide mature transport, versioning, serialization, compatibility, and tooling patterns. LSTP should learn from those systems rather than reimplement network transport. A practical architecture can place an LSTP packet inside an existing reliable transport or message bus.

## 14.8 Provenance models

W3C PROV offers a mature conceptual framework for provenance. LSTP's evidence field is intentionally lighter. If evidence becomes central to high-assurance use, mappings to richer provenance representations may be preferable to expanding LSTP into a second provenance standard.

---

# 15. Limitations

## 15.1 Implementation maturity

The reference implementation is working and the protocol contract is reconciled, but the project has not yet produced a clean full release-check execution covering every supported Python version and built artifact. Operational production claims therefore remain premature.

## 15.2 Semantic normalization

The Octad defines where semantic information goes, but not a universal method for deriving the “correct” atoms and relations from language. Different compilers or models may produce different valid packets for the same utterance.

## 15.3 Residual ambiguity

Formal syntax does not guarantee unambiguous meaning. Relation labels, atom values, domain units, and reference targets can remain ambiguous without shared vocabularies and context.

## 15.4 Ontology dependence

Interoperability requires more than syntax agreement. Domain vocabularies, stable identifiers, relation semantics, and mapping rules are still needed.

## 15.5 Schema evolution

v0.1 now has a strict version boundary, namespaced extensions, and explicit rejection of superseded candidate fields. A broader multi-version negotiation and long-term migration policy remains future release-governance work.

## 15.6 Context drift

References can become stale, inaccessible, or semantically inconsistent as state changes. The protocol does not currently specify snapshot semantics, retention, or conflict resolution.

## 15.7 Human learning cost

Lattice requires users or developers to learn specialized symbols and field structures. Compactness may reduce readability for newcomers. Human usability has not been studied.

## 15.8 Security versus permission representation

Permission fields are not security boundaries. They do not provide authentication, authorization, sandboxing, isolation, secret handling, or cryptographic integrity.

## 15.9 Carrier maturity

Canonical JSON and canonical/compact Lattice are implemented and tested. Additional carriers remain conceptual until they have explicit mappings, loss models, fixtures, and round-trip evidence.

## 15.10 Benchmarking gap

The project has no empirical evidence for claims about token reduction, model quality, latency, hallucinations, reasoning, or coordination. Such claims should remain hypotheses.

## 15.11 SLAI integration gap

The required `SLAI/model/LSTP/` gitlink and root `SLAI/run_lstp.py` launcher are implemented and merged. The remaining limitation is final clean executable cross-repository release evidence.

---


# 16. Future Work and Roadmap

## 16.1 Freeze v0.1 rather than expand it

The v0.1 semantic contract is reconciled. Until the pre-training release audit is complete, new core fields, modes, carriers, or authority mechanisms should not be added unless a demonstrated defect requires a versioned correction.

## 16.2 Complete clean executable verification

Run `tools/run_release_checks.py` from a clean checkout and archive the results. The final evidence should include schema drift checks, Ruff, formatting, strict mypy, pytest/property/conformance tests, package build, independent JavaScript interoperability, wheel installation, sdist installation, and CLI smoke checks.

## 16.3 Complete cross-repository SLAI smoke evidence

Initialize the pinned SLAI submodule, install the local LSTP package normally, and execute the real `LanguageAgent -> LinguisticFrame -> Octad -> canonical JSON` smoke test from a clean SLAI checkout.

## 16.4 Publish reproducible documentation

The Whitepaper source, source figures, and PDF build command should live in the repository. Publication generation must fail if referenced figure assets are missing and should produce a visually inspected PDF.

## 16.5 Final release and pre-training audit

The final audit should review package provenance, compatibility/migration notes, canonical fixtures, independent interoperability evidence, SLAI pinning, publication synchronization, supported Python versions, and release identifiers before `training_ready=true` is set.

## 16.6 Empirical research after protocol freeze

Performance and human-facing claims remain research work. Future studies may measure:

- natural-language versus LSTP ambiguity recovery;
- human error-detection and workload;
- tokenization by model/tokenizer;
- parse/serialize latency and memory;
- downstream reasoning or hallucination outcomes;
- larger multi-agent interoperability exercises.

These studies should report datasets, protocol versions, model/tokenizer versions, hardware, and statistical methods sufficient for reproduction.

## 16.7 Later-version extension governance

A later protocol version may standardize additional carriers, richer evidence syntax, negotiation, or host-security metadata only through an explicit versioned process. v0.1 should remain stable enough to support pre-training and interoperability baselines.

---

# 17. Discussion

## 17.1 Compactness versus readability

Lattice can be more compact than verbose JSON, but the compression moves complexity into specialized syntax. Compactness is valuable only if users and systems can still detect errors. The project should therefore treat Lattice and JSON as complementary rather than assuming one is universally preferable.

## 17.2 Flexibility versus formal rigor

Extensible relation names and attributes make LSTP adaptable, but excessive openness weakens interoperability. Conversely, a fixed global vocabulary would be unrealistic across domains. A core-plus-namespaced-extension model is likely more defensible than unconstrained global terms.

## 17.3 Expressiveness versus deterministic interpretation

The more expressive a semantic language becomes, the harder deterministic compilation can be. Macros, approximation, contextual references, semantic zoom, and domain operators all increase expressive power while increasing resolver complexity. The protocol should prefer explicit failure over silent inference when deterministic interpretation is unavailable.

## 17.4 AI efficiency versus human inspectability

A representation optimized for language-model tokenization may differ from one optimized for a human auditor. Because tokenization also varies by model, “AI-efficient” syntax cannot be inferred from character count. LSTP should optimize first for semantic correctness and inspectability, then measure model-facing efficiency.

## 17.5 Interoperability versus project-specific semantics

The Octad is intentionally project-specific. This provides focus but means external systems need adapters. Interoperability will depend on stable vocabularies, versioning, mappings, and independent implementations. Merely publishing a schema is necessary but insufficient.

## 17.6 Specification-first development: strength and risk

The project followed a specification-first path and now has a reference implementation substantial enough to expose specification defects through executable tests and independent vectors. The principal lesson is that documentation, schema, grammar, implementation, and conformance evidence must be versioned together; the earlier Whitepaper drift demonstrated the risk of allowing any one layer to outrun the others.

## 17.7 SLAI fit

The current SLAI Language Agent already performs language interpretation, context handling, response generation, and safety-related checks. LSTP should enter that architecture as a transport/representation boundary rather than duplicate language intelligence. LANTRA can remain a model capability, while LSTP can become a schema-controlled interchange form. This separation is now implemented through the pinned SLAI adapter; final clean cross-repository execution remains part of release verification.

---


# 18. Conclusion

LSTP v0.1 has progressed from a specification-only design into an executable pre-training candidate for structured semantic transport. The reconciled protocol provides the eight-field Octad, canonical JSON with deterministic bytes, canonical and compact Lattice carriers, typed validation, requested-authority semantics, host-side authorization and replay controls, a shared conformance corpus, an independent JavaScript verifier, and a pinned SLAI v2.3 integration.

The central architectural boundary remains unchanged: a packet represents semantics and requested authority, not authenticated authority. The six permission modes are interpreted together with explicit scope and constraints, while concrete execution capability, trusted authorization metadata, delegation identity, and replay protection are enforced by the consuming host.

Current evidence is sufficient to demonstrate executable structure, fail-closed behavior on the tested boundary, semantic round trips, and shared-vector cross-language agreement. It is not sufficient to claim general improvements in reasoning quality, hallucination rate, token efficiency, latency, human usability, or safety outcomes.

The remaining path to pre-training readiness is therefore finite rather than architectural: obtain a clean full release-check run, verify the merged cross-repository SLAI smoke path in that release environment, synchronize the publication artifacts, and complete the final compatibility/provenance/freeze audit. Only after those gates pass should `training_ready=true` be set.

LSTP should now prefer stability over feature growth. Further semantic expansion belongs in explicitly versioned future work so that v0.1 can serve as a reproducible training and interoperability baseline.

---

# References

Bray, T. (Ed.). (2017). *The JavaScript Object Notation (JSON) Data Interchange Format* (RFC 8259). Internet Engineering Task Force. https://www.rfc-editor.org/rfc/rfc8259

Cyganiak, R., Wood, D., & Lanthaler, M. (Eds.). (2014). *RDF 1.1 concepts and abstract syntax*. World Wide Web Consortium. https://www.w3.org/TR/rdf11-concepts/

Gruber, T. R. (1993). A translation approach to portable ontology specifications. *Knowledge Acquisition, 5*(2), 199-220. https://doi.org/10.1006/knac.1993.1008

Mernik, M., Heering, J., & Sloane, A. M. (2005). When and how to develop domain-specific languages. *ACM Computing Surveys, 37*(4), 316-344. https://doi.org/10.1145/1118890.1118892

Moreau, L., & Missier, P. (Eds.). (2013). *PROV-DM: The PROV data model*. World Wide Web Consortium. https://www.w3.org/TR/prov-dm/

Tabassi, E. (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)* (NIST AI 100-1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.AI.100-1

Wright, A., Andrews, H., Hutton, B., & Dennis, G. (2022). *JSON Schema: A media type for describing JSON documents* (Draft 2020-12). JSON Schema. https://json-schema.org/draft/2020-12/json-schema-core

### Primary project sources

LSTP project. (2025). *LSTP v0.1 - Protocol & canonical representation specification* [Draft specification]. `spec/lstp-v0.1.md`, analyzed at commit `18d947a45f2db220267f70c7ddb07112fc3181d4`.

LSTP project. (2026). *Lattice grammar* [EBNF]. `spec/grammar.ebnf`, analyzed at commit `18d947a45f2db220267f70c7ddb07112fc3181d4`.

LSTP project. (2026). *LSTP v0.1 operator table* [Normative Phase-1 reference]. `spec/operator-table.md`, analyzed at commit `18d947a45f2db220267f70c7ddb07112fc3181d4`.

LSTP project. (2026). *LSTP v0.1 Octad Packet* [JSON Schema Draft 2020-12]. `spec/octad_schema.json`, analyzed at commit `18d947a45f2db220267f70c7ddb07112fc3181d4`.

LSTP project. (2026). *Permissions and safety specification*. `spec/permissions-safety.md`, analyzed at commit `18d947a45f2db220267f70c7ddb07112fc3181d4`.

SLAI project. (2026). *SLAI v2.3 repository*, branch `SLAI-v.2.3`, analyzed at commit `ce4cfe7b1939bc862725e3cb59f488a5b96b1423`.

---

## Document traceability

| Item | State used |
|---|---|
| LSTP repository | `The-Outsider-97/LSTP` |
| LSTP branch | `main` |
| LSTP reconciled baseline | `da804741bc34e3ff4dbe7178f022286b3f6c4893` |
| SLAI repository | `The-Outsider-97/SLAI` |
| SLAI branch | `main` |
| SLAI integration merge | `ec55660b02db84305409cc14aa5ba230052927f5` |
| Analysis date | 7 October 2026 |
| Protocol version discussed | LSTP v0.1 |
| Whitepaper revision | 3.0 |

