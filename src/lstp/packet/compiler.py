"""Deterministic Lattice -> canonical LSTP v0.1 compiler."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from lstp.errors import CompilationError, Diagnostic
from lstp.models import (
    EVIDENCE_SOURCE_TYPES,
    OUTPUT_FORMATS,
    Atom,
    Context,
    ContextReference as CanonicalContextReference,
    EvidenceItem,
    Octad,
    Output,
    PacketEnvelope,
    Permissions,
    Pragmatics,
    Relation,
    Resource,
)
from lstp.packet.validator import CORE_RELATIONS, require_semantic_validity
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
    NullLiteral,
    NumberLiteral,
    OutputClause,
    OutputTopLevel,
    ScopeAssignment,
    ScopeExpression,
    ScopeRange,
    ScopeValue,
    StringLiteral,
    TargetReference,
    UnaryExpression,
)
from lstp.text.parser import parse

ContextResolver = Callable[[int, str | None], str | None]


@dataclass(frozen=True, slots=True)
class CompilerOptions:
    packet_id: str
    thread_id: str
    default_confidence: float = 1.0
    default_output: str = "NL"
    context_resolver: ContextResolver | None = None


class _Compiler:
    def __init__(self, options: CompilerOptions) -> None:
        self.options = options
        self.atoms: list[Atom] = []
        self.relations: list[Relation] = []
        self.evidence: list[EvidenceItem] = []
        self.context_refs: list[CanonicalContextReference] = []
        self.capabilities: list[str] = []
        self.resources: list[Resource] = []
        self.forbid: list[str] = []
        self.profile: str | None = None
        self.confirm = False
        self.review = False
        self.logging = False
        self.urgency: float | None = None
        self.register: str | None = None
        self.output: Output | None = None
        self.confidence: float | None = None
        self.audit_metadata: dict[str, object] = {}
        self.macros: dict[str, Expression] = {}
        self._macro_stack: list[str] = []

    def _error(
        self, code: str, message: str, expression: Expression | None = None
    ) -> CompilationError:
        line = expression.span.line if expression is not None else None
        column = expression.span.column if expression is not None else None
        return CompilationError(Diagnostic(code, message, line, column))

    def _next_atom(self) -> str:
        return f"a{len(self.atoms)}"

    def _next_relation(self) -> str:
        return f"r{len(self.relations)}"

    def _next_evidence(self) -> str:
        return f"e{len(self.evidence)}"

    def _expand(self, expression: Expression) -> Expression:
        if isinstance(expression, MacroReference):
            body = self.macros.get(expression.name)
            if body is None:
                raise self._error(
                    "unresolved_macro", f"macro {expression.name!r} is not defined", expression
                )
            if expression.name in self._macro_stack:
                raise self._error(
                    "recursive_macro", f"recursive macro {expression.name!r}", expression
                )
            self._macro_stack.append(expression.name)
            try:
                return self._expand(body)
            finally:
                self._macro_stack.pop()
        if isinstance(expression, CallExpression):
            return CallExpression(
                expression.name,
                tuple(self._expand(item) for item in expression.arguments),
                expression.span,
            )
        if isinstance(expression, ListExpression):
            return ListExpression(
                tuple(self._expand(item) for item in expression.items), expression.span
            )
        if isinstance(expression, UnaryExpression):
            return UnaryExpression(
                expression.operator, self._expand(expression.operand), expression.span
            )
        if isinstance(expression, ApproximationExpression):
            return ApproximationExpression(self._expand(expression.operand), expression.span)
        if isinstance(expression, CompositionExpression):
            return CompositionExpression(
                tuple(self._expand(item) for item in expression.items), expression.span
            )
        if isinstance(expression, AlternativeExpression):
            return AlternativeExpression(
                tuple(self._expand(item) for item in expression.items), expression.span
            )
        if isinstance(expression, AnnotationExpression):
            return AnnotationExpression(
                expression.label, self._expand(expression.value), expression.span
            )
        return expression

    def _literal(self, expression: Expression) -> object:
        expression = self._expand(expression)
        if isinstance(expression, Identifier):
            return expression.value
        if isinstance(expression, StringLiteral):
            return expression.value
        if isinstance(expression, NumberLiteral):
            return expression.value
        if isinstance(expression, BooleanLiteral):
            return expression.value
        if isinstance(expression, NullLiteral):
            return None
        if isinstance(expression, ListExpression):
            return [self._literal(item) for item in expression.items]
        raise self._error("expected_literal", "expected scalar or list literal", expression)

    def _string_list(self, expression: Expression, name: str) -> list[str]:
        value = self._literal(expression)
        values = value if isinstance(value, list) else [value]
        if not all(isinstance(item, str) for item in values):
            raise self._error(
                "constraint_type", f"{name} must contain strings or identifiers", expression
            )
        return [str(item) for item in values]

    def _boolean(self, expression: Expression, name: str) -> bool:
        value = self._literal(expression)
        if not isinstance(value, bool):
            raise self._error(
                "constraint_type", f"{name} must be true or false", expression
            )
        return value

    @staticmethod
    def _scope_value(value: ScopeValue) -> object:
        return value.value

    def _scope_attributes(self, scope: ScopeExpression | None) -> dict[str, object]:
        if scope is None:
            return {}
        items: list[object] = []
        for item in scope.items:
            if isinstance(item, ScopeValue):
                items.append({"value": self._scope_value(item)})
            elif isinstance(item, ScopeAssignment):
                items.append({"key": item.key, "value": self._scope_value(item.value)})
            elif isinstance(item, ScopeRange):
                items.append(
                    {
                        "range": [
                            self._scope_value(item.start),
                            self._scope_value(item.end),
                        ]
                    }
                )
        return {"lstp_scope": {"items": items, "joiners": list(scope.joiners)}}

    def _materialize_target(self, target: TargetReference) -> str:
        atom_id = self._next_atom()
        self.atoms.append(
            Atom(
                atom_id,
                "resource",
                value=target.name,
                attributes=self._scope_attributes(target.scope),
            )
        )
        return atom_id

    def _add_value_atom(self, value: object, *, kind: str = "value") -> str:
        atom_id = self._next_atom()
        self.atoms.append(Atom(atom_id, kind, value=value))
        return atom_id

    def _add_relation(
        self,
        relation_type: str,
        arguments: list[str],
        *,
        attributes: dict[str, object] | None = None,
    ) -> str:
        relation_id = self._next_relation()
        self.relations.append(
            Relation(
                relation_type,
                tuple(arguments),
                id=relation_id,
                attributes=attributes or {},
            )
        )
        return relation_id

    def _relation_result_atom(self, relation_id: str) -> str:
        return self._add_value_atom({"relation": relation_id}, kind="proposition")

    def _materialize_expression(self, expression: Expression) -> str:
        expression = self._expand(expression)
        if isinstance(expression, TargetReference):
            return self._materialize_target(expression)
        if isinstance(expression, ContextReference):
            self._resolve_context(expression)
            return self._add_value_atom(
                {"context_packet": self.context_refs[-1].packet_id}, kind="resource"
            )
        if isinstance(
            expression,
            (Identifier, StringLiteral, NumberLiteral, BooleanLiteral, NullLiteral),
        ):
            value = self._literal(expression)
            kind = "concept" if isinstance(expression, Identifier) else "value"
            return self._add_value_atom(value, kind=kind)
        if isinstance(expression, ListExpression):
            refs = [self._materialize_expression(item) for item in expression.items]
            relation_id = self._add_relation("lstp.list", refs)
            return self._relation_result_atom(relation_id)
        if isinstance(expression, CallExpression):
            if expression.name not in CORE_RELATIONS and "." not in expression.name:
                raise self._error(
                    "unnamespaced_relation",
                    "operation must use a core or namespaced relation",
                    expression,
                )
            refs = [self._materialize_expression(item) for item in expression.arguments]
            if not refs:
                raise self._error(
                    "relation_requires_argument",
                    "relation requires at least one argument",
                    expression,
                )
            relation_id = self._add_relation(expression.name, refs)
            return self._relation_result_atom(relation_id)
        if isinstance(expression, CompositionExpression):
            refs = [self._materialize_expression(item) for item in expression.items]
            return self._relation_result_atom(self._add_relation("lstp.compose", refs))
        if isinstance(expression, AlternativeExpression):
            refs = [self._materialize_expression(item) for item in expression.items]
            return self._relation_result_atom(self._add_relation("lstp.alternative", refs))
        if isinstance(expression, UnaryExpression):
            ref = self._materialize_expression(expression.operand)
            return self._relation_result_atom(self._add_relation("lstp.exclude", [ref]))
        if isinstance(expression, ApproximationExpression):
            ref = self._materialize_expression(expression.operand)
            return self._relation_result_atom(
                self._add_relation("lstp.approximate", [ref])
            )
        if isinstance(expression, AnnotationExpression):
            label = self._add_value_atom(expression.label, kind="concept")
            value = self._materialize_expression(expression.value)
            return self._relation_result_atom(
                self._add_relation("lstp.annotation", [label, value])
            )
        raise self._error("unsupported_expression", "expression has no canonical mapping", expression)

    def _compile_operation(self, expression: Expression, focus: str | None) -> None:
        expression = self._expand(expression)
        if isinstance(expression, CallExpression):
            if expression.name not in CORE_RELATIONS and "." not in expression.name:
                raise self._error(
                    "unnamespaced_relation",
                    "operation must use a core or namespaced relation",
                    expression,
                )
            args: list[str] = []
            if focus is not None:
                args.append(focus)
            args.extend(self._materialize_expression(item) for item in expression.arguments)
            if not args:
                raise self._error(
                    "relation_requires_argument",
                    "relation requires at least one argument",
                    expression,
                )
            self._add_relation(expression.name, args)
            return
        ref = self._materialize_expression(expression)
        args = ([focus] if focus is not None else []) + [ref]
        self._add_relation("lstp.operation", args)

    def _compile_constraints(self, block: ConstraintBlock) -> None:
        for entry in block.entries:
            key = entry.key
            if entry.separator == ":":
                label = self._add_value_atom(key, kind="concept")
                value = self._materialize_expression(entry.value)
                self._add_relation("lstp.constraint_annotation", [label, value])
                continue
            if key == "capabilities":
                self.capabilities.extend(self._string_list(entry.value, key))
            elif key == "resources":
                self.resources.extend(
                    Resource(item) for item in self._string_list(entry.value, key)
                )
            elif key == "forbid":
                self.forbid.extend(self._string_list(entry.value, key))
            elif key == "profile":
                value = self._literal(entry.value)
                if not isinstance(value, str):
                    raise self._error(
                        "constraint_type", "profile must be a string", entry.value
                    )
                if self.profile is not None and self.profile != value:
                    raise self._error(
                        "duplicate_profile", "conflicting permission profiles", entry.value
                    )
                self.profile = value
            elif key in {"confirm", "require_confirmation"}:
                self.confirm = self._boolean(entry.value, key)
            elif key in {"review", "require_review"}:
                self.review = self._boolean(entry.value, key)
            elif key in {"log", "require_logging"}:
                self.logging = self._boolean(entry.value, key)
            elif key == "urgency":
                value = self._literal(entry.value)
                if isinstance(value, bool) or not isinstance(
                    value, (int, float, Decimal)
                ):
                    raise self._error(
                        "constraint_type", "urgency must be numeric", entry.value
                    )
                self.urgency = float(value)
            elif key == "register":
                value = self._literal(entry.value)
                if not isinstance(value, str):
                    raise self._error(
                        "constraint_type", "register must be a string", entry.value
                    )
                self.register = value
            elif key == "mode":
                raise self._error(
                    "legacy_permission_mode",
                    "legacy 'mode' is not canonical; use capabilities/profile",
                    entry.value,
                )
            else:
                raise self._error(
                    "unknown_constraint",
                    f"constraint {key!r} has no canonical v0.1 mapping",
                    entry.value,
                )

    def _resolve_context(self, reference: ContextReference) -> None:
        if self.options.context_resolver is None:
            raise self._error(
                "unresolved_context",
                "relative context reference requires a context_resolver",
                reference,
            )
        packet_id = self.options.context_resolver(reference.depth, reference.agent)
        if not packet_id:
            raise self._error(
                "unresolved_context", "context reference could not be resolved", reference
            )
        self.context_refs.append(
            CanonicalContextReference(packet_id, reference.depth, reference.agent)
        )

    def _expression_summary(self, expression: Expression) -> str:
        expression = self._expand(expression)
        if isinstance(expression, Identifier):
            return expression.value
        if isinstance(expression, StringLiteral):
            return expression.value
        if isinstance(expression, NumberLiteral):
            return str(expression.value)
        if isinstance(expression, BooleanLiteral):
            return "true" if expression.value else "false"
        if isinstance(expression, NullLiteral):
            return "null"
        if isinstance(expression, CallExpression):
            return f"{expression.name}(...)"
        return type(expression).__name__

    def _compile_evidence(self, clause: EvidenceClause) -> None:
        if clause.keyword == "because":
            for item in clause.items:
                item = self._expand(item)
                if not isinstance(item, CallExpression):
                    raise self._error(
                        "evidence_constructor_required",
                        "evidence requires provenance constructors such as user(...) or tool(...)",
                        item,
                    )
                if item.name not in EVIDENCE_SOURCE_TYPES:
                    raise self._error(
                        "unknown_evidence_source",
                        f"unknown evidence source {item.name!r}",
                        item,
                    )
                if len(item.arguments) > 1:
                    raise self._error(
                        "evidence_constructor_arity",
                        "evidence constructor accepts at most one source reference",
                        item,
                    )
                source_ref = None
                if item.arguments:
                    value = self._literal(item.arguments[0])
                    if not isinstance(value, str):
                        raise self._error(
                            "evidence_source_ref_type",
                            "evidence source reference must be a string",
                            item,
                        )
                    source_ref = value
                self.evidence.append(
                    EvidenceItem(self._next_evidence(), item.name, source_ref=source_ref)
                )
            return
        role = "assumption" if clause.keyword == "assume" else "challenge"
        for item in clause.items:
            self.evidence.append(
                EvidenceItem(
                    self._next_evidence(),
                    "inferred",
                    description=self._expression_summary(item),
                    extensions={"lstp": {"role": role}},
                )
            )

    def _compile_output(self, clause: OutputClause) -> None:
        if clause.format not in OUTPUT_FORMATS:
            raise self._error(
                "unknown_output_format",
                f"output format {clause.format!r} is not canonical",
            )
        extensions = {} if clause.zoom is None else {"lstp": {"zoom": clause.zoom}}
        candidate = Output(clause.format, extensions=extensions)
        if self.output is not None and self.output != candidate:
            raise self._error("duplicate_output", "conflicting output clauses")
        self.output = candidate

    def _compile_metadata(self, clause: MetadataClause) -> None:
        for reference in clause.context_refs:
            self._resolve_context(reference)
        for item in clause.items:
            if item.separator != "=":
                raise self._error(
                    "metadata_annotation_unsupported",
                    "metadata ':' annotations are not envelope assignments",
                    item.value,
                )
            value = self._literal(item.value)
            if item.key in self.audit_metadata and self.audit_metadata[item.key] != value:
                raise self._error(
                    "duplicate_metadata", f"conflicting metadata key {item.key!r}", item.value
                )
            self.audit_metadata[item.key] = value

    def _register_macros(self, document: Document) -> None:
        for clause in document.clauses:
            if isinstance(clause, MacroDefinition):
                if clause.body is None:
                    raise self._error(
                        "empty_macro", f"macro {clause.name!r} has no expression body"
                    )
                if clause.name in self.macros:
                    raise self._error(
                        "duplicate_macro", f"macro {clause.name!r} is defined more than once"
                    )
                self.macros[clause.name] = clause.body

    def compile(self, document: Document) -> PacketEnvelope:
        self._register_macros(document)
        mains = [item for item in document.clauses if isinstance(item, MainClause)]
        if len(mains) != 1:
            raise self._error(
                "main_clause_cardinality", "compiler requires exactly one main clause"
            )
        main = mains[0]
        act = {
            "!": "request",
            "!!": "request",
            "?": "question",
            ".": "inform",
        }[main.force]
        modifiers = ("urgent",) if main.force == "!!" else ()

        focus: str | None = None
        if isinstance(main.focus, TargetReference):
            focus = self._materialize_target(main.focus)
        elif isinstance(main.focus, ContextReference):
            self._resolve_context(main.focus)

        if main.relation_tail is not None:
            if focus is None:
                raise self._error(
                    "relation_tail_focus",
                    "relation tail requires a target focus",
                    main.relation_tail.value,
                )
            value = self._materialize_expression(main.relation_tail.value)
            relation_type = "is" if main.relation_tail.separator == "=" else "lstp.annotation"
            self._add_relation(relation_type, [focus, value])

        if main.operation is not None:
            self._compile_operation(main.operation, focus)
        for block in main.constraints:
            self._compile_constraints(block)
        for evidence in main.evidence:
            self._compile_evidence(evidence)
        if main.output is not None:
            self._compile_output(main.output)
        if main.confidence is not None:
            self.confidence = float(main.confidence)
        if main.metadata is not None:
            self._compile_metadata(main.metadata)

        for clause in document.clauses:
            if isinstance(clause, ConstraintTopLevel):
                self._compile_constraints(clause.block)
            elif isinstance(clause, OutputTopLevel):
                self._compile_output(clause.output)
            elif isinstance(clause, ConfidenceTopLevel):
                value = float(clause.confidence)
                if self.confidence is not None and self.confidence != value:
                    raise self._error(
                        "duplicate_confidence", "conflicting confidence clauses"
                    )
                self.confidence = value
            elif isinstance(clause, EvidenceTopLevel):
                self._compile_evidence(clause.evidence)
            elif isinstance(clause, MetadataClause):
                self._compile_metadata(clause)
            elif isinstance(clause, ClaimClause):
                ref = self._materialize_expression(clause.value)
                self._add_relation("lstp.claim", [ref])
            elif isinstance(clause, AmbiguityClause):
                key = self._add_value_atom(clause.key, kind="concept")
                alternatives = [
                    self._materialize_expression(item) for item in clause.alternatives
                ]
                self._add_relation("lstp.ambiguity", [key, *alternatives])
            elif isinstance(clause, ContextCommand):
                raise self._error(
                    "runtime_context_command",
                    "ctx.push/ctx.pop are runtime commands and cannot be serialized as canonical packet semantics",
                )
            elif isinstance(clause, MacroDefinition):
                continue

        packet = PacketEnvelope(
            Octad(
                Pragmatics(
                    act,
                    goal=main.action,
                    modifiers=modifiers,
                    register=self.register,
                    urgency=self.urgency,
                ),
                tuple(self.atoms),
                tuple(self.relations),
                Context(self.options.thread_id, references=tuple(self.context_refs)),
                self.options.default_confidence
                if self.confidence is None
                else self.confidence,
                Permissions(
                    tuple(self.capabilities),
                    tuple(self.resources),
                    self.profile,
                    tuple(self.forbid),
                    self.confirm,
                    self.review,
                    self.logging,
                ),
                tuple(self.evidence),
                self.output or Output(self.options.default_output),
            ),
            self.options.packet_id,
            "0.1",
            carrier={"source": "lattice_text"},
            audit=self.audit_metadata,
        )
        return require_semantic_validity(packet)


def compile_document(document: Document, *, options: CompilerOptions) -> PacketEnvelope:
    return _Compiler(options).compile(document)


def compile_lattice(source: str, *, options: CompilerOptions) -> PacketEnvelope:
    return compile_document(parse(source), options=options)
