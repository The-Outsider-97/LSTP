from __future__ import annotations

from pathlib import Path

from lstp import canonical_loads
from lstp.packet.compiler import CompilerOptions, compile_lattice


ROOT = Path(__file__).resolve().parents[1]
LATTICE = ROOT / "examples" / "lattice"
PACKETS = ROOT / "examples" / "packets"

CASES = (
    "analyze-sales",
    "context-reference",
    "decision",
    "preview-email",
    "summarize-meeting",
)


def _resolver(depth: int, agent: str | None) -> str:
    return f"{agent}-{depth}" if agent is not None else f"history-{depth}"


def test_all_documented_examples_compile_to_their_canonical_packets() -> None:
    for name in CASES:
        source = (LATTICE / f"{name}.lat").read_text(encoding="utf-8")
        expected = canonical_loads(
            (PACKETS / f"{name}.packet.json").read_bytes()
        )
        compiled = compile_lattice(
            source,
            options=CompilerOptions(
                packet_id=f"example-{name}",
                thread_id="example-thread",
                context_resolver=_resolver,
            ),
        )
        assert compiled == expected, name


def test_examples_are_nonempty_and_pairwise_complete() -> None:
    lattice_names = {path.stem for path in LATTICE.glob("*.lat")}
    packet_names = {
        path.name.removesuffix(".packet.json")
        for path in PACKETS.glob("*.packet.json")
    }
    assert lattice_names == packet_names == set(CASES)
    for directory in (LATTICE, PACKETS):
        for path in directory.iterdir():
            if path.is_file():
                assert path.read_bytes().strip(), path
