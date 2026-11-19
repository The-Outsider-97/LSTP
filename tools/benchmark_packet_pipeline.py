"""Time real packet operations on a recorded synthetic JSONL corpus, without API calls.

Each row contains canonical_lstp (a JSON string) and gold (seven named strings),
as emitted by SLAI's benchmarks.lstp.cases.Case.as_record(). Run in separate
processes with each implementation on PYTHONPATH. The input selector uses byte
length ONLY to exercise its CPU path; this tool reports no model tokens/costs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
from collections.abc import Callable
from pathlib import Path

import lstp
from lstp import (
    canonical_dumps,
    canonical_loads,
    incremental_dumps,
    incremental_loads,
    prepare_action_input,
    project_action,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if args.repeats < 3:
        parser.error("at least three timing repeats are required")
    corpus = args.corpus.read_bytes()
    rows = [json.loads(line) for line in corpus.splitlines() if line.strip()]
    if not rows:
        parser.error("corpus must contain cases")
    packets = [canonical_loads(row["canonical_lstp"]) for row in rows]
    canonical = [canonical_dumps(packet) for packet in packets]
    typed = [incremental_dumps(packet) for packet in packets]
    for packet, wire, carrier, row in zip(packets, canonical, typed, rows, strict=True):
        if canonical_dumps(incremental_loads(carrier)) != wire:
            raise SystemExit("lossless carrier verification failed")
        if project_action(packet).as_mapping() != row["gold"]:
            raise SystemExit("exact projection verification failed")

    def selector_cost(system: str, user: str) -> int:
        return len(system.encode("utf-8")) + len(user.encode("utf-8"))

    operations: dict[str, Callable[[], None]] = {}

    def encode() -> None:
        for packet in packets:
            canonical_dumps(packet)

    def decode() -> None:
        for wire in canonical:
            canonical_loads(wire)

    def typed_encode() -> None:
        for packet in packets:
            incremental_dumps(packet)

    def typed_decode() -> None:
        for wire in typed:
            incremental_loads(wire)

    def project() -> None:
        for packet in packets:
            project_action(packet)

    def prepare() -> None:
        for packet in packets:
            prepare_action_input(packet, selector_cost)

    operations.update(
        canonical_encode=encode,
        canonical_decode=decode,
        typed_encode=typed_encode,
        typed_decode=typed_decode,
        projection=project,
        prepare_action_input=prepare,
    )
    timings = {}
    for name, operation in operations.items():
        operation()  # Untimed warm-up, identical in each implementation.
        runs = []
        for _ in range(args.repeats):
            start = time.perf_counter_ns()
            operation()
            runs.append((time.perf_counter_ns() - start) / len(rows) / 1000)
        timings[name] = {"median_us_per_packet": statistics.median(runs), "runs_us": runs}
    result = {
        "label": args.label,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "implementation_sha256": hashlib.sha256(
            b"".join(
                path.relative_to(Path(lstp.__file__).parent).as_posix().encode()
                + b"\0"
                + path.read_bytes()
                for path in sorted(Path(lstp.__file__).parent.rglob("*.py"))
            )
        ).hexdigest(),
        "corpus_sha256": hashlib.sha256(corpus).hexdigest(),
        "canonical_payloads_sha256": hashlib.sha256(b"\n".join(canonical)).hexdigest(),
        "typed_payloads_sha256": hashlib.sha256(b"\n".join(typed)).hexdigest(),
        "cases": len(rows),
        "repeats": args.repeats,
        "verified_exact_projections": len(rows),
        "verified_lossless_carriers": len(rows),
        "selector_counter": "UTF-8 byte length for CPU timing only; not model tokens",
        "api_calls": 0,
        "timings": timings,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"label": args.label, "cases": len(rows), "timings": timings}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
