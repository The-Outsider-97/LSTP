"""Real canonical protocol targets and negative LANTRA dataset preflight cases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lstp import canonical_dumps, canonical_loads
from tools.check_lantra_targets import TrainingTargetError, verify_targets


def _target() -> str:
    # Use the production decoder/serializer and a checked-in conformance vector.
    source = Path(__file__).resolve().parents[1] / "conformance/v0.1/positive/minimal.json"
    return canonical_dumps(canonical_loads(source.read_bytes())).decode("utf-8")


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _row(sample_id: str, split: str, prompt: str, target: str | None = None) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "split": split,
        "input": prompt,
        "target": _target() if target is None else target,
    }


def test_real_canonical_targets_validate_in_all_splits(tmp_path: Path) -> None:
    path = tmp_path / "targets.jsonl"
    _write(path, [
        _row("001", "train", "one"),
        _row("002", "validation", "two"),
        _row("003", "test", "three"),
    ])
    report = verify_targets([path], require_all_splits=True)
    assert report["status"] == "passed"
    assert report["samples"] == 3
    assert report["splits"] == {"test": 1, "train": 1, "validation": 1}
    assert report["model_training_executed"] is False


def test_split_leakage_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "targets.jsonl"
    _write(path, [_row("001", "train", "same"), _row("002", "test", "same")])
    with pytest.raises(TrainingTargetError, match="leakage"):
        verify_targets([path])


def test_bad_semantic_reference_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "targets.jsonl"
    target = json.loads(_target())
    target["relations"] = [{"type": "is", "arguments": ["a777"]}]
    _write(path, [_row("001", "train", "one", json.dumps(target, separators=(",", ":")))])
    with pytest.raises(TrainingTargetError, match="canonical/semantic"):
        verify_targets([path])


def test_noncanonical_target_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "targets.jsonl"
    _write(path, [_row("001", "train", "one", json.dumps(json.loads(_target()), indent=2))])
    with pytest.raises(TrainingTargetError, match="canonical/semantic"):
        verify_targets([path])


def test_duplicate_id_and_record_shape_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "targets.jsonl"
    _write(path, [_row("001", "train", "one"), _row("001", "train", "two")])
    with pytest.raises(TrainingTargetError, match="duplicate sample_id"):
        verify_targets([path])
    row = _row("001", "train", "one")
    row["unexpected"] = "untrusted"
    _write(path, [row])
    with pytest.raises(TrainingTargetError, match="exactly"):
        verify_targets([path])


def test_missing_split_and_empty_file_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "targets.jsonl"
    _write(path, [_row("001", "train", "one")])
    with pytest.raises(TrainingTargetError, match="all be non-empty"):
        verify_targets([path], require_all_splits=True)
    path.write_bytes(b"")
    with pytest.raises(TrainingTargetError, match="no supervision"):
        verify_targets([path])
