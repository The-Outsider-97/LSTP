# LSTP - Lattice Semantic Transport Protocol

**Status:** Draft protocol specification (v0.1), Phase 1 / pre-reference-implementation  
**Repository analyzed:** `The-Outsider-97/LSTP`, branch `main`, commit `18d947a45f2db220267f70c7ddb07112fc3181d4`  
**SLAI baseline:** `The-Outsider-97/SLAI`, branch `SLAI-v.2.3`, commit `ce4cfe7b1939bc862725e3cb59f488a5b96b1423`  
**Analysis date:** 2026-09-21

LSTP is a specification-first protocol for transporting structured semantic content between humans, AI systems, and AI agents. Its current Phase-1 artifacts define a canonical eight-part semantic packet (the **Octad Packet**), a compact **Lattice** text carrier, JSON Schema validation rules, operator semantics, context references, and permission declarations.

> **One meaning. Many carriers. Always inspectable.**

This phrase expresses the design objective: semantic content should have a canonical, inspectable form that can be represented through different carriers. It is **not** an empirical claim that LSTP already guarantees identical interpretation across heterogeneous systems.

## What LSTP is

Natural-language messages often combine intent, entities, relations, context, uncertainty, authority, evidence, and desired output in an implicit form. LSTP proposes that these dimensions can be made explicit in a transport representation so that a receiver can inspect, validate, serialize, and reason about the communicated structure before taking an action.

LSTP is designed around several use cases:

- **Human -> AI:** translate a human request into an inspectable semantic packet before downstream execution.
- **AI -> AI:** exchange explicit semantic structures between agents without requiring the transport representation to be free-form prose.
- **AI -> human:** render structured packets into a human-readable carrier while preserving inspectable semantics.
- **Audit and replay:** preserve context, evidence, confidence, permissions, and output requirements as explicit packet fields.
- **Carrier separation:** distinguish semantic content from the syntax or encoding used to transport it.

LSTP is **not** intended to replace natural language universally, act as an ontology for every domain, or provide security merely by encoding a permission field. The current repository is also **not yet a runnable reference implementation**: the formal specification is substantive, while the Python runtime modules are scaffolds.

## Core principles

1. **Canonical semantics.** The Octad provides a stable semantic structure independent of a particular text or wire carrier.
2. **Inspectability.** Important communication dimensions are represented explicitly rather than hidden only in prose.
3. **Recoverable representation.** A carrier should preserve enough information to reconstruct the canonical semantic packet. Round-trip fidelity is a design requirement that still requires implementation and empirical validation.
4. **Explicit authority.** Permissions describe requested authority, scope, limits, and confirmation/review requirements. They do not grant authority by themselves.
5. **Structured context.** Thread, packet, parent, conversation, turn, temporal, speaker, audience, binding, and reference information can be represented explicitly.
6. **Carrier independence.** Lattice is the current compact text carrier and canonical JSON is the structured representation defined in the Phase-1 specification. Additional carriers remain future work unless separately implemented.
7. **Fail closed.** The permissions specification states that unsupported or disallowed operations should fail rather than silently widen authority.

## Architecture overview

The current repository contains **formal protocol artifacts**, not an executable protocol stack. The implemented repository state should therefore be understood as follows:

```text
                  CURRENT PHASE-1 ARTIFACTS

 Human / Agent intent
          |
          v
 +----------------------+       +-----------------------+
 | Lattice text syntax  |       | Canonical JSON form   |
 | grammar.ebnf         |       | octad_schema.json     |
 +----------+-----------+       +-----------+-----------+
            \                         /
             \                       /
              v                     v
             +-----------------------+
             |   Canonical Octad     |
             | π A R C κ Π E Ω       |
             +-----------------------+
                       |
             specification rules
                       |
       +---------------+----------------+
       | operator table / permissions   |
       | protocol spec / vocabulary     |
       +--------------------------------+

  Parser -> compiler -> validator -> serializer -> runtime
                    [PLANNED / SCAFFOLDED]
```

The files under `src/lstp/` currently establish intended module names (`parser.py`, `compiler.py`, `validator.py`, `serializer.py`, `runtime.py`, `cli.py`, and related modules), but at the analyzed commit they contain no substantive executable implementation. Consequently, the documentation does not describe these modules as operational.

## The Octad Packet

The canonical v0.1 semantic representation contains exactly eight semantic fields:

| Symbol | Field | Purpose |
|---|---|---|
| `π` | `pragmatics` | Communicative type, speech act, modifiers, goals, register, urgency |
| `A` | `atoms` | Typed semantic atoms: entities, concepts, values, events, times, locations, resources, propositions, unknowns |
| `R` | `relations` | Typed relations/edges connecting atoms or special references |
| `C` | `context` | Thread/conversation identity, temporal state, bindings, references, speaker and audience |
| `κ` | `confidence` | Packet-level confidence in the closed interval `[0,1]` |
| `Π` | `permissions` | Requested mode, scope, forbids, limits, confirmation/review/logging requirements |
| `E` | `evidence` | Evidence/provenance items such as user, sensor, model, tool, retrieved, or inferred evidence |
| `Ω` | `output` | Requested output representation, schema/channel/target/language/size constraints |

Packet identity, version information, carrier metadata, transport metadata, and audit-envelope information are **outside** the Octad in the v0.1 specification.

The JSON representation is governed by [`spec/octad_schema.json`](spec/octad_schema.json), which declares JSON Schema Draft 2020-12 and requires all eight top-level Octad fields.

## Lattice syntax

The normative grammar is [`spec/grammar.ebnf`](spec/grammar.ebnf). An Octad core is an ordered sequence of eight segments:

```text
π | A | R | C | κ | Π | E | Ω
```

A grammar-conforming example from the current specification is:

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

Another valid structural example using read-only authority is:

```lattice
[π=(TYPE=REQUEST,SPEECH_ACT=QUERY)
 |A=(a0:RES("quarterly-report"){ROLE=TARGET})
 |R=(SUMMARIZE(a0))
 |C=(THREAD="finance-review",TURN=3)
 |κ=0.90
 |Π=(MODE=RO,SCOPE=["quarterly-report"],LOG=true)
 |E=(USER("summarize the quarterly report"))
 |Ω=(FORMAT=NL,LANG="en")]
```

These examples are checked against the current EBNF structure and schema terminology. They have **not** been executed by a repository parser because a working parser is not present at the analyzed commit.

The repository also contains a compact operator table with directive (`!`), interrogative (`?`), target (`@`), operation (`::`), output (`->`), confidence (`%`), context-reference (`↑n`), semantic-zoom (`@z0`...`@z5`, `@zmax`), and related tokens. The operator table explicitly states that parsing should stabilize before semantics such as macro resolution are implemented.

## Repository structure

```text
LSTP/
├── README.md                  # project entry point
├── LICENSE                    # MIT, Copyright (c) 2026 J.E. Remy
├── docs/
│   ├── WHITEPAPER.md          # academic/technical publication source
│   └── LSTP_Whitepaper*.pdf   # publication PDF
├── spec/
│   ├── lstp-v0.1.md           # Phase-1 protocol specification
│   ├── grammar.ebnf           # normative Lattice grammar
│   ├── operator-table.md      # normative Phase-1 operator semantics
│   ├── octad_schema.json      # canonical Octad JSON Schema
│   ├── permissions-safety.md  # proposed permission/safety semantics
│   └── vocabulary.md          # vocabulary placeholder/minimal scaffold
├── src/lstp/                  # Python runtime/module scaffolds; not yet substantive
├── examples/                  # example scaffolds; not a validated conformance suite
└── pyproject.toml             # currently empty; packaging not yet defined
```

## SLAI integration

### Current state

At the analyzed SLAI v2.3 commit:

- there is **no** root `model/` directory;
- there is **no** root `run_lstp.py` launcher;
- the current `LanguageAgent` integrates its own language-processing path and LANTRA-facing functionality, but contains **no LSTP import or adapter**;
- no repository evidence demonstrates an operational LSTP packet path between SLAI agents.

Therefore, LSTP/SLAI integration is **not currently implemented**.

### Required target layout

The project integration target is:

```text
SLAI/
├── run_lstp.py                 # SLAI-root launcher/adapter entry point
├── model/
│   └── LSTP/                   # clone of this repository
│       ├── README.md
│       ├── LICENSE
│       ├── docs/
│       ├── spec/
│       ├── src/
│       └── examples/
├── src/
├── checkpointing/
├── applications/
├── data/
├── deployment/
└── ...
```

`SLAI/model/` must therefore be created as part of integration while the current SLAI repository does not contain it.

### Supported future integration boundaries

Based on the current SLAI v2.3 architecture, defensible integration points are:

- a **human -> LSTP -> SLAI language boundary**, where the Language Agent may consume a validated canonical packet or emit one after semantic analysis;
- an **agent -> LSTP -> agent boundary**, where SLAI message routing can carry canonical packet payloads without equating LSTP permission declarations with runtime authorization;
- a **LANTRA-adjacent language boundary**, where LANTRA remains a model/runtime component and LSTP remains a semantic transport representation; neither should be documented as replacing the other;
- a **safety boundary**, where LSTP `permissions` are inputs to host policy rather than bypasses around SLAI safety/ethics checks;
- a **context boundary**, where LSTP context references can be mapped to SLAI conversation/task state only through an explicit adapter.

All of these are **integration targets**, not present capabilities at the analyzed commits.

## Installation

Because `pyproject.toml` is currently empty and the runtime modules are scaffolds, there is no truthful package-install command or dependency set to publish yet. The reproducible operation today is repository placement.

### Platform-neutral shell

```bash
git clone --branch SLAI-v.2.3 https://github.com/The-Outsider-97/SLAI.git
cd SLAI
mkdir -p model
git clone https://github.com/The-Outsider-97/LSTP.git model/LSTP

python -m venv .venv
# Activate the environment using your platform's standard venv command.
```

### PowerShell

```powershell
git clone --branch SLAI-v.2.3 https://github.com/The-Outsider-97/SLAI.git
Set-Location SLAI
New-Item -ItemType Directory -Force model | Out-Null
git clone https://github.com/The-Outsider-97/LSTP.git model/LSTP

py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Do **not** infer or install dependencies from this README. Dependency declarations should be added only when the reference implementation defines them.

## Running LSTP

The required integrated launcher location is:

```text
SLAI/run_lstp.py
```

The intended invocation from the SLAI root is:

```bash
python run_lstp.py
```

or, on Windows installations that use the Python launcher:

```powershell
py run_lstp.py
```

**Current limitation:** `run_lstp.py` does not exist in the analyzed SLAI v2.3 branch, and the LSTP runtime/CLI modules are not implemented. The command above is the **target launcher contract**, not a command that works at the analyzed commits. No CLI flags are documented until the launcher and CLI exist.

## Usage model

The current usable artifacts support design-time and implementation-time workflows:

1. author or inspect a Lattice packet against `spec/grammar.ebnf`;
2. map semantic content to the eight Octad fields;
3. validate JSON structures against `spec/octad_schema.json` using a JSON Schema 2020-12 compatible validator supplied by the host environment;
4. interpret operators according to `spec/operator-table.md`;
5. interpret requested permission semantics according to `spec/permissions-safety.md`;
6. preserve unsupported extensions rather than silently inventing meaning.

### Human -> AI conceptual flow

```text
Natural-language request
        |
        | future semantic compiler/adapter
        v
Canonical Octad -> host validation -> SLAI language/task handling
```

**Conceptual example - not currently implemented by repository code.**

### AI -> AI conceptual flow

```text
Agent A state -> canonical Octad -> carrier -> canonical Octad -> Agent B policy/runtime
```

**Conceptual example - not currently implemented by repository code.**

## Specification map

| Artifact | Role | Status |
|---|---|---|
| `spec/lstp-v0.1.md` | Protocol and canonical-representation specification | Draft Phase 1 |
| `spec/grammar.ebnf` | Lattice grammar | Normative Phase-1 grammar |
| `spec/operator-table.md` | Operator/delimiter semantics | Normative Phase-1 reference |
| `spec/octad_schema.json` | Octad JSON validation contract | Substantive schema; `$id` still uses `example.org` |
| `spec/permissions-safety.md` | Permission and safety semantics | Proposed language/spec design |
| `spec/vocabulary.md` | Core vocabulary | Minimal/incomplete |

## Safety and permissions

LSTP permission declarations represent **requested authority**, not proof of authorization. The current permission modes are ordered conceptually as:

```text
RO <= SUGGEST <= PREVIEW <= RW <= EXEC <= COMMIT
```

A wider mode does not automatically widen scope. `FORBID` declarations override allowed scope, and requested limits/confirmation/review/logging can be represented explicitly.

The permission specification defines effective authority conceptually as the intersection of:

```text
sender request ∩ local policy ∩ runtime capabilities
```

Enforcement therefore belongs to the consuming application/runtime. LSTP can make authority requests inspectable; it cannot by itself prevent unsafe execution, authenticate a sender, authorize a resource, or guarantee policy compliance.

## Development status

| Capability | Status at analyzed commit |
|---|---|
| Octad semantic model | **Specified** |
| JSON Schema | **Specified** |
| Lattice EBNF grammar | **Specified** |
| Operator semantics | **Specified** |
| Permission semantics | **Proposed/specification-level** |
| Python parser | **Scaffold only** |
| Compiler | **Scaffold only** |
| Validator wrapper | **Scaffold only** |
| Serializer | **Scaffold only** |
| Runtime | **Scaffold only** |
| CLI | **Scaffold only** |
| Carrier implementations | **Scaffold/conceptual** |
| Test suite | **Absent** |
| SLAI adapter | **Not implemented** |
| `SLAI/run_lstp.py` | **Target requirement; absent** |
| Benchmarks | **Absent** |

## Testing and validation

No `tests/` directory or executable LSTP test suite is present at the analyzed `main` commit. The grammar, schema, operator table, and specification provide a basis for future conformance tests, but they are not a substitute for parser, round-trip, security, and interoperability testing.

A future test suite should at minimum cover:

- grammar-positive and grammar-negative fixtures;
- JSON Schema positive/negative fixtures;
- Lattice -> Octad -> Lattice round-trip invariants;
- JSON -> Octad -> JSON canonicalization behavior;
- permission preservation and fail-closed policy integration;
- context-reference correctness;
- malformed/hostile inputs;
- version/schema evolution;
- multi-agent interoperability fixtures;
- deterministic diagnostics for invalid packets.

## Limitations

The current project has important limitations:

- the reference implementation is not yet operational;
- the Python packaging contract is undefined;
- no executable conformance test suite exists;
- no empirical benchmark demonstrates reduced ambiguity, token use, latency, hallucination, or improved reasoning;
- semantic equivalence across carriers is a design objective, not yet a proven invariant;
- the core vocabulary is incomplete;
- domain semantics still require vocabularies/ontologies or host mappings;
- context references require a host context resolver;
- permission encoding is not enforcement;
- schema `$id` metadata still points to `example.org`;
- some specification prose uses the obsolete path spelling `octad-schema.json` instead of the repository file `octad_schema.json`;
- multimodal and additional carrier support remains future work.

## Roadmap

The repository direction supports the following sequence:

1. stabilize v0.1 schema, grammar, operator semantics, and vocabulary;
2. implement parser/tokenizer and structured diagnostics;
3. implement compiler/canonical packet model and schema validation;
4. implement deterministic serialization and round-trip tests;
5. define packaging/dependencies and a real CLI;
6. add a conformance fixture suite and CI;
7. implement the SLAI-root `run_lstp.py` adapter while keeping LSTP cloned at `SLAI/model/LSTP/`;
8. validate human-to-agent and agent-to-agent workflows empirically;
9. define version negotiation, extension governance, and additional carriers only after the core is testable.

## Documentation

- [Whitepaper](docs/WHITEPAPER.md)
- [Protocol v0.1](spec/lstp-v0.1.md)
- [Lattice grammar](spec/grammar.ebnf)
- [Operator table](spec/operator-table.md)
- [Octad JSON Schema](spec/octad_schema.json)
- [Permissions and safety](spec/permissions-safety.md)
- [Vocabulary](spec/vocabulary.md)

## Contributing

Contributions should preserve the source-of-truth order used by the project: executable implementation first, then formal schemas/specifications, tests/validated examples, integration evidence, and finally explanatory prose. New syntax should not be documented as supported until the grammar and implementation agree.

For implementation work, prefer focused changes that include conformance fixtures and avoid adding semantics that are not represented in the protocol specification.

## License

LSTP is licensed under the **MIT License**. See [`LICENSE`](LICENSE).

---

LSTP is an experimental research/engineering protocol. Its current value is primarily in the explicit specification of a semantic transport model; claims about performance, intelligence, safety outcomes, or cross-system interoperability remain hypotheses until validated by implementation and evaluation.
