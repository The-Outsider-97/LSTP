"""Release-runner archive and packaging smoke regressions."""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

from tools.run_release_checks import _safe_extract_sdist

ROOT = Path(__file__).resolve().parents[1]


def test_sdist_extraction_preserves_regular_files(tmp_path: Path) -> None:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        directory = tarfile.TarInfo("pkg/")
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        content = b"print(1)"
        module = tarfile.TarInfo("pkg/module.py")
        module.size = len(content)
        archive.addfile(module, io.BytesIO(content))
    stream.seek(0)
    with tarfile.open(fileobj=stream, mode="r:") as archive:
        _safe_extract_sdist(archive, tmp_path)
    assert (tmp_path / "pkg/module.py").read_bytes() == b"print(1)"


def test_sdist_includes_interoperability_assets() -> None:
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "recursive-include conformance *.json *.lstp *.md" in manifest
    assert "recursive-include interop *.mjs *.json" in manifest
    assert (ROOT / "interop/js/verify.mjs").is_file()

    directory = ROOT / "conformance/v0.1"
    fixtures = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    paths = [
        *fixtures["positive_json"],
        *[item["path"] for item in fixtures["negative_json"]],
        *fixtures["positive_lattice"],
        *[item["path"] for item in fixtures["negative_lattice"]],
    ]
    assert paths
    assert all((directory / path).is_file() for path in paths)
