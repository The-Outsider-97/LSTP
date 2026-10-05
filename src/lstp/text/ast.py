"""AST nodes for strict LSTP v0.1 Lattice text."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class SourceSpan:
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class Identifier:
    value: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class StringLiteral:
    value: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class NumberLiteral:
    value: Decimal
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class BooleanLiteral:
    value: bool
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class NullLiteral:
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ContextReference:
    depth: int
    agent: str | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ScopeValue:
    value: str | Decimal | bool | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ScopeAssignment:
    key: str
    value: ScopeValue
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ScopeRange:
    start: ScopeValue
    end: ScopeValue
    span: SourceSpan


ScopeItem: TypeAlias = ScopeValue | ScopeAssignment | ScopeRange


@dataclass(frozen=True, slots=True)
class ScopeExpression:
    items: tuple[ScopeItem, ...]
    joiners: tuple[str, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class TargetReference:
    name: str
    scope: ScopeExpression | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ListExpression:
    items: tuple["Expression", ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class CallExpression:
    name: str
    arguments: tuple["Expression", ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class MacroReference:
    name: str
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class UnaryExpression:
    operator: str
    operand: "Expression"
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ApproximationExpression:
    operand: "Expression"
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class CompositionExpression:
    items: tuple["Expression", ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class AlternativeExpression:
    items: tuple["Expression", ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class AnnotationExpression:
    label: str
    value: "Expression"
    span: SourceSpan


Expression: TypeAlias = (
    Identifier
    | StringLiteral
    | NumberLiteral
    | BooleanLiteral
    | NullLiteral
    | ContextReference
    | TargetReference
    | ListExpression
    | CallExpression
    | MacroReference
    | UnaryExpression
    | ApproximationExpression
    | CompositionExpression
    | AlternativeExpression
    | AnnotationExpression
)


@dataclass(frozen=True, slots=True)
class RelationTail:
    separator: str
    value: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ConstraintEntry:
    key: str
    separator: str
    value: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ConstraintBlock:
    entries: tuple[ConstraintEntry, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class OutputClause:
    format: str
    zoom: int | str | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class EvidenceClause:
    keyword: str
    items: tuple[Expression, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class MetadataItem:
    key: str
    separator: str
    value: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class MetadataClause:
    context_refs: tuple[ContextReference, ...]
    items: tuple[MetadataItem, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class MainClause:
    force: str
    action: str
    focus: TargetReference | ContextReference | None
    relation_tail: RelationTail | None
    operation: Expression | None
    constraints: tuple[ConstraintBlock, ...]
    evidence: tuple[EvidenceClause, ...]
    output: OutputClause | None
    confidence: Decimal | None
    metadata: MetadataClause | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ConstraintTopLevel:
    block: ConstraintBlock
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class OutputTopLevel:
    output: OutputClause
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ConfidenceTopLevel:
    confidence: Decimal
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class EvidenceTopLevel:
    evidence: EvidenceClause
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ClaimClause:
    value: Expression
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class AmbiguityClause:
    key: str
    alternatives: tuple[Expression, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class ContextCommand:
    action: str
    block: ConstraintBlock | None
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class MacroDefinition:
    name: str
    body: Expression | None
    span: SourceSpan


TopLevelClause: TypeAlias = (
    MainClause
    | ConstraintTopLevel
    | OutputTopLevel
    | ConfidenceTopLevel
    | EvidenceTopLevel
    | MetadataClause
    | ClaimClause
    | AmbiguityClause
    | ContextCommand
    | MacroDefinition
)


@dataclass(frozen=True, slots=True)
class Document:
    clauses: tuple[TopLevelClause, ...]
