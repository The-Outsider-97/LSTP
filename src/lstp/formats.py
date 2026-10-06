"""Shared semantic format validators used by the v0.1 model and host runtime."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

_RFC3339_RE = re.compile(
    r"^(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12]\d|3[01])"
    r"[Tt](?P<hour>[01]\d|2[0-3]):(?P<minute>[0-5]\d):"
    r"(?P<second>[0-5]\d|60)(?P<fraction>\.\d+)?"
    r"(?P<zone>[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)

_GRANDFATHERED = frozenset(
    {
        "art-lojban",
        "cel-gaulish",
        "en-gb-oed",
        "i-ami",
        "i-bnn",
        "i-default",
        "i-enochian",
        "i-hak",
        "i-klingon",
        "i-lux",
        "i-mingo",
        "i-navajo",
        "i-pwn",
        "i-tao",
        "i-tay",
        "i-tsu",
        "no-bok",
        "no-nyn",
        "sgn-be-fr",
        "sgn-be-nl",
        "sgn-ch-de",
        "zh-guoyu",
        "zh-hakka",
        "zh-min",
        "zh-min-nan",
        "zh-xiang",
    }
)
_ALNUM_RE = re.compile(r"^[A-Za-z0-9]+$")
_ALPHA_RE = re.compile(r"^[A-Za-z]+$")
_DIGIT_RE = re.compile(r"^\d+$")


def parse_rfc3339(value: str) -> datetime:
    """Validate an RFC 3339 date-time and return an aware UTC datetime.

    Leap-second ``:60`` is accepted and normalized to the first instant of the
    following minute. Fractions beyond microseconds are floored for host-side
    comparisons, which can expire an authorization slightly early but never
    extends its lifetime.
    """
    if not isinstance(value, str):
        raise TypeError("RFC 3339 value must be a string")
    match = _RFC3339_RE.fullmatch(value)
    if match is None:
        raise ValueError("invalid RFC 3339 date-time")

    year = int(match.group("year"))
    if year == 0:
        raise ValueError("RFC 3339 year 0000 is outside the LSTP runtime profile")
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))

    fraction = match.group("fraction")
    microsecond = 0
    if fraction is not None:
        digits = fraction[1:]
        microsecond = int((digits[:6] + "000000")[:6])

    zone = match.group("zone")
    if zone.lower() == "z":
        tz = timezone.utc
    else:
        sign = 1 if zone[0] == "+" else -1
        offset_hours = int(zone[1:3])
        offset_minutes = int(zone[4:6])
        offset = timedelta(hours=offset_hours, minutes=offset_minutes) * sign
        tz = timezone(offset)

    leap_second = second == 60
    safe_second = 59 if leap_second else second
    try:
        parsed = datetime(
            year,
            month,
            day,
            hour,
            minute,
            safe_second,
            microsecond,
            tzinfo=tz,
        )
    except ValueError as exc:
        raise ValueError("invalid RFC 3339 calendar date-time") from exc
    if leap_second:
        parsed += timedelta(seconds=1)
    return parsed.astimezone(timezone.utc)


def is_well_formed_bcp47(value: str) -> bool:
    """Return whether *value* is structurally well-formed under BCP 47/RFC 5646.

    This validates the language-tag grammar, duplicate variants, and duplicate
    extension singletons. It intentionally does not claim IANA registry
    membership for individual subtags.
    """
    if not isinstance(value, str) or not value or len(value) > 255:
        return False
    if "_" in value or value.startswith("-") or value.endswith("-") or "--" in value:
        return False
    lower = value.lower()
    if lower in _GRANDFATHERED:
        return True

    parts = value.split("-")
    if any(not (1 <= len(part) <= 8 and _ALNUM_RE.fullmatch(part)) for part in parts):
        return False

    index = 0
    if parts[0].lower() == "x":
        return len(parts) >= 2 and all(1 <= len(part) <= 8 for part in parts[1:])

    language = parts[index]
    if not _ALPHA_RE.fullmatch(language) or not (2 <= len(language) <= 8):
        return False
    index += 1

    if 2 <= len(language) <= 3:
        extlang_count = 0
        while (
            index < len(parts)
            and len(parts[index]) == 3
            and _ALPHA_RE.fullmatch(parts[index])
            and extlang_count < 3
        ):
            extlang_count += 1
            index += 1

    if index < len(parts) and len(parts[index]) == 4 and _ALPHA_RE.fullmatch(parts[index]):
        index += 1

    if index < len(parts):
        region = parts[index]
        if (len(region) == 2 and _ALPHA_RE.fullmatch(region)) or (
            len(region) == 3 and _DIGIT_RE.fullmatch(region)
        ):
            index += 1

    variants: set[str] = set()
    while index < len(parts):
        part = parts[index]
        is_variant = (
            5 <= len(part) <= 8
            or (len(part) == 4 and part[0].isdigit())
        )
        if not is_variant:
            break
        key = part.lower()
        if key in variants:
            return False
        variants.add(key)
        index += 1

    singletons: set[str] = set()
    while index < len(parts):
        singleton = parts[index]
        if len(singleton) != 1 or singleton.lower() == "x" or not _ALNUM_RE.fullmatch(singleton):
            break
        key = singleton.lower()
        if key in singletons:
            return False
        singletons.add(key)
        index += 1
        start = index
        while index < len(parts) and 2 <= len(parts[index]) <= 8:
            index += 1
        if index == start:
            return False

    if index < len(parts) and parts[index].lower() == "x":
        index += 1
        if index >= len(parts):
            return False
        while index < len(parts):
            if not 1 <= len(parts[index]) <= 8:
                return False
            index += 1

    return index == len(parts)


def validate_bcp47(value: str) -> None:
    """Raise ``ValueError`` unless *value* is a well-formed BCP 47 language tag."""
    if not is_well_formed_bcp47(value):
        raise ValueError("invalid BCP 47 language tag")
