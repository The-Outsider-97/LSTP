# LSTP compatibility and efficiency refinement

Date: 19 November 2026. Scope: confirmed defects and measured packet-pipeline improvements on main.

## Confirmed issues and repairs

Main at `4414a997ad602b3b4635a74c4fac7dc5d3f99108` could not import: `inference.py` imported `FIELDS` from a compact module that no longer defined it. The merged public export list also named missing incremental functions and repeated compact exports. Two specifications independently assigned L1/D1 to different wire shapes.

The codec now retains both existing profiles. `compact_dumps` defaults to flat, preserving current-main flat fixtures. `profile="typed"` and `incremental_dumps` select the nested tuples. Both loaders discriminate using disjoint arities; no slot order or fixture marker changed. Flat L1 has 12/13 elements and D1 has 3; typed L1 has 2 and D1 has 5. Unknown arities, invalid types, unknown fields and unavailable bases fail closed. Typed D1 checks both base and restored-target canonical digests. Flat D1 retains its existing base digest; neither digest authorizes a packet. Host signatures, policy and replay checks still consume complete canonical state.

Canonical input was parsed twice by overlapping public/internal validation paths. One strict decoder now performs bounded parsing, structural/type checks, Unicode/numeric checks, construction and semantic validation. Its serializer entry point enforces the same checks. Encoding and model preparation reuse a local validated mapping instead of repeatedly serializing the same packet.

The narrow action projection compares complete normalized state with its defined inverse, refusing extra semantic information. It retains a normalized source copy and its digest, protecting an accepted view from subsequent mutation of caller-owned sequences. There is no global packet-validation cache.

Compact decoding accepts semantically valid explicit optional defaults and normalizes them, as the earlier codecs did. `require_compact_bytes=True` separately rejects nonminimal encodings. All supplied and expanded data remain bounded. This avoids an unnecessary canonical re-encoding on every standalone decode without relaxing semantic validation.

## Model-facing defaults informed by the live experiment

The seven-string projection retains the exact tuple input instruction from the completed live benchmark. The selector still measures complete instructions plus payload with the caller's tokenizer. The default flat carrier instruction and the explicit typed instruction now describe their corresponding wire formats. Schema-heavy typed compact model input requires `allow_compact=True`; transport byte savings alone never enable it. Unsupported projections preserve full canonical data and use explicit field-path instructions with named JSON output by default. `ModelInput.tuple_output` identifies the actual result contract; callers may explicitly override automatic output selection. The new canonical fallback instruction has not received a new paid-model accuracy measurement.

## Recorded API evidence

These are existing live results from 18 November, not additional API calls or savings caused by today's CPU changes. The experiment contains 18,000 successful responses: 1,000 cases in each of nine conditions on each model. Models are recorded as OpenAI `gpt-6-luna` and Gemini `gemini-3.1-flash-lite`. Costs use the run's recorded nominal rates, not new price quotes or invoices.

| Model / condition | Exact matches | Combined input/output tokens | Recorded estimated USD |
| --- | ---: | ---: | ---: |
| OpenAI ordinary JSON | 1000/1000 | 281312 | 0.0647324 |
| OpenAI projection tuple | 1000/1000 | 144984 | 0.0361684 |
| OpenAI full typed compact | 979/1000 | 529849 | 0.1016541 |
| Gemini ordinary JSON | 1000/1000 | 282756 | 0.17428650 |
| Gemini projection tuple | 1000/1000 | 134744 | 0.08101850 |
| Gemini full typed compact | 998/1000 | 488839 | 0.17330475 |

Projection tuples reduced combined tokens by **48.46% / 52.35%** and estimated cost per correct task by **44.13% / 53.51%** against the original ordinary-JSON workflow (OpenAI / Gemini). Against canonical LSTP, the recorded reductions per correct task were approximately **67.20% / 67.28%** in tokens and **62.24% / 60.78%** in cost.

An equally optimized JSON tuple control has identical request content. It matched Gemini usage exactly; the small OpenAI difference and one mismatched control answer establish no intrinsic protocol advantage. Thus the original workflow comparison passes 25% on this narrow corpus, but a universal or optimized-JSON competitive claim is unproven. Full typed compact input had more tokens and worse correctness, which motivates the explicit opt-in.

## New CPU measurements

| Operation | Before (µs) | After (µs) | Time reduction |
| --- | ---: | ---: | ---: |
| canonical_encode | 241.36 | 230.97 | 4.31% |
| canonical_decode | 370.85 | 239.53 | 35.41% |
| typed_encode | 327.71 | 163.24 | 50.19% |
| typed_decode | 728.40 | 482.43 | 33.77% |
| projection | 766.83 | 309.22 | 59.68% |
| prepare_action_input | 1458.36 | 306.47 | 78.99% |

Timing uses `tools/benchmark_packet_pipeline.py` on the same 1,000 paired synthetic cases (seed 20261117), with one warm-up and five timed batches per operation. Both versions run sequentially in separate processes using the same Python/runtime/host. Values are medians of microseconds per packet across batches. Timing is sensitive to scheduling and host load; no cross-platform or end-to-end API latency claim follows.

Current main could not execute, so the comparator is the last working local implementation `29755e35ac62f62825c8524f2da3ac97d9bf9186`, corresponding to the original optimization implementation. Both versions validate 1,000 exact projections and 1,000 lossless typed-carrier round trips. Their canonical and typed payload digests must match; the attached receipts record all runs and corpus/source hashes. Request preparation intentionally omits the schema-heavy candidate by default, so its timing reflects both eliminated repeated work and the new eligible-candidate policy. Its counter measures UTF-8 bytes solely to exercise CPU work; it supplies no model-token estimate.

The corpus uses SLAI's `benchmarks.lstp.cases.generate_cases(1000, seed=20261117)`, one `Case.as_record()` JSON object per UTF-8 JSONL line. Run the tool separately with each checkout on PYTHONPATH, supplying the same `--corpus`, `--output`, `--label` and `--repeats 5`. It fails if lossless reconstruction or exact gold extraction fails.

## Verification and limits

Executed checks passed: all 361 core tests, all 361 source-distribution tests against a freshly installed wheel, 16 SLAI benchmark/adapter tests, schema checks, Ruff lint/format, strict mypy, wheel/sdist builds and the independent JavaScript verifier. Developer/build dependencies were reused locally; fresh online dependency resolution and the full OS/Python matrix are not claimed.

Verification receipts are in [program/evidence/refinement-2026-11-19](program/evidence/refinement-2026-11-19/). Regression coverage includes public exports/imports, both existing wire profiles, explicit optional defaults, exact base recovery, corrupt typed target digests, bool-versus-number preservation, expanded resource limits, strict types, duplicate rejection, one JSON parse, one preparation validation snapshot, mutable source ownership and the exact measured tuple prompt.

This refinement does not certify an absence of every possible defect. The existing readiness ledger still records VERIFY-001, DOC-001 and REL-001: full supported-platform release evidence, publication reconciliation, and independently validated SLAI/LANTRA pilot/training acceptance require their own evidence. Today's engineering, package and finite-number JavaScript checks do not imply that those broader gates have closed. No new paid API requests were made.
