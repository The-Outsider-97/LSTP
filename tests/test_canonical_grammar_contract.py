from __future__ import annotations

from pathlib import Path


CANONICAL = Path("spec/grammar.ebnf")
COMPACT = Path("spec/compact-grammar.ebnf")


def _canonical() -> str:
    return CANONICAL.read_text(encoding="utf-8")


def test_canonical_grammar_defines_all_whitepaper_packet_forms() -> None:
    text = _canonical()
    for production in (
        "atomic_packet = octad_core",
        'framed_packet = "[", layout_space_opt, octad_core',
        "named_packet = identifier",
        "stream_packet = named_packet",
        "packet_sep = line_break_plus",
    ):
        assert production in text


def test_octad_core_has_whitepaper_order() -> None:
    text = _canonical()
    block = text.split("octad_core =", 1)[1].split(";", 1)[0]
    expected = [
        "pragmatics_segment",
        "atoms_segment",
        "relations_segment",
        "context_segment",
        "confidence_segment",
        "permissions_segment",
        "evidence_segment",
        "output_segment",
    ]
    offsets = [block.index(item) for item in expected]
    assert offsets == sorted(offsets)


def test_canonical_pragmatics_exposes_type_and_speech_act() -> None:
    text = _canonical()
    assert '"TYPE", assign, identifier_value' in text
    assert '"SPEECH_ACT", assign, identifier_value' in text
    assert '"act"' not in text


def test_canonical_permission_modes_are_exactly_whitepaper_six() -> None:
    text = _canonical()
    line = text.split("permission_mode =", 1)[1].split(";", 1)[0]
    for mode in ("RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT"):
        assert f'"{mode}"' in line
    for candidate in ("AUTO", "SANDBOX", "ADVISORY", "capabilities", "profile"):
        assert candidate not in line


def test_compact_grammar_remains_separate_profile() -> None:
    canonical = _canonical()
    compact = COMPACT.read_text(encoding="utf-8")
    assert "main_clause =" not in canonical
    assert "main_clause =" in compact
    assert "force_prefix =" in compact
