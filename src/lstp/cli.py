"""Development CLI: JSON input inspection, without protocol validation claims."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from lstp.errors import LSTPError
from lstp.json_input import DEFAULT_LIMITS, loads_json
from lstp.packet.canonical import canonical_dumps, canonical_loads
from lstp.packet.compact import compact_dumps, compact_loads
from lstp.version import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"LSTP tooling {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("json-check", help="Check bounded JSON input, NOT LSTP validity")
    check.add_argument("input", nargs="?", default="-", help="UTF-8 file or - for stdin")
    for name, help_text in (
        ("compact-encode", "Validate canonical LSTP and encode the lossless L1 carrier"),
        ("compact-decode", "Restore and validate canonical LSTP from the L1 carrier"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("input", nargs="?", default="-", help="UTF-8 file or - for stdin")
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            data = sys.stdin.buffer.read(DEFAULT_LIMITS.max_bytes + 1)
        else:
            with Path(args.input).open("rb") as stream:
                data = stream.read(DEFAULT_LIMITS.max_bytes + 1)
        if args.command == "compact-encode":
            sys.stdout.buffer.write(compact_dumps(canonical_loads(data)))
            return 0
        if args.command == "compact-decode":
            sys.stdout.buffer.write(canonical_dumps(compact_loads(data)))
            return 0
        loads_json(data)
    except LSTPError as error:
        print(json.dumps(asdict(error.diagnostic)), file=sys.stderr)
        return 1
    except OSError:
        print(json.dumps({"code": "input_io", "message": "Cannot read input."}), file=sys.stderr)
        return 3
    print(
        json.dumps(
            {
                "json_valid": True,
                "protocol_validated": False,
                "authorization_evaluated": False,
            },
            sort_keys=True,
        )
    )
    return 0
