# LSTP token optimization: implementation and verification

Historical offline report. See [19 November refinement](REFINEMENT_2026-11-19.md) for the subsequent live evidence and current implementation.

Date: 18 November 2026. Status: implementation verified offline; live token/cost targets remain unverified.

## Outcome

The new implementation provides a lossless compact carrier, explicit task projections, compact result decoding, content-addressed transport deltas, provider-independent input selection and cost accounting, and callable SLAI adapter entry points. It preserves complete canonical source packets for signing, replay protection and host authorization. It adds no core runtime dependencies.

The engineering runner passes schema checks, lint, formatting, strict type checking, all 338 Python tests, wheel/source-distribution builds and the independent JavaScript verifier. A fresh wheel installation passes its CLI round trip and all 338 tests from the source distribution. The SLAI benchmark/integration suite passes all 16 tests. Developer verification dependencies were reused locally; no fresh online dependency installation or final-readiness certification is claimed.

No new live model responses were collected. Network requests from the execution environment failed DNS resolution, and a local model tokenizer was unavailable. Byte measurements, deterministic extraction and mocked client tests do not establish new API savings or model accuracy.

## Source and baseline

LSTP source baseline: 8808b0980d478c732d964bde5d9af44e845c47e9. SLAI source baseline: c4ab98c3733d5f833111bc03200d669c2358e982. Work is in writable review checkouts because the G: project directories are read-only in this session. The original project folders and remote branches were not updated.

The 1,000-case corpus is reproduced with seed 20261117. Its digest remains ff36c7a544b217aac33b38424ede65e4218938e0e036fe5efcb7685fd320fc24. The historical raw logs contain 6,000 successful responses across OpenAI gpt-6-luna and Gemini gemini-3.1-flash-lite. The historical manifest incorrectly names Gemini gemini-2.5-flash-lite. The new audit groups by each row's actual recorded model and retains original files and SHA-256 digests. It does not rewrite historical model metadata.

| Historical condition | Input tokens | Output tokens | Exact matches | Recorded nominal USD |
| --- | ---: | ---: | ---: | ---: |
| OpenAI ordinary JSON | 189809 | 91689 | 1000/1000 | 0.0648254 |
| OpenAI canonical LSTP | 312176 | 129392 | 998/1000 | 0.0959136 |
| Gemini ordinary JSON | 199878 | 82878 | 1000/1000 | 0.1742865 |
| Gemini canonical LSTP | 328963 | 82878 | 1000/1000 | 0.20655775 |

These are the recorded historical text-token estimates, not invoices or new pricing measurements. Comparisons remain within each model. Original full-request scaffolding was the same across formats, and canonical JSON was already minified.

## Why ordinary JSON was cheaper

The extraction task asks for seven strings. Canonical LSTP additionally transports typed atom identifiers/kinds/roles, request and speech-act semantics, a separate goal, permissions and repeated resource scope, confidence, evidence identity/type, stable packet/thread identity, required Octad domains, version, carrier and audit structure. An action appears in both an ACTION atom and a goal; a resource appears in its atom and permission scope; case identity appears in several provenance fields. These costs buy transport/interpretation guarantees beyond the extraction rubric. Whitespace removal cannot explain a large additional gain because the baseline was already compact JSON.

The model-facing projection can retain the complete signed/authorized source at the host while presenting only the explicitly supported task fields. It verifies an inverse reconstruction of the entire canonical packet before accepting that view. Extra constraints, richer evidence, relations, uncertainty or context refuse the narrow projection. General packets remain complete canonical/L1 candidates.

OpenAI's median visible response was 188 bytes for both ordinary JSON and canonical LSTP, while mean billed output tokens were 91.689 versus 129.392. Gemini's median was 217 bytes and mean output usage 82.878 in both conditions. The older logs do not contain enough reasoning/cache detail to attribute OpenAI's difference to a particular internal mechanism. Hidden reasoning or response-token behavior is a hypothesis, not a confirmed cause.

## New measured results

| Representation | Median payload bytes | Median instruction plus payload bytes |
| --- | ---: | ---: |
| Original canonical LSTP | 618 | 1310 |
| Original ordinary JSON | 211 | 903 |
| Lossless L1 with complete schema explanation | 309 | 1639 |
| Extraction object | 188 | 387 |
| Extraction tuple | 107 | 339 |
| Equivalent ordinary-JSON tuple control | 107 | 339 |

The table counts UTF-8 content, excludes API framing and generated output, and is not a token comparison. L1 reduces median payload size by 50.0% against canonical bytes. The narrow tuple is 49.3% smaller than the original ordinary-JSON payload. However, a full L1 schema explanation makes the request larger than the original canonical request in content bytes. The selector therefore measures complete instructions and payload with a caller-supplied real tokenizer; it never selects by byte size alone.

Every one of the 1,000 L1 packets restores identical canonical bytes. Every deterministic projection matches all seven gold fields. Every projection-tuple request is byte-identical to its independently normalized ordinary-JSON tuple control. These checks validate software behavior, not language-model inference.

Median preprocessing on this host was 0.38285 ms for canonical encoding, 0.52255 ms for L1 encoding, 0.9843999999999999 ms for L1 decoding, and 1.1929 ms for strict projection. This is measurable local overhead. It does not prove the absence of end-to-end latency regressions.

Gzip reduced the canonical median to 369 network bytes; Base64 of that payload was 492 bytes. Neither is treated as model-readable compression or assigned a token-saving claim. D1 deltas include base and target digests and use a self-contained L1 fallback when their full byte cost is not beneficial. Missing, stale, corrupted and restarted contexts are covered by tests. Application dictionaries and ontology bindings retain literal meaning; no opaque inference dictionary was introduced without tokenizer/quality evidence.

## Implemented boundaries and fixes

- L1 preserves all canonical fields and generic application maps, with deterministic decoding, unknown-profile rejection and input/expanded-output limits.
- D1 reuses an explicit content-addressed base for transport/storage, never unavailable model context. It must be expanded before normal inference.
- ActionProjection retains the complete source and rejects unsupported semantics. Strict response decoding preserves all seven required values; projections cannot become authorization decisions.
- prepare_action_input compares complete canonical, L1, object and tuple requests using the host's token counter. Output tuples avoid repeated property generation and support deterministic reconstruction.
- Provider clients expose cached-input usage and requested/returned model identity. Prices are passed to the new benchmark explicitly; no provider features or universal rates enter the protocol core.
- Cost accounting includes incorrect/failed/retried attempts and unique successful tasks. Missing usage or cache prices stay unknown. Conservative reservations persist through crashes; unresolved calls are not automatically resent or counted as free. Run identities and an exclusive live-run lock protect resumes.
- The tokenizer previously looped forever when an identifier reached EOF because Python considers the empty string a substring of the allowed punctuation string. An explicit nonempty check fixes this; a bounded subprocess regression test prevents recurrence.
- Canonical decimal serialization used Decimal.normalize(), which could round exact values under the ambient precision. Context-independent trailing-zero removal fixes it and is tested under deliberately low precision.
- Existing Ruff/format/type findings were resolved so engineering verification can run. Much of the broader diff is mechanical formatting; compiler annotations/frozen literal handling and small validation/type fixes are covered by the full suite.

## Target assessment

| Requirement | Assessment |
| --- | --- |
| At least 25% lower combined input/output tokens than current LSTP | Unverified: no new provider usage |
| At least 25% lower API cost per successful task than current LSTP | Unverified: no new paid-task results |
| At least 25% lower tokens and costs than equivalent ordinary JSON | Unverified; an identical optimized JSON tuple has the same request content |
| Software information integrity and protocol conformance | Verified within the recorded tests and 1,000 exact byte round trips |
| Equivalent/better model correctness, compatibility and end-to-end latency | Unverified for the new views |
| Complete final production/pre-training release acceptance | Not claimed; the existing readiness ledger remains authoritative |

Matching an efficient JSON encoding removes LSTP-specific overhead; it cannot establish a unique advantage over an identical JSON request. For pure extraction of already structured fields, the deterministic API eliminates the model call for both LSTP and ordinary JSON. It is inappropriate to advertise that as a special protocol compression gain.

## Remaining evidence and adoption

Run the nine-condition paired live benchmark with the same two explicitly selected models and include the optimized JSON controls. It records real input, output and cached-input usage, failed attempts, correctness and costs per successful task. All five preflight checks must pass; partial/budget-limited runs cannot certify the full targets. The default conservative cap is USD 0.50 per provider and may not fund all 18,000 planned responses.

The SLAI adapter exposes callable compact transport, incremental restore, deterministic extraction and measured-request preparation. Consumers must explicitly choose the inference task and supply their model's tokenizer; existing language-agent requests are not automatically rewritten. Real independently annotated tasks, richer packets and multiple model families are still needed before general model-facing performance claims. The narrow projection intentionally falls back for unsupported packets.

Model-time ontology/context reuse, automatic provider-specific structured output, explicit cache-object creation/storage, and discounted provider Batch/Flex operation were evaluated as separate integration concerns and were not enabled or credited as savings. D1 does not implement model-memory compression. Provider discounts would need equivalent JSON controls and complete cache-write/storage accounting before any competitive claim. Current text rates and capability documentation are linked in the SLAI evaluation instructions; nothing assumes they remain universal or unchanged.

See spec/compact-json-v1.md for the mapping, benchmarks/lstp/OPTIMIZATION.md in the SLAI overlay for reproduction, and docs/program/evidence/token-optimization/ for the raw verification records. Code and apply patches are bundled for review. The package is an implemented, tested optimization change set; the requested quantitative outcome remains an open empirical gate.
