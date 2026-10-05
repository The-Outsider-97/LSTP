"""Token definitions for strict LSTP v0.1 Lattice text."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenKind(str, Enum):
    DIRECTIVE = "DIRECTIVE"
    URGENT_DIRECTIVE = "URGENT_DIRECTIVE"
    QUESTION = "QUESTION"
    DECLARATIVE = "DECLARATIVE"
    AT = "AT"
    CONTEXT = "CONTEXT"
    ARROW = "ARROW"
    DOUBLE_COLON = "DOUBLE_COLON"
    EQUAL = "EQUAL"
    COLON = "COLON"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    PIPE = "PIPE"
    PLUS = "PLUS"
    MINUS = "MINUS"
    TILDE = "TILDE"
    PERCENT = "PERCENT"
    SEMICOLON = "SEMICOLON"
    HASH = "HASH"
    RANGE = "RANGE"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    value: str
    line: int
    column: int
