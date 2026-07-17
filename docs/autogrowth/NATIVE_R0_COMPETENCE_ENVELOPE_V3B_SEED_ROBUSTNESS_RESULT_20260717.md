# Native R0 competence-envelope V3B seed-robustness result

V3B completed the preregistered 32-seed matched cohort with every organism
retained. Both mechanism-discrimination and reliability gates passed.

## Freeze and integrity

The runner and preregistration were committed and pushed first at `28cb2c4`.
Only then were 32 unique genome seeds derived by SHA-256 from the full pushed
commit plus ordinal. All seeds exceeded the externally explored 1--1000 range.
The complete manifest was committed and pushed at `52ce849` before either arm
ran.

- seed-list digest: `22c4f372d255cea4576ef9d8d70e35189ce6eb4d71c2284bf1f7f98343dc63e1`;
- canonical V3 artifact remained byte-exact;
- frozen learner and 64 signal rows remained byte-exact;
- connected and shuffled used the same seed and request order per pair;
- all non-seed configuration fields matched V3;
- all 64 read-only audits had identical before/after pickle and manifest
  digests;
- all 64 full envelope organisms, including non-engaged envelopes, restored
  exactly from compressed pickle;
- validation, regression, retired successors, R1, and fresh data were not
  accessed.

## Preregistered verdict

| Measure | Required | Observed | Gate |
|---|---:|---:|---|
| Connected engagement | >=24/32 | **31/32** | pass |
| Shuffled engagement | <=6/32 | **0/32** | pass |
| Connected-only minus shuffled-only | >=20 | **31** | pass |
| Connected reliability | >=28/32 | **31/32** | pass |

Paired outcomes were 31 connected-only, zero shuffled-only, zero both, and one
neither. The sole non-engaging connected organism was ordinal 13, seed
`4017493945575328316`.

Mechanism discrimination therefore passed, and reliability independently
passed. The preregistered interpretation is
`content_blind_seed_robust_and_discriminative`.

## What grew

The 31 engaged connected organisms matured 117 cells in total; every mature
cell was positive/AVAILABLE with zero failures. First maturity occurred at
review 2 for 13 seeds and review 3 for 18. Connected mature-cell counts ranged
from 1 to 25. The connected organisms covered between 1 and 35 of the 64
training rows when engaged; the single non-engaging organism covered zero.
Every shuffled organism matured zero cells and classified all rows outside a
mature envelope.

Per seed, the artifact retains raw member identities, exact 64-bit activation
masks, unique-mask groups, pair/triple nominations, maturity round, polarity,
support/failures, coverage, and minimal/redundant composition classifications.
Across connected organisms, 3,147 learned compositions were minimal under the
exact-mask strict-subset definition and 693 were redundant strict supersets.
The corresponding shuffled counts were 3,366 and 726.

The frozen order-sensitive conjunction deduplication was not repaired. The
audit found three order-variant missed duplicate admissions across connected
organisms and three across shuffled organisms. Canonical V3 was unaffected.

## Superseding interpretation

Canonical V3 remains a valid result for its fixed seed: that seed nominated no
support-qualified pure pattern and matured no competence cell. V3B supersedes
only the broad interpretation of that event. It was not evidence that the
frozen content-blind genome generally cannot nominate useful conjunctions. On
this touched 64-row tape, 31/32 independently derived seeds matured selective
cells from real outcomes, while the identical outcome-shuffled control did so
in 0/32.

This is strong touched-training evidence that the existing mechanism is capable
and seed-robust at engagement. It does **not** establish held-out selectivity,
KRK R1 transfer, fully self-contained terminal-trace provenance, or that a
residual-responsibility mechanism is necessary. No residual-responsibility
mechanism was implemented or tested. Per the preregistration, V3B closes here.

## Artifacts

- result:
  `reports/autogrowth/native_authority/native_competence_envelope_v3b_seed_robustness.json`;
- result SHA-256:
  `90a5393e92516256b25f35f43c1a9b2355b15b0e450c2b8836989f1a9c5ce920`;
- 64 restorable organism files:
  `reports/autogrowth/native_authority/native_competence_envelope_v3b_organisms/`;
- canonical organism-index digest:
  `8762aab81cbf72440371d40fef3e4a297bf312f7754d8afb30b372ed34ce2f3e`;
- index-digest encoding: SHA-256 of canonical JSON rows containing ordinal,
  seed, arm, path, compressed SHA-256, and uncompressed SHA-256;
- observed first-organism-to-final-artifact write span: **177.18 seconds**;
- focused pre-cohort validation: **19 passed**;
- post-cohort full repository suite: **925 passed in 52m45s**.

The post-cohort suite did not alter the scientific verdict.
