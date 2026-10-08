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


## Versioned training representation profile: `lantra-lstp-json-v0.1`

**Representation decision (frozen for engineering evaluation, not training authorization):**
the learner-visible target is the exact UTF-8 text of the canonical JSON
serialization of a semantically valid LSTP v0.1 `PacketEnvelope`. The source
of truth is `lstp.canonical_dumps`; no separately handwritten JSON dialect,
compact-Lattice aliases, schema coercions, or lossy field projections.

This is a **single canonical profile** for 42M–1B LANTRA experiments.
Model-size-specific curricula MAY vary complexity and dataset sampling, but
MUST NOT reinterpret protocol fields or introduce divergent wire formats.

### Contract identification and pinning

- Profile ID: `lantra-lstp-json-v0.1`.
- Protocol version: `0.1` (reject all others).
- Package version at this candidate stage: `0.1.0a1`.
- Implementation revision: full SHA of the final reviewed release commit,
  recorded in the run manifest before any examples are built; do not use
  floating `main` at training time.
- Tokenizer revision: immutable tokenizer artifact digest, recorded with its
  vocabulary size, special-token mapping, normalizer and pre-tokenizer.
- Dataset digest: SHA-256 over original JSONL bytes in their read order,
  recorded alongside train/validation/test split counts.
- Examples must pass the existing `tools/check_lantra_targets.py` preflight.
- Changes to canonical semantic fields or their interpretation require a new
  profile version and regeneration/validation of training targets.

### Target and host-ownership boundaries

The dataset `target` string is the **full canonical packet**. In generation,
the host may deterministically supply immutable envelope fields before
validation, but it MUST NOT re-interpret or repair model-generated semantic
fields without labeling that transformation and counting its cost.
Model predictions have zero authorization authority. The host authenticates
actors, authorizes operations, assigns packet IDs, enforces replay prevention
and performs side effects. Never train the model to grant itself host authority.

For controlled evaluation, prefer packets with empty canonical permissions
and stable, deterministic test IDs. Context, provenance, entity IDs, relations
and confidence must be retained and checked; do not remove them to improve
apparent parse success. Untrusted model-produced evidence is a **claim of
source**, not authenticated proof of provenance.

### Teacher-forced causal objective

The LANTRA trainer MUST provide an explicit boundary separating conditioning
tokens from target tokens. For a sequence `prompt || target || eos`, loss
labels are `-100` for prompt/padding and target token IDs for the answer
(including EOS when present). Verify that causal shifting is handled exactly
once by the model/trainer and that labels are aligned with target tokens.

Tokenizer special tokens, exact prompt template, EOS behavior and maximum
length are integration-specific and **not frozen here** because the real
LANTRA tokenizer/trainer is absent from the connected SLAI `main`. Do not
invent reserved token IDs or claim tokenizer compatibility prematurely.
Any truncated target is invalid; fail preflight rather than training against
partial canonical JSON.

### Generation and decoding

The default acceptance path is strict
`canonical_loads(generated_utf8, require_canonical_bytes=True)`, followed by
semantic validation. Measure both strict byte-canonical success and
parseable-but-noncanonical outputs separately. Host-side canonicalization of
otherwise valid outputs is a recorded repair, not a free success. Wrong
versions, unknown fields, broken references, permission escalation or
malformed Unicode must be rejected. Count failed attempts and repair latency.

### LANTRA pilot completion proof

A real pilot must report: model implementation SHA; tokenizer revision and
digest; LSTP profile and pin; dataset/splits/digest; forward loss; backward
gradient norm; optimizer and scheduler step; pre-save and post-resume step;
model/optimizer/scheduler/RNG checkpoint state; numerical comparison between
continuous and resumed training at deterministic tolerance; held-out
evaluation; strict LSTP decode and malformed output rejection. A synthetic
tokenizer or toy neural net cannot satisfy the **LANTRA pipeline** gate.

**Freeze status:** this document freezes the **wire target profile** for
further verification. The **full training interface** is deliberately
UNFROZEN until the actual LANTRA tokenizer, prompt template, masking,
checkpoint and resume contracts are inspected and tested. This is not a
`TRAINING AUTHORIZED` signal.
