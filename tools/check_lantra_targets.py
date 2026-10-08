"""Validate real LANTRA→LSTP JSONL supervision before spending training compute.

This checks syntax, canonical bytes, semantic references, provenance types,
protocol pinning and data leakage. It deliberately cannot certify that a
model learns the targets or that the annotation is factually correct.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from lstp import LSTPError, canonical_loads, canonical_dumps, loads_json

FIELDS = frozenset({"sample_id", "split", "input", "target"})
SPLITS = frozenset({"train", "validation", "test"})
SAMPLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
MAX_LINE_BYTES = 1_048_576


class TrainingTargetError(ValueError):
    """A supervision record is unsafe, incompatible or ambiguous."""


def _parse_record(raw: bytes, *, path: Path, line_no: int) -> dict[str, str]:
    where = f"{path}:{line_no}"
    if len(raw) > MAX_LINE_BYTES:
        raise TrainingTargetError(f"{where}: line exceeds byte limit")
    try:
        obj = loads_json(raw)
    except (LSTPError, ValueError, TypeError) as exc:
        raise TrainingTargetError(f"{where}: malformed JSONL record ({type(exc).__name__})") from exc
    if not isinstance(obj, dict):
        raise TrainingTargetError(f"{where}: record must be an object")
    if set(obj) != FIELDS:
        raise TrainingTargetError(f"{where}: record requires exactly {sorted(FIELDS)}")
    if any(not isinstance(obj[k], str) for k in FIELDS):
        raise TrainingTargetError(f"{where}: every record field must be a string")
    if not SAMPLE_ID_RE.fullmatch(obj["sample_id"]):
        raise TrainingTargetError(f"{where}: invalid sample_id")
    if obj["split"] not in SPLITS:
        raise TrainingTargetError(f"{where}: split must be train, validation or test")
    if not obj["input"].strip():
        raise TrainingTargetError(f"{where}: empty input")
    if not obj["target"]:
        raise TrainingTargetError(f"{where}: empty target")
    return obj


def verify_targets(paths: list[Path], *, require_all_splits: bool = False) -> dict[str, object]:
    """Stream records and reject malformed targets, duplicates or split leakage."""
    if not paths:
        raise TrainingTargetError("at least one JSONL path is required")
    counts: Counter[str] = Counter()
    seen_ids: set[str] = set()
    seen_inputs: dict[str, str] = {}
    seen_pairs: set[str] = set()
    total_target_bytes = 0
    total_input_bytes = 0
    digest = hashlib.sha256()
    for path in paths:
        if not path.is_file():
            raise TrainingTargetError(f"{path}: file does not exist")
        with path.open("rb") as stream:
            line_no = 0
            while raw := stream.readline(MAX_LINE_BYTES + 1):
                line_no += 1
                where = f"{path}:{line_no}"
                if len(raw) > MAX_LINE_BYTES:
                    raise TrainingTargetError(f"{where}: line exceeds byte limit")
                if not raw.strip():
                    raise TrainingTargetError(f"{where}: blank record")
                obj = _parse_record(raw, path=path, line_no=line_no)
                sid = obj["sample_id"]
                if sid in seen_ids:
                    raise TrainingTargetError(f"{where}: duplicate sample_id")
                seen_ids.add(sid)

                prompt_key = hashlib.sha256(obj["input"].strip().encode("utf-8")).hexdigest()
                old_split = seen_inputs.get(prompt_key)
                if old_split is not None and old_split != obj["split"]:
                    raise TrainingTargetError(f"{where}: input leakage across data splits")
                seen_inputs[prompt_key] = obj["split"]

                target = obj["target"].encode("utf-8")
                try:
                    packet = canonical_loads(target, require_canonical_bytes=True)
                except (LSTPError, ValueError, TypeError) as exc:
                    raise TrainingTargetError(
                        f"{where}: invalid canonical/semantic LSTP target ({type(exc).__name__})"
                    ) from exc
                if packet.protocol_version != "0.1":
                    raise TrainingTargetError(f"{where}: unsupported target version")
                if canonical_dumps(packet) != target:
                    raise TrainingTargetError(f"{where}: target changed on round trip")
                pair_key = hashlib.sha256(
                    prompt_key.encode("ascii") + b"\0" + target
                ).hexdigest()
                if pair_key in seen_pairs:
                    raise TrainingTargetError(f"{where}: duplicate input/target pair")
                seen_pairs.add(pair_key)

                counts[obj["split"]] += 1
                total_input_bytes += len(obj["input"].encode("utf-8"))
                total_target_bytes += len(target)
                digest.update(len(raw).to_bytes(8, "big"))
                digest.update(raw)

    if not sum(counts.values()):
        raise TrainingTargetError("no supervision examples found")
    if require_all_splits and any(counts[split] == 0 for split in SPLITS):
        raise TrainingTargetError("train, validation and test must all be non-empty")
    return {
        "status": "passed",
        "protocol_version": "0.1",
        "samples": sum(counts.values()),
        "splits": {split: counts[split] for split in sorted(SPLITS)},
        "target_bytes": total_target_bytes,
        "input_bytes": total_input_bytes,
        "dataset_sha256": digest.hexdigest(),
        "checks": [
            "bounded-utf8-jsonl",
            "canonical-json-bytes",
            "semantic-validation",
            "protocol-version",
            "unique-identifiers",
            "duplicate-pairs",
            "split-leakage",
        ],
        "model_training_executed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="one or more JSONL dataset paths")
    parser.add_argument(
        "--require-all-splits",
        action="store_true",
        help="fail unless train/validation/test each contain samples",
    )
    args = parser.parse_args(argv)
    try:
        report = verify_targets(args.paths, require_all_splits=args.require_all_splits)
    except TrainingTargetError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
