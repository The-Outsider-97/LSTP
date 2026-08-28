# LSTP v0.1 Operator Table

**Status:** Normative Phase 1 reference  
**Protocol:** Lattice Semantic Transport Protocol (LSTP)  
**Text carrier:** Lattice text  
**Version:** 0.1

---

## 1. Purpose

This document defines the operators and delimiters used by the Lattice text carrier in LSTP v0.1.

The whitepaper establishes the compact notation but leaves several examples syntactically overloaded. Phase 1 therefore stabilizes operator meaning before the text parser is implemented.

The governing principles are:

1. operators MUST have deterministic lexical roles;
2. the same glyph MAY have more than one role only when the grammar distinguishes those roles unambiguously by position or lookahead;
3. undefined glyphs from draft examples MUST NOT acquire invented semantics;
4. compact syntax MUST expand into inspectable Octad fields;
5. permission syntax MUST never imply that authorization has been granted.

---

## 2. Core operator summary

| Token | Name | Core meaning | Typical Octad mapping | Example |
|---|---|---|---|---|
| `!` | Directive prefix | Command/request force | `pragmatics` | `!analyze` |
| `!!` | Urgent directive prefix | Directive with elevated urgency | `pragmatics` | `!!alert` |
| `?` | Interrogative prefix | Question/information request | `pragmatics` | `?cause` |
| `.` | Declarative prefix | Statement/context declaration when leading a clause | `pragmatics` / `context` | `.note` |
| `@` | Target/reference prefix | Entity, source, or target reference | `atoms`, `relations` | `@sales` |
| `.` | Path separator | Qualified target/identifier path when internal | atom reference | `@dog.color` |
| `::` | Operation delimiter | Begins operation expression for a clause | `relations` / `pragmatics.action` | `:: cmp(region)` |
| `+` | Composition | Combine/include sibling expression terms | operations/constraints | `risk + cost` |
| `-` | Exclusion | Exclude or negate a term in an expression | qualifier/relation semantics | `-jargon` |
| `->` | Output delimiter | Begins requested output description | `output` | `-> brief@z2` |
| `{ ... }` | Constraint block | Constraints, assumptions, permission declarations, modifiers | several Octad fields | `{mode=readonly}` |
| `[ ... ]` | Scope block | Target scope, time range, filter, or list | atom/context scope | `@sales[-4Q]` |
| `( ... )` | Call/grouping | Function-like operation arguments or expression grouping | relations/operation AST | `cmp(region)` |
| `%` | Confidence marker | Confidence value in `[0,1]` | `confidence` | `%0.82` |
| `~` | Approximation marker | Marks the immediately preceding term as approximate/uncertain | `confidence` / qualifier | `cause~` |
| `#` | Macro reference | References a named macro | deferred Phase 3 resolution | `#Decision` |
| `@z0`…`@z5` | Zoom marker | Requested semantic expansion depth | `output.zoom` | `brief@z3` |
| `@zmax` | Maximum zoom | Maximum available semantic expansion | `output.zoom="max"` | `memo@zmax` |
| `↑n` | Context reference | Context stack depth `n` | `context.refs` | `↑2` |
| `↑n@agent` | Agent context reference | Context stack depth in named agent namespace | `context.refs` | `↑2@agent_risk` |
| `=` | Assignment/equality delimiter | Associates a key/value or explicit relational value | constraints/relations | `tone=warm` |
| `:` | Annotation delimiter | Associates an annotation key with a value | constraints/annotations | `assume:market_stable` |
| `|` | Alternative | Separates explicit alternatives | ambiguity/scope expression | `finance | river_edge` |
| `,` | Separator | Separates entries or arguments | structural | `mode=preview, tone=warm` |
| `;` | Metadata delimiter | Introduces clause-level metadata | `context`, `audit`, extensions | `; ctx↑0` |

---

## 3. Force prefixes

### 3.1 `!` — directive

Syntax:

```lattice
!<action>
```

Example:

```lattice
!summarize @meeting :: extract(decisions + owners + deadlines)
```

`!` indicates that the principal communicative force is directive: the sender is asking the receiver to perform or prepare an operation.

It does **not** imply real-world execution permission. Execution remains governed by the `permissions` Octad field.

A parser SHOULD preserve the literal action identifier and SHOULD map the force into `pragmatics.force`.

### 3.2 `!!` — urgent directive

Syntax:

```lattice
!!<action>
```

`!!` is a lexical token and MUST be recognized before `!`.

It denotes a directive with elevated urgency. Urgency affects scheduling, prioritization, or presentation only according to host policy. It MUST NOT bypass safety, confirmation, rate limits, or permissions.

### 3.3 `?` — interrogative

Syntax:

```lattice
?<action-or-question>
```

Example:

```lattice
?risk ↑2@agent_risk -> summary@z2
```

This requests information, explanation, evaluation, or clarification.

### 3.4 leading `.` — declaration

At the beginning of a main clause, `.` denotes declarative/contextual force.

Example:

```lattice
.note @experiment :: result(valid)
```

The dot in this position is distinct from the dot inside a qualified identifier.

---

## 4. References and addressing

### 4.1 `@` — target or atom reference

Syntax:

```lattice
@identifier
@qualified.identifier
@identifier[scope]
```

Examples:

```lattice
@sales
@dog.color
@sales[-4Q]
```

`@` does not dereference external data by itself. It marks a symbolic target/reference in the text carrier. Resolution is performed by the host, context resolver, or packet compiler.

### 4.2 `.` — path separator

Inside an identifier, `.` separates qualified path segments:

```lattice
@dog.color
@report.section_3
```

Leading `.` remains the declarative prefix. Parsers MUST distinguish the two by position.

### 4.3 `↑n` — context stack reference

Syntax:

```lattice
↑0
↑2
↑2@agent_risk
```

`n` is a non-negative integer. The optional `@agent` suffix identifies an agent-specific context namespace.

Stack resolution is a Phase 3 semantic operation. Phase 2 may parse and preserve the reference without resolving it.

### 4.4 No postfix trend meaning for `↑` in core v0.1

Draft examples use forms such as:

```text
churn↑
```

while the operator table defines `↑n` as a context-stack reference. Because the draft does not formally define a postfix trend operator, **postfix `↑` without a following integer is not a core v0.1 operator**.

Writers SHOULD express trend semantics explicitly, for example:

```lattice
trend(churn, up)
```

or through a domain vocabulary.

A strict v0.1 parser SHOULD reject an isolated postfix `↑`. A permissive parser MAY preserve it as an opaque extension token, but MUST NOT assign causal, temporal, or numerical meaning without an extension vocabulary.

The same rule applies to an undefined postfix `↓`.

---

## 5. Operation syntax

### 5.1 `::` — operation delimiter

Syntax:

```lattice
<main-clause> :: <expression>
```

Example:

```lattice
!analyze @sales[-4Q] :: cmp(region) + detect(anomaly) + infer(cause~)
```

`::` separates the main communicative clause from the operation expression. It is not a generic relation operator.

### 5.2 `()` — operation call and grouping

Examples:

```lattice
cmp(region)
detect(anomaly)
infer(cause~)
eval(risk + upside + effort)
```

A function-like operation name is a symbolic operation identifier, not an instruction to invoke arbitrary host code. The host MUST map supported operation identifiers to allowed capabilities.

Parentheses MAY also group an expression:

```lattice
eval((risk + cost) | defer)
```

### 5.3 `+` — composition

`+` combines sibling terms.

Examples:

```lattice
risk + cost
warm + firm
decisions + owners + deadlines
```

`+` means "include/compose these terms" at the syntax level. Domain-specific meaning remains dependent on the enclosing operation or field.

It is not numerical addition unless the active vocabulary explicitly defines numerical semantics.

### 5.4 unary `-` — exclusion

Outside a scope literal, a leading `-` excludes or negates a term:

```lattice
-jargon
```

Inside a scope, forms such as `-4Q` are parsed as signed period literals, not as exclusion of `4Q`.

This distinction is grammar-defined and MUST be preserved by the tokenizer.

### 5.5 `|` — alternative

`|` separates explicit alternatives:

```lattice
finance | river_edge
```

It does not mean boolean OR unless an enclosing vocabulary defines that interpretation.

---

## 6. Constraints and scopes

### 6.1 `{ ... }` — constraint block

A brace block contains comma-separated entries.

Examples:

```lattice
{mode=readonly}
{mode=preview, tone=warm+firm}
{mode=readonly, assume:market_stable}
```

Entries use either:

```text
key=value
key:value
```

The difference is intentionally narrow in v0.1:

- `=` is a direct value assignment;
- `:` marks an annotation/classification relationship.

Both compile into structured packet fields according to the recognized key vocabulary.

Recognized core keys include at least:

- `mode`
- `tone`
- `assume`

Unknown keys MAY be retained as constraints or namespaced extensions. They MUST NOT be allowed to override core permissions by using a misleading synonym.

### 6.2 `[ ... ]` — scope

Immediately after a target, a bracket block scopes that target.

Examples:

```lattice
@sales[-4Q]
@product_launch[next_Q]
```

The grammar supports identifiers, strings, numbers, signed period literals, key/value filters, and explicit alternatives inside a scope.

The protocol does not claim universal semantics for units such as `Q` or `M`; a host or domain vocabulary is responsible for interpreting a scope literal. The parser's responsibility is to preserve it deterministically.

### 6.3 Brackets in evidence/context forms

Brackets also occur in named constructs such as:

```lattice
because[...]
assume[...]
challenge[...]
```

The enclosing keyword determines their role. A parser MUST NOT treat every bracket pair as target scope.

---

## 7. Output syntax

### 7.1 `->` — requested output

Syntax:

```lattice
-> <format>
-> <format>@z<n>
```

Examples:

```lattice
-> brief@z2
-> recommendation@z4
-> explanation@z2
```

`->` expresses the desired response representation. It does not itself create a side effect.

### 7.2 `@z<n>` — semantic zoom

Core values:

| Token | Canonical value | Meaning |
|---|---:|---|
| `@z0` | `0` | Signal only |
| `@z1` | `1` | Minimal answer |
| `@z2` | `2` | Concise useful answer |
| `@z3` | `3` | Working detail |
| `@z4` | `4` | Deep analysis |
| `@z5` | `5` | Full reasoning structure |
| `@zmax` | `"max"` | Maximum available expansion |

Zoom controls requested semantic depth rather than a guaranteed token count.

A consumer MAY be unable to satisfy the exact requested depth. If it reduces or cannot satisfy the requested zoom, it SHOULD make that limitation inspectable rather than silently changing the packet's requested value.

---

## 8. Confidence and approximation

### 8.1 `%` — confidence

Syntax:

```lattice
%0.82
```

The numeric value MUST be between `0` and `1`, inclusive.

At the end of a packet-level clause set, `%value` maps to packet-level `confidence.value`.

A future vocabulary may define relation- or claim-specific attachment. Until then, a parser MUST NOT guess a more specific attachment when the syntax is ambiguous.

### 8.2 `~` — approximate/uncertain modifier

Syntax:

```lattice
cause~
```

`~` modifies the immediately preceding term. It signals that the term is approximate, provisional, fuzzy, or uncertain.

It does not supply a numerical probability. If both `~` and `%` are present, both MUST be preserved.

---

## 9. Macros

### 9.1 `#` — macro reference

Example:

```lattice
#Decision
```

Macro reference syntax is defined in v0.1 so it can be parsed and inspected. Macro expansion is a Phase 3 responsibility.

An unresolved macro MUST NOT be silently replaced with guessed content.

### 9.2 `def` — macro definition form

Example:

```lattice
def #Decision = {
  options + criteria + tradeoffs + reversibility + risks + recommendation
}
```

`def` is a reserved keyword, not an operator glyph.

A Phase 2 parser MAY construct an AST node for a definition. It does not need to execute or expand the macro until Phase 3.

Macro expansion MUST remain inspectable.

---

## 10. Metadata

### 10.1 `;` — metadata delimiter

Example:

```lattice
; ctx↑0
```

The semicolon begins a metadata clause. It is **not** a general statement terminator in Lattice v0.1.

This choice avoids ambiguity with the established whitepaper form.

Multiple metadata items are comma-separated:

```lattice
; ctx↑0, source=manual
```

### 10.2 Newlines

Newlines delimit top-level clauses and improve readability. They do not alter semantics where the grammar explicitly allows an inline continuation.

---

## 11. Relational and annotation delimiters

### 11.1 `=`

`=` has two stabilized uses:

1. key/value assignment in a constraint or metadata entry;
2. an explicit simple relational assignment after a target.

Example:

```lattice
!state @dog.color = blue
```

A packet compiler SHOULD represent the second form as an inspectable relation rather than as direct mutation of an object.

`=` does not imply execution or state change.

### 11.2 `:`

`:` associates an annotation key and value:

```lattice
assume:market_stable
```

It also appears in named forms such as:

```lattice
claim: ...
```

The enclosing keyword determines the canonical packet mapping.

### 11.3 Undefined relational glyphs

The whitepaper contains the draft example:

```text
claim: churn↑ <= onboarding_friction↑ %0.74
```

Neither `<=` nor the postfix trend form `↑` is defined in the whitepaper's operator table.

Therefore:

- `<=` is RESERVED in core v0.1;
- it has no core causal, implication, ordering, or comparison meaning;
- strict parsers SHOULD reject it until a relation vocabulary defines it;
- permissive parsers MAY retain it as an opaque extension operator without interpretation.

Writers SHOULD replace such draft notation with an explicit named relation, for example:

```lattice
claim: causes(onboarding_friction, churn)
%0.74
```

only when `causes` is in fact the intended relation.

The protocol specification MUST NOT infer that intention from the undefined glyph.

---

## 12. Delimiter precedence and lexical disambiguation

The tokenizer MUST apply longest-token matching for multi-character tokens.

Minimum ordering:

```text
"!!" before "!"
"::" before ":"
"->" before "-"
"@zmax" / "@zN" recognized in output position
"↑" + DIGITS recognized as context reference
```

Recommended expression precedence, highest to lowest:

| Precedence | Constructs |
|---:|---|
| 1 | references, literals, function calls, parenthesized expressions, macro refs |
| 2 | postfix `~`, attached `%confidence` |
| 3 | unary exclusion `-` |
| 4 | composition `+` |
| 5 | alternative `|` |
| 6 | relational assignment `=` / annotation `:` in positions permitted by grammar |
| 7 | `::` operation delimiter |
| 8 | `->` output delimiter |
| 9 | `;` metadata delimiter |

`::`, `->`, and `;` are clause delimiters rather than ordinary expression operators; the precedence table documents parser binding, not algebraic meaning.

---

## 13. Reserved characters

The following glyphs are reserved for protocol evolution or extension vocabularies and MUST NOT receive implicit core semantics solely because they appear in draft prose:

```text
<=  >=  =>  <=>  &&  ||  ^  ↓
```

An implementation MAY expose a permissive extension mode that tokenizes them, but core semantic compilation MUST require an explicitly registered vocabulary.

---

## 14. Strings and identifiers

### 14.1 Encoding

Lattice text files MUST be UTF-8.

String literals MAY contain Unicode.

### 14.2 Core identifiers

For parser portability, core unquoted identifiers use:

```text
[A-Za-z_][A-Za-z0-9_-]*
```

Qualified identifiers use dot-separated core identifiers.

Examples:

```text
sales
agent_risk
product-launch
dog.color
```

Human-language labels that do not fit this lexical form SHOULD be written as strings or represented as atom values rather than forcing them into the identifier grammar.

This restriction applies to symbolic names, not to natural-language content carried in strings or external referenced data.

---

## 15. Permission mode tokens

The following values are reserved core permission values when used as the value of `mode`:

```text
readonly
preview
sandbox
confirm
commit
auto
advisory
reply_or_explain_only
```

A parser MUST reject an unknown value when compiling `mode` into the core `permissions.mode` field.

A host-specific mode MUST NOT masquerade as a core mode. It belongs in a namespaced extension and cannot override core safety behavior.

---

## 16. Examples

### 16.1 Read-only analysis

```lattice
!analyze @sales[-4Q] :: cmp(region) + detect(anomaly) + infer(cause~)
{mode=readonly, assume:market_stable}
-> brief@z2
%0.82
; ctx↑0
```

### 16.2 Preview

```lattice
!email @client :: propose_meeting
{mode=preview, tone=warm+firm}
-> draft@z2
```

### 16.3 Context reference

```lattice
?risk ↑2@agent_risk
-> summary@z2
```

### 16.4 Explicit relation without undefined glyphs

```lattice
!state @dog.color = blue
{mode=reply_or_explain_only}
-> explanation@z2
```

### 16.5 Advisory decision

```lattice
!decide @product_launch[next_Q] :: eval(demand + readiness + legal_risk + support_burden)
{risk_tolerance=med, mode=advisory}
-> recommendation@z4
```

---

## 17. Parser requirements

A conforming strict parser MUST:

- tokenize multi-character operators by longest match;
- preserve UTF-8 string content;
- distinguish target `@name` from zoom `@zN` by grammatical position;
- distinguish `↑n` from undefined postfix arrows;
- distinguish scope `-4Q` from expression exclusion `-term`;
- reject confidence outside `[0,1]`;
- reject zoom values outside `0..5` except `max`;
- reject unknown core permission modes;
- preserve unresolved macro and context references without inventing their values;
- reject undefined core operators such as `<=` in strict mode;
- produce an error rather than silently changing permission semantics.

---

## 18. Relationship to `grammar.ebnf`

`spec/grammar.ebnf` is authoritative for syntactic acceptance.

This table is authoritative for the intended core meaning of accepted operator tokens.

If the grammar accepts a syntactic extension that this table does not assign core semantics, the result MUST remain an extension or unresolved AST construct until a vocabulary defines it.
