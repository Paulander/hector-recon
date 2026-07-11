# Generic-Core Policy/Credit Work Package

Date: 2026-07-12. Track: generic-core science. Status: frozen development
contract; no KRK autonomy or confirmation claim.

## Factor A: policy-prediction identity

Hypothesis: learning is incoherent when TD subtracts a private exact-cell value
but action choice ranks a different graph output. Supplying the exact graph
score that confirmed the acted branch as the TD prediction will make the score
used for choice move toward the observed target.

Strongest null: graph-score prediction changes bookkeeping only; the broad M3
update still fails to move the chosen graph output toward its target, or causes
equal/opposite movement in unrelated actions.

Changed factor: optional explicit prediction supplied to the generic intrinsic
credit transition and consumed by the native observed-action path. No feature,
pool, reward, topology, availability, curriculum, or learning-rate change.

Boundary: the prediction is learner-visible graph output. The laboratory may
assert direction-of-change in tests but supplies no correct action.

Predictions:

- positive terminal target: chosen graph score increases;
- negative terminal target: chosen graph score decreases;
- `CreditEvent.predicted_value` exactly equals the pre-update graph score;
- unrelated masked branches do not receive direct exact-triplet credit.

Kill criterion: any identity/direction test fails, or the implementation must
read a solution label to obtain the prediction.

Budget: focused unit tests plus one tiny randomized generic benchmark. No KRK
training rerun is authorized by this factor.

## Factor B: rare-refutation lower tail

Hypothesis: a graph-local empirical return distribution with retained
catastrophic outcomes will prefer a consistently adequate option over an option
with higher mean return but a rare catastrophic response.

Strongest null: lower-tail selection differs only because the benchmark exposes
the answer, fails under shuffled action identities/response order, or requires a
task-specific catastrophe label.

Changed factor: scalar return aggregation only—mean versus preregistered lower
quantile. Outcomes remain generic scalar valence.

Predictions across randomized seeds:

- mean selector prefers the usually-good/refutable option;
- lower-tail selector prefers the consistently adequate option after observing
  the refutation;
- before the refutation, the robust selector remains uncertain rather than
  claiming knowledge;
- action IDs and response order do not change the verdict.

Kill criterion: fewer than all frozen randomized instances show the predicted
mean/lower-tail disagreement after identical observations.

Budget: 20 randomized instances, no parameter tuning after results.

## Factor C: delayed-fork eligibility

Hypothesis: beginning eligibility once per real episode allows terminal-only
outcome to update the early branch responsible for a 4–6 step delayed fork.

Strongest null: the early branch receives no credit, or receives identical
credit when eligibility is incorrectly reset every step.

Changed factor: episode boundary only. Reward and graph remain fixed.

Predictions:

- persistent episode trace gives the first branch a nonzero signed update;
- per-step reset removes that delayed update;
- randomized action identities and delays 4–6 preserve the result.
