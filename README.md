# LSTP — Lattice Semantic Transport Protocol

**Pre-alpha reference implementation work; protocol contract reconciled, implementation still incomplete.**

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

The 22 September 2026 audit found two incompatible contracts both presented as LSTP v0.1. The 4 October 2026 canonical reconciliation branch resolves that design split at the specification level.

Canonical v0.1 now has:

- one eight-domain Octad shape;
- one canonical JSON Schema;
- one orthogonal capability-based permission model;
- one evidence/provenance representation;
- stable context-reference requirements;
- one core vocabulary baseline;
- one explicit response/outcome vocabulary;
- one source-of-truth hierarchy for implementation and conformance.

The repository is **not yet production-ready or training-ready** because parser/compiler, semantic validation, canonical serialization, full conformance fixtures, interoperability evidence, and SLAI integration remain incomplete.

Implemented engineering foundation includes:

- Python package and CLI;
- bounded UTF-8 JSON inspection with duplicate-key and resource checks;
- immutable Octad/envelope foundation types;
- fail-closed v0.1 envelope version handling;
- namespaced extension isolation;
- unit/adversarial/CLI/schema-contract tests;
- CI engineering matrix;
- readiness and traceability records.

## Source of truth

For v0.1 implementation and conformance:

1. [`spec/CANONICAL-v0.1.md`](spec/CANONICAL-v0.1.md) — normative semantic and behavioral contract;
2. [`spec/octad_schema.json`](spec/octad_schema.json) — normative canonical JSON structure;
3. [`spec/grammar.ebnf`](spec/grammar.ebnf), [`spec/operator-table.md`](spec/operator-table.md), [`spec/permissions-safety.md`](spec/permissions-safety.md), and [`spec/vocabulary.md`](spec/vocabulary.md) — normative carrier/operator/security/vocabulary profiles where consistent with 1–2;
4. conformance fixtures/tests — executable evidence;
5. reference implementation — must implement the contract and may not redefine it;
6. Whitepaper — informative rationale, research framing, design history, and evaluation narrative.

This hierarchy deliberately replaces the earlier PDF-first development hierarchy that caused machine-readable artifacts to remain blocked behind draft prose conflicts. The Whitepaper should be revised for publication to record this governance transition; the existing PDF remains a historical design document until that revision is published.

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

All eight Octad domains are required in canonical JSON. Compact carriers may omit default/empty material only when their compiler can reconstruct this canonical state deterministically.

## Permissions

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

Effective authority remains a host-side intersection of requested capabilities, authenticated principal authority, policy, runtime capability, resources, and constraints.

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

`json-check` currently checks bounded JSON input only. It does **not** certify LSTP semantic conformance or authorization.

Successful generic JSON inspection reports:

```json
{"authorization_evaluated": false, "json_valid": true, "protocol_validated": false}
```

## Protocol readiness

`python tools/check_readiness.py` remains a release/training ledger. The canonical-contract split is no longer the blocker on this reconciliation branch; implementation, conformance, canonicalization, interoperability, and publication synchronization remain open.

Training data generation must wait until the readiness gate is green and versioned conformance fixtures exist.

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
