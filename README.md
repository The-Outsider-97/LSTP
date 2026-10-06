# LSTP — Lattice Semantic Transport Protocol

**Pre-alpha reference implementation; canonical v0.1 contract reconciled and core runtime now executable.**

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

The 22 September 2026 audit found two incompatible contracts both presented as LSTP v0.1. The October canonical reconciliation resolved that design split. The reference implementation now contains an executable typed packet model, semantic validator, strict Lattice tokenizer/parser/AST/compiler, deterministic canonical JSON serializer/deserializer, permission-aware host authorization, delegation attenuation, replay/idempotency protection, and an initial versioned conformance-vector suite.

Canonical v0.1 now has:

- one eight-domain Octad shape;
- one canonical JSON Schema;
- one orthogonal capability-based permission model;
- one evidence/provenance representation;
- stable context-reference requirements;
- one core vocabulary baseline;
- one explicit response/outcome vocabulary;
- deterministic Lattice-to-Octad mappings for the normative grammar surface;
- one canonical JSON byte profile;
- semantic RFC 3339 and structural BCP 47 validation;
- one host-authorization intersection model;
- one replay-store interface with in-process and durable SQLite reference implementations;
- positive and negative executable conformance fixtures.

The repository is **not yet production-ready or training-ready**. Remaining blockers include broader adversarial/conformance coverage, distributed replay-store integrations where required, application-specific permission-limit enforcement, a second independent implementation, SLAI integration, Whitepaper publication synchronization, and the final release/pre-training audit.

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

For v0.1 implementation and conformance:

1. [`spec/CANONICAL-v0.1.md`](spec/CANONICAL-v0.1.md) — normative semantic and behavioral contract;
2. [`spec/octad_schema.json`](spec/octad_schema.json) — normative canonical JSON structure;
3. [`spec/canonical-json-v0.1.md`](spec/canonical-json-v0.1.md), [`spec/grammar.ebnf`](spec/grammar.ebnf), [`spec/operator-table.md`](spec/operator-table.md), [`spec/permissions-safety.md`](spec/permissions-safety.md), and [`spec/vocabulary.md`](spec/vocabulary.md) — normative serialization/carrier/operator/security/vocabulary profiles where consistent with 1–2;
4. [`conformance/v0.1/`](conformance/v0.1/) and tests — executable evidence;
5. reference implementation — must implement the contract and may not redefine it;
6. Whitepaper — informative rationale, research framing, design history, and evaluation narrative.

This hierarchy replaces the earlier PDF-first development hierarchy that caused machine-readable artifacts to remain blocked behind draft prose conflicts. The Whitepaper should be revised for publication to record this governance transition; the existing PDF remains a historical design document until that revision is published.

## Canonical packet

A minimal canonical packet resembles:

```json
{
  "id": "pkt_example_001",
  "version": "0.1",
  "pragmatics": {"act": "request"},
  "atoms": [],
  "relations": [],
  "context": {"thread_id": "thread_example", "references": []},
  "confidence": 1.0,
  "permissions": {"capabilities": [], "resources": []},
  "evidence": [],
  "output": {"format": "NL"},
  "carrier": {},
  "audit": {},
  "extensions": {}
}
```

All eight Octad domains are required in canonical JSON. Compact carriers may omit default/empty material only when their compiler reconstructs canonical state deterministically.

## Lattice text

Lattice is an authoring/carrier surface, not a second semantic contract. The strict parser recognizes the normative grammar including target scopes/ranges, composition, alternatives, annotations, approximation, exclusion, claims, ambiguity forms, macros, metadata, context references, and context commands.

Only constructs with deterministic canonical semantics are compiled into packets. Runtime-only constructs such as `ctx.push`/`ctx.pop` are parsed for inspectability but fail canonical packet compilation rather than being assigned invented semantics.

Relative references such as `↑2` must resolve to stable packet IDs before canonical transport, replay, hashing, or storage.

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

Permissions use orthogonal requested capabilities:

```text
read
suggest
prepare
write
execute
commit
```

Convenience profiles (`RO`, `SUGGEST`, `PREVIEW`, `RW`, `EXEC`, `COMMIT`) are named bundles, **not** a numeric privilege ladder. Resource scope is represented by typed resource records rather than free-form scope strings.

Effective authority is evaluated as an exact host-side intersection of requested capabilities/resources, authenticated principal authority, host policy, runtime capability, and explicit constraints. Delegation may only attenuate authority.

Action-capable hosts can use the reference authorization API together with any `ReplayStore` implementation. `ReplayGuard` is process-local; `SQLiteReplayStore` is durable for hosts that share one file-backed SQLite database. Multi-node/distributed deployments should provide another `ReplayStore` with equivalent atomic reservation semantics instead of changing authorization logic.

## Semantic formats

Fields declared by the canonical contract now receive semantic format validation:

- `context.time` — RFC 3339 date-time;
- `permissions.expires_at` — RFC 3339 date-time;
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

Positive canonical-byte fixtures must decode, validate and re-encode byte-for-byte identically. Negative fixtures must fail closed at the structural or semantic layer and must never be silently migrated into a different meaning.

The vector corpus is an initial executable baseline, not yet the independent interoperability evidence required for release/training freeze.

## Protocol readiness

`python tools/check_readiness.py` remains a release/training ledger. The canonical-contract split, typed runtime, parser/compiler, canonical serializer, core host authorization, semantic RFC3339/BCP47 validation, and replay-store abstraction are no longer principal blockers. Broader conformance/adversarial evidence, independent interoperability, SLAI integration, publication synchronization, and final release validation remain open.

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
