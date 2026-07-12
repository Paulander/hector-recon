# Generic-Core Role-Blind Causal-Rent Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before implementation or fresh execution.

## Basis and question

The contextual ceiling proved that bounded additive pairs can preserve the old
mapping while learning the changed mapping. The subsequent ecology experiment
showed that residual-ranked nomination with eight host-assigned slots in the
known door channels was useful, but its preregistered semantic-coverage gate
failed. Post-run ablations also found mature candidates with negative effects
and channels saturated at their local limit. The supported result is therefore
useful nomination under manually assigned capacity, not autonomous topology
allocation.

Question: can one task-agnostic, role-blind causal-rent law allocate, revalidate
and retire candidates from a single global topology budget in proportion to
hidden compositional demand, while preserving a mastered mapping?

Strongest null: any benefit comes from fixed extra capacity, replay, privileged
channel allocation, or closed-loop trajectory divergence; causal rent either
fails to match fixed capacity, cannot distinguish ranked from shuffled
nomination, retains equal topology at all demand levels, or binds its safety
allowance.

## Learner/laboratory boundary and demand gradient

Use fresh seeds 20261901--20261920. Each seed creates one anonymous task and one
common regime-0 checkpoint after 4,096 outcome-only episodes. Require joint
success >=0.85 on 512 disjoint development rows, serialize the complete state,
and clone it into every arm and demand stratum. Shared biases and primitive
weights are then frozen byte-identically.

For each seed, generate one matched set of 4,096 regime-1 experience rows and
512 evaluation rows. Reuse the same observations and nuisance bits at all three
demand levels; only the outcome-generating mapping differs:

- `m=0`: neither of the two cue-conditioned mappings changes;
- `m=1`: exactly one hash-selected cue-conditioned mapping changes;
- `m=2`: both cue-conditioned mappings change.

The learner sees anonymous terminals, the ordinary anonymous regime terminal,
legal action IDs, its own scores/topology and terminal return. It never sees
`m`, cue meaning, action/channel role, mapping-change flags, cohort names,
correct actions, or evaluation labels. The regime terminal is deliberately
present even at `m=0`; whether it is useful must be learned. Laboratory code may
use demand and correct-action metadata only to generate returns and evaluate.

## Common lifetime experience reservoir

Every arm receives the same content-blind reservoir mechanism. It holds at most
2,048 decision traces and uses deterministic learner-local Algorithm-R uniform
sampling over the complete lifetime, including regime 0. A trace contains only
anonymous active terminal IDs, legal and selected action IDs, decision-time
scores, terminal return, discount, and a monotonic learner-local time index. It
does not contain regime, demand, phase, channel role, correctness or semantic
labels. Fixed-capacity arms collect the same traces even though they do not use
rent for lifecycle decisions.

The reservoir is necessary evidence, not replayed supervision: a current
candidate is counterfactually scored on stored observations using its current
weight. No stored correct action or host verdict is available.

## Arms and exactly changed scientific factor

All arms use [-1,1] prediction/parameter bounds, terminal-only outcome credit,
the same exploration, proposal interval 128, minimum nomination support 16,
64 lifetime proposals per channel, phase-1 rows, RNG accounting and reservoir.
All capacity rules apply identically to every anonymous action channel.

1. **role-blind fixed-8 ranked**: residual-ranked proposals; at most eight live
   candidates in every action channel; existing promote/prune lifecycle; no
   mature revalidation.
2. **role-blind fixed-8 random**: matched-random proposals with the same local
   bounds and opportunities.
3. **causal-rent ranked**: residual-ranked proposals governed by the global rent
   law below.
4. **causal-rent shuffled**: identical rent law, but proposal ranks are shuffled
   with learner-local RNG while preserving proposal timing, support threshold,
   candidate shape and budget.

Thus the primary factor is fixed local capacity versus role-blind global
metabolism, with matched nomination-selectivity controls. No host code may test
whether an action is a key or door action when allocating capacity.

## Frozen causal-rent law

The rent arms lease at most 32 live topology slots globally across all action
channels. One temporary shadow challenger may exceed that budget, so the hard
safety ceiling is 33. Reviews occur after each 512 phase-1 episodes and at the
end. A candidate needs at least 32 eligible reservoir traces; otherwise its
status is uncertain.

For candidate `i`, eligible traces are those on which its action was selected,
its anonymous predicate is active, and another legal action supplies a margin.
Using the current frozen shared parameters and current mature topology, compute
the selected action prediction and selected-versus-best-alternative margin with
and without `i`:

```text
predictive_benefit_i = mean((return - prediction_without_i)^2
                            - (return - prediction_with_i)^2)
rent_i = predictive_benefit_i - 0.002
margin_utility_i = mean(return * (margin_with_i - margin_without_i))
```

This is decision/action-margin evidence, not undifferentiated episode reward.
Candidate weights may continue their existing fast update between reviews;
shared parameters remain frozen.

- A challenger is promoted only when `rent_i > +0.01` and
  `margin_utility_i > 0`.
- A challenger in the uncertainty band remains temporary for at most two
  consecutive reviews, then is pruned unless it clears promotion.
- Every mature candidate is re-audited at every review with adequate support.
- A mature candidate is retired after `rent_i < -0.01` or
  `margin_utility_i < 0` in two consecutive adequately supported reviews.
- If 32 slots are occupied, promotion requires simultaneous retirement of the
  lowest-rent adequately supported mature candidate, and the challenger must
  exceed that candidate's rent by >0.01. Otherwise the challenger is pruned.
- Unsupported mature candidates remain leased but do not block the one
  temporary challenger from being tested. The live count may never exceed 33.
- Proposal, promotion, uncertainty, replacement, retirement and ceiling events
  are recorded with anonymous action/candidate IDs and causal statistics.

No semantic coverage, channel type, demand level, regime ID or laboratory
correctness may enter nomination, rent, leasing or death.

## Common-experience shadow cohort

Closed-loop arms may encounter different selected-action traces. As a separate
diagnostic, record the role-blind fixed-8-ranked experience stream for each
seed/demand cell and replay that exact anonymous observation/action/return
stream into non-acting ranked-nomination and shuffled-nomination shadow
learners. Their proposal opportunities, candidate shapes and budgets are
matched. Compare candidate counterfactual rent on the same terminal reservoir.
This cohort diagnoses nomination quality only; it cannot promote the primary
closed-loop result or repair a failed gate.

## Measurements and frozen gates

Record phase-0 mastery and clone parity; old/new joint success; checkpoints at
512/1024/2048/4096; selected-action and observation digests; complete occupancy
and lifecycle trajectories; rent/support/margin histories; reservoir count,
replacement count and digest; proposal opportunities/counts; shared hashes;
clipping; trial leakage; graph/update parity; and the hard ceiling.

Report candidate-on/off effects separately on (a) regime-0 retention rows,
(b) regime-1 changed-cue rows, (c) regime-1 unchanged-cue rows, and (d) nuisance
slices. Semantic contextual coverage may be reported after the fact only and is
not a gate or lifecycle input.

Development support requires every gate:

1. At `m=2`, fixed-8 ranked has median old and new joint success each >=0.85,
   at least 16/20 tasks have both >=0.85, exceeds fixed-8 random on minimum
   old/new success in at least 14/20 tasks, and has median paired advantage
   >=0.10.
2. At `m=2`, causal-rent ranked has median old and new joint success each
   >=0.85, at least 16/20 tasks have both >=0.85, and its median paired minimum
   old/new difference versus fixed-8 ranked is >=-0.05.
3. At `m=2`, causal-rent ranked exceeds causal-rent shuffled on minimum old/new
   success in at least 14/20 tasks with median paired advantage >=0.10.
4. Causal-rent-ranked final mature occupancy has nondecreasing medians from
   `m=0` through `m=2`; at least 14/20 matched seeds satisfy
   `occupancy(m0) <= occupancy(m1) <= occupancy(m2)`; and median
   `occupancy(m2)-occupancy(m0) >=4`.
5. At `m=0`, causal-rent ranked retains at least four fewer candidates in the
   median than fixed-8 ranked, while median old and new joint success are each
   >=0.85.
6. In the common-experience cohort, ranked nomination exceeds shuffled
   nomination in mean positive counterfactual rent in at least 14/20 `m=2`
   tasks and has positive median paired advantage.
7. The 33-slot safety ceiling never binds as a rejected or skipped proposal;
   maximum live count is <=33 and maximum non-temporary occupancy is <=32 in
   every rent run.
8. Shared hashes remain fixed; phase-0 clones, row manifests and experience
   budgets match; reservoir operation is content-blind and bounded; no learner
   allocation record contains role/demand/correctness fields; trial candidates
   never leak into deployed graph roots; graph/update parity and all configured
   proposal/resource bounds hold in every run.

## Predicted outcomes, kill criterion and transfer

Prediction: fixed-8 ranked replicates the `m=2` capacity result; causal-rent
ranked is noninferior there, beats shuffled nomination, sheds unnecessary
topology at `m=0`, and grows monotonically with hidden demand without touching
shared weights or the safety ceiling.

Any failed gate is a negative completion of this package. In particular, no
threshold, reservoir size, review cadence, demand mapping, candidate family or
arm may be repaired after fresh rows are viewed. A ceiling bind falsifies the
bounded mechanism even if task accuracy is high. No standalone fixed-eight
confirmation, semantic-coverage rescue or KRK claim follows automatically.

Compute/change budget: one generic lifecycle/reservoir implementation, one
runner, focused unit tests, retired-seed smoke tests, then exactly 20 fresh
matched seeds x 3 demands x 4 arms plus the diagnostic shadow cohort. Commit
and push the contract before mechanism code; commit and push implementation and
tests before fresh execution; checkpoint each seed/demand cell independently.

Frozen transfer test: none in this development package. If and only if all
gates pass, the next separately authorized bridge must test learner-local
plasticity routing and latent context before any fresh KRK transfer.
