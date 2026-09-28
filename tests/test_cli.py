import json
import subprocess
import sys

import pytest


def run(*args, data=b""):
    return subprocess.run([sys.executable, "-m", "lstp", *args], input=data, capture_output=True)


def test_help_and_version():
    assert run("--help").returncode == 0
    assert b"0.1.0a1" in run("--version").stdout


def test_stdin_is_not_protocol_validation_or_authority():
    result = run("json-check", data=b'{"permissions":{"mode":"anything"}}')
    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "json_valid": True,
        "protocol_validated": False,
        "authorization_evaluated": False,
    }
    assert result.stderr == b""


def test_file(tmp_path):
    path = tmp_path / "input.json"
    path.write_bytes(b"{}")
    assert run("json-check", str(path)).returncode == 0


@pytest.mark.parametrize(
    "data", [b"{", b'"\xff"', b" " * 1_048_577], ids=["syntax", "utf8", "oversized"]
)
def test_invalid_stdin(data):
    result = run("json-check", data=data)
    assert result.returncode == 1
    assert json.loads(result.stderr)["code"]
    assert result.stdout == b""
    assert b"Traceback" not in result.stderr


def test_io_and_usage_exit_codes(tmp_path):
    assert run("json-check", str(tmp_path / "missing")).returncode == 3
    assert run("validate").returncode == 2
    assert run().returncode == 2
