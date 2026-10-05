"""Deterministic strict-subset Lattice -> canonical LSTP v0.1 compiler."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from lstp.errors import CompilationError, Diagnostic
from lstp.models import (
    EVIDENCE_SOURCE_TYPES, OUTPUT_FORMATS, Atom, Context,
    ContextReference as CanonicalContextReference, EvidenceItem, Octad, Output,
    PacketEnvelope, Permissions, Pragmatics, Relation, Resource,
)
from lstp.packet.validator import CORE_RELATIONS, require_semantic_validity
from lstp.text.ast import (
    CallExpression, ConfidenceTopLevel, ConstraintBlock, ConstraintTopLevel,
    ContextReference, Document, EvidenceClause, EvidenceTopLevel, Expression,
    Identifier, ListExpression, MainClause, MetadataClause, NumberLiteral,
    OutputClause, OutputTopLevel, StringLiteral, TargetReference,
    BooleanLiteral, NullLiteral,
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

    def _error(self, code: str, message: str, expression: Expression | None = None) -> CompilationError:
        line = expression.span.line if expression is not None else None
        column = expression.span.column if expression is not None else None
        return CompilationError(Diagnostic(code, message, line, column))

    def _next_atom(self) -> str: return f"a{len(self.atoms)}"
    def _next_relation(self) -> str: return f"r{len(self.relations)}"
    def _next_evidence(self) -> str: return f"e{len(self.evidence)}"

    def _literal(self, expression: Expression) -> object:
        if isinstance(expression, Identifier): return expression.value
        if isinstance(expression, StringLiteral): return expression.value
        if isinstance(expression, NumberLiteral): return expression.value
        if isinstance(expression, BooleanLiteral): return expression.value
        if isinstance(expression, NullLiteral): return None
        if isinstance(expression, ListExpression): return [self._literal(x) for x in expression.items]
        raise self._error("expected_literal", "expected scalar or list literal", expression)

    def _string_list(self, expression: Expression, name: str) -> list[str]:
        value = self._literal(expression)
        values = value if isinstance(value, list) else [value]
        if not all(isinstance(x, str) for x in values):
            raise self._error("constraint_type", f"{name} must contain strings or identifiers", expression)
        return [str(x) for x in values]

    def _boolean(self, expression: Expression, name: str) -> bool:
        value = self._literal(expression)
        if not isinstance(value, bool):
            raise self._error("constraint_type", f"{name} must be true or false", expression)
        return value

    def _materialize_target(self, target: TargetReference) -> str:
        atom_id = self._next_atom()
        self.atoms.append(Atom(atom_id, "resource", value=target.name))
        return atom_id

    def _materialize_scalar(self, expression: Expression) -> str:
        if isinstance(expression, TargetReference):
            return self._materialize_target(expression)
        value = self._literal(expression)
        kind = "concept" if isinstance(expression, Identifier) else "value"
        atom_id = self._next_atom()
        self.atoms.append(Atom(atom_id, kind, value=value))
        return atom_id

    def _compile_call(self, call: CallExpression, focus: str | None) -> None:
        if call.name not in CORE_RELATIONS and "." not in call.name:
            raise self._error("unnamespaced_relation", "operation must use a core or namespaced relation", call)
        args: list[str] = []
        if focus is not None:
            args.append(focus)
        args.extend(self._materialize_scalar(x) for x in call.arguments)
        if not args:
            raise self._error("relation_requires_argument", "relation requires at least one argument", call)
        self.relations.append(Relation(call.name, tuple(args), id=self._next_relation()))

    def _compile_constraints(self, block: ConstraintBlock) -> None:
        for entry in block.entries:
            if entry.separator != "=":
                raise self._error("annotation_constraint_unsupported", "':' constraint annotations have no canonical mapping", entry.value)
            key = entry.key
            if key == "capabilities": self.capabilities.extend(self._string_list(entry.value, key))
            elif key == "resources": self.resources.extend(Resource(x) for x in self._string_list(entry.value, key))
            elif key == "forbid": self.forbid.extend(self._string_list(entry.value, key))
            elif key == "profile":
                value = self._literal(entry.value)
                if not isinstance(value, str): raise self._error("constraint_type", "profile must be a string", entry.value)
                if self.profile is not None and self.profile != value: raise self._error("duplicate_profile", "conflicting permission profiles", entry.value)
                self.profile = value
            elif key in {"confirm", "require_confirmation"}: self.confirm = self._boolean(entry.value, key)
            elif key in {"review", "require_review"}: self.review = self._boolean(entry.value, key)
            elif key in {"log", "require_logging"}: self.logging = self._boolean(entry.value, key)
            elif key == "urgency":
                value = self._literal(entry.value)
                if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)): raise self._error("constraint_type", "urgency must be numeric", entry.value)
                self.urgency = float(value)
            elif key == "register":
                value = self._literal(entry.value)
                if not isinstance(value, str): raise self._error("constraint_type", "register must be a string", entry.value)
                self.register = value
            elif key == "mode":
                raise self._error("legacy_permission_mode", "legacy 'mode' is not canonical; use capabilities/profile", entry.value)
            else:
                raise self._error("unknown_constraint", f"constraint {key!r} has no canonical v0.1 mapping", entry.value)

    def _resolve_context(self, reference: ContextReference) -> None:
        if self.options.context_resolver is None:
            raise self._error("unresolved_context", "relative context reference requires a context_resolver", reference)
        packet_id = self.options.context_resolver(reference.depth, reference.agent)
        if not packet_id:
            raise self._error("unresolved_context", "context reference could not be resolved", reference)
        self.context_refs.append(CanonicalContextReference(packet_id, reference.depth, reference.agent))

    def _compile_evidence(self, clause: EvidenceClause) -> None:
        if clause.keyword != "because":
            raise self._error("unsupported_evidence_clause", "only because[...] maps to canonical evidence in v0.1")
        for item in clause.items:
            if not isinstance(item, CallExpression):
                raise self._error("evidence_constructor_required", "evidence requires provenance constructors such as user(...) or tool(...)", item)
            if item.name not in EVIDENCE_SOURCE_TYPES:
                raise self._error("unknown_evidence_source", f"unknown evidence source {item.name!r}", item)
            if len(item.arguments) > 1:
                raise self._error("evidence_constructor_arity", "evidence constructor accepts at most one source reference", item)
            source_ref = None
            if item.arguments:
                value = self._literal(item.arguments[0])
                if not isinstance(value, str): raise self._error("evidence_source_ref_type", "evidence source reference must be a string", item)
                source_ref = value
            self.evidence.append(EvidenceItem(self._next_evidence(), item.name, source_ref=source_ref))

    def _compile_output(self, clause: OutputClause) -> None:
        if clause.format not in OUTPUT_FORMATS:
            raise self._error("unknown_output_format", f"output format {clause.format!r} is not canonical")
        candidate = Output(clause.format)
        if self.output is not None and self.output != candidate:
            raise self._error("duplicate_output", "conflicting output clauses")
        self.output = candidate

    def compile(self, document: Document) -> PacketEnvelope:
        mains = [x for x in document.clauses if isinstance(x, MainClause)]
        if len(mains) != 1:
            raise self._error("main_clause_cardinality", "compiler requires exactly one main clause")
        main = mains[0]
        act = {"!": "request", "!!": "request", "?": "question", ".": "inform"}[main.force]
        modifiers = ("urgent",) if main.force == "!!" else ()
        focus: str | None = None
        if isinstance(main.focus, TargetReference): focus = self._materialize_target(main.focus)
        elif isinstance(main.focus, ContextReference): self._resolve_context(main.focus)
        if main.operation is not None:
            if not isinstance(main.operation, CallExpression):
                raise self._error("unsupported_operation", "compiler currently maps operation calls only", main.operation)
            self._compile_call(main.operation, focus)
        for block in main.constraints: self._compile_constraints(block)
        for evidence in main.evidence: self._compile_evidence(evidence)
        if main.output is not None: self._compile_output(main.output)
        if main.confidence is not None: self.confidence = float(main.confidence)
        if main.metadata is not None:
            for ref in main.metadata.context_refs: self._resolve_context(ref)
        for clause in document.clauses:
            if isinstance(clause, ConstraintTopLevel): self._compile_constraints(clause.block)
            elif isinstance(clause, OutputTopLevel): self._compile_output(clause.output)
            elif isinstance(clause, ConfidenceTopLevel):
                value = float(clause.confidence)
                if self.confidence is not None and self.confidence != value: raise self._error("duplicate_confidence", "conflicting confidence clauses")
                self.confidence = value
            elif isinstance(clause, EvidenceTopLevel): self._compile_evidence(clause.evidence)
            elif isinstance(clause, MetadataClause):
                for ref in clause.context_refs: self._resolve_context(ref)
        packet = PacketEnvelope(
            Octad(
                Pragmatics(act, goal=main.action, modifiers=modifiers, register=self.register, urgency=self.urgency),
                tuple(self.atoms), tuple(self.relations),
                Context(self.options.thread_id, references=tuple(self.context_refs)),
                self.options.default_confidence if self.confidence is None else self.confidence,
                Permissions(tuple(self.capabilities), tuple(self.resources), self.profile, tuple(self.forbid), self.confirm, self.review, self.logging),
                tuple(self.evidence), self.output or Output(self.options.default_output),
            ),
            self.options.packet_id, "0.1", carrier={"source": "lattice_text"}, audit={},
        )
        return require_semantic_validity(packet)


def compile_document(document: Document, *, options: CompilerOptions) -> PacketEnvelope:
    return _Compiler(options).compile(document)


def compile_lattice(source: str, *, options: CompilerOptions) -> PacketEnvelope:
    return compile_document(parse(source), options=options)
