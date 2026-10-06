"""Typed canonical semantic model for LSTP v0.1.

The classes in this module implement the local, field-level invariants of
``spec/CANONICAL-v0.1.md``. Cross-field and referential rules live in
``lstp.packet.validator`` so callers can inspect deterministic diagnostics.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

JSONNumber: TypeAlias = int | float | Decimal
JSONValue: TypeAlias = None | bool | JSONNumber | str | tuple["JSONValue", ...] | Mapping[str, "JSONValue"]

SUPPORTED_PROTOCOL_VERSIONS = frozenset({"0.1"})
ATOM_KINDS = frozenset({"entity", "concept", "value", "event", "time", "location", "resource", "proposition", "unknown"})
SPECIAL_ARGUMENTS = frozenset({"SELF", "NOW", "USER", "SYSTEM"})
PERMISSION_MODES = frozenset({"RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT"})
EVIDENCE_SOURCE_TYPES = frozenset({"user", "sensor", "model", "tool", "retrieved", "inferred"})
OUTPUT_FORMATS = frozenset({"NL", "LATTICE", "JSON", "YAML", "TABLE", "CODE", "FILE", "NONE"})

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_QUALIFIED_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*$")
_ATOM_ID_RE = re.compile(r"^a(?:0|[1-9][0-9]*)$")
_RELATION_ID_RE = re.compile(r"^r(?:0|[1-9][0-9]*)$")
_EVIDENCE_ID_RE = re.compile(r"^e(?:0|[1-9][0-9]*)$")


def _finite_number(value: object, *, path: str) -> JSONNumber:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"expected JSON number at {path}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {path}")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError(f"non-finite number at {path}")
    return value


def _bounded_confidence(value: object, *, path: str) -> float:
    number = _finite_number(value, path=path)
    numeric = float(number)
    if not 0.0 <= numeric <= 1.0:
        raise ValueError(f"value at {path} must be between 0 and 1")
    return numeric


def _identifier(value: object, *, path: str, qualified: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected string identifier at {path}")
    pattern = _QUALIFIED_IDENTIFIER_RE if qualified else _IDENTIFIER_RE
    if not pattern.fullmatch(value):
        raise ValueError(f"invalid identifier at {path}")
    return value


def _non_empty_string(value: object, *, path: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected string at {path}")
    if not value:
        raise ValueError(f"value at {path} must not be empty")
    return value


def _freeze(value: Any, *, path: str = "$") -> JSONValue:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return _finite_number(value, path=path)
    if isinstance(value, Mapping):
        frozen: dict[str, JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non-string object key at {path}: {type(key).__name__}")
            frozen[key] = _freeze(item, path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, path=f"{path}[{index}]") for index, item in enumerate(value))
    raise TypeError(f"unsupported canonical value type at {path}: {type(value).__name__}")


def _freeze_object(value: object, *, path: str) -> Mapping[str, JSONValue]:
    frozen = _freeze(value, path=path)
    if not isinstance(frozen, Mapping):
        raise TypeError(f"expected object at {path}")
    return frozen


def _freeze_extensions(value: object, *, path: str) -> Mapping[str, JSONValue]:
    extensions = _freeze_object(value, path=path)
    for namespace, payload in extensions.items():
        if not namespace or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,127}", namespace):
            raise ValueError(f"invalid extension namespace at {path}")
        if not isinstance(payload, Mapping):
            raise TypeError(f"extension namespace {namespace!r} must contain an object")
    return extensions


def _mapping(value: object, *, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"expected object at {path}")
    for key in value:
        if not isinstance(key, str):
            raise TypeError(f"non-string object key at {path}: {type(key).__name__}")
    return value


def _sequence(value: object, *, path: str) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"expected array at {path}")
    return list(value)


def _reject_unknown_keys(
    data: Mapping[str, Any],
    *,
    allowed: set[str],
    path: str,
) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"unknown field at {path}: {unknown[0]!r}")


def _optional_string(
    data: Mapping[str, Any],
    key: str,
    *,
    path: str,
) -> str | None:
    if key not in data or data[key] is None:
        return None
    return _non_empty_string(data[key], path=f"{path}.{key}")


def _optional_bool(
    data: Mapping[str, Any],
    key: str,
    *,
    path: str,
    default: bool = False,
) -> bool:
    if key not in data:
        return default
    value = data[key]
    if not isinstance(value, bool):
        raise TypeError(f"expected boolean at {path}.{key}")
    return value


def _optional_non_negative_int(
    data: Mapping[str, Any],
    key: str,
    *,
    path: str,
) -> int | None:
    if key not in data or data[key] is None:
        return None
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"expected integer at {path}.{key}")
    if value < 0:
        raise ValueError(f"value at {path}.{key} must be non-negative")
    return value


@dataclass(frozen=True, slots=True)
class Pragmatics:
    type: str
    speech_act: str | None = None
    goal: str | None = None
    modifiers: tuple[str, ...] = ()
    register: str | None = None
    urgency: float | None = None
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.type, path="$.pragmatics.type", qualified=True)
        if self.speech_act is not None:
            _identifier(self.speech_act, path="$.pragmatics.speech_act", qualified=True)
        if self.goal is not None:
            _identifier(self.goal, path="$.pragmatics.goal", qualified=True)
        for index, modifier in enumerate(self.modifiers):
            _identifier(modifier, path=f"$.pragmatics.modifiers[{index}]", qualified=True)
        if len(set(self.modifiers)) != len(self.modifiers):
            raise ValueError("duplicate pragmatics modifier")
        if self.register is not None:
            _identifier(self.register, path="$.pragmatics.register", qualified=True)
        if self.urgency is not None:
            object.__setattr__(
                self,
                "urgency",
                _bounded_confidence(self.urgency, path="$.pragmatics.urgency"),
            )
        object.__setattr__(
            self,
            "extensions",
            _freeze_extensions(self.extensions, path="$.pragmatics.extensions"),
        )

    @classmethod
    def from_mapping(cls, value: object) -> "Pragmatics":
        data = _mapping(value, path="$.pragmatics")
        _reject_unknown_keys(
            data,
            allowed={
                "type",
                "speech_act",
                "goal",
                "modifiers",
                "register",
                "urgency",
                "extensions",
            },
            path="$.pragmatics",
        )
        return cls(
            type=_non_empty_string(data.get("type"), path="$.pragmatics.type"),
            speech_act=_optional_string(
                data,
                "speech_act",
                path="$.pragmatics",
            ),
            goal=_optional_string(data, "goal", path="$.pragmatics"),
            modifiers=tuple(
                _non_empty_string(x, path="$.pragmatics.modifiers[]")
                for x in _sequence(
                    data.get("modifiers", []),
                    path="$.pragmatics.modifiers",
                )
            ),
            register=_optional_string(
                data,
                "register",
                path="$.pragmatics",
            ),
            urgency=(
                None
                if data.get("urgency") is None
                else _bounded_confidence(
                    data["urgency"],
                    path="$.pragmatics.urgency",
                )
            ),
            extensions=_mapping(
                data.get("extensions", {}),
                path="$.pragmatics.extensions",
            ),
        )


@dataclass(frozen=True, slots=True)
class Atom:
    id: str
    kind: str
    value: JSONValue = None
    role: str | None = None
    datatype: str | None = None
    language: str | None = None
    attributes: Mapping[str, JSONValue] = field(default_factory=dict)
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _ATOM_ID_RE.fullmatch(self.id):
            raise ValueError(f"invalid atom id: {self.id!r}")
        if self.kind not in ATOM_KINDS:
            raise ValueError(f"unknown atom kind: {self.kind!r}")
        object.__setattr__(self, "value", _freeze(self.value, path=f"$.atoms[{self.id}].value"))
        if self.role is not None:
            _identifier(self.role, path=f"$.atoms[{self.id}].role", qualified=True)
        object.__setattr__(self, "attributes", _freeze_object(self.attributes, path=f"$.atoms[{self.id}].attributes"))
        object.__setattr__(self, "extensions", _freeze_extensions(self.extensions, path=f"$.atoms[{self.id}].extensions"))

    @classmethod
    def from_mapping(cls, value: object) -> "Atom":
        data = _mapping(value, path="$.atoms[]")
        return cls(
            id=_non_empty_string(data.get("id"), path="$.atoms[].id"),
            kind=_non_empty_string(data.get("kind"), path="$.atoms[].kind"),
            value=data.get("value"),
            role=data.get("role") if isinstance(data.get("role"), str) else None,
            datatype=data.get("datatype") if isinstance(data.get("datatype"), str) else None,
            language=data.get("language") if isinstance(data.get("language"), str) else None,
            attributes=_mapping(data.get("attributes", {}), path="$.atoms[].attributes"),
            extensions=_mapping(data.get("extensions", {}), path="$.atoms[].extensions"),
        )


@dataclass(frozen=True, slots=True)
class Relation:
    type: str
    arguments: tuple[str, ...]
    id: str | None = None
    confidence: float | None = None
    attributes: Mapping[str, JSONValue] = field(default_factory=dict)
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.type, path="$.relations[].type", qualified=True)
        if not self.arguments:
            raise ValueError("relation arguments must not be empty")
        for argument in self.arguments:
            if argument not in SPECIAL_ARGUMENTS and not _ATOM_ID_RE.fullmatch(argument):
                raise ValueError(f"invalid relation argument: {argument!r}")
        if self.id is not None and not _RELATION_ID_RE.fullmatch(self.id):
            raise ValueError(f"invalid relation id: {self.id!r}")
        if self.confidence is not None:
            object.__setattr__(self, "confidence", _bounded_confidence(self.confidence, path="$.relations[].confidence"))
        object.__setattr__(self, "attributes", _freeze_object(self.attributes, path="$.relations[].attributes"))
        object.__setattr__(self, "extensions", _freeze_extensions(self.extensions, path="$.relations[].extensions"))

    @classmethod
    def from_mapping(cls, value: object) -> "Relation":
        data = _mapping(value, path="$.relations[]")
        return cls(
            type=_non_empty_string(data.get("type"), path="$.relations[].type"),
            arguments=tuple(_non_empty_string(x, path="$.relations[].arguments[]") for x in _sequence(data.get("arguments"), path="$.relations[].arguments")),
            id=data.get("id") if isinstance(data.get("id"), str) else None,
            confidence=None if data.get("confidence") is None else _bounded_confidence(data["confidence"], path="$.relations[].confidence"),
            attributes=_mapping(data.get("attributes", {}), path="$.relations[].attributes"),
            extensions=_mapping(data.get("extensions", {}), path="$.relations[].extensions"),
        )


@dataclass(frozen=True, slots=True)
class ContextReference:
    packet_id: str
    depth: int | None = None
    agent: str | None = None
    label: str | None = None
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _non_empty_string(self.packet_id, path="$.context.references[].packet_id")
        if self.depth is not None and (isinstance(self.depth, bool) or self.depth < 0):
            raise ValueError("context reference depth must be a non-negative integer")
        if self.agent is not None:
            _identifier(self.agent, path="$.context.references[].agent")
        object.__setattr__(self, "extensions", _freeze_extensions(self.extensions, path="$.context.references[].extensions"))

    @classmethod
    def from_mapping(cls, value: object) -> "ContextReference":
        data = _mapping(value, path="$.context.references[]")
        depth = data.get("depth")
        if depth is not None and (isinstance(depth, bool) or not isinstance(depth, int)):
            raise TypeError("context reference depth must be an integer")
        return cls(
            packet_id=_non_empty_string(data.get("packet_id"), path="$.context.references[].packet_id"),
            depth=depth,
            agent=data.get("agent") if isinstance(data.get("agent"), str) else None,
            label=data.get("label") if isinstance(data.get("label"), str) else None,
            extensions=_mapping(data.get("extensions", {}), path="$.context.references[].extensions"),
        )


@dataclass(frozen=True, slots=True)
class Context:
    thread_id: str
    references: tuple[ContextReference, ...] = ()
    packet_id: str | None = None
    parent_packet_id: str | None = None
    conversation_id: str | None = None
    turn: int | None = None
    speaker: str | None = None
    audience: tuple[str, ...] = ()
    time: str | None = None
    timezone: str | None = None
    window: JSONValue = None
    location: JSONValue = None
    bindings: Mapping[str, JSONValue] = field(default_factory=dict)
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _non_empty_string(self.thread_id, path="$.context.thread_id")
        for name, value in (
            ("packet_id", self.packet_id),
            ("parent_packet_id", self.parent_packet_id),
            ("conversation_id", self.conversation_id),
            ("timezone", self.timezone),
        ):
            if value is not None:
                _non_empty_string(value, path=f"$.context.{name}")
        if self.turn is not None and (isinstance(self.turn, bool) or self.turn < 0):
            raise ValueError("context turn must be a non-negative integer")
        if self.speaker is not None:
            _identifier(self.speaker, path="$.context.speaker", qualified=True)
        object.__setattr__(self, "window", _freeze(self.window, path="$.context.window"))
        object.__setattr__(self, "location", _freeze(self.location, path="$.context.location"))
        object.__setattr__(
            self,
            "bindings",
            _freeze_object(self.bindings, path="$.context.bindings"),
        )
        object.__setattr__(
            self,
            "extensions",
            _freeze_extensions(self.extensions, path="$.context.extensions"),
        )

    @classmethod
    def from_mapping(cls, value: object) -> "Context":
        data = _mapping(value, path="$.context")
        _reject_unknown_keys(
            data,
            allowed={
                "thread_id",
                "references",
                "packet_id",
                "parent_packet_id",
                "conversation_id",
                "turn",
                "speaker",
                "audience",
                "time",
                "timezone",
                "window",
                "location",
                "bindings",
                "extensions",
            },
            path="$.context",
        )
        return cls(
            thread_id=_non_empty_string(data.get("thread_id"), path="$.context.thread_id"),
            references=tuple(
                ContextReference.from_mapping(x)
                for x in _sequence(
                    data.get("references"),
                    path="$.context.references",
                )
            ),
            packet_id=_optional_string(data, "packet_id", path="$.context"),
            parent_packet_id=_optional_string(
                data,
                "parent_packet_id",
                path="$.context",
            ),
            conversation_id=_optional_string(
                data,
                "conversation_id",
                path="$.context",
            ),
            turn=_optional_non_negative_int(data, "turn", path="$.context"),
            speaker=_optional_string(data, "speaker", path="$.context"),
            audience=tuple(
                _non_empty_string(x, path="$.context.audience[]")
                for x in _sequence(
                    data.get("audience", []),
                    path="$.context.audience",
                )
            ),
            time=_optional_string(data, "time", path="$.context"),
            timezone=_optional_string(data, "timezone", path="$.context"),
            window=data.get("window"),
            location=data.get("location"),
            bindings=_mapping(data.get("bindings", {}), path="$.context.bindings"),
            extensions=_mapping(
                data.get("extensions", {}),
                path="$.context.extensions",
            ),
        )


@dataclass(frozen=True, slots=True)
class Delegation:
    parent_packet: str | None = None
    delegator: str | None = None
    principal: str | None = None
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.delegator is not None:
            _identifier(self.delegator, path="$.permissions.delegation.delegator", qualified=True)
        if self.principal is not None:
            _identifier(self.principal, path="$.permissions.delegation.principal", qualified=True)
        object.__setattr__(self, "extensions", _freeze_extensions(self.extensions, path="$.permissions.delegation.extensions"))

    @classmethod
    def from_mapping(cls, value: object) -> "Delegation":
        data = _mapping(value, path="$.permissions.delegation")
        return cls(
            parent_packet=data.get("parent_packet") if isinstance(data.get("parent_packet"), str) else None,
            delegator=data.get("delegator") if isinstance(data.get("delegator"), str) else None,
            principal=data.get("principal") if isinstance(data.get("principal"), str) else None,
            extensions=_mapping(data.get("extensions", {}), path="$.permissions.delegation.extensions"),
        )


@dataclass(frozen=True, slots=True)
class Permissions:
    mode: str | None = None
    scope: tuple[str, ...] = ()
    forbid: tuple[str, ...] = ()
    require_confirmation: bool = False
    require_review: bool = False
    require_logging: bool = False
    limits: Mapping[str, JSONValue] = field(default_factory=dict)
    authorization_ref: str | None = None
    expires_at: str | None = None
    delegation: Delegation | None = None
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode is not None and self.mode not in PERMISSION_MODES:
            raise ValueError(f"unknown permission mode: {self.mode!r}")
        for index, item in enumerate(self.scope):
            _non_empty_string(item, path=f"$.permissions.scope[{index}]")
        if len(set(self.scope)) != len(self.scope):
            raise ValueError("duplicate permission scope")
        for index, item in enumerate(self.forbid):
            _non_empty_string(item, path=f"$.permissions.forbid[{index}]")
        if len(set(self.forbid)) != len(self.forbid):
            raise ValueError("duplicate permission forbid")
        if self.authorization_ref is not None:
            _non_empty_string(
                self.authorization_ref,
                path="$.permissions.authorization_ref",
            )
        if self.expires_at is not None:
            _non_empty_string(self.expires_at, path="$.permissions.expires_at")
        object.__setattr__(
            self,
            "limits",
            _freeze_object(self.limits, path="$.permissions.limits"),
        )
        object.__setattr__(
            self,
            "extensions",
            _freeze_extensions(self.extensions, path="$.permissions.extensions"),
        )

    @classmethod
    def from_mapping(cls, value: object) -> "Permissions":
        data = _mapping(value, path="$.permissions")
        _reject_unknown_keys(
            data,
            allowed={
                "mode",
                "scope",
                "forbid",
                "require_confirmation",
                "require_review",
                "require_logging",
                "limits",
                "authorization_ref",
                "expires_at",
                "delegation",
                "extensions",
            },
            path="$.permissions",
        )
        delegation = data.get("delegation")
        return cls(
            mode=_optional_string(data, "mode", path="$.permissions"),
            scope=tuple(
                _non_empty_string(x, path="$.permissions.scope[]")
                for x in _sequence(data.get("scope", []), path="$.permissions.scope")
            ),
            forbid=tuple(
                _non_empty_string(x, path="$.permissions.forbid[]")
                for x in _sequence(data.get("forbid", []), path="$.permissions.forbid")
            ),
            require_confirmation=_optional_bool(
                data,
                "require_confirmation",
                path="$.permissions",
            ),
            require_review=_optional_bool(
                data,
                "require_review",
                path="$.permissions",
            ),
            require_logging=_optional_bool(
                data,
                "require_logging",
                path="$.permissions",
            ),
            limits=_mapping(data.get("limits", {}), path="$.permissions.limits"),
            authorization_ref=_optional_string(
                data,
                "authorization_ref",
                path="$.permissions",
            ),
            expires_at=_optional_string(
                data,
                "expires_at",
                path="$.permissions",
            ),
            delegation=(
                Delegation.from_mapping(delegation)
                if delegation is not None
                else None
            ),
            extensions=_mapping(
                data.get("extensions", {}),
                path="$.permissions.extensions",
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    id: str
    source_type: str
    source_ref: str | None = None
    input_hash: str | None = None
    span: JSONValue = None
    supports: tuple[str, ...] = ()
    description: str | None = None
    confidence: float | None = None
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _EVIDENCE_ID_RE.fullmatch(self.id):
            raise ValueError(f"invalid evidence id: {self.id!r}")
        if self.source_type not in EVIDENCE_SOURCE_TYPES:
            raise ValueError(f"unknown evidence source type: {self.source_type!r}")
        object.__setattr__(self, "span", _freeze(self.span, path="$.evidence[].span"))
        for support in self.supports:
            if not (_RELATION_ID_RE.fullmatch(support) or _ATOM_ID_RE.fullmatch(support)):
                raise ValueError(f"invalid evidence support reference: {support!r}")
        if self.confidence is not None:
            object.__setattr__(self, "confidence", _bounded_confidence(self.confidence, path="$.evidence[].confidence"))
        object.__setattr__(self, "extensions", _freeze_extensions(self.extensions, path="$.evidence[].extensions"))

    @classmethod
    def from_mapping(cls, value: object) -> "EvidenceItem":
        data = _mapping(value, path="$.evidence[]")
        return cls(
            id=_non_empty_string(data.get("id"), path="$.evidence[].id"),
            source_type=_non_empty_string(data.get("source_type"), path="$.evidence[].source_type"),
            source_ref=data.get("source_ref") if isinstance(data.get("source_ref"), str) else None,
            input_hash=data.get("input_hash") if isinstance(data.get("input_hash"), str) else None,
            span=data.get("span"),
            supports=tuple(_non_empty_string(x, path="$.evidence[].supports[]") for x in _sequence(data.get("supports", []), path="$.evidence[].supports")),
            description=data.get("description") if isinstance(data.get("description"), str) else None,
            confidence=None if data.get("confidence") is None else _bounded_confidence(data["confidence"], path="$.evidence[].confidence"),
            extensions=_mapping(data.get("extensions", {}), path="$.evidence[].extensions"),
        )


@dataclass(frozen=True, slots=True)
class Output:
    format: str
    schema: str | None = None
    channel: str | None = None
    target: str | None = None
    language: str | None = None
    max_bytes: int | None = None
    requirements: tuple[str, ...] = ()
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.format not in OUTPUT_FORMATS:
            raise ValueError(f"unknown output format: {self.format!r}")
        if self.channel is not None:
            _identifier(self.channel, path="$.output.channel", qualified=True)
        if self.max_bytes is not None and (isinstance(self.max_bytes, bool) or self.max_bytes < 1):
            raise ValueError("output max_bytes must be a positive integer")
        object.__setattr__(self, "extensions", _freeze_extensions(self.extensions, path="$.output.extensions"))

    @classmethod
    def from_mapping(cls, value: object) -> "Output":
        data = _mapping(value, path="$.output")
        return cls(
            format=_non_empty_string(data.get("format"), path="$.output.format"),
            schema=data.get("schema") if isinstance(data.get("schema"), str) else None,
            channel=data.get("channel") if isinstance(data.get("channel"), str) else None,
            target=data.get("target") if isinstance(data.get("target"), str) else None,
            language=data.get("language") if isinstance(data.get("language"), str) else None,
            max_bytes=data.get("max_bytes") if isinstance(data.get("max_bytes"), int) and not isinstance(data.get("max_bytes"), bool) else None,
            requirements=tuple(_non_empty_string(x, path="$.output.requirements[]") for x in _sequence(data.get("requirements", []), path="$.output.requirements")),
            extensions=_mapping(data.get("extensions", {}), path="$.output.extensions"),
        )


@dataclass(frozen=True, slots=True)
class Octad:
    pragmatics: Pragmatics
    atoms: tuple[Atom, ...]
    relations: tuple[Relation, ...]
    context: Context
    confidence: float
    permissions: Permissions
    evidence: tuple[EvidenceItem, ...]
    output: Output

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", _bounded_confidence(self.confidence, path="$.confidence"))

    def semantic_items(self) -> tuple[tuple[str, object], ...]:
        return (("pragmatics", self.pragmatics), ("atoms", self.atoms), ("relations", self.relations), ("context", self.context), ("confidence", self.confidence), ("permissions", self.permissions), ("evidence", self.evidence), ("output", self.output))

    @classmethod
    def from_mapping(cls, value: object) -> "Octad":
        data = _mapping(value, path="$")
        return cls(
            pragmatics=Pragmatics.from_mapping(data.get("pragmatics")),
            atoms=tuple(Atom.from_mapping(x) for x in _sequence(data.get("atoms"), path="$.atoms")),
            relations=tuple(Relation.from_mapping(x) for x in _sequence(data.get("relations"), path="$.relations")),
            context=Context.from_mapping(data.get("context")),
            confidence=_bounded_confidence(data.get("confidence"), path="$.confidence"),
            permissions=Permissions.from_mapping(data.get("permissions")),
            evidence=tuple(EvidenceItem.from_mapping(x) for x in _sequence(data.get("evidence"), path="$.evidence")),
            output=Output.from_mapping(data.get("output")),
        )


@dataclass(frozen=True, slots=True)
class PacketEnvelope:
    octad: Octad
    packet_id: str
    protocol_version: str
    carrier: Mapping[str, JSONValue] = field(default_factory=dict)
    audit: Mapping[str, JSONValue] = field(default_factory=dict)
    extensions: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _non_empty_string(self.packet_id, path="$.id")
        if self.protocol_version not in SUPPORTED_PROTOCOL_VERSIONS:
            raise ValueError(f"unsupported protocol_version: {self.protocol_version!r}")
        object.__setattr__(self, "carrier", _freeze_object(self.carrier, path="$.carrier"))
        object.__setattr__(self, "audit", _freeze_object(self.audit, path="$.audit"))
        object.__setattr__(self, "extensions", _freeze_extensions(self.extensions, path="$.extensions"))

    def semantically_equals(self, other: object) -> bool:
        return isinstance(other, PacketEnvelope) and self.octad == other.octad

    @classmethod
    def from_mapping(cls, value: object) -> "PacketEnvelope":
        data = _mapping(value, path="$")
        return cls(
            octad=Octad.from_mapping(data),
            packet_id=_non_empty_string(data.get("id"), path="$.id"),
            protocol_version=_non_empty_string(data.get("version"), path="$.version"),
            carrier=_mapping(data.get("carrier"), path="$.carrier"),
            audit=_mapping(data.get("audit"), path="$.audit"),
            extensions=_mapping(data.get("extensions", {}), path="$.extensions"),
        )
