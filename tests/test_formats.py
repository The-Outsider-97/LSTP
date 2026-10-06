from __future__ import annotations

from datetime import timezone

from lstp.formats import is_well_formed_bcp47, parse_rfc3339
from lstp.models import Atom, Context, Octad, Output, PacketEnvelope, Permissions, Pragmatics
from lstp.packet.validator import validate_packet


def _packet(*, context_time: str | None = None, output_language: str | None = None, atom_language: str | None = None, expires_at: str | None = None) -> PacketEnvelope:
    atoms = () if atom_language is None else (Atom("a0", "concept", value="hello", language=atom_language),)
    return PacketEnvelope(
        Octad(
            Pragmatics("inform"),
            atoms,
            (),
            Context("thread-1", time=context_time),
            1.0,
            Permissions((), (), expires_at=expires_at),
            (),
            Output("NL", language=output_language),
        ),
        "packet-1",
        "0.1",
    )


def test_rfc3339_requires_valid_calendar_and_timezone() -> None:
    parsed = parse_rfc3339("2026-10-05T21:11:12.123456789+02:00")
    assert parsed.tzinfo is timezone.utc

    for invalid in (
        "2026-02-30T12:00:00Z",
        "2026-10-05T12:00:00",
        "2026-13-05T12:00:00Z",
        "0000-01-01T00:00:00Z",
        "2026-10-05 12:00:00Z",
    ):
        try:
            parse_rfc3339(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid RFC3339 value: {invalid}")


def test_rfc3339_accepts_leap_second_conservatively() -> None:
    parsed = parse_rfc3339("2016-12-31T23:59:60Z")
    assert parsed.isoformat() == "2017-01-01T00:00:00+00:00"


def test_bcp47_structural_validation() -> None:
    valid = ("en", "en-US", "zh-Hant-TW", "sl-rozaj-biske", "de-CH-1901", "x-private", "i-klingon")
    invalid = ("", "en_US", "en--US", "a", "en-", "en-US-US", "en-a", "en-a-foo-a-bar")
    assert all(is_well_formed_bcp47(value) for value in valid)
    assert all(not is_well_formed_bcp47(value) for value in invalid)


def test_semantic_validator_reports_format_fields_without_constructor_duplication() -> None:
    result = validate_packet(
        _packet(
            context_time="2026-02-30T12:00:00Z",
            output_language="en_US",
            atom_language="bad_tag",
            expires_at="2026-10-05T12:00:00",
        )
    )
    codes = {item.code for item in result.diagnostics}
    assert codes >= {
        "invalid_context_time",
        "invalid_output_language",
        "invalid_atom_language",
        "invalid_permission_expiry",
    }
