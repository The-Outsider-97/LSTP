# LSTP — Lattice Semantic Transport Protocol

**Pre-alpha engineering foundation; not production-ready or training-ready.**

LSTP represents semantic messages through an eight-part Octad: pragmatics (π),
atoms (A), relations (R), context (C), confidence (κ), permissions (Π), evidence (E),
and output (Ω). Packet/envelope identity, version, carrier, transport and audit
metadata are separate from these eight semantic components.

LSTP is a semantic transport protocol, not a language model, universal ontology,
authorization system or safety system. Permission data requests authority; a host
must independently intersect that request with policy and runtime capabilities.

## Current status

The [22 September audit](docs/program/AUDIT-2026-09-22.md) found incompatible
Whitepaper and specification contracts. The authoritative PDF describes canonical
Octad syntax, numeric confidence and uppercase permission modes. The current EBNF
and schema describe a competing compact notation and different field shapes.
These conflicts remain open. The PDF has not been modified.

Implemented foundation:

- Python package and installed CLI;
- bounded UTF-8 JSON inspection with duplicate-key, Unicode and resource checks;
- structured diagnostics that do not echo input content;
- unit, property, adversarial and CLI tests;
- CI engineering matrix and a separate, deliberately failing readiness gate;
- initial inventory, conflict register, requirement candidates and program plan.

**Not implemented:** Lattice parser/compiler, canonical Octad model, semantic or
permission validator, carrier serializer/deserializer, host runtime, context
resolver, SLAI adapter and protocol round trips. Existing empty modules and example
files are tracked gaps, not functioning features. No performance, security or
interoperability superiority is claimed.

## Source of truth

1. [Authoritative Whitepaper PDF](docs/LSTP_Whitepaper.pdf).
2. This README as subordinate project guidance.
3. [Specification](spec/lstp-v0.1.md), [EBNF](spec/grammar.ebnf),
   [schema](spec/octad_schema.json), [operators](spec/operator-table.md),
   [permissions](spec/permissions-safety.md), [vocabulary](spec/vocabulary.md).
4. Implementation and tests, which must implement the authority rather than redefine it.

The [Markdown Whitepaper source](docs/WHITEPAPER.md) retains the same publication
revision as the PDF. Its referenced figure source files are missing. Full
publication reproducibility and semantic reconciliation are outstanding.

## Install and check the foundation

Development support target: Python 3.11–3.14; see the latest CI run for actual
matrix outcomes. The initial local validation environment is Python 3.12 on Linux.
Package version `0.1.0a1` is not a protocol freeze or an assertion of v0.1 conformance.

```bash
git clone https://github.com/The-Outsider-97/LSTP.git
cd LSTP
python -m venv .venv
# POSIX activation:
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
ruff format --check .
mypy
python -m build
lstp --help
lstp --version
```

On PowerShell, activate with `.\.venv\Scripts\Activate.ps1`; the remaining Python
commands are the same. These commands apply to a checkout containing this
foundation increment, not the original scaffold commit.

Production dependencies: none in this foundation. The `dev` extra includes
JSON Schema tooling, tests, lint/types and build tools. Dependency ranges are
bounded; exact versions for each measured run belong in its report. A reproducible
cross-platform lock and reproducible-byte builds are not yet established.

## CLI

```bash
lstp json-check path/to/input.json
python -m lstp json-check path/to/input.json
```

Omit the path or use `-` to read stdin. Successful output is:

```json
{"authorization_evaluated": false, "json_valid": true, "protocol_validated": false}
```

This command only checks JSON under the documented input profile. It does not
check Octad shape, references, versions, permissions, evidence truth or execution
authority. It does not execute or dereference anything. Exit codes: `0` JSON
accepted, `1` invalid/over-limit input, `2` CLI usage error, `3` input I/O failure.
Errors are JSON diagnostics on stderr; successful results go to stdout.

## Library API and input profile

```python
from lstp import JSONInputError, ResourceLimitError, loads_json

data = loads_json(b'{"example": 0.125}')
# data["example"] is Decimal("0.125"), not binary float.
```

`loads_json` accepts UTF-8 bytes or a Python string and decodes a single JSON value.
It rejects duplicate object keys (including escaped equivalents), non-finite
constants, invalid UTF-8, unpaired surrogate code points, BOMs, malformed syntax,
and inputs outside its resource limits. Valid surrogate pairs and escaped control
characters inside strings are preserved. No Unicode normalization is applied.
Fraction/exponent tokens use `Decimal`; integers use `int`. This is not a JSON
serializer or a frozen LSTP canonicalization/numeric profile.

Default limits: 1,048,576 input bytes; 64 nested containers; 65,536 decoded
characters per string/key; 10,000 items per collection; 50,000 total decoded
nodes (including keys); 128 characters per numeric token. `InputLimits` allows
positive custom limits, but depth cannot exceed 64. Input bytes/depth are checked
before recursive decoding; collection/string/node limits are checked during or
after decoding, with allocation bounded by the input-byte limit. These are local
resource limits, not protocol validity rules. No wall-clock timeout is promised.

## Protocol readiness

```bash
python tools/check_readiness.py
```

This currently exits **1** and lists unresolved blockers. It is a review ledger and
release gate, not a conformance implementation. Engineering tests can pass while
this gate fails; the overall workflow must not present missing protocol work as
green. No core conformance tests are silently skipped or marked expected-failure.

See [program](docs/program/PROGRAM.md), [traceability](docs/program/TRACEABILITY.md),
[audit](docs/program/AUDIT-2026-09-22.md), and [readiness ledger](docs/program/readiness.json).
Training data generation must wait for reconciled and explicitly versioned grammar,
schema, vocabulary, operators and serialization behavior.

## SLAI boundary

The integration target remains:

```text
SLAI/
├── run_lstp.py
└── model/
    └── LSTP/
```

Clone LSTP into `SLAI/model/LSTP/`; the eventual launcher belongs at the SLAI root.
The launcher and integration remain unimplemented. LSTP core must work independently
and must not import SLAI internals. LANTRA, the Language Agent, routing, host
authorization, safety and model inference remain distinct responsibilities.

## Contributing and license

Follow the source hierarchy and [program](docs/program/PROGRAM.md). Use focused
branches and reviewable commits with tests and documented decisions. Do not silently
alter the Whitepaper or reinterpret unknown permission/extension data.

MIT License, Copyright (c) 2026 J.E. Remy. See [LICENSE](LICENSE).
