# Generic-Core Consolidation Dose Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before implementation.

## Predecessor

On 20 fresh randomized key-door tasks, immediate hard consolidation at the
first causally mature composite improved old-regime joint success from a median
of 0.0 to 0.803711, but reduced new-regime success from 1.0 to 0.645508. The
hard-freeze package therefore falsified binary scale 0.0 while showing that the
learner-local maturity event causally controls the stability-plasticity tradeoff.

## Hypothesis and strongest null

Hypothesis: an intermediate post-maturity shared-learning scale will retain the
old anonymous regime while preserving enough plasticity to acquire the new one,
with both behaviors remaining dependent on self-grown composite topology.

Strongest null: the apparent endpoint tradeoff has no useful coexistence region;
every reduced scale either forgets the old regime, impairs the new regime, or
passes only through random task variation, topology leakage, unequal experience,
or a post-hoc choice among doses.

## Exactly one scientific factor

Four arms use the same task, observations, actions, rewards, trace lifetime,
topology budget, maturity rule, training budget, and evaluation budget. The only
changed factor is `shared_learning_after_maturity_scale`:

- 0.10;
- 0.25;
- 0.50;
- 1.00, the renewable-topology control.

The scale applies only to shared bias and primitive-weight updates after the
first causally mature composite in an action channel. Candidate weights remain
plastic. No replay, phase event, external freeze, target network, reward change,
extra operator, or learner-visible task identity is added.

## Learner/laboratory boundary

The learner receives anonymous literals, its selected action, the resulting
transition, and terminal +/-1 valence. It does not receive regime, phase,
correctness, hidden mappings, evaluation status, seed, or dose identity. The
laboratory constructs randomized tasks, changes regime after the frozen budget,
evaluates both regimes without learning, and adjudicates the frozen gates.

## Frozen environment and budget

Run once on 20 fresh seeds 20261301--20261320, excluded from all earlier generic
packages. For every seed and arm:

- 4,096 regime-0 episodes followed by 4,096 regime-1 episodes;
- no regime-0 replay and no boundary notification;
- 512 untouched evaluation episodes per regime;
- anonymous observable regime terminal, two learner-selected actions, and one
  action-dependent transition per episode;
- epsilon 0.15, discount 0.97, terminal-only +/-1 valence;
- learning rate 0.08, proposal interval 128, support 16, burn-in 8,
  32 confirmations, causal margin 0.01, resource cost 0.002, expiry 512;
- at most four live and 64 total proposals per action channel;
- identical random seed and stochastic-call budget across the four arms.

Reuse and hash the frozen key-door, renewable-topology, and local-consolidation
runners. This is a development dose-selection package, not confirmation.

## Measurements and invariant gates

Record per task, regime, and dose: joint/key/door performance; full versus
composite-disabled behavior; mature contextual pairs; first maturity time;
shared and candidate updates after maturity; live/total candidate counts;
graph-selection/update parity; trial-root leakage; experience, action, and RNG
budgets; task manifests and all relevant source hashes.

Every eligible non-control dose must satisfy all of:

1. median joint success at least 0.85 in each regime;
2. median key accuracy at least 0.90 in each regime;
3. old-regime joint success greater than the 1.00 control on at least 16/20
   paired tasks;
4. new-regime median joint success no more than 0.05 below the 1.00 control;
5. mature regime-1 contextual pair on at least 16/20 tasks;
6. median across-task mean full-minus-composite-disabled joint effect at least
   0.15;
7. at least one matured channel and post-maturity candidate updates on every
   task;
8. shared update events after maturity are nonzero in every positive-scale arm;
   the configured multiplier semantics remain covered by the frozen lifecycle
   tests (event counts are not treated as update magnitudes);
9. proposal/live bounds, graph parity, trial isolation, experience, action, and
   RNG equality pass on 20/20 tasks.

## Frozen deterministic selection

First discard every non-control dose failing any eligibility gate. If none is
eligible, the package is negative and selects no dose. Otherwise select the
eligible dose maximizing
`min(median_regime_0_joint, median_regime_1_joint)`. Break an exact tie by the
larger arithmetic mean of those medians, then by the larger scale (retaining
more plasticity). The 1.00 control is never a selected consolidation dose.

Per-dose means, task-level paired differences, and the dose-response curve are
descriptive diagnostics only. They cannot override the rule. A selected dose is
a development candidate for later fresh sealed confirmation, not a proven law.

## Predictions, kill criterion, and transfer freeze

Prediction: scale 0.10 or 0.25 will lie nearest the coexistence region; 0.50 may
retain too little old behavior, and 1.00 should reproduce catastrophic old
forgetting. A smooth old-down/new-up dose response would support a real local
plasticity mechanism even if no dose clears every coexistence gate.

The package is killed by no eligible dose, any invariant failure, a runner/code
change after tasks are generated, or reuse/viewing of a frozen seed before the
committed execution. Commit and push this contract and the runner, pass the full
generic-core suite, then execute exactly once. No result authorizes automatic
tuning, adaptive consolidation, replay, or KRK transfer. Frozen confirmation and
an explicit integration package are required before any KRK claim.
