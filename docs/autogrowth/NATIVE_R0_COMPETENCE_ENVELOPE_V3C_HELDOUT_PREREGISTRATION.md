# Native R0 competence-envelope V3C held-out cohort preregistration

Date: 2026-07-18
Status: frozen before any envelope-held-out frame execution
Source commit: `152fc01c165f64d9fe87e3d9ddf2fb0dd2c2151a`

## Purpose and strongest null

V3C is inference-only. It tests all 32 connected and all 32 outcome-shuffled
V3B competence envelopes on envelope-unseen historical R0 validation contexts
and, only if a validation transfer gate passes, the unchanged historical R0
regression contexts.

Hypothesis: connected envelopes contain outcome-selective abstractions that
transfer beyond their 64 training rows without false AVAILABLE emissions. The
strongest null is that mature cells are training-local or overgeneralize, so
fewer than 24 connected envelopes recognize any held-out success or any
connected envelope emits AVAILABLE on a held-out noncompletion.

These are **envelope-held-out historical pools**, never fresh pools. V3C makes
no project-fresh, terminal-trace-native, native R1, or end-to-end KRK claim.

## Frozen information boundary

The inference organism is the exact frozen R0 snapshot plus one persisted V3B
envelope. Every one of the 64 V3B envelope artifacts is retained. Connected
ordinal 13, seed `4017493945575328316`, remains included despite having no
mature cell. No seed selection, ensemble, voting, cell union, averaging, or
cohort-owned runtime decision is allowed.

The laboratory may reconstruct the hash-frozen historical pools, enumerate
rows in the fixed order, execute the graph-emitted R0 action, observe the real
completion terminal, compare real and virtual inference, and aggregate metrics.
It may not supply pool identity, expected class, correctness, mate predicates,
or reward to an envelope. It may not call the envelope classifier directly or
rewrite availability. Classification must be emitted inside
`NativeR0CompetenceOrganism.dream_session` and consumed from that session's
`EnvelopeClassification` provenance.

`extract_active_competence_signals` remains unchanged. Its reconstruction of
generic signals from board, action, and graph maps rather than an actual
frame-local terminal trace remains explicit architectural debt.

## Source and pool commitments

- V3B result SHA-256:
  `90a5393e92516256b25f35f43c1a9b2355b15b0e450c2b8836989f1a9c5ce920`;
- V3B organism-index digest:
  `8762aab81cbf72440371d40fef3e4a297bf312f7754d8afb30b372ed34ce2f3e`;
- V3B seed-manifest SHA-256:
  `4e9faa8700645de174cd8c552cf51bee4d517aa79833bff250fe789dd1530098`;
- frozen R0 pickle SHA-256:
  `bb58b7d64bd3ab5b696713a7253555e051bd0e9fdef4637db7c27e7517495eaf`;
- R0 metadata SHA-256:
  `d594fe8de89dee3b99b7c57a1cddb84949470fd91253d81f0a71a657147a348b`;
- source curriculum artifact SHA-256:
  `c55a4097547713edb5d9ef27a250bbfac62fb9886d86afae87b387b72869c792`;
- competence-envelope learner SHA-256:
  `65dda4f09bc1181a6fe3780c27b56da4fc888a377ae3cfffe3c728e9d11d2a7b`.
- V3 training-provenance artifact SHA-256:
  `91b3ae80773f2c2dd20cd00b82f5a1fde8190deef670623ea9ba39db9d514d94`.

Pool commitments, each with exactly 16 rows:

- R0 validation:
  `2100368431445bf95f045f4387858f662c4510320b12a6907cdeca1d46022599`;
- validation decoys:
  `196c5bfec16b1d5efa1f41d1a868ebf90f0401d5cc5b353c05cd4a204a5ab44f`;
- R0 regression:
  `964c8d543e03cc6d756eb0f52218133e9af95fdb6c97dc9c0aff8b8e58858f69`;
- regression decoys:
  `acdafa01d92b7ee77053de438168c828bbf94d5006cc6dfe5d0cf42299ee64e8`.

The fixed validation order is the 16 positive rows in source order followed by
the 16 validation decoys in source order. Its pre-data commitment over pool
hashes, segment ordinals, counts, and indices is
`f531156e7630950587e149c435f31994340f7eb4aeb0c31667502bfcf4ac7d76`.
The analogous conditional-regression commitment is
`24899b4a004cf68d5e4a4105ea479496d26fea884d447a105e339cf783bffee4`.
The runner records the concrete FEN-order digest after opening each authorized
split.

Positive train/validation/regression D4-orbit overlap and decoy exact/D4
overlap are descriptive provenance checks. No row is removed, regenerated, or
reordered because of overlap.

## Frozen authority path

For every row, the exact frozen R0 emits one real graph-owned action. The host
executes exactly that action on a real board clone; the observed completion
terminal supplies competence success. Each envelope is independently attached
to a newly loaded exact R0, serialized/restored as a
`NativeR0CompetenceOrganism`, and queried in fixed row order through one virtual
dream session.

Complete `GraphActuation`, including bit-exact activation, and exact active
signal identities must equal the real reference. The laboratory consumes only
the wrapper-owned classification manifest. Boolean availability injection,
direct experiment-level classification, host fallback, old weighted selection,
provider fallback, and child-priority choice fail hard.

Evaluation inserts no evidence and changes no topology, weights, credit,
lifecycle, maturity, reward, rent, or grounding. Before/after R0, envelope, and
combined-wrapper state digests must be identical. All effect attempts and dream
mutation counts must be zero.

## Admission

Each opened 32-row split requires:

- 32 graph-owned R0 policy responses with zero host fallback;
- 16 actual completions in its positive segment;
- 16 actual noncompletions in its decoy segment;
- zero real/virtual actuation or signal mismatches across all 64 wrappers;
- zero mutation, effect, injection, and authority violations.

Admission failure is an instrument/source abort. It cannot authorize repair.

## Metrics

For every organism persist TP, FP, positive UNKNOWN, safe UNKNOWN,
REFUTED-positive, REFUTED-negative, positive coverage, and selective precision.
Precision is undefined if there is no AVAILABLE output. Persist each frame's
FEN, actual outcome, wrapper state/probability/uncertainty, matching mature cell
IDs, actuation/signal digest, and parity rows. Also persist per-cell held-out
hits, per-row cohort state counts, complete per-seed confusion matrices, and
every zero-maturity envelope.

Individual strict pass is `TP >= 14/16 and FP == 0/16`. Individual safe-narrow
pass is `TP >= 1/16 and FP == 0/16`.

## Validation gates

Strict generalization requires all of:

- zero connected FP across 512 negative decisions;
- at least 28/32 connected individual strict passes;
- at most 4/32 shuffled individual strict passes;
- connected-only minus shuffled-only strict-pass margin at least 24;
- all integrity and authority gates.

Safe-narrow transfer requires all of:

- zero connected FP across 512 negative decisions;
- at least 24/32 connected organisms with at least one TP;
- connected-only minus shuffled-only safe-pass margin at least 20;
- all integrity and authority gates.

Regression opens through the unchanged path if either validation verdict
passes. If neither passes, V3C closes without regression.

## Conditional regression gates

Strict replication requires all of:

- zero connected regression FP;
- at least 28/32 connected regression strict passes;
- at least 28/32 connected organisms with combined validation+regression
  `TP >= 29/32` and zero combined FP;
- at most 4/32 shuffled regression strict passes;
- connected-only minus shuffled-only regression strict margin at least 24;
- all integrity and authority gates.

Safe-narrow replication requires all of:

- zero connected regression FP;
- at least 24/32 connected organisms with at least one regression TP;
- at least 24/32 connected organisms with nonzero TP on both splits;
- at most 4/32 shuffled regression safe-narrow passes;
- connected-only minus shuffled-only regression safe margin at least 20;
- all integrity and authority gates.

## Frozen interpretation and stop rules

- strict replication: robust envelope-held-out competence generalization, but
  not project-fresh, terminal-trace-native, or R1 evidence;
- safe-narrow replication: real abstractions transfer safely, while ecological
  coverage/generalization is binding rather than nomination;
- any held-out connected FP: training-pure conjunctions overgeneralize and
  selectivity/representation is binding;
- fewer than 24 connected organisms with any validation TP: cells are mostly
  training-local; inspect representation equivalence and terminal provenance
  before changing lifecycle or responsibility;
- any integrity/parity failure: instrument abort.

The exact compute budget is 64 wrappers times 32 validation frames and, only if
authorized by validation, the same 64 wrappers times 32 regression frames.
Parallel workers may change wall time only; every organism retains fixed row
order and is adjudicated independently. Run focused synthetic-only tests before
evaluation and one full repository suite after closure. Stop after result,
ledger update, commit, and push. No in-package repair, threshold change, new
pool, selected organism, ensemble, residual-responsibility mechanism, or R1
canary is authorized.
