# Final KRK ecological closure preregistration

Status: frozen before fresh-pool generation or execution of an experimental arm.

The question is whether outcome-only ecological learning in the frozen KRK host can turn exact point cells, signature-coarsened cells, or content-blind widened cells into a causal held-out improvement, and whether widening is selective relative to a population- and firing-matched random merge. This is not a test of ReCoN's already-demonstrated authored representational ceiling and cannot certify a fully autonomous hierarchy.

The machine contract is `preregistration.json`; if this summary and that file differ, the JSON controls.

## Frozen experiment

- Five paired seeds: `20273101` through `20273105`; frozen flat-host seeds cycle through `20272911`, `20272912`, and `20272913`.
- Fresh, orbit-disjoint TRAIN, VALIDATION, and FINAL-TEST pools contain 256 rows each. Each split has exact white-king/black-king Chebyshev-distance quotas across distances 3–7. Exact FENs and canonical D4 orbits used by named prior KRK pools are excluded.
- TRAIN alone supplies episodes, births, resources, XP, weights, and candidate construction. VALIDATION alone supplies detectability checks, random firing-rate matching, route/dose selection, and the final configuration freeze. FINAL-TEST is sealed before selection and is touched at most once.
- A game runs for at most 128 plies with the frozen white host and one declared deterministic-greedy Black policy. Only the actual terminal result supplies credit: win `+1`, draw or horizon `0`, loss/catastrophic endpoint `-1`. Recognizers, stage labels, authored skill confirmations, exact move validators, and imagined confirmations cannot affect learning, survival, selection, or analysis inclusion.
- Point cells require an exact generic percept signature and both learned child keys. Signature-coarsened cells remove the signature equality while retaining both keys. Widened cells deterministically merge outcome-nominated prototypes, use at most six child keys, and confirm at content-blind quorum `k=2`. Random controls have the same population, `n`, `k`, and validation firing-rate target, but their children are seeded draws from frequency-matched learner-visible keys.
- `G` is a single off/on binary eligibility comparison. `L` is additive routing at fixed doses `x1`, `x3`, `x9`, and `x27`. Every arm restores the same immutable snapshot and reacquires cells by stable ID before applying an intervention.

## Gates and stopping

Measurement requires exact baseline/no-op parity, common snapshots and provenance, observed live interventions, predicate-evaluation evidence, and a successful constructed routing ceiling. A cell is detectable only with at least eight evaluated firing rows; a topology is adequately detectable only when at least one cell qualifies in at least three of five seeds.

Validation freezes one configuration per topology using the declared lexicographic rule. FINAL-TEST remains sealed unless measurement passes and at least one non-random topology has adequate detectability, favorable discordant balance, a paired Wilson balance interval above 0.5, and a Holm-adjusted one-sided sign-test `p <= 0.05` on VALIDATION.

On FINAL-TEST, the causal gate additionally requires a conservative paired non-inferiority lower bound of at least `-6/256`. Widening is selective only if its paired comparison with the matched-random arm passes the same positive-balance and Holm requirements. The full primary family and tie rules are frozen in the machine contract.

If outcome-only credit produces no candidates or inadequate support, that is reported as ecological starvation/under-detectability, not as a causal null. If all non-oracle arms are flat with adequate support, the result is a detectable null. A failed no-op or constructed ceiling invalidates the experiment. Whatever happens, this is the only v1 KRK closure; KRK then freezes as a regression/transfer benchmark and the next research question moves to KPK.
