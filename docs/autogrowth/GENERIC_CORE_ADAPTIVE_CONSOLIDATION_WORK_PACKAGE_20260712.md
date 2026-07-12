# Generic-Core Adaptive Local Consolidation Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before implementation.

## Predecessor

The fixed-dose package produced an ordered stability-plasticity response but no
eligible coexistence dose. On fresh tasks, fixed scales 0.10/0.25/0.50/1.00
gave old-regime medians 0.671875/0.427734/0.211914/0.0 while every arm retained
new-regime median 1.0. The separate hard-zero package retained more old behavior
but impaired new acquisition. Constant post-maturity plasticity is therefore
causal but insufficient at the preregistered coexistence level.

## Hypothesis and strongest null

Hypothesis: shared weights need full plasticity while the first mature local
structure is still accumulating experience, followed by gradual protection as
that causally mature structure repeatedly fires. A learner-local decay driven
only by mature-composite activations will preserve both anonymous regimes better
than either permanently full or immediately reduced shared plasticity.

Strongest null: activation-driven decay merely delays forgetting, collapses to
one fixed control, uses a hidden proxy for the laboratory phase, reduces new
learning, or appears useful only through unequal compute, action leakage,
unbounded topology, or post-hoc schedule choice.

## Exactly one scientific factor

Three persistent-trace arms use identical randomized tasks:

1. fixed-full control: post-maturity shared scale 1.00;
2. fixed-low control: post-maturity shared scale 0.10;
3. adaptive: mature-activation decay defined below.

All other learner, topology, reward, experience, action, and evaluation settings
are identical. No replay, phase event, regime label, target network, external
freeze, reward change, extra composite operator, or curriculum signal is added.

## Frozen adaptive law

Add an opt-in shared-learning schedule named `mature_activation_decay`; legacy
default remains `fixed`.

For each action channel:

- before any mature composite exists, shared scale is 1.0;
- count at most one evidence unit per observation when at least one mature
  composite is active in the current anonymous atom set;
- with cumulative evidence `e`, use
  `scale = 1.0 - 0.90 * min(1.0, e / 1024)`;
- the resulting floor is exactly 0.10;
- use that scale only for shared bias and primitive-weight updates;
- trial and mature candidate weights remain at full learning rate;
- evidence never resets and no wall-clock, observation index, task identity,
  regime, action correctness, or outcome sign enters the schedule.

The activation is internal affordance evidence: the already causally mature
child structure recognizes the current context. It is not a laboratory stage
signal.

Instrument cumulative mature-evidence activations, current/minimum/mean applied
post-maturity scale, and update counts. Snapshot and artifact fields must make
the schedule auditable.

## Tests

Lifecycle tests must show:

1. default/fixed behavior is unchanged;
2. no mature candidate means scale 1.0 and zero evidence;
3. an inactive mature candidate does not advance evidence;
4. one or several active mature candidates advance evidence by exactly one per
   observation;
5. scale follows the frozen linear formula and never falls below 0.10;
6. shared updates use the adaptive scale while mature/trial candidate updates
   remain fully plastic;
7. snapshot counters and scale summaries are exact.

## Frozen environment and budget

Run once on 20 fresh seeds 20261501--20261520, disjoint from every earlier
generic-core package:

- the frozen randomized anonymous key-door environment;
- 4,096 regime-0 then 4,096 regime-1 episodes, no replay;
- 512 evaluation episodes per regime;
- observable anonymous regime terminal but no transition notification;
- terminal-only +/-1 valence;
- epsilon 0.15, discount 0.97;
- online learning rate 0.08, proposal interval 128, support 16, four live and
  64 total proposals, burn-in 8, 32 confirmations, causal margin 0.01, resource
  cost 0.002, expiry 512;
- same random seed, episode count, total action count, evaluation count, and RNG
  call count across arms.

Per-action selection distributions are expected behavioral outputs and are not
required to match. Reuse and hash the frozen environment and enrichment helpers.

## Measurements

Record old/new joint, key, and door performance; full versus
composite-disabled behavior; mature contextual pairs; maturity timing; adaptive
evidence and scale trajectory summaries; shared/candidate update counts;
primitive/candidate weight summaries; proposal/live bounds; parity and trial
leakage; total experience/action/RNG budgets; task manifests; source and helper
hashes.

## Gates

Development support requires every gate:

1. adaptive median joint success at least 0.85 in both regimes;
2. adaptive median key accuracy at least 0.90 in both regimes;
3. adaptive old-regime joint exceeds fixed-full on at least 16/20 tasks;
4. adaptive old-regime joint exceeds fixed-low on at least 14/20 tasks;
5. adaptive new-regime median is no more than 0.05 below either control;
6. adaptive mature regime-1 contextual pair on at least 16/20 tasks;
7. adaptive median mean-regime composite-ablation effect at least 0.15;
8. every adaptive task has a mature channel, mature-evidence activations,
   post-maturity shared updates, and post-maturity candidate updates;
9. at least 16/20 adaptive tasks have some action channel reach applied scale
   at most 0.20, proving material consolidation exposure;
10. proposal/live bounds, graph parity, trial isolation, and equal episode,
    evaluation, total-action, and RNG budgets pass on 20/20 tasks.

No arm is selected or tuned by this package. Means, timing, per-action choices,
and dose comparisons outside these gates are descriptive.

## Predictions and kill criterion

Predicted adaptive medians are at least 0.85 old and 0.95 new, with performance
strictly above fixed-low on old retention while remaining near fixed-full on new
acquisition. If adaptive resembles fixed-full, decay was too late or weak; if it
resembles fixed-low, mature activation did not provide a useful equilibration
period; if it harms both, the local schedule destabilized shared/candidate
division of labor.

Commit and push contract, implementation, tests, and runner before fresh task
generation. Pass the complete core and new lifecycle/runner tests. Execute once.
Any exception, missing artifact, source change, invariant failure, or failed
scientific gate closes the package without changing horizon, floor, trigger,
environment, or pools.

Builder-run support is not independent confirmation. Even a full pass authorizes
neither automatic integration nor KRK transfer; those require separate frozen
packages.
