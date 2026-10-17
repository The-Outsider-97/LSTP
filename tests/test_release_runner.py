"""Release-runner archive and packaging smoke regressions."""

from __future__ import annotations

import io
import json
import tarfile
from typing import cast

import pytest
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


def _extract_entries(
    tmp_path: Path, entries: list[tuple[tarfile.TarInfo, bytes | None]]
) -> None:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        for member, payload in entries:
            archive.addfile(member, io.BytesIO(payload) if payload is not None else None)
    stream.seek(0)
    with tarfile.open(fileobj=stream, mode="r:") as archive:
        _safe_extract_sdist(archive, tmp_path)


def _regular(name: str) -> tuple[tarfile.TarInfo, bytes]:
    member = tarfile.TarInfo(name)
    member.size = 2
    return member, b"ok"


@pytest.mark.parametrize(
    "name",
    [
        "../escape", "/absolute", "pkg/../escape", "pkg/./file", "pkg//file",
        r"pkg\\file", "pkg/CON", "pkg/aux.txt", "pkg/COM1.log",
        "pkg/trailing.", "pkg/trailing ", "pkg/colon:bad", ".", "pkg/..",
    ],
)
def test_sdist_rejects_unsafe_member_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(SystemExit, match="unsafe source distribution"):
        _extract_entries(tmp_path, [_regular(name)])
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "kind",
    [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE,
     tarfile.BLKTYPE, tarfile.FIFOTYPE],
)
def test_sdist_rejects_links_and_special_files(tmp_path: Path, kind: bytes) -> None:
    member = tarfile.TarInfo("pkg/unsafe")
    member.type = kind
    member.linkname = "../../escape"
    with pytest.raises(SystemExit, match="unsafe source distribution"):
        _extract_entries(tmp_path, [(member, None)])
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "names",
    [
        ["pkg/a", "pkg/a"],
        ["pkg/a", "pkg/A"],
        ["pkg/a", "pkg/a/child"],
        ["pkg/Dir", "pkg/dir/child"],
    ],
)
def test_sdist_rejects_duplicate_and_casefold_parent_collisions(
    tmp_path: Path, names: list[str]
) -> None:
    with pytest.raises(SystemExit, match="unsafe source distribution"):
        _extract_entries(tmp_path, [_regular(name) for name in names])
    assert not list(tmp_path.iterdir())


def test_sdist_rejects_late_unsafe_member_without_partial_extraction(
    tmp_path: Path,
) -> None:
    link = tarfile.TarInfo("pkg/link")
    link.type = tarfile.SYMTYPE
    link.linkname = "../../escape"
    with pytest.raises(SystemExit, match="unsafe source distribution"):
        _extract_entries(tmp_path, [_regular("pkg/valid.py"), (link, None)])
    assert not (tmp_path / "pkg/valid.py").exists()


class _NoExtractArchive:
    def __init__(self, members: list[tarfile.TarInfo]) -> None:
        self.members = members

    def getmembers(self) -> list[tarfile.TarInfo]:
        return self.members

    def extractall(self, *_args: object, **_kwargs: object) -> None:
        raise AssertionError("extraction must not start")


def test_sdist_rejects_oversized_member(tmp_path: Path) -> None:
    member = tarfile.TarInfo("pkg/large")
    member.size = 128 * 1024 * 1024 + 1
    archive = cast(tarfile.TarFile, _NoExtractArchive([member]))
    with pytest.raises(SystemExit, match="file too large"):
        _safe_extract_sdist(archive, tmp_path)


def test_sdist_rejects_member_count_limit(tmp_path: Path) -> None:
    member = tarfile.TarInfo("pkg/a")
    archive = cast(tarfile.TarFile, _NoExtractArchive([member] * 20_001))
    with pytest.raises(SystemExit, match="too many members"):
        _safe_extract_sdist(archive, tmp_path)


def test_sdist_requires_secure_filter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    member = tarfile.TarInfo("pkg/a")
    archive = cast(tarfile.TarFile, _NoExtractArchive([member]))
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    with pytest.raises(SystemExit, match="secure tar extraction is unavailable"):
        _safe_extract_sdist(archive, tmp_path)


@pytest.mark.parametrize(
    "flags",
    [
        ["--final", "--skip-build-smoke"],
        ["--distribution-only", "--skip-build-smoke"],
        ["--final", "--distribution-only"],
    ],
)
def test_release_rejects_conflicting_flags(flags: list[str]) -> None:
    from tools import run_release_checks as release

    with pytest.raises(SystemExit) as exc:
        release.main(flags)
    assert exc.value.code == 2


def test_distribution_mode_runs_isolated_package_smoke(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from tools import run_release_checks as release

    names: list[str] = []

    def fake_run(name: str, command: list[str], *, cwd: Path = tmp_path) -> release.CheckResult:
        names.append(name)
        return release.CheckResult(name, tuple(command), 0)

    def fake_smoke(results: list[release.CheckResult]) -> None:
        names.append("isolated distribution smoke")

    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "_run", fake_run)
    monkeypatch.setattr(release, "_clean_distribution_smoke", fake_smoke)
    monkeypatch.setattr(release.shutil, "which", lambda _: "node")

    assert release.main(["--distribution-only"]) == 0
    assert names == [
        "build",
        "independent JavaScript interoperability",
        "isolated distribution smoke",
    ]
    assert '"mode": "distribution"' in capsys.readouterr().out
