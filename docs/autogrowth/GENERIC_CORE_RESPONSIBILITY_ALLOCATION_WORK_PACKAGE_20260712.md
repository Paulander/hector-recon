# Generic-Core Phase-Split Responsibility Allocation Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before implementation.

## Correction motivating this package

Prior packages establish that post-maturity shared plasticity causally controls
final old/new performance. They do not establish acquire-then-forget because no
regime-0 evaluation occurred before regime-1 training. Their aggregate topology
ablation is predominantly new-regime behavior, while old contextual coverage
and gain are sparse.

The current learner also duplicates one terminal residual: shared bias and
active primitives receive one complete shared budget, every active trial shadow
learns again, and every active mature composite receives the full residual
again. Decision traces record active graph nodes but credit does not use them.

## Hypothesis and strongest null

Hypothesis: after verified regime-0 mastery, conserving one residual-update
budget and allocating it according to decision-time, learner-local parameter
importance will reduce measured forgetting while preserving regime-1
acquisition. Correct responsibility must outperform a shuffled,
update-budget-matched allocation.

Strongest null: phase-0 mastery is absent; final loss is incomplete acquisition
rather than forgetting; contextual coverage or bounded gain is insufficient;
any benefit comes only from reducing total update norm; stored graph
responsibility is stale or unused; or the shared-frozen diagnostic ceiling also
cannot support coexistence.

## Information boundary

The learner may use only:

- decision-time active graph components;
- each component's previously accumulated local importance;
- selected action, delayed terminal return, and eligibility trace;
- its current topology, weights, proposal evidence, and RNG.

It may not use regime, phase, correctness, hidden mapping, seed, evaluation,
coverage verdict, future outcome when forming decision-time responsibility, or
laboratory arm identity as a feature. The laboratory phase boundary is used only
to create one common checkpoint and switch experimental arms. The proposed
allocator itself contains no phase detector.

## Phase-0 common checkpoint

Use 20 fresh seeds 20261601--20261620. For each task:

1. train the current residual-broadcast learner for exactly 4,096 regime-0
   episodes;
2. evaluate 512 disjoint regime-0 development rows generated after all frozen
   train/final pools;
3. require joint success at least 0.85 on every task;
4. serialize and hash the complete state: policy and learner RNG states, empty
   trace state, bias/primitives, candidate weights/topology/lifecycle,
   pair/proposal evidence, importance accumulators, counters, and graph;
5. deep-clone that identical state into every arm and prove pre-configuration
   clone parity.

No seed may be dropped or replaced. If any task misses mastery, write the
phase-0 artifact and stop the entire package before phase 1. That is an
acquisition failure, not forgetting evidence.

Final evaluation pools remain untouched until all phase-1 training is complete.
The development pool may be reused read-only at phase-1 checkpoints; its results
never alter learning.

## Learner-local importance

Every bias, primitive, trial, and mature-candidate parameter has nonnegative
importance `C_j`, initialized to zero. After any update, importance changes
only for future decisions:

`C_j <- C_j + abs(delta * actual_parameter_change_j)`

where `delta` is that decision's terminal residual and actual change is after
parameter clipping. Thus current/future outcome cannot influence the
responsibility snapshot used for the same decision.

At action selection, store each active component's binary eligibility, raw
contribution, lifecycle state, and pre-decision `C_j` in the trace. Bias is
always active; primitives and candidate adapters are active only when their
graph predicate fires. Trial adapters remain shadow-only behaviorally but
participate in allocation while active; their consumed budget is reported
separately.

## Exactly one scientific factor and five arms

Every arm starts from the same phase-0 checkpoint and consumes the same
exogenous phase-1 rows, seed schedule, episode/evaluation budget, and legal
action interface. Action-conditioned observations and action distributions may
diverge and must be recorded.

1. **Broadcast:** unchanged scale-1 residual duplication.
2. **Fixed-low:** unchanged broadcast with post-maturity shared scale 0.10.
3. **Responsibility allocation:** conserved rule below.
4. **Shuffled responsibility:** identical conserved rule, but importance values
   are permuted among simultaneously eligible components.
5. **Shared-frozen ceiling:** laboratory diagnostic; shared bias/primitives are
   frozen throughout phase 1 while contextual trial/mature weights remain
   plastic under the legacy candidate rule.

The ceiling is not an autonomous mechanism and cannot be selected.

## Frozen conserved rule

Eligibility is binary, so it is not applied twice. For the components active in
the stored decision trace:

`u_j = 1 / (0.01 + C_j)`

`rho_j = u_j / sum_k(u_k)`

`requested_delta_w_j = learning_rate * delta * rho_j`

The signed requested updates therefore sum to
`learning_rate * delta`, and requested L1 norm is
`learning_rate * abs(delta)`. Actual changes may be smaller only because of
the existing [-1, 1] parameter bounds.

In the shuffled arm, sort component IDs, permute the same multiset of importance
values, then apply the same equations. The real and shuffled arms make the same
number of allocator-RNG calls; the real arm generates and discards the matched
permutation. Record conservation error, requested/actual L1, allocation share
by component class, missing/stale responsibility, and clipping.

Lifecycle evidence and causal promote/prune gates remain unchanged. Allocation
changes only where the already-computed residual is written.

## Frozen training and longitudinal measurements

Phase 1 uses exactly 4,096 regime-1 episodes with no replay or phase signal.
Measure old development performance without learning after phase-1 episodes
512, 1,024, 2,048, and 4,096. Final old/new performance uses separate untouched
512-row pools.

For every arm/task record:

- phase-0 mastery and the full forgetting trajectory;
- final old/new joint, key, and door performance;
- all-composite ablation separately by regime;
- each mature candidate's individual ablation separately by regime;
- complete door-action x cue x regime mature-pair coverage (eight possible
  components), expected-sign agreement, and saturated contextual weights;
- raw bias, primitive, and contextual score contributions plus output clipping;
- parameter clipping by component class;
- phase-1 action-sequence digest and action-conditioned observation digest;
- importance and allocation-share distributions;
- proposal/live bounds, graph parity, trial isolation, experience and RNG
  budgets.

For each final arm also evaluate:

1. phase-0 shared weights plus final contextual topology/weights;
2. final shared weights plus phase-0 contextual topology/weights;
3. unchanged phase-0 shared plus phase-0 contextual state.

These counterfactual assemblies are diagnostics only.

## Gates

If all 20 phase-0 tasks pass mastery, development support requires every gate:

1. responsibility allocation final median joint success at least 0.85 in both
   regimes;
2. median old-regime drop from the phase-0 checkpoint no more than 0.05;
3. median new-regime joint success no more than 0.05 below broadcast and
   fixed-low;
4. allocation old-regime joint exceeds broadcast on at least 16/20 tasks and
   fixed-low on at least 14/20;
5. allocation per-task minimum(old,new) exceeds shuffled on at least 16/20,
   with median paired advantage at least 0.10;
6. allocation median all-composite effect at least 0.10 separately in both
   regimes;
7. responsibility and shuffled arms both use the conserved path; maximum
   requested-budget error at most 1e-12; matched allocator-RNG calls and equal
   component/update opportunities;
8. stored decision-time responsibility is present on every credited decision,
   with zero stale/missing-component update;
9. proposal/live bounds, graph parity, trial isolation, and equal episode,
   evaluation, total-action, policy-RNG, and exogenous-row budgets pass on
   20/20 tasks.

Coverage, sign, clipping, counterfactual assemblies, and the shared-frozen
ceiling discriminate failure causes but cannot rescue a failed gate.

## Predeclared interpretations

- Allocation passes and beats shuffled: residual ownership is causally useful;
  proceed only to independent generic confirmation.
- Allocation equals shuffled: reduced norm or random redistribution, not real
  responsibility, explains any benefit.
- Allocation fails while shared-frozen ceiling passes: allocator/importance is
  wrong; do not add memory stores yet.
- Allocation and ceiling both fail with sparse coverage or saturated gain:
  contextual expressivity/coverage is binding.
- Phase-0 mastery fails: close as acquisition failure; no forgetting claim.

## Stop rule and transfer freeze

Commit and push contract, implementation, tests, and runner before fresh task
generation. Pass the complete core plus checkpoint, allocation, shuffle,
counterfactual, and runner tests. Execute once. Any exception, invariant failure,
missing artifact, or post-generation change closes the package without tuning
epsilon, importance, eligibility, arms, topology, gain, pools, or gates.

This is builder-run generic-core development. It cannot authorize direct native
KRK integration. Even a pass requires independent confirmation followed by an
anonymous predecessor-child bridge on the native substrate.
