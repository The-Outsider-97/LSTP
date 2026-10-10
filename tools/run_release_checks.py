"""Cross-platform LSTP engineering and release verification runner.

Default mode verifies the implementation independently of the readiness ledger.
Use --final only when all release blockers are expected to be closed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    command: tuple[str, ...]
    returncode: int


def _run(name: str, command: list[str], *, cwd: Path = ROOT) -> CheckResult:
    print(f"==> {name}")
    print(" ".join(command))
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode:
        raise SystemExit(
            json.dumps(
                {
                    "check": name,
                    "command": command,
                    "returncode": result.returncode,
                },
                sort_keys=True,
            )
        )
    return CheckResult(name, tuple(command), result.returncode)


def _python(*args: str) -> list[str]:
    return [sys.executable, *args]


def _venv_python(directory: Path) -> Path:
    if os.name == "nt":
        return directory / "Scripts" / "python.exe"
    return directory / "bin" / "python"


def _venv_script(directory: Path, name: str) -> Path:
    if os.name == "nt":
        return directory / "Scripts" / f"{name}.exe"
    return directory / "bin" / name


_WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)
}


def _safe_extract_sdist(archive: tarfile.TarFile, destination: Path) -> None:
    """Reject unsafe or ambiguous members before data-filtered extraction."""
    root = destination.resolve()
    folded: set[str] = set()
    files: set[str] = set()
    parents: set[str] = set()
    total = 0
    members = archive.getmembers()
    if len(members) > 20_000:
        raise SystemExit("unsafe source distribution: too many members")
    for member in members:
        name = member.name.removesuffix("/") if member.isdir() else member.name
        parts = name.split("/")
        if (
            not name
            or name.startswith("/")
            or "\\" in name
            or any(
                part in {"", ".", ".."}
                or ":" in part
                or part.endswith((" ", "."))
                or part.split(".", 1)[0].upper() in _WINDOWS_DEVICES
                for part in parts
            )
            or not (member.isfile() or member.isdir())
            or name.casefold() in folded
        ):
            raise SystemExit(f"unsafe source distribution member: {member.name!r}")
        candidate = (destination / name).resolve()
        if candidate == root or root not in candidate.parents:
            raise SystemExit(f"unsafe source distribution path: {member.name!r}")
        if member.isfile():
            if member.size < 0 or member.size > 128 * 1024 * 1024:
                raise SystemExit("unsafe source distribution: file too large")
            total += member.size
            files.add(name)
        elif member.size != 0:
            raise SystemExit("unsafe source distribution: directory contains data")
        folded.add(name.casefold())
        parents.update("/".join(parts[:i]) for i in range(1, len(parts)))
    if total > 512 * 1024 * 1024 or files & parents:
        raise SystemExit("unsafe source distribution: size or parent collision")
    if not hasattr(tarfile, "data_filter"):
        raise SystemExit("secure tar extraction is unavailable in this Python runtime")
    archive.extractall(destination, filter="data")


def _clean_distribution_smoke(results: list[CheckResult]) -> None:
    dist = ROOT / "dist"
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("expected exactly one wheel and one source distribution")

    with tempfile.TemporaryDirectory(prefix="lstp-release-") as raw:
        temp = Path(raw)

        wheel_env = temp / "wheel-env"
        results.append(_run("create wheel venv", _python("-m", "venv", str(wheel_env))))
        wheel_python = _venv_python(wheel_env)
        results.append(
            _run(
                "install wheel",
                [str(wheel_python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
            )
        )
        cli = _venv_script(wheel_env, "lstp")
        results.append(_run("wheel CLI version", [str(cli), "--version"], cwd=temp))
        results.append(_run("wheel CLI help", [str(cli), "--help"], cwd=temp))

        source_root = temp / "source"
        source_root.mkdir()
        with tarfile.open(sdists[0], "r:gz") as archive:
            _safe_extract_sdist(archive, source_root)
        extracted = [path for path in source_root.iterdir() if path.is_dir()]
        if len(extracted) != 1:
            raise SystemExit("source distribution must contain one top-level directory")

        sdist_env = temp / "sdist-env"
        results.append(_run("create sdist venv", _python("-m", "venv", str(sdist_env))))
        sdist_python = _venv_python(sdist_env)
        source_dir = extracted[0]
        results.append(
            _run(
                "install extracted sdist with test dependencies",
                [str(sdist_python), "-m", "pip", "install", ".[dev]"],
                cwd=source_dir,
            )
        )
        results.append(
            _run(
                "sdist import smoke",
                [str(sdist_python), "-c", "import lstp; print(lstp.__version__)"],
                cwd=temp,
            )
        )
        results.append(
            _run(
                "sdist tests",
                [str(sdist_python), "-m", "pytest"],
                cwd=source_dir,
            )
        )
        node = shutil.which("node")
        if node is None:
            raise SystemExit("node is required for sdist interoperability verification")
        results.append(
            _run(
                "sdist independent JS interoperability",
                [node, "interop/js/verify.mjs"],
                cwd=source_dir,
            )
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--final",
        action="store_true",
        help="also require tools/check_readiness.py to pass",
    )
    parser.add_argument(
        "--skip-build-smoke",
        action="store_true",
        help="skip wheel/sdist clean-install smoke checks",
    )
    args = parser.parse_args(argv)

    results: list[CheckResult] = []
    results.append(
        _run(
            "schema contract",
            _python("tools/check_schema_contract.py"),
        )
    )
    results.append(_run("ruff", _python("-m", "ruff", "check", ".")))
    results.append(
        _run("ruff format", _python("-m", "ruff", "format", "--check", "."))
    )
    results.append(_run("mypy", _python("-m", "mypy")))
    results.append(_run("pytest", _python("-m", "pytest")))

    dist = ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    results.append(_run("build", _python("-m", "build")))

    node = shutil.which("node")
    if node is None:
        raise SystemExit("node is required for the independent interoperability check")
    results.append(
        _run(
            "independent JavaScript interoperability",
            [node, "interop/js/verify.mjs"],
        )
    )

    if not args.skip_build_smoke:
        _clean_distribution_smoke(results)

    if args.final:
        results.append(
            _run(
                "final readiness",
                _python("tools/check_readiness.py"),
            )
        )

    print(
        json.dumps(
            {
                "mode": "final" if args.final else "engineering",
                "checks": [asdict(item) for item in results],
                "status": "passed",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
