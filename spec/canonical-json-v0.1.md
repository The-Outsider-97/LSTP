# LSTP v0.1 Canonical JSON Byte Profile

Status: normative serialization profile subordinate to `spec/CANONICAL-v0.1.md` and `spec/octad_schema.json`.

This profile defines deterministic JSON bytes for LSTP v0.1 packets. It does not change Octad semantics. A packet may be semantically valid without already being in canonical byte form; canonical serialization is the deterministic representation used for byte equality, fixture comparison, hashing inputs, caching inputs, and future signature profiles.

## 1. Encoding

Canonical LSTP JSON MUST be encoded as UTF-8 without a BOM.

No insignificant whitespace is permitted. Objects and arrays use the compact JSON delimiters `:`, `,`, `{}`, and `[]` without surrounding spaces or line breaks.

## 2. Object member ordering

Object member names MUST be ordered lexicographically by their UTF-16 code-unit representation.

This ordering applies recursively to every JSON object, including `carrier`, `audit`, `attributes`, `bindings`, `limits`, and namespaced extension payloads.

Array order is semantic and MUST be preserved.

## 3. Strings and Unicode

Canonical strings MUST already be Unicode NFC.

A canonicalizer MUST NOT silently change a non-NFC input into NFC because doing so would transform packet content during byte canonicalization. Non-NFC input therefore fails canonical decoding/encoding until the producer explicitly normalizes it.

Unpaired surrogate code points are forbidden.

The following bidirectional formatting/control characters are forbidden in canonical strings and object keys:

- U+061C ARABIC LETTER MARK;
- U+200E LEFT-TO-RIGHT MARK;
- U+200F RIGHT-TO-LEFT MARK;
- U+202A through U+202E;
- U+2066 through U+2069.

Human-language Unicode remains permitted. This rule is targeted at deterministic and inspectable protocol text; it is not an ASCII-only content restriction.

JSON string escaping uses the shortest ordinary JSON representation available to the reference serializer. Quotation mark, reverse solidus, and required control characters are escaped. Solidus `/` is not escaped merely for presentation.

## 4. Numbers

Canonical LSTP JSON permits only finite JSON numbers.

The v0.1 numeric byte profile is decimal and deliberately does not use a binary64/ECMAScript number-formatting dependency.

Rules:

1. integers are emitted in base 10 with no leading `+` and no unnecessary leading zero;
2. decimal values are emitted without exponent notation;
3. unnecessary fractional trailing zeroes are removed;
4. the decimal point is omitted when the value is integral;
5. negative zero is emitted as `0`;
6. NaN and positive/negative infinity are forbidden;
7. the reference implementation limits one canonical numeric representation to 1024 characters as an implementation safety bound.

Examples:

| Input semantic value | Canonical token |
|---|---|
| `1.0` | `1` |
| `0.5000` | `0.5` |
| `-0.0` | `0` |
| `1e-3` | `0.001` |
| `1e3` | `1000` |

The 1024-character implementation bound is not an invitation to treat very large numeric values as portable domain semantics. Domain profiles SHOULD define narrower numeric ranges where appropriate.

## 5. Optional fields and defaults

The serializer MUST emit all top-level fields required by `spec/octad_schema.json`.

Optional fields MAY be omitted when their in-memory value is the protocol-defined absent/default state. Omission MUST NOT change Octad semantics.

`extensions` MAY be omitted when empty. Required Octad domains themselves are never omitted.

## 6. Canonical decoding

A canonical decoder MUST perform all of the following before reporting canonical packet acceptance:

1. bounded UTF-8 JSON decoding;
2. duplicate-object-key rejection;
3. unknown core-field rejection (`additionalProperties: false` behavior);
4. schema-relevant JSON type checks;
5. NFC and bidi-control checks;
6. typed canonical model construction;
7. semantic validation.

When strict byte conformance is requested, the decoder MUST re-encode the validated packet and require byte-for-byte equality with the supplied input.

A decoder MUST NOT silently migrate legacy field names, legacy permission modes, alternate casing, unsupported protocol versions, or unknown core fields.

## 7. Semantic equality versus byte equality

Octad semantic equality is distinct from envelope equality and canonical byte equality.

Two packets can have semantically equal Octads while having different envelope IDs or carrier/audit metadata. They can also arrive through non-canonical JSON formatting and normalize to the same canonical packet bytes only after successful structural and semantic validation.

Applications MUST state which equality relation they use.

## 8. RFC 8785 relationship

The profile intentionally adopts the deterministic JSON goals and UTF-16 object-member ordering associated with RFC 8785, but it is not a claim of unmodified RFC 8785 conformance because LSTP v0.1 uses the decimal number profile in section 4 instead of ECMAScript binary64 number serialization.

Implementations MUST follow this document and the shared byte fixtures rather than assuming a generic JCS library is automatically LSTP-compatible.

## 9. Conformance evidence

Canonical byte fixtures live under `conformance/v0.1/positive/`.

A positive canonical-byte vector MUST:

- decode successfully;
- pass typed construction;
- pass semantic validation;
- re-encode byte-for-byte identically.

Negative vectors under `conformance/v0.1/negative/` MUST fail closed at their appropriate structural or semantic layer.

Byte-profile changes require versioned fixture updates and MUST be treated as protocol compatibility changes.
