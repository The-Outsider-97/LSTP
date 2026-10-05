"""Recursive-descent parser for the strict LSTP v0.1 carrier subset."""

from __future__ import annotations

from decimal import Decimal

from lstp.errors import Diagnostic, LatticeSyntaxError
from lstp.text.ast import (
    CallExpression, ConfidenceTopLevel, ConstraintBlock, ConstraintEntry,
    ConstraintTopLevel, ContextReference, Document, EvidenceClause,
    EvidenceTopLevel, Expression, Identifier, ListExpression, MainClause,
    MetadataClause, NumberLiteral, OutputClause, OutputTopLevel, SourceSpan,
    StringLiteral, TargetReference, BooleanLiteral, NullLiteral,
)
from lstp.text.tokenizer import tokenize
from lstp.text.tokens import Token, TokenKind

_FORCE = {TokenKind.DIRECTIVE, TokenKind.URGENT_DIRECTIVE, TokenKind.QUESTION, TokenKind.DECLARATIVE}


class Parser:
    def __init__(self, tokens: tuple[Token, ...]) -> None:
        self.tokens = tokens
        self.index = 0

    def _current(self) -> Token:
        return self.tokens[self.index]

    def _peek(self, offset: int = 1) -> Token:
        return self.tokens[min(self.index + offset, len(self.tokens) - 1)]

    def _advance(self) -> Token:
        token = self._current()
        if token.kind is not TokenKind.EOF:
            self.index += 1
        return token

    def _span(self, token: Token) -> SourceSpan:
        return SourceSpan(token.line, token.column)

    def _error(self, code: str, message: str, token: Token | None = None) -> LatticeSyntaxError:
        token = token or self._current()
        return LatticeSyntaxError(Diagnostic(code, message, token.line, token.column))

    def _match(self, kind: TokenKind) -> Token | None:
        if self._current().kind is kind:
            return self._advance()
        return None

    def _expect(self, kind: TokenKind, message: str) -> Token:
        if self._current().kind is not kind:
            raise self._error("unexpected_token", message)
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._match(TokenKind.NEWLINE):
            pass

    def parse_document(self) -> Document:
        clauses = []
        self._skip_newlines()
        while self._current().kind is not TokenKind.EOF:
            clauses.append(self._parse_top_level())
            if self._current().kind is TokenKind.EOF:
                break
            if self._current().kind is not TokenKind.NEWLINE:
                raise self._error("expected_clause_boundary", "expected newline between top-level clauses")
            self._skip_newlines()
        return Document(tuple(clauses))

    def _parse_top_level(self):
        token = self._current()
        if token.kind in _FORCE:
            return self._parse_main()
        if token.kind is TokenKind.LBRACE:
            block = self._parse_constraints(); return ConstraintTopLevel(block, block.span)
        if token.kind is TokenKind.ARROW:
            out = self._parse_output(); return OutputTopLevel(out, out.span)
        if token.kind is TokenKind.PERCENT:
            span = self._span(token); return ConfidenceTopLevel(self._parse_confidence(), span)
        if token.kind is TokenKind.SEMICOLON:
            return self._parse_metadata()
        if token.kind is TokenKind.IDENTIFIER and token.value in {"because", "assume", "challenge"}:
            ev = self._parse_evidence(); return EvidenceTopLevel(ev, ev.span)
        raise self._error("unsupported_top_level", "top-level construct is not implemented by the strict v0.1 parser")

    def _parse_main(self) -> MainClause:
        force = self._advance()
        action = self._expect(TokenKind.IDENTIFIER, "expected action identifier")
        focus: TargetReference | ContextReference | None = None
        if self._current().kind is TokenKind.AT:
            focus = self._parse_target()
        elif self._current().kind is TokenKind.CONTEXT:
            focus = self._parse_context_ref()
        operation: Expression | None = None
        if self._match(TokenKind.DOUBLE_COLON):
            operation = self._parse_expression()
        constraints: list[ConstraintBlock] = []
        evidence: list[EvidenceClause] = []
        while True:
            if self._current().kind is TokenKind.LBRACE:
                constraints.append(self._parse_constraints())
            elif self._current().kind is TokenKind.IDENTIFIER and self._current().value in {"because", "assume", "challenge"}:
                evidence.append(self._parse_evidence())
            else:
                break
        output = self._parse_output() if self._current().kind is TokenKind.ARROW else None
        confidence = self._parse_confidence() if self._current().kind is TokenKind.PERCENT else None
        metadata = self._parse_metadata() if self._current().kind is TokenKind.SEMICOLON else None
        if self._current().kind not in {TokenKind.NEWLINE, TokenKind.EOF}:
            raise self._error("unexpected_clause_suffix", "unexpected token after main clause")
        return MainClause(force.value, action.value, focus, operation, tuple(constraints), tuple(evidence), output, confidence, metadata, self._span(force))

    def _parse_target(self) -> TargetReference:
        start = self._expect(TokenKind.AT, "expected '@'")
        name = self._expect(TokenKind.IDENTIFIER, "expected target identifier")
        if self._current().kind is TokenKind.LBRACKET:
            raise self._error("scope_not_yet_compilable", "target scope parsing is reserved for the next compiler increment")
        return TargetReference(name.value, (), self._span(start))

    def _parse_context_ref(self) -> ContextReference:
        start = self._expect(TokenKind.CONTEXT, "expected context reference")
        depth = self._expect(TokenKind.NUMBER, "expected context depth")
        if "." in depth.value:
            raise self._error("context_depth_integer", "context depth must be an integer", depth)
        agent = None
        if self._match(TokenKind.AT):
            agent = self._expect(TokenKind.IDENTIFIER, "expected agent identifier").value
        return ContextReference(int(depth.value), agent, self._span(start))

    def _parse_constraints(self) -> ConstraintBlock:
        start = self._expect(TokenKind.LBRACE, "expected '{'")
        entries: list[ConstraintEntry] = []
        if self._match(TokenKind.RBRACE):
            return ConstraintBlock((), self._span(start))
        while True:
            key = self._expect(TokenKind.IDENTIFIER, "expected constraint key")
            sep = self._current()
            if sep.kind not in {TokenKind.EQUAL, TokenKind.COLON}:
                raise self._error("expected_constraint_separator", "expected '=' or ':'")
            self._advance()
            entries.append(ConstraintEntry(key.value, sep.value, self._parse_expression(), self._span(key)))
            if not self._match(TokenKind.COMMA):
                break
        self._expect(TokenKind.RBRACE, "expected '}'")
        return ConstraintBlock(tuple(entries), self._span(start))

    def _parse_output(self) -> OutputClause:
        start = self._expect(TokenKind.ARROW, "expected '->'")
        token = self._current()
        if token.kind not in {TokenKind.IDENTIFIER, TokenKind.STRING}:
            raise self._error("expected_output_format", "expected output format")
        self._advance()
        if self._current().kind is TokenKind.AT:
            raise self._error("unsupported_zoom", "@z zoom has no canonical v0.1 field")
        return OutputClause(token.value, None, self._span(start))

    def _parse_confidence(self) -> Decimal:
        self._expect(TokenKind.PERCENT, "expected '%'")
        token = self._expect(TokenKind.NUMBER, "expected confidence number")
        value = Decimal(token.value)
        if not Decimal("0") <= value <= Decimal("1"):
            raise self._error("confidence_range", "confidence must be between 0 and 1", token)
        return value

    def _parse_metadata(self) -> MetadataClause:
        start = self._expect(TokenKind.SEMICOLON, "expected ';'")
        refs: list[ContextReference] = []
        if self._current().kind is TokenKind.IDENTIFIER and self._current().value == "ctx" and self._peek().kind is TokenKind.CONTEXT:
            self._advance(); refs.append(self._parse_context_ref())
        else:
            raise self._error("unsupported_metadata", "only '; ctx↑N' metadata is canonical in this compiler increment")
        return MetadataClause(tuple(refs), self._span(start))

    def _parse_evidence(self) -> EvidenceClause:
        key = self._expect(TokenKind.IDENTIFIER, "expected evidence keyword")
        self._expect(TokenKind.LBRACKET, "expected '['")
        items: list[Expression] = []
        if self._current().kind is not TokenKind.RBRACKET:
            items.append(self._parse_expression())
            while self._match(TokenKind.COMMA):
                items.append(self._parse_expression())
        self._expect(TokenKind.RBRACKET, "expected ']'")
        return EvidenceClause(key.value, tuple(items), self._span(key))

    def _parse_expression(self) -> Expression:
        first = self._parse_primary()
        if self._current().kind in {TokenKind.PLUS, TokenKind.PIPE, TokenKind.MINUS, TokenKind.TILDE, TokenKind.COLON}:
            raise self._error("unsupported_expression", "this expression form is parsed by the grammar but not yet in the canonical compiler subset")
        return first

    def _parse_primary(self) -> Expression:
        token = self._current()
        if token.kind is TokenKind.IDENTIFIER:
            self._advance()
            if token.value == "true": return BooleanLiteral(True, self._span(token))
            if token.value == "false": return BooleanLiteral(False, self._span(token))
            if token.value == "null": return NullLiteral(self._span(token))
            if self._match(TokenKind.LPAREN):
                args: list[Expression] = []
                if self._current().kind is not TokenKind.RPAREN:
                    args.append(self._parse_expression())
                    while self._match(TokenKind.COMMA): args.append(self._parse_expression())
                self._expect(TokenKind.RPAREN, "expected ')'")
                return CallExpression(token.value, tuple(args), self._span(token))
            return Identifier(token.value, self._span(token))
        if token.kind is TokenKind.STRING:
            self._advance(); return StringLiteral(token.value, self._span(token))
        if token.kind is TokenKind.NUMBER:
            self._advance(); return NumberLiteral(Decimal(token.value), self._span(token))
        if token.kind is TokenKind.LBRACKET:
            start = self._advance(); items: list[Expression] = []
            if self._current().kind is not TokenKind.RBRACKET:
                items.append(self._parse_expression())
                while self._match(TokenKind.COMMA): items.append(self._parse_expression())
            self._expect(TokenKind.RBRACKET, "expected ']'")
            return ListExpression(tuple(items), self._span(start))
        if token.kind is TokenKind.AT: return self._parse_target()
        if token.kind is TokenKind.CONTEXT: return self._parse_context_ref()
        raise self._error("expected_expression", "expected Lattice expression")


def parse(source: str) -> Document:
    return Parser(tokenize(source)).parse_document()
