"""Parser for the Whitepaper canonical ordered-Octad Lattice carrier."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import TypeVar, cast

from lstp.errors import Diagnostic, LatticeSyntaxError
from lstp.models import (
    Atom,
    Context,
    ContextReference,
    EvidenceItem,
    JSONValue,
    Octad,
    Output,
    Permissions,
    Pragmatics,
    Relation,
)

_T = TypeVar("_T")
_IDENTIFIER_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*"
)
_ATOM_ID_RE = re.compile(r"a(?:0|[1-9][0-9]*)")
_NUMBER_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
_UINT_RE = re.compile(r"(?:0|[1-9][0-9]*)")

_ATOM_KINDS = {
    "ENT": "entity",
    "CONCEPT": "concept",
    "VALUE": "value",
    "EVENT": "event",
    "TIME": "time",
    "LOCATION": "location",
    "RES": "resource",
    "PROPOSITION": "proposition",
    "UNKNOWN": "unknown",
}
_PERMISSION_MODES = {"RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT"}
_EVIDENCE_SOURCES = {
    "USER": "user",
    "SENSOR": "sensor",
    "MODEL": "model",
    "TOOL": "tool",
    "RETRIEVED": "retrieved",
    "INFERRED": "inferred",
}
_OUTPUT_FORMATS = {"NL", "LATTICE", "JSON", "YAML", "TABLE", "CODE", "FILE", "NONE"}
_SPECIAL_ARGUMENTS = {"SELF", "NOW", "USER", "SYSTEM"}


@dataclass(frozen=True, slots=True)
class CanonicalLatticePacket:
    """One canonical Octad plus an optional carrier-level label."""

    octad: Octad
    label: str | None = None


@dataclass(frozen=True, slots=True)
class CanonicalLatticeDocument:
    """Atomic/framed/named packet or a named packet stream."""

    packets: tuple[CanonicalLatticePacket, ...]


class _Parser:
    def __init__(self, source: str) -> None:
        self.source = source[1:] if source.startswith("\ufeff") else source
        self.index = 0

    def _line_column(self) -> tuple[int, int]:
        prefix = self.source[: self.index]
        line = prefix.count("\n") + 1
        last = prefix.rfind("\n")
        return line, self.index + 1 if last < 0 else self.index - last

    def _error(self, code: str, message: str) -> LatticeSyntaxError:
        line, column = self._line_column()
        return LatticeSyntaxError(Diagnostic(code, message, line, column))

    def _peek(self) -> str:
        return self.source[self.index : self.index + 1]

    def _skip_horizontal(self) -> None:
        while self._peek() in {" ", "\t"}:
            self.index += 1

    def _skip_layout(self) -> None:
        while self._peek() in {" ", "\t", "\r", "\n"}:
            self.index += 1

    def _expect(self, text: str, *, layout: bool = False) -> None:
        if layout:
            self._skip_layout()
        else:
            self._skip_horizontal()
        if not self.source.startswith(text, self.index):
            raise self._error("expected_token", f"expected {text!r}")
        self.index += len(text)

    def _identifier(self) -> str:
        self._skip_layout()
        match = _IDENTIFIER_RE.match(self.source, self.index)
        if match is None:
            raise self._error("expected_identifier", "expected canonical identifier")
        self.index = match.end()
        return match.group(0)

    def _atom_id(self) -> str:
        self._skip_layout()
        match = _ATOM_ID_RE.match(self.source, self.index)
        if match is None:
            raise self._error("expected_atom_id", "expected atom id such as a0")
        self.index = match.end()
        return match.group(0)

    def _unsigned_integer(self) -> int:
        self._skip_layout()
        match = _UINT_RE.match(self.source, self.index)
        if match is None:
            raise self._error("expected_integer", "expected unsigned integer")
        self.index = match.end()
        return int(match.group(0))

    def _number(self) -> Decimal:
        self._skip_layout()
        match = _NUMBER_RE.match(self.source, self.index)
        if match is None:
            raise self._error("expected_number", "expected canonical number")
        self.index = match.end()
        return Decimal(match.group(0))

    def _string(self) -> str:
        self._skip_layout()
        if self._peek() != '"':
            raise self._error("expected_string", "expected JSON string literal")
        try:
            value, consumed = json.JSONDecoder().raw_decode(self.source[self.index :])
        except json.JSONDecodeError as exc:
            raise self._error("invalid_string", exc.msg) from None
        if not isinstance(value, str):
            raise self._error("expected_string", "expected JSON string literal")
        self.index += consumed
        return value

    def _json_value(self) -> JSONValue:
        self._skip_layout()
        try:
            value, consumed = json.JSONDecoder(
                parse_float=Decimal,
                parse_int=int,
            ).raw_decode(self.source[self.index :])
        except json.JSONDecodeError as exc:
            raise self._error("invalid_json_value", exc.msg) from None
        self.index += consumed
        return cast(JSONValue, value)

    def _string_or_identifier(self) -> str:
        self._skip_layout()
        return self._string() if self._peek() == '"' else self._identifier()

    def _boolean(self) -> bool:
        value = self._identifier()
        if value == "true":
            return True
        if value == "false":
            return False
        raise self._error("expected_boolean", "expected true or false")

    def _list(self, item_parser: Callable[[], _T]) -> tuple[_T, ...]:
        self._expect("[", layout=True)
        self._skip_layout()
        items: list[_T] = []
        if self._peek() != "]":
            while True:
                items.append(item_parser())
                self._skip_layout()
                if self._peek() != ",":
                    break
                self.index += 1
        self._expect("]", layout=True)
        return tuple(items)

    def _entries(
        self,
        value_parser: Callable[[str], object],
    ) -> dict[str, object]:
        self._expect("(", layout=True)
        self._skip_layout()
        result: dict[str, object] = {}
        if self._peek() == ")":
            self.index += 1
            return result
        while True:
            key = self._identifier()
            if key in result:
                raise self._error(
                    "duplicate_canonical_field",
                    f"duplicate canonical field {key!r}",
                )
            self._expect("=")
            result[key] = value_parser(key)
            self._skip_layout()
            if self._peek() != ",":
                break
            self.index += 1
        self._expect(")", layout=True)
        return result

    def _pragmatics(self) -> Pragmatics:
        self._expect("π", layout=True)
        self._expect("=")

        def parse_value(key: str) -> object:
            if key in {"TYPE", "SPEECH_ACT", "GOAL", "REGISTER"}:
                return self._identifier()
            if key == "MOD":
                return self._list(self._identifier)
            if key == "URGENCY":
                return self._number()
            raise self._error(
                "unknown_pragmatics_field",
                f"unknown canonical pragmatics field {key!r}",
            )

        entries = self._entries(parse_value)
        if "TYPE" not in entries:
            raise self._error("missing_pragmatics_type", "π requires TYPE")
        return Pragmatics(
            type=str(entries["TYPE"]).lower(),
            speech_act=(
                str(entries["SPEECH_ACT"]).lower()
                if "SPEECH_ACT" in entries
                else None
            ),
            goal=str(entries["GOAL"]) if "GOAL" in entries else None,
            modifiers=tuple(entries.get("MOD", ())),  # type: ignore[arg-type]
            register=str(entries["REGISTER"]) if "REGISTER" in entries else None,
            urgency=entries.get("URGENCY"),  # type: ignore[arg-type]
        )

    def _atom(self) -> Atom:
        atom_id = self._atom_id()
        self._expect(":")
        kind_token = self._identifier()
        kind = _ATOM_KINDS.get(kind_token)
        if kind is None:
            raise self._error(
                "unknown_atom_constructor",
                f"unknown canonical atom constructor {kind_token!r}",
            )
        self._expect("(")
        self._skip_layout()
        value: object = None
        if self._peek() != ")":
            value = self._json_value()
        self._expect(")", layout=True)

        role: str | None = None
        datatype: str | None = None
        language: str | None = None
        self._skip_layout()
        if self._peek() == "{":
            self.index += 1
            seen: set[str] = set()
            while True:
                self._skip_layout()
                key = self._identifier()
                if key in seen:
                    raise self._error(
                        "duplicate_atom_metadata",
                        f"duplicate atom metadata {key!r}",
                    )
                seen.add(key)
                self._expect("=")
                if key == "ROLE":
                    role = self._identifier()
                elif key == "DATATYPE":
                    datatype = self._string_or_identifier()
                elif key == "LANGUAGE":
                    language = self._string_or_identifier()
                else:
                    raise self._error(
                        "unknown_atom_metadata",
                        f"unknown canonical atom metadata {key!r}",
                    )
                self._skip_layout()
                if self._peek() != ",":
                    break
                self.index += 1
            self._expect("}", layout=True)

        return Atom(
            atom_id,
            kind,
            value=value,
            role=role,
            datatype=datatype,
            language=language,
        )

    def _atoms(self) -> tuple[Atom, ...]:
        self._expect("A", layout=True)
        self._expect("=")
        self._expect("(")
        self._skip_layout()
        atoms: list[Atom] = []
        if self._peek() != ")":
            while True:
                atoms.append(self._atom())
                self._skip_layout()
                if self._peek() != ",":
                    break
                self.index += 1
        self._expect(")", layout=True)
        return tuple(atoms)

    def _relation(self) -> Relation:
        relation_type = self._identifier()
        self._expect("(")
        arguments: list[str] = []
        while True:
            self._skip_layout()
            if self.source.startswith("a", self.index):
                match = _ATOM_ID_RE.match(self.source, self.index)
            else:
                match = None
            if match is not None:
                argument = match.group(0)
                self.index = match.end()
            else:
                argument = self._identifier()
                if argument not in _SPECIAL_ARGUMENTS:
                    raise self._error(
                        "invalid_relation_argument",
                        "canonical relation arguments must reference atoms or special arguments",
                    )
            arguments.append(argument)
            self._skip_layout()
            if self._peek() != ",":
                break
            self.index += 1
        self._expect(")", layout=True)
        return Relation(relation_type, tuple(arguments))

    def _relations(self) -> tuple[Relation, ...]:
        self._expect("R", layout=True)
        self._expect("=")
        self._expect("(")
        self._skip_layout()
        relations: list[Relation] = []
        if self._peek() != ")":
            while True:
                relations.append(self._relation())
                self._skip_layout()
                if self._peek() != ",":
                    break
                self.index += 1
        self._expect(")", layout=True)
        return tuple(relations)

    def _context(self) -> Context:
        self._expect("C", layout=True)
        self._expect("=")

        def parse_value(key: str) -> object:
            if key in {"THREAD", "PACKET", "PARENT", "CONVERSATION", "TIMEZONE"}:
                return self._string_or_identifier()
            if key == "TURN":
                return self._unsigned_integer()
            if key == "TIME":
                return self._string()
            if key in {"WINDOW", "LOCATION"}:
                return self._json_value()
            if key == "BINDINGS":
                value = self._json_value()
                if not isinstance(value, dict):
                    raise self._error("expected_object", "BINDINGS requires a JSON object")
                return value
            if key == "REFERENCES":
                return self._list(self._string_or_identifier)
            if key == "SPEAKER":
                return self._identifier()
            if key == "AUDIENCE":
                return self._list(self._identifier)
            raise self._error(
                "unknown_context_field",
                f"unknown canonical context field {key!r}",
            )

        entries = self._entries(parse_value)
        if "THREAD" not in entries:
            raise self._error("missing_context_thread", "C requires THREAD")
        references = tuple(
            ContextReference(str(packet_id))
            for packet_id in entries.get("REFERENCES", ())  # type: ignore[arg-type]
        )
        return Context(
            thread_id=str(entries["THREAD"]),
            references=references,
            packet_id=str(entries["PACKET"]) if "PACKET" in entries else None,
            parent_packet_id=str(entries["PARENT"]) if "PARENT" in entries else None,
            conversation_id=(
                str(entries["CONVERSATION"])
                if "CONVERSATION" in entries
                else None
            ),
            turn=entries.get("TURN"),  # type: ignore[arg-type]
            speaker=str(entries["SPEAKER"]) if "SPEAKER" in entries else None,
            audience=tuple(entries.get("AUDIENCE", ())),  # type: ignore[arg-type]
            time=str(entries["TIME"]) if "TIME" in entries else None,
            timezone=str(entries["TIMEZONE"]) if "TIMEZONE" in entries else None,
            window=entries.get("WINDOW"),
            location=entries.get("LOCATION"),
            bindings=entries.get("BINDINGS", {}),  # type: ignore[arg-type]
        )

    def _confidence(self) -> float:
        self._expect("κ", layout=True)
        self._expect("=")
        value = self._number()
        if value < 0 or value > 1:
            raise self._error("confidence_range", "κ must be between 0 and 1")
        return float(value)

    def _permissions(self) -> Permissions:
        self._expect("Π", layout=True)
        self._expect("=")

        def parse_value(key: str) -> object:
            if key == "MODE":
                mode = self._identifier()
                if mode not in _PERMISSION_MODES:
                    raise self._error(
                        "unknown_permission_mode",
                        f"unknown canonical permission mode {mode!r}",
                    )
                return mode
            if key in {"SCOPE", "FORBID"}:
                return self._list(self._string_or_identifier)
            if key == "LIMITS":
                value = self._json_value()
                if not isinstance(value, dict):
                    raise self._error("expected_object", "LIMITS requires a JSON object")
                return value
            if key in {"REQUIRE_CONFIRM", "REQUIRE_REVIEW", "LOG"}:
                return self._boolean()
            raise self._error(
                "unknown_permission_field",
                f"unknown canonical permission field {key!r}",
            )

        entries = self._entries(parse_value)
        return Permissions(
            mode=str(entries["MODE"]) if "MODE" in entries else None,
            scope=tuple(entries.get("SCOPE", ())),  # type: ignore[arg-type]
            forbid=tuple(entries.get("FORBID", ())),  # type: ignore[arg-type]
            require_confirmation=bool(entries.get("REQUIRE_CONFIRM", False)),
            require_review=bool(entries.get("REQUIRE_REVIEW", False)),
            require_logging=bool(entries.get("LOG", False)),
            limits=entries.get("LIMITS", {}),  # type: ignore[arg-type]
        )

    def _evidence_item(self, index: int) -> EvidenceItem:
        source_token = self._identifier()
        source = _EVIDENCE_SOURCES.get(source_token)
        if source is None:
            raise self._error(
                "unknown_evidence_source",
                f"unknown canonical evidence constructor {source_token!r}",
            )
        self._expect("(")
        self._skip_layout()
        source_ref: str | None = None
        if self._peek() != ")":
            source_ref = self._string()
        self._expect(")", layout=True)
        return EvidenceItem(f"e{index}", source, source_ref=source_ref)

    def _evidence(self) -> tuple[EvidenceItem, ...]:
        self._expect("E", layout=True)
        self._expect("=")
        self._expect("(")
        self._skip_layout()
        evidence: list[EvidenceItem] = []
        if self._peek() != ")":
            while True:
                evidence.append(self._evidence_item(len(evidence)))
                self._skip_layout()
                if self._peek() != ",":
                    break
                self.index += 1
        self._expect(")", layout=True)
        return tuple(evidence)

    def _output(self) -> Output:
        self._expect("Ω", layout=True)
        self._expect("=")

        def parse_value(key: str) -> object:
            if key == "FORMAT":
                value = self._identifier()
                if value not in _OUTPUT_FORMATS:
                    raise self._error(
                        "unknown_output_format",
                        f"unknown canonical output format {value!r}",
                    )
                return value
            if key in {"SCHEMA", "TARGET", "LANG"}:
                return self._string_or_identifier()
            if key == "CHANNEL":
                return self._identifier()
            if key == "MAX_BYTES":
                return self._unsigned_integer()
            if key == "REQUIREMENTS":
                return self._list(self._string_or_identifier)
            raise self._error(
                "unknown_output_field",
                f"unknown canonical output field {key!r}",
            )

        entries = self._entries(parse_value)
        if "FORMAT" not in entries:
            raise self._error("missing_output_format", "Ω requires FORMAT")
        return Output(
            format=str(entries["FORMAT"]),
            schema=str(entries["SCHEMA"]) if "SCHEMA" in entries else None,
            channel=str(entries["CHANNEL"]) if "CHANNEL" in entries else None,
            target=str(entries["TARGET"]) if "TARGET" in entries else None,
            language=str(entries["LANG"]) if "LANG" in entries else None,
            max_bytes=entries.get("MAX_BYTES"),  # type: ignore[arg-type]
            requirements=tuple(entries.get("REQUIREMENTS", ())),  # type: ignore[arg-type]
        )

    def _octad(self) -> Octad:
        pragmatics = self._pragmatics()
        self._expect("|", layout=True)
        atoms = self._atoms()
        self._expect("|", layout=True)
        relations = self._relations()
        self._expect("|", layout=True)
        context = self._context()
        self._expect("|", layout=True)
        confidence = self._confidence()
        self._expect("|", layout=True)
        permissions = self._permissions()
        self._expect("|", layout=True)
        evidence = self._evidence()
        self._expect("|", layout=True)
        output = self._output()
        return Octad(
            pragmatics,
            atoms,
            relations,
            context,
            confidence,
            permissions,
            evidence,
            output,
        )

    def _framed(self) -> Octad:
        self._expect("[", layout=True)
        octad = self._octad()
        self._expect("]", layout=True)
        return octad

    def _named(self) -> CanonicalLatticePacket:
        label = self._identifier()
        self._expect(":")
        return CanonicalLatticePacket(self._framed(), label=label)

    def parse(self) -> CanonicalLatticeDocument:
        self._skip_horizontal()
        if self._peek() == "[":
            packet = CanonicalLatticePacket(self._framed())
            self._skip_horizontal()
            if self.index != len(self.source):
                raise self._error("trailing_input", "unexpected input after framed packet")
            return CanonicalLatticeDocument((packet,))
        if self._peek() == "π":
            packet = CanonicalLatticePacket(self._octad())
            self._skip_horizontal()
            if self.index != len(self.source):
                raise self._error("trailing_input", "unexpected input after atomic packet")
            return CanonicalLatticeDocument((packet,))

        packets = [self._named()]
        while True:
            self._skip_horizontal()
            if self.index == len(self.source):
                break
            if self._peek() not in {"\r", "\n"}:
                raise self._error(
                    "stream_separator",
                    "named packet streams require a line-break separator",
                )
            while self._peek() in {"\r", "\n"}:
                if self._peek() == "\r":
                    self.index += 1
                    if self._peek() == "\n":
                        self.index += 1
                else:
                    self.index += 1
            self._skip_horizontal()
            if self.index == len(self.source):
                raise self._error(
                    "trailing_stream_separator",
                    "packet stream must not end with an empty packet",
                )
            packets.append(self._named())
        return CanonicalLatticeDocument(tuple(packets))


def parse_canonical_lattice(source: str) -> CanonicalLatticeDocument:
    """Parse canonical ordered-Octad Lattice without inventing envelope metadata."""

    return _Parser(source).parse()


__all__ = [
    "CanonicalLatticeDocument",
    "CanonicalLatticePacket",
    "parse_canonical_lattice",
]
