"""Deterministic tokenizer for strict LSTP v0.1 Lattice text."""

from __future__ import annotations

import json

from lstp.errors import Diagnostic, LatticeSyntaxError
from lstp.text.tokens import Token, TokenKind

_SINGLE = {
    "!": TokenKind.DIRECTIVE, "?": TokenKind.QUESTION, ".": TokenKind.DECLARATIVE,
    "@": TokenKind.AT, "↑": TokenKind.CONTEXT, "=": TokenKind.EQUAL,
    ":": TokenKind.COLON, "{": TokenKind.LBRACE, "}": TokenKind.RBRACE,
    "[": TokenKind.LBRACKET, "]": TokenKind.RBRACKET, "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN, ",": TokenKind.COMMA, "|": TokenKind.PIPE,
    "+": TokenKind.PLUS, "-": TokenKind.MINUS, "~": TokenKind.TILDE,
    "%": TokenKind.PERCENT, ";": TokenKind.SEMICOLON, "#": TokenKind.HASH,
}


class Tokenizer:
    def __init__(self, source: str) -> None:
        self.source = source[1:] if source.startswith("\ufeff") else source
        self.index = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> str:
        index = self.index + offset
        return self.source[index] if index < len(self.source) else ""

    def _advance(self) -> str:
        char = self._peek()
        if not char:
            return ""
        self.index += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _error(self, code: str, message: str) -> LatticeSyntaxError:
        return LatticeSyntaxError(Diagnostic(code, message, self.line, self.column))

    def _token(self, kind: TokenKind, value: str, line: int, column: int) -> Token:
        return Token(kind, value, line, column)

    def _read_string(self) -> Token:
        line, column, start = self.line, self.column, self.index
        self._advance()
        escaped = False
        while True:
            char = self._peek()
            if not char:
                raise self._error("unterminated_string", "unterminated Lattice string literal")
            if char in "\r\n":
                raise self._error("newline_in_string", "unescaped newline in string literal")
            self._advance()
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                break
        try:
            value = json.loads(self.source[start:self.index])
        except json.JSONDecodeError:
            raise self._error("invalid_string", "invalid JSON-style string escape") from None
        return self._token(TokenKind.STRING, value, line, column)

    def _read_number(self) -> Token:
        line, column, start = self.line, self.column, self.index
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        return self._token(TokenKind.NUMBER, self.source[start:self.index], line, column)

    def _read_identifier(self) -> Token:
        line, column, start = self.line, self.column, self.index
        self._advance()
        while True:
            char = self._peek()
            if char.isascii() and (char.isalnum() or char in "_-"):
                self._advance()
            elif char == "." and self._peek(1).isascii() and (self._peek(1).isalpha() or self._peek(1) == "_"):
                self._advance()
                self._advance()
            else:
                break
        return self._token(TokenKind.IDENTIFIER, self.source[start:self.index], line, column)

    def tokenize(self) -> tuple[Token, ...]:
        tokens: list[Token] = []
        while self.index < len(self.source):
            char = self._peek()
            if char in " \t":
                self._advance(); continue
            if char in "\r\n":
                line, column = self.line, self.column
                if char == "\r":
                    self._advance()
                    if self._peek() == "\n": self._advance()
                else: self._advance()
                tokens.append(self._token(TokenKind.NEWLINE, "\n", line, column)); continue
            line, column = self.line, self.column
            pair = self.source[self.index:self.index + 2]
            if pair in {"!!", "->", "::", ".."}:
                kind = {"!!": TokenKind.URGENT_DIRECTIVE, "->": TokenKind.ARROW, "::": TokenKind.DOUBLE_COLON, "..": TokenKind.RANGE}[pair]
                self._advance(); self._advance(); tokens.append(self._token(kind, pair, line, column)); continue
            if char == '"': tokens.append(self._read_string()); continue
            if char.isdigit(): tokens.append(self._read_number()); continue
            if char.isascii() and (char.isalpha() or char == "_"): tokens.append(self._read_identifier()); continue
            kind = _SINGLE.get(char)
            if kind is not None:
                self._advance(); tokens.append(self._token(kind, char, line, column)); continue
            raise self._error("unexpected_character", f"unexpected Lattice character U+{ord(char):04X}")
        tokens.append(self._token(TokenKind.EOF, "", self.line, self.column))
        return tuple(tokens)


def tokenize(source: str) -> tuple[Token, ...]:
    return Tokenizer(source).tokenize()
