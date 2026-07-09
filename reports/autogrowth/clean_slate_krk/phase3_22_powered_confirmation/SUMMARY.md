# Phase 3.22 Powered Confirmation Summary

- Artifact: `reports/autogrowth/clean_slate_krk/phase3_22_powered_confirmation/summary.json`.
- Run: 5 seeds, full persistent ladder, outcome auditions, G/L dose arms, predicate-eval guard permanent.
- Stop status: 5/5 seeds completed; no population, gate regression, audition starvation, or scheduled-unjudged stop.
- Constructed conditional-gate move-flip proof: passed.
- Seed33 instability: did not recur; artifact diagnosis is mechanism divergence from 3.20, not an observed unpinned RNG replay.
- Validation source: 512-row samples from the standing recent exact-stratified train split; gate heldout untouched.
- Limitation: no standalone recent Stage A/B generator exists here, so rows were not freshly regenerated.
- Nominees tested: 165 probation records; Stage A 33, Stage B 132.
- Power: adequate-power nominees 0/165.
- Firing support: runtime firing rows histogram = 0:68, 1-2:56, 3-7:37, 8-15:4; max 9.
- Arm G confirmations: 0; Arm L confirmations: 0.
- Guard: 1256 combined G/L dose-arm predicate-eval failures.
- G signal: nonzero discordant dose tests exist, but all are underpowered or guard-voided.
- L signal: essentially flat; no confirmation.
- Heldout confirmed-cell ablation: none, because no cells confirmed.
- Interpretation: powered confirmation did not validate either routing channel, but also did not produce an adequately powered rejection.
- Boundary finding: exact habitat/source-signature cells are too sparse under the current validation supply.
- Next: repair habitat coverage or source-signature granularity before treating G/L inertness as a real decision-relevance result.
