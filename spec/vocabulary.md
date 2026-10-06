# LSTP v0.1 Core Vocabulary

Status: normative vocabulary profile subordinate to `spec/CANONICAL-v0.1.md`.

The core vocabulary is intentionally small. It standardizes only concepts required for interoperable v0.1 packets. Domain semantics belong in namespaced vocabularies.

## 1. Identifier rules

Core identifiers use ASCII letters, digits, `_`, and `-` as defined by the canonical schema. Domain-specific semantic identifiers MUST be namespaced with dot-separated identifiers, for example:

```text
slai.route
finance.position
robotics.move
```

Unknown namespaced values MAY be preserved but MUST NOT be assigned invented semantics by a core consumer.

## 2. Pragmatic type and speech-act identifiers

The Whitepaper canonical field is `pragmatics.type`, with an optional distinct
`pragmatics.speech_act`. The two fields MUST NOT be collapsed into one
`act` value.

The following type identifiers are recommended for interoperable core traffic:

- `assert`
- `request`
- `question`
- `inform`
- `correct`
- `acknowledge`
- `refuse`
- `respond`

The compact reference compiler additionally uses speech-act identifiers
`command`, `question`, and `statement` for directive, interrogative, and
declarative prefixes respectively.

These identifiers describe communication semantics only. They do not imply
execution authority.

## 3. Atom kinds

Canonical atom kinds:

- `entity`
- `concept`
- `value`
- `event`
- `time`
- `location`
- `resource`
- `proposition`
- `unknown`

## 4. Special relation arguments

The following argument identifiers are reserved:

- `SELF` — the current producer/agent where resolved by the host;
- `NOW` — current temporal reference where resolved by the host;
- `USER` — originating user/principal reference where resolved by the host;
- `SYSTEM` — host/system reference where resolved by the host.

They are semantic references, not credentials or authority tokens.

## 5. Core semantic relations

Core relation types are deliberately generic:

| Relation | Intended semantics |
|---|---|
| `is` | identity/classification/value relation |
| `has` | possession/attribute relation |
| `part_of` | compositional membership |
| `located_at` | spatial/logical location |
| `causes` | declared causal relation |
| `requires` | declared dependency/precondition |
| `references` | semantic reference/link |
| `produces` | declared output/result relation |
| `requests` | relation expresses requested operation/content |
| `answers` | relation answers another relation/proposition/request |

Consumers MUST NOT perform domain-specific inference from these labels beyond their documented generic semantics.

## 6. Outcome relations

Protocol responses use the same Octad. Standard outcome relation types are:

- `outcome.success`
- `outcome.failure`
- `outcome.partial`
- `outcome.refused`
- `outcome.unsupported`
- `outcome.needs_confirmation`
- `outcome.needs_context`

An outcome SHOULD reference the originating request/relation when possible.

## 7. Permission modes

Canonical requested authority is represented by one of the six Whitepaper modes:

- `RO`
- `SUGGEST`
- `PREVIEW`
- `RW`
- `EXEC`
- `COMMIT`

Their conceptual order is:

```text
RO <= SUGGEST <= PREVIEW <= RW <= EXEC <= COMMIT
```

Scope and forbids remain independent; a stronger mode never widens scope.

## 8. Host-internal authorization capabilities

The reference host translates the wire mode into internal capabilities
`read`, `suggest`, `prepare`, `write`, `execute`, and `commit` for
authorization intersection. These are implementation vocabulary, not canonical
packet fields.

Normative safety behavior is defined by `spec/permissions-safety.md`.

## 9. Evidence source types

Core provenance constructors:

- `user`
- `sensor`
- `model`
- `tool`
- `retrieved`
- `inferred`

Evidence records declared support/provenance; source type alone does not establish truth.

## 10. Output formats

Canonical output formats:

- `NL`
- `LATTICE`
- `JSON`
- `YAML`
- `TABLE`
- `CODE`
- `FILE`
- `NONE`

## 11. Namespaced extensions versus namespaced vocabulary

These are distinct:

- a namespaced **vocabulary identifier** may appear in a core semantic field that permits qualified identifiers;
- an `extensions` namespace contains opaque structured metadata outside core semantics.

An extension MUST NOT override a core semantic value. A namespaced vocabulary value participates in semantics only where the receiving implementation understands or explicitly preserves that identifier.

## 12. Reserved growth rule

Adding a new core pragmatic type, permission mode, atom kind, evidence source type, output format, or special relation argument is a protocol change and requires versioned conformance updates.

Adding a domain-specific namespaced relation or goal does not change core v0.1, provided it does not reinterpret a core identifier or permission rule.
