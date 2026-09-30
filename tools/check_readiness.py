"""Fail CI/release gates while recorded production-critical requirements are open.

This is an explicit engineering sign-off ledger, not an automatic proof of
protocol correctness. Clearing it requires independent evidence and review.
"""

import json
from pathlib import Path

from check_schema_contract import contract_failures

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    state = json.loads((ROOT / "docs/program/readiness.json").read_text(encoding="utf-8"))
    blockers = state["blockers"]
    failures = [f"{item['id']}: {item['summary']}" for item in blockers]

    schema = json.loads((ROOT / "spec/octad_schema.json").read_text(encoding="utf-8"))
    failures.extend(f"SCHEMA: {finding}" for finding in contract_failures(schema))

    for path in sorted((ROOT / "examples").rglob("*")):
        if path.is_file() and not path.read_bytes().strip():
            failures.append(f"EMPTY: {path.relative_to(ROOT)}")
    if not state["training_ready"]:
        failures.append("Pre-training freeze has not been approved.")
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
