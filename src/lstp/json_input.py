"""Bounded JSON decoding, NOT Octad or permission validation.

Decimals preserve decimal values without binary float overflow/underflow.
Object duplicates and unpaired surrogates are rejected; data is never executed.
Limits are implementation policy, not assertions about the LSTP wire standard.
"""

import json
from dataclasses import dataclass, fields
from decimal import Context, Decimal, InvalidOperation
from typing import Any, NoReturn

from lstp.errors import Diagnostic, JSONInputError, ResourceLimitError


@dataclass(frozen=True)
class InputLimits:
    max_bytes: int = 1_048_576
    max_depth: int = 64
    max_string_chars: int = 65_536
    max_collection_items: int = 10_000
    max_nodes: int = 50_000
    max_number_chars: int = 128

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{field.name} must be a positive integer")
        # Keep the standard decoder below its recursive-stack failure boundary.
        if self.max_depth > 64:
            raise ValueError("max_depth must not exceed 64")


DEFAULT_LIMITS = InputLimits()


def _limit(code: str, message: str) -> NoReturn:
    raise ResourceLimitError(Diagnostic(code, message))


def _unicode_scalar(text: str) -> None:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in text):
        raise JSONInputError(Diagnostic("invalid_unicode", "Unpaired Unicode surrogate."))


def _scan_depth(text: str, maximum: int) -> None:
    """Count containers before invoking the recursive standard JSON decoder."""
    depth = 0
    quoted = False
    escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > maximum:
                _limit("depth_limit", "JSON nesting exceeds the input limit.")
        elif char in "]}":
            depth -= 1
            if depth < 0:
                # Do not let malformed prefixes conceal excessive later depth.
                raise JSONInputError(Diagnostic("json_syntax", "Unmatched JSON closing delimiter."))


def loads_json(source: str | bytes, *, limits: InputLimits = DEFAULT_LIMITS) -> Any:
    """Decode one JSON value under explicit limits; never certify protocol validity.

    Integers become int and fraction/exponent tokens become Decimal. No Unicode
    normalization is performed. Locations, where available, are 1-based Unicode
    code-point positions. Diagnostic messages never echo input values or keys.
    """
    if isinstance(source, bytes):
        if len(source) > limits.max_bytes:
            _limit("byte_limit", "JSON input exceeds the byte limit.")
        try:
            text = source.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise JSONInputError(Diagnostic("invalid_utf8", "Input must be UTF-8.")) from None
    elif isinstance(source, str):
        if len(source) > limits.max_bytes:
            _limit("byte_limit", "JSON input exceeds the byte limit.")
        _unicode_scalar(source)
        if len(source.encode("utf-8")) > limits.max_bytes:
            _limit("byte_limit", "JSON input exceeds the byte limit.")
        text = source
    else:
        raise TypeError("source must be str or bytes")

    _scan_depth(text, limits.max_depth)

    def number(token: str) -> int | Decimal:
        if len(token) > limits.max_number_chars:
            _limit("number_limit", "JSON numeric token exceeds the input limit.")
        try:
            value = (
                Decimal(token, context=Context(traps=[InvalidOperation]))
                if any(c in token for c in ".eE")
                else int(token)
            )
        except (ValueError, InvalidOperation):
            raise JSONInputError(Diagnostic("invalid_number", "Unsupported JSON number.")) from None
        if isinstance(value, Decimal) and not value.is_finite():
            # Defense in depth: only finite values cross the input boundary.
            raise JSONInputError(Diagnostic("invalid_number", "Unsupported JSON number."))
        return value

    def reject_constant(token: str) -> NoReturn:
        raise JSONInputError(Diagnostic("nonfinite_number", "JSON requires finite numbers."))

    def pairs(entries: list[tuple[str, Any]]) -> dict[str, Any]:
        if len(entries) > limits.max_collection_items:
            _limit("collection_limit", "JSON object exceeds the item limit.")
        result: dict[str, Any] = {}
        for key, value in entries:
            if key in result:
                raise JSONInputError(Diagnostic("duplicate_key", "Duplicate JSON object key."))
            result[key] = value
        return result

    try:
        value = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_int=number,
            parse_float=number,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as error:
        raise JSONInputError(
            Diagnostic(
                "json_syntax",
                "Malformed JSON; check delimiters, literals and escaping.",
                error.lineno,
                error.colno,
            )
        ) from None
    except RecursionError:
        raise ResourceLimitError(
            Diagnostic("depth_limit", "JSON decoder depth exceeded.")
        ) from None

    # Iterative walk also checks object keys and decoded escape sequences.
    pending = [value]
    count = 0
    while pending:
        item = pending.pop()
        count += 1
        if count > limits.max_nodes:
            _limit("node_limit", "JSON value exceeds the total node limit.")
        if isinstance(item, str):
            if len(item) > limits.max_string_chars:
                _limit("string_limit", "JSON string exceeds the character limit.")
            _unicode_scalar(item)
        elif isinstance(item, (dict, list)):
            if len(item) > limits.max_collection_items:
                _limit("collection_limit", "JSON collection exceeds the item limit.")
            if isinstance(item, dict):
                pending.extend(item.keys())
                pending.extend(item.values())
            else:
                pending.extend(item)
    return value
