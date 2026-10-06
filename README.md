# LSTP — Lattice Semantic Transport Protocol

**Pre-alpha reference implementation with a Whitepaper-reconciled v0.1 contract. The remaining work is release evidence, interoperability, SLAI integration, publication synchronization, and final freeze.**

LSTP represents semantic messages through an eight-part Octad:

1. pragmatics (π);
2. atoms (A);
3. relations (R);
4. context (C);
5. confidence (κ);
6. permissions (Π);
7. evidence (E);
8. output (Ω).

Packet identity, version, carrier, audit, and extension metadata are outside Octad semantic equality.

LSTP is a semantic transport protocol. It is not a language model, authentication system, universal ontology, policy engine, or safety controller. Permission data requests authority; the consuming host independently decides whether authority exists.

## Current status

The 22 September 2026 audit found two incompatible contracts both presented as LSTP v0.1. The 6 October Whitepaper-first repair reconciled the contract across the typed model, schema, canonical JSON, canonical/compact Lattice, permission wire semantics, context, evidence, serialization, and host authorization boundary. `contract_reconciled=true` is now recorded in the readiness ledger.

Canonical v0.1 now has:

- one eight-domain Octad shape;
- one canonical JSON Schema;
- one Whitepaper mode/scope permission wire model, with concrete capabilities kept internal to host authorization;
- one evidence/provenance representation;
- stable context-reference requirements;
- one core vocabulary baseline;
- one explicit response/outcome vocabulary;
- deterministic compact-Lattice-to-Octad mappings for the currently implemented compact carrier surface;
- one canonical JSON byte profile;
- semantic RFC 3339 and structural BCP 47 validation;
- one host-authorization intersection model;
- one replay-store interface with in-process and durable SQLite reference implementations;
- positive and negative executable conformance fixtures.

The repository is **not yet production-ready or training-ready**, but the remaining work is finite and explicitly gated. The six release blockers are clean executable verification, production conformance/adversarial coverage, independent interoperability, SLAI integration, Whitepaper publication synchronization, and the final release/pre-training audit.

Implemented engineering/runtime foundation includes:

- Python package and CLI;
- bounded UTF-8 JSON inspection with duplicate-key and resource checks;
- immutable typed canonical Octad/envelope model;
- strict v0.1 version handling;
- semantic/reference/permission/format validation;
- Lattice tokenizer, AST, parser and compiler;
- stable resolution requirement for relative context references;
- deterministic canonical JSON serialization/deserialization;
- NFC and bidirectional-control canonicalization safeguards;
- permission-aware host authorization with exact capability/resource intersection;
- authenticated delegation attenuation;
- confirmation, review, logging, expiry and trusted authorization-reference enforcement;
- replay/idempotency reservation through a pluggable `ReplayStore` contract;
- thread-safe in-process `ReplayGuard` and durable file-backed `SQLiteReplayStore`;
- namespaced extension isolation;
- unit, adversarial, parser/compiler, canonicalization, authorization, replay-store and conformance-vector tests;
- CI engineering matrix;
- readiness and traceability records.

## Source of truth

The active production-hardening mandate defines this hierarchy:

1. [`docs/LSTP_Whitepaper.pdf`](docs/LSTP_Whitepaper.pdf) — Level 1 authoritative conceptual and protocol reference;
2. this root README — Level 2 project guidance;
3. [`spec/`](spec/) — Level 3 normative technical artifacts, including `CANONICAL-v0.1.md`, schema, grammar, serialization, permission, operator, and vocabulary profiles;
4. [`src/lstp/`](src/lstp/) — Level 4 reference implementation.

Executable tests and conformance vectors provide evidence but do not override a higher-authority source. The Whitepaper-first governance conflict is now closed; the remaining readiness work is evidence and integration work.

The field-by-field reconciliation record is [`docs/program/WHITEPAPER-AUTHORITY-AUDIT-2026-10-06.md`](docs/program/WHITEPAPER-AUTHORITY-AUDIT-2026-10-06.md). The finite release ledger is [`docs/program/readiness.json`](docs/program/readiness.json).

## Canonical packet

A minimal canonical packet resembles:

```json
{
  "id": "pkt_example_001",
  "version": "0.1",
  "pragmatics": {"type": "request", "speech_act": "command"},
  "atoms": [],
  "relations": [],
  "context": {"thread_id": "thread_example", "references": []},
  "confidence": 1.0,
  "permissions": {"mode": "PREVIEW", "scope": ["urn:example:document:1"]},
  "evidence": [],
  "output": {"format": "NL"},
  "carrier": {},
  "audit": {},
  "extensions": {}
}
```

All eight Octad domains are required in canonical JSON. Compact carriers may omit default/empty material only when their compiler reconstructs canonical state deterministically.

## Lattice text

LSTP now has two explicit Lattice carrier profiles with one semantic Octad:

1. **Canonical Lattice** — `spec/grammar.ebnf`; ordered
   `π | A | R | C | κ | Π | E | Ω`, with atomic, framed, named, and named-stream
   packet forms.
2. **Compact Lattice** — `spec/compact-grammar.ebnf`; the operator-oriented
   authoring surface using directives, targets, scopes, `::`, `->`, `%`,
   context references, macros, and related shorthand.

The canonical carrier parser is exposed as:

```python
from lstp import (
    canonical_lattice_dumps,
    compile_canonical_lattice,
    parse_canonical_lattice,
)

document = parse_canonical_lattice(
    '[π=(TYPE=REQUEST,SPEECH_ACT=COMMAND)'
    '|A=(a0:ENT("door"){ROLE=TARGET})'
    '|R=(OPEN(a0))'
    '|C=(THREAD="t1")'
    '|κ=0.95'
    '|Π=(MODE=EXEC,SCOPE=["door"])'
    '|E=(USER("open the door"))'
    '|Ω=(FORMAT=NL)]'
)
```

Compact Lattice continues to use `parse()` / `compile_lattice()`. Compact
syntax is not silently accepted as canonical ordered-Octad syntax, and packet
labels in named canonical streams remain carrier labels rather than becoming
envelope IDs.

For the governed canonical surface, `canonical_lattice_dumps(octad)` emits one
deterministic framed representation and `compile_canonical_lattice()` validates
the result back into typed semantics. The encoder fails closed rather than
dropping fields whose canonical Lattice syntax is not governed, including richer
evidence metadata.

Relative compact references such as `↑2` must still resolve to stable packet
IDs before canonical transport, replay, hashing, or storage.

## Canonical JSON bytes

`spec/canonical-json-v0.1.md` defines the v0.1 byte profile. The reference serializer uses:

- UTF-8 without BOM;
- NFC strings;
- rejection of bidirectional formatting controls;
- recursive UTF-16 code-unit object-key ordering;
- no insignificant whitespace;
- finite normalized decimal number tokens;
- `-0` canonicalized to `0`.

The profile is RFC 8785-inspired but deliberately uses an LSTP decimal-number profile instead of ECMAScript binary64 serialization.

Python API:

```python
from lstp import canonical_dumps, canonical_loads

encoded: bytes = canonical_dumps(packet)
round_tripped = canonical_loads(encoded, require_canonical_bytes=True)
```

## Permissions and host authorization

Canonical packet permissions use the Whitepaper wire model:

```text
RO <= SUGGEST <= PREVIEW <= RW <= EXEC <= COMMIT
```

A packet carries `mode`, explicit `scope`, optional `forbid`, limits, and
confirmation/review/logging constraints. A stronger mode never widens scope and
never removes constraints.

The action-capable host translates that mode into concrete internal capabilities
(`read`, `suggest`, `prepare`, `write`, `execute`, `commit`) only at
the authorization boundary. Those capabilities are not canonical packet fields.

Effective authority is an exact intersection of mode-derived internal
capabilities, packet scope after forbids, authenticated principal authority,
host policy, and runtime capability. Empty scope is never a wildcard.

Delegation, expiry, trusted authorization references, and replay protection are
host-security hardening, not canonical v0.1 packet fields. The reference API
accepts expiry/reference/delegation through trusted `HostAuthorizationContext`
metadata supplied alongside the packet. Canonical JSON rejects those fields when
placed inside `permissions`.

Action-capable hosts can use the reference authorization API together with any
`ReplayStore` implementation. `ReplayGuard` is process-local;
`SQLiteReplayStore` is durable for hosts sharing one file-backed SQLite
database. Multi-node deployments need another store with equivalent atomic
reservation semantics.

## Semantic formats

Fields declared by the canonical contract now receive semantic format validation:

- `context.time` — RFC 3339 date-time;
- `atoms[].language` — structurally well-formed BCP 47 language tag;
- `output.language` — structurally well-formed BCP 47 language tag.

BCP 47 validation is grammar-level and does not claim IANA registry membership for every individual subtag.

## Install and engineering checks

Development target: Python 3.11–3.14; actual support is established only by observed CI runs.

```bash
git clone https://github.com/The-Outsider-97/LSTP.git
cd LSTP
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
ruff format --check .
mypy
python -m build
python tools/check_schema_contract.py
python tools/check_readiness.py
```

PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

## CLI

```bash
lstp json-check path/to/input.json
python -m lstp json-check path/to/input.json
```

`json-check` checks bounded generic JSON only. It does **not** certify LSTP semantic conformance or authorization. Library-level canonical decoding, semantic validation, and host authorization are implemented; CLI protocol commands are being hardened separately so generic JSON inspection remains clearly distinct from protocol certification.

Successful generic JSON inspection reports:

```json
{"authorization_evaluated": false, "json_valid": true, "protocol_validated": false}
```

## Conformance vectors

Versioned vectors live under [`conformance/v0.1/`](conformance/v0.1/).

Canonical JSON positive fixtures must decode, validate and re-encode
byte-for-byte identically. Negative JSON fixtures must fail closed at the
structural or semantic layer.

Canonical Lattice fixtures live under
`conformance/v0.1/lattice/canonical/` and are executed through
`parse_canonical_lattice()` / `compile_canonical_lattice()`. The initial
corpus includes a semantically valid Whitepaper-style packet, strict
segment-order rejection, and JSON-backed vectors that prove canonical Lattice
encoding fails closed for currently ungoverned GOV-EXT and rich-evidence fields.

The vector corpus is still an initial baseline, not yet the independent
interoperability evidence required for release/training freeze.

## Protocol readiness

`python tools/check_readiness.py` remains the release/training ledger. The Whitepaper-aligned semantic model and canonical Lattice grammar are implemented as candidates, but Phase B/Phase C verification, GOV-EXT, broader conformance/adversarial evidence, independent interoperability, SLAI integration, publication synchronization, and final release validation remain open.

Training data generation must wait until the readiness gate is green and the versioned conformance suite is sufficiently complete for the freeze criteria.

## SLAI boundary

The requested integration layout remains:

```text
SLAI/
├── run_lstp.py
└── model/
    └── LSTP/
```

LSTP SHOULD be pinned as an independent package/submodule at `SLAI/model/LSTP/`, avoiding `sys.path` manipulation. `run_lstp.py` belongs at the SLAI root.

The intended semantic flow is:

```text
human natural language
        ↓
SLAI Language Agent / LANTRA
        ↓
canonical LSTP Octad
        ↓
validation / transport / agent routing
```

LSTP should be the semantic interchange contract rather than a second competing natural-language-understanding pass.

## Project records

See:

- [`docs/program/AUDIT-2026-09-22.md`](docs/program/AUDIT-2026-09-22.md)
- [`docs/program/CANONICAL-RECONCILIATION-2026-10-04.md`](docs/program/CANONICAL-RECONCILIATION-2026-10-04.md)
- [`docs/program/DECISIONS.md`](docs/program/DECISIONS.md)
- [`docs/program/TRACEABILITY.md`](docs/program/TRACEABILITY.md)
- [`docs/program/readiness.json`](docs/program/readiness.json)

## License

MIT License, Copyright (c) 2026 J.E. Remy. See [`LICENSE`](LICENSE).
