# Native R0 competence-envelope V3B seed-robustness preregistration

Date: 2026-07-17
Status: frozen before seed generation
Source: canonical V3 commit `c377378`

## Objective and fixed scope

V3B adjudicates whether V3's content-blind nomination failure is robust to the
member-choice genome seed. It changes no responsibility mechanism and makes no
learner repair.

Replay the exact 64 persisted V3 signal/outcome rows. Do not query boards or
access validation, regression, the 65 retired successors, R1, final, or fresh
data. Preserve V3 and its artifact byte-for-byte. Do not change learner source,
thresholds, capacities, request order, lifecycle, or outcome-shuffle control.

Each genome seed runs a matched pair:

1. connected actual outcomes;
2. the frozen V3 outcome-shuffled permutation.

Engagement means at least one cell reaches the learner's frozen MATURE state.
Every seed and both organisms are retained regardless of outcome. No seed may be
selected for continuation.

Hypothesis: V3's frozen content-blind genome can nominate and mature selective
competence cells under a robust majority of cryptographically chosen seeds,
while the matched outcome-shuffled control rarely engages. Strongest null: the
canonical V3 engagement was a seed accident, or shuffled outcomes engage at a
similar rate, so the frozen mechanism does not discriminate real local outcome
structure reliably.

Predicted outcomes are either (a) discrimination and reliability both pass,
(b) discrimination passes but reliability fails (capable but too stochastic),
or (c) discrimination fails. The kill criterion is completion of all 32 matched
pairs or any integrity failure; no observed arm outcome authorizes a repair or
selective rerun. The compute budget is exactly 64 three-round organisms plus
focused pre-cohort tests and one post-cohort full suite. There is no transfer
test and no authorization to open downstream data in V3B.

## Seed manifest law

The preregistration and runner must be committed and pushed before generating
seeds. Generate exactly 32 unique seeds from the pushed preregistration commit
and ordinals 0--31 using SHA-256. Seeds 1--1000 are forbidden because external
audit already explored them. Any excluded value or collision is rederived with
an explicit counter. Persist the ordinal, counter, full derivation digest, and
integer seed. Commit and push the complete manifest before executing any arm.

## Frozen factors

- source V3 artifact SHA-256:
  `91b3ae80773f2c2dd20cd00b82f5a1fde8190deef670623ea9ba39db9d514d94`;
- source 64-row digest:
  `f70b28153ba01ab7d6549de36b670fd5f356906f7514fbbbfcef2b3457ced34d`;
- learner source SHA-256:
  `65dda4f09bc1181a6fe3780c27b56da4fc888a377ae3cfffe3c728e9d11d2a7b`;
- V3 outcome permutation digest:
  `501f16f2cce5cfff487152ed5a444ecadb7ebc76e29fdc032c9b6f016df90d0e`;
- support 4, Wilson z 1.6448536269514722, lower bound 0.55;
- positive/refuted capacities 32/32, trial/proposal caps 192/192;
- exactly three structural rounds and fixed request order.

The only paired factor is the cryptographically derived content-blind genome
seed. The same seed is used in connected and shuffled arms.

## Preregistered gates

Report these independently.

Mechanism discrimination passes only if all hold:

- connected engagement >= 24/32;
- shuffled engagement <= 6/32;
- connected-only minus shuffled-only >= 20 paired seeds.

Reliability passes only if connected engagement >= 28/32.

A discrimination pass with reliability failure means “capable but too
stochastic.” It does not prove a residual-responsibility mechanism necessary.
V3B contains no such mechanism.

## Per-seed persistence

For both arms persist:

- full compressed organism manifest, including empty envelopes;
- first maturity round;
- singleton/pair/triple and contextual nomination counts;
- mature-cell count, polarity, support, failures, and raw members;
- training coverage;
- raw pattern identities and exact 64-bit activation masks;
- unique activation-mask groups;
- minimal versus strict-superset-redundant compositions;
- raw duplicate rejections, member-order-canonical duplicate groups, and
  order-sensitive missed duplicate admissions;
- before/after exact state digests around the read-only audit; and
- connected/shuffled paired engagement category.

The existing order-sensitive conjunction deduplication remains untouched.
Canonical V3 was unaffected. V3B records its consequences as audit statistics.

Checkpoint after every complete paired seed. Resume only a verified contiguous
prefix. Never selectively rerun or omit a seed.

## Closure

Run focused tests once before the cohort and one full repository suite after it.
Close after adjudication. Add a superseding ledger interpretation without
rewriting or retiring the canonical V3 artifact.
