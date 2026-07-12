# Generic-Core Local Consolidation Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before implementation.

## Predecessor

Renewable topology formed regime-1 cue composites on 20/20 tasks, bounded live
capacity at four, and retained perfect new-regime behavior, but median old-regime
success remained 0.0. Both old and new contextual structures existed; shared
fast bias/primitive weights still moved beneath mature old structure.

## Hypothesis

Learner-local consolidation triggered by the first causally mature composite
will preserve the action channel's shared representational baseline while new
context-specific composites remain plastic. With renewable capacity unchanged,
this will allow old and new key-door regimes to coexist without replay or a
laboratory phase signal.

## Strongest null

Hard shared-weight consolidation occurs too early, freezes a spurious baseline,
prevents new-regime learning, merely shifts adaptation into unconstrained
candidate weights, or appears successful only because of extra compute,
different topology, or hidden phase knowledge.

## Exactly one factor

Two persistent-trace arms use identical fresh tasks:

- renewable control: shared bias and primitive weights retain scale 1.0 after
  candidates mature, matching the predecessor;
- consolidated: after any candidate in that action channel first reaches
  `mature` through the frozen future causal-benefit gate, subsequent shared
  bias/primitive updates use scale 0.0.

In both arms:

- trial shadow weights remain plastic;
- mature candidate weights remain plastic only when their conjunction is active;
- renewable four-live/64-total topology is unchanged;
- no replay, slow target network, phase-boundary event, external freeze,
  learning-rate schedule, reward change, or extra operator is added.

The maturity event is learner-local and task-agnostic. It does not expose regime,
stage, signal identity, correctness, or evaluation.

## Frozen implementation contract

- add `shared_learning_after_maturity_scale`, default 1.0;
- validate it lies in [0, 1];
- determine maturity after trial causal decisions and before each shared update;
- scale only bias and primitive updates;
- do not scale trial or mature composite updates;
- record first consolidation observation, shared update counts before/after
  maturity, and final consolidated state;
- legacy/default behavior and previous tests remain unchanged.

Lifecycle tests must show:

1. default scale preserves shared updates after maturity;
2. scale 0 freezes shared bias/primitive weights immediately after maturity;
3. mature candidate weights can still change;
4. new trials can still be proposed and trained under consolidation;
5. no frozen task seed is used.

## Frozen environment

Reuse the predecessor key-door environment exactly on 20 fresh seeds
20261201–20261220:

- 4,096 regime-0 then 4,096 regime-1 episodes;
- no regime-0 replay;
- 512 untouched evaluation episodes per regime;
- observable anonymous regime terminal but no phase notification;
- two learner-selected actions and one action-dependent transition per episode;
- terminal-only ±1 valence;
- epsilon 0.15, discount 0.97;
- online learning rate 0.08, proposal interval 128, support 16, four live and
  64 total proposals, burn-in 8, 32 confirmations, causal margin 0.01, resource
  cost 0.002, expiry 512.

The runner must reuse and hash the frozen predecessor environment.

## Measurements

- old/new joint, key, and door performance for both arms;
- full versus composite-disabled behavior;
- mature regime-0 and regime-1 pairs;
- first consolidation observation by action;
- shared update counts before and after maturity;
- primitive/bias and candidate weight summaries;
- candidate live/total/resource bounds;
- graph/update parity, trial leakage, experience and RNG budgets;
- all source/row/implementation/runner hashes.

## Gates

Development support requires every gate:

1. consolidated median regime-0 joint success at least 0.85;
2. consolidated median regime-1 joint success at least 0.85;
3. consolidated median key accuracy at least 0.90 in both regimes;
4. consolidated old-regime joint success exceeds renewable control on at least
   16/20 tasks;
5. consolidated new-regime joint success is no more than 0.05 below control in
   median;
6. consolidated mature cue/regime-1 pair on at least 16/20 tasks;
7. median consolidated full-minus-composite-disabled joint effect at least 0.15;
8. consolidated shared updates after maturity are zero while candidate updates
   after maturity are nonzero;
9. proposal/live bounds, graph parity, trial isolation, experience, action, and
   RNG budgets pass on 20/20 tasks.

## Stop rule

Commit and push contract, implementation, and runner before generating fresh
tasks. Execute once. Any failed gate closes this package without changing the
consolidation scale, adding replay, modifying maturity, or rerunning. Builder-run
measurements are not independent confirmation; KRK transfer remains disallowed.
