"""Recursive-descent parser for the strict LSTP v0.1 Lattice grammar."""

from __future__ import annotations

from decimal import Decimal

from lstp.errors import Diagnostic, LatticeSyntaxError
from lstp.text.ast import (
    AlternativeExpression,
    AmbiguityClause,
    AnnotationExpression,
    ApproximationExpression,
    BooleanLiteral,
    CallExpression,
    ClaimClause,
    CompositionExpression,
    ConfidenceTopLevel,
    ConstraintBlock,
    ConstraintEntry,
    ConstraintTopLevel,
    ContextCommand,
    ContextReference,
    Document,
    EvidenceClause,
    EvidenceTopLevel,
    Expression,
    Identifier,
    ListExpression,
    MacroDefinition,
    MacroReference,
    MainClause,
    MetadataClause,
    MetadataItem,
    NullLiteral,
    NumberLiteral,
    OutputClause,
    OutputTopLevel,
    RelationTail,
    ScopeAssignment,
    ScopeExpression,
    ScopeItem,
    ScopeRange,
    ScopeValue,
    SourceSpan,
    StringLiteral,
    TargetReference,
    UnaryExpression,
)
from lstp.text.tokenizer import tokenize
from lstp.text.tokens import Token, TokenKind

_FORCE = {
    TokenKind.DIRECTIVE,
    TokenKind.URGENT_DIRECTIVE,
    TokenKind.QUESTION,
    TokenKind.DECLARATIVE,
}
_PERIOD_UNITS = {"s", "m", "h", "D", "W", "M", "Q", "Y"}


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

    @staticmethod
    def _span(token: Token) -> SourceSpan:
        return SourceSpan(token.line, token.column)

    def _error(
        self, code: str, message: str, token: Token | None = None
    ) -> LatticeSyntaxError:
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
                raise self._error(
                    "expected_clause_boundary",
                    "expected newline between top-level clauses",
                )
            self._skip_newlines()
        return Document(tuple(clauses))

    def _parse_top_level(self):
        token = self._current()
        if token.kind in _FORCE:
            return self._parse_main()
        if token.kind is TokenKind.LBRACE:
            block = self._parse_constraints()
            return ConstraintTopLevel(block, block.span)
        if token.kind is TokenKind.ARROW:
            out = self._parse_output()
            return OutputTopLevel(out, out.span)
        if token.kind is TokenKind.PERCENT:
            span = self._span(token)
            return ConfidenceTopLevel(self._parse_confidence(), span)
        if token.kind is TokenKind.SEMICOLON:
            return self._parse_metadata()
        if token.kind is TokenKind.IDENTIFIER:
            if token.value in {"because", "assume", "challenge"}:
                ev = self._parse_evidence()
                return EvidenceTopLevel(ev, ev.span)
            if token.value == "claim":
                return self._parse_claim()
            if token.value == "ambig":
                return self._parse_ambiguity()
            if token.value in {"ctx.push", "ctx.pop"}:
                return self._parse_context_command()
            if token.value == "def":
                return self._parse_macro_definition()
        raise self._error(
            "unsupported_top_level",
            "top-level construct is not part of strict LSTP v0.1",
        )

    def _parse_main(self) -> MainClause:
        force = self._advance()
        action = self._expect(TokenKind.IDENTIFIER, "expected action identifier")
        focus: TargetReference | ContextReference | None = None
        if self._current().kind is TokenKind.AT:
            focus = self._parse_target()
        elif self._current().kind is TokenKind.CONTEXT:
            focus = self._parse_context_ref()

        relation_tail: RelationTail | None = None
        if self._current().kind in {TokenKind.EQUAL, TokenKind.COLON}:
            separator = self._advance()
            relation_tail = RelationTail(
                separator.value,
                self._parse_expression(),
                self._span(separator),
            )

        operation: Expression | None = None
        if self._match(TokenKind.DOUBLE_COLON):
            operation = self._parse_expression()

        constraints: list[ConstraintBlock] = []
        evidence: list[EvidenceClause] = []
        while True:
            if self._current().kind is TokenKind.LBRACE:
                constraints.append(self._parse_constraints())
            elif (
                self._current().kind is TokenKind.IDENTIFIER
                and self._current().value in {"because", "assume", "challenge"}
            ):
                evidence.append(self._parse_evidence())
            else:
                break

        output = self._parse_output() if self._current().kind is TokenKind.ARROW else None
        confidence = (
            self._parse_confidence()
            if self._current().kind is TokenKind.PERCENT
            else None
        )
        metadata = (
            self._parse_metadata()
            if self._current().kind is TokenKind.SEMICOLON
            else None
        )
        if self._current().kind not in {TokenKind.NEWLINE, TokenKind.EOF}:
            raise self._error(
                "unexpected_clause_suffix", "unexpected token after main clause"
            )
        return MainClause(
            force.value,
            action.value,
            focus,
            relation_tail,
            operation,
            tuple(constraints),
            tuple(evidence),
            output,
            confidence,
            metadata,
            self._span(force),
        )

    def _parse_target(self) -> TargetReference:
        start = self._expect(TokenKind.AT, "expected '@'")
        name = self._expect(TokenKind.IDENTIFIER, "expected target identifier")
        scope = self._parse_scope() if self._current().kind is TokenKind.LBRACKET else None
        return TargetReference(name.value, scope, self._span(start))

    def _parse_scope(self) -> ScopeExpression:
        start = self._expect(TokenKind.LBRACKET, "expected '['")
        items: list[ScopeItem] = []
        joiners: list[str] = []
        if self._match(TokenKind.RBRACKET):
            return ScopeExpression((), (), self._span(start))
        items.append(self._parse_scope_item())
        while self._current().kind in {TokenKind.COMMA, TokenKind.PIPE}:
            joiners.append(self._advance().value)
            items.append(self._parse_scope_item())
        self._expect(TokenKind.RBRACKET, "expected ']' after target scope")
        return ScopeExpression(tuple(items), tuple(joiners), self._span(start))

    def _parse_scope_item(self) -> ScopeItem:
        start = self._current()
        if (
            start.kind is TokenKind.IDENTIFIER
            and self._peek().kind in {TokenKind.EQUAL, TokenKind.COLON}
        ):
            key = self._advance().value
            self._advance()
            return ScopeAssignment(key, self._parse_scope_value(), self._span(start))
        left = self._parse_scope_value()
        if self._match(TokenKind.RANGE):
            return ScopeRange(left, self._parse_scope_value(), left.span)
        return left

    def _parse_scope_value(self) -> ScopeValue:
        start = self._current()
        sign = ""
        if start.kind in {TokenKind.PLUS, TokenKind.MINUS}:
            sign = self._advance().value
            start = self._current()
        if start.kind is TokenKind.NUMBER:
            token = self._advance()
            if (
                self._current().kind is TokenKind.IDENTIFIER
                and self._current().value in _PERIOD_UNITS
            ):
                unit = self._advance().value
                return ScopeValue(f"{sign}{token.value}{unit}", self._span(start))
            return ScopeValue(Decimal(f"{sign}{token.value}"), self._span(start))
        if sign:
            raise self._error("signed_scope_value", "scope sign must precede a number", start)
        if start.kind is TokenKind.STRING:
            self._advance()
            return ScopeValue(start.value, self._span(start))
        if start.kind is TokenKind.IDENTIFIER:
            self._advance()
            if start.value == "true":
                return ScopeValue(True, self._span(start))
            if start.value == "false":
                return ScopeValue(False, self._span(start))
            if start.value == "null":
                return ScopeValue(None, self._span(start))
            return ScopeValue(start.value, self._span(start))
        raise self._error("expected_scope_value", "expected scope value", start)

    def _parse_context_ref(self) -> ContextReference:
        start = self._expect(TokenKind.CONTEXT, "expected context reference")
        depth = self._expect(TokenKind.NUMBER, "expected context depth")
        if "." in depth.value:
            raise self._error(
                "context_depth_integer", "context depth must be an integer", depth
            )
        agent = None
        if self._match(TokenKind.AT):
            agent = self._expect(
                TokenKind.IDENTIFIER, "expected agent identifier"
            ).value
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
                raise self._error(
                    "expected_constraint_separator", "expected '=' or ':'"
                )
            self._advance()
            entries.append(
                ConstraintEntry(
                    key.value, sep.value, self._parse_expression(), self._span(key)
                )
            )
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
        zoom: int | str | None = None
        if self._match(TokenKind.AT):
            marker = self._expect(TokenKind.IDENTIFIER, "expected zoom marker")
            if marker.value == "zmax":
                zoom = "max"
            elif marker.value.startswith("z") and marker.value[1:].isdigit():
                value = int(marker.value[1:])
                if not 0 <= value <= 5:
                    raise self._error("zoom_range", "zoom must be z0..z5 or zmax", marker)
                zoom = value
            else:
                raise self._error("invalid_zoom", "expected z0..z5 or zmax", marker)
        return OutputClause(token.value, zoom, self._span(start))

    def _parse_confidence(self) -> Decimal:
        self._expect(TokenKind.PERCENT, "expected '%'")
        token = self._expect(TokenKind.NUMBER, "expected confidence number")
        value = Decimal(token.value)
        if not Decimal("0") <= value <= Decimal("1"):
            raise self._error(
                "confidence_range", "confidence must be between 0 and 1", token
            )
        return value

    def _parse_metadata(self) -> MetadataClause:
        start = self._expect(TokenKind.SEMICOLON, "expected ';'")
        refs: list[ContextReference] = []
        items: list[MetadataItem] = []
        while True:
            if (
                self._current().kind is TokenKind.IDENTIFIER
                and self._current().value == "ctx"
                and self._peek().kind is TokenKind.CONTEXT
            ):
                self._advance()
                refs.append(self._parse_context_ref())
            else:
                key = self._expect(TokenKind.IDENTIFIER, "expected metadata key")
                sep = self._current()
                if sep.kind not in {TokenKind.EQUAL, TokenKind.COLON}:
                    raise self._error(
                        "expected_metadata_separator", "expected '=' or ':'"
                    )
                self._advance()
                items.append(
                    MetadataItem(
                        key.value,
                        sep.value,
                        self._parse_expression(),
                        self._span(key),
                    )
                )
            if not self._match(TokenKind.COMMA):
                break
        return MetadataClause(tuple(refs), tuple(items), self._span(start))

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

    def _parse_claim(self) -> ClaimClause:
        start = self._expect(TokenKind.IDENTIFIER, "expected claim")
        self._expect(TokenKind.COLON, "expected ':' after claim")
        return ClaimClause(self._parse_expression(), self._span(start))

    def _parse_ambiguity(self) -> AmbiguityClause:
        start = self._expect(TokenKind.IDENTIFIER, "expected ambig")
        self._expect(TokenKind.LBRACE, "expected '{' after ambig")
        key_token = self._current()
        if key_token.kind not in {TokenKind.IDENTIFIER, TokenKind.STRING}:
            raise self._error("ambiguity_key", "expected ambiguity key", key_token)
        self._advance()
        self._expect(TokenKind.COLON, "expected ':' after ambiguity key")
        alternatives = [self._parse_primary()]
        while self._match(TokenKind.PIPE):
            alternatives.append(self._parse_primary())
        self._expect(TokenKind.RBRACE, "expected '}' after ambiguity alternatives")
        return AmbiguityClause(
            key_token.value, tuple(alternatives), self._span(start)
        )

    def _parse_context_command(self) -> ContextCommand:
        token = self._expect(TokenKind.IDENTIFIER, "expected context command")
        action = token.value.split(".", 1)[1]
        block = None
        if action == "push":
            block = self._parse_constraints()
        return ContextCommand(action, block, self._span(token))

    def _parse_macro_definition(self) -> MacroDefinition:
        start = self._expect(TokenKind.IDENTIFIER, "expected def")
        self._expect(TokenKind.HASH, "expected macro name")
        name = self._expect(TokenKind.IDENTIFIER, "expected macro identifier")
        self._expect(TokenKind.EQUAL, "expected '=' in macro definition")
        self._expect(TokenKind.LBRACE, "expected '{' in macro definition")
        body = None if self._current().kind is TokenKind.RBRACE else self._parse_expression()
        self._expect(TokenKind.RBRACE, "expected '}' in macro definition")
        return MacroDefinition(name.value, body, self._span(start))

    def _parse_expression(self) -> Expression:
        if (
            self._current().kind is TokenKind.IDENTIFIER
            and self._peek().kind is TokenKind.COLON
        ):
            label = self._advance()
            self._advance()
            return AnnotationExpression(
                label.value, self._parse_alternative(), self._span(label)
            )
        return self._parse_alternative()

    def _parse_alternative(self) -> Expression:
        first = self._parse_composition()
        items = [first]
        while self._match(TokenKind.PIPE):
            items.append(self._parse_composition())
        if len(items) == 1:
            return first
        return AlternativeExpression(tuple(items), first.span)

    def _parse_composition(self) -> Expression:
        first = self._parse_unary()
        items = [first]
        while self._match(TokenKind.PLUS):
            items.append(self._parse_unary())
        if len(items) == 1:
            return first
        return CompositionExpression(tuple(items), first.span)

    def _parse_unary(self) -> Expression:
        minus = self._match(TokenKind.MINUS)
        operand = self._parse_postfix()
        if minus is not None:
            return UnaryExpression("-", operand, self._span(minus))
        return operand

    def _parse_postfix(self) -> Expression:
        expression = self._parse_primary()
        if self._match(TokenKind.TILDE):
            return ApproximationExpression(expression, expression.span)
        return expression

    def _parse_primary(self) -> Expression:
        token = self._current()
        if token.kind is TokenKind.IDENTIFIER:
            self._advance()
            if token.value == "true":
                return BooleanLiteral(True, self._span(token))
            if token.value == "false":
                return BooleanLiteral(False, self._span(token))
            if token.value == "null":
                return NullLiteral(self._span(token))
            if self._match(TokenKind.LPAREN):
                args: list[Expression] = []
                if self._current().kind is not TokenKind.RPAREN:
                    args.append(self._parse_expression())
                    while self._match(TokenKind.COMMA):
                        args.append(self._parse_expression())
                self._expect(TokenKind.RPAREN, "expected ')'")
                return CallExpression(token.value, tuple(args), self._span(token))
            return Identifier(token.value, self._span(token))
        if token.kind is TokenKind.STRING:
            self._advance()
            return StringLiteral(token.value, self._span(token))
        if token.kind is TokenKind.NUMBER:
            self._advance()
            return NumberLiteral(Decimal(token.value), self._span(token))
        if token.kind is TokenKind.LBRACKET:
            start = self._advance()
            items: list[Expression] = []
            if self._current().kind is not TokenKind.RBRACKET:
                items.append(self._parse_expression())
                while self._match(TokenKind.COMMA):
                    items.append(self._parse_expression())
            self._expect(TokenKind.RBRACKET, "expected ']'")
            return ListExpression(tuple(items), self._span(start))
        if token.kind is TokenKind.LPAREN:
            self._advance()
            value = self._parse_expression()
            self._expect(TokenKind.RPAREN, "expected ')'")
            return value
        if token.kind is TokenKind.HASH:
            start = self._advance()
            name = self._expect(TokenKind.IDENTIFIER, "expected macro identifier")
            return MacroReference(name.value, self._span(start))
        if token.kind is TokenKind.AT:
            return self._parse_target()
        if token.kind is TokenKind.CONTEXT:
            return self._parse_context_ref()
        raise self._error("expected_expression", "expected Lattice expression")


def parse(source: str) -> Document:
    return Parser(tokenize(source)).parse_document()
