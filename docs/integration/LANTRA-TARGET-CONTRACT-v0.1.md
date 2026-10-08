# LANTRA ↔ LSTP v0.1 — Candidate supervised-target contract

**Status:** experimental integration contract; not a frozen LANTRA training authorization.
**Protocol authority:** `docs/LSTP_Whitepaper.pdf` > root README > `spec/` > code.
**Protocol:** LSTP v0.1; examples and targets must be generated and validated with
a pinned LSTP commit. This document does not amend normative Octad semantics.

## Dataset JSONL format

One UTF-8 JSON object per line, with exactly four string fields:

```json
{"sample_id":"sample-001","split":"train","input":"Summarize the report.","target":"<canonical LSTP JSON string>"}
```

The angle-bracket target in this **schema illustration is not a real target**.
Real `target` strings MUST be produced by `lstp.canonical_dumps(packet)`
and validated with `lstp.canonical_loads(target, require_canonical_bytes=True)`.
The `input` is source text and is not trusted as executable instructions.
IDs identify dataset examples, not authenticated packet producers. Splits are
`train`, `validation`, `test`. A sample must not occur in multiple splits.

Usage, after installing the LSTP package:

```bash
python tools/check_lantra_targets.py data/lantra_lstp.jsonl --require-all-splits
```

The preflight fails closed on invalid JSON, extra fields, empty targets, wrong
protocol versions, non-canonical bytes, broken relations, duplicate examples,
cross-split identical prompts and invalid references. It reports dataset digest,
counts and bytes. A green preflight **does not** certify factual annotation
correctness, model learnability or training authorization.

## Training integration boundary

The existing SLAI `run_lstp.py` is a `LanguageAgent →
LinguisticFrame → Octad` adapter. It is not a LANTRA training pipeline. The
LANTRA training owner MUST define and test the following against its real
model/tokenizer implementation before training:

1. Pin an exact LSTP commit, dataset schema/profile and tokenizer revision.
2. Reconcile tokenizer context and special tokens; report actual target token counts.
3. Construct teacher-forced causal examples with explicit prompt/response
   boundaries and loss masking restricted to desired target tokens.
4. Keep random IDs, host-supplied transport fields and trusted authorization
   contexts outside learned authority decisions.
5. Decode generated targets with the strict canonical parser; count malformed
   outputs, retries, latency and repair attempts, including failures.
6. Test actual optimizer step, backward pass, checkpoint save/load, resumed
   optimizer/scheduler state and evaluation on held-out examples.
7. Compare matched LANTRA baseline natural language, generic JSON, constrained
   JSON, reduced LSTP and full LSTP on identical semantic examples.
8. Keep the language model at **zero trusted execution authority**. Tool
   execution requires host-side authorization of a concrete operation.

Do not substitute `modules/model_trainer.py` from the currently connected
SLAI `main`: that module operates classical scikit-learn models, not the
LANTRA_42M–1B transformer family.

## Pilot acceptance

Training remains NOT AUTHORIZED until clean Python/JS release checks, package
smoke checks, semantic regressions, actual SLAI cross-repository execution and
a real LANTRA tokenizer/forward/backward/resume/evaluation pilot have been
verified and recorded. No model-quality claim is implied by the data preflight.

LSTP `docs/program/readiness.json` remains the only canonical protocol
release ledger. This document is the LANTRA integration evidence checklist and
must not be treated as a parallel release authority.
