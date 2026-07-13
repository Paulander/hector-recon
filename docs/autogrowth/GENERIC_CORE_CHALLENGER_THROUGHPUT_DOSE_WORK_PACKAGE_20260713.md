# Generic-Core Challenger-Throughput Dose Work Package

Date: 2026-07-13. Track: generic-core development. Status: PI-authorized and
frozen before implementation or fresh execution.

## Basis and question

The closed role-blind causal-rent package separated two facts. Residual-ranked
nomination remained informative: ranked beat shuffled in all 20 matched `m=2`
tasks, both closed-loop and on the common fixed-ranked experience stream. The
rent ecology nevertheless failed noninferiority and the occupancy-gradient
gate. At `m=2`, its median final mature occupancy was 10 versus 22.5 for the
successful fixed ecology. It proposed a median 9 candidates, promoted 6 and
retired 4. With one temporary challenger per 512-episode review, the mechanism
could promote at most eight challengers during the 4,096-episode phase, whereas
the fixed ecology commonly needed roughly fifteen additional mature
candidates.

Question: was the negative result caused by a hard challenger-throughput
ceiling rather than absent nomination signal or an intrinsically wrong
causal-rent criterion?

Hypothesis: allowing a bounded batch of concurrent temporary challengers will
produce a dose-dependent increase in useful mature topology and recover the
changed mapping while preserving the old mapping and low-demand compression.

Strongest null: additional concurrent challengers merely increase transient or
harmful topology. Accuracy will not improve monotonically with dose, the
highest dose will remain inferior to fixed capacity, or ranked nomination will
not beat a matched shuffled control even when throughput is available.

## Learner/laboratory boundary

Use fresh seeds 20262001--20262020, never used in the preceding package. Each
seed creates the same anonymous-task family and common quiescent regime-0
checkpoint as the closed package: 4,096 terminal-outcome-only episodes, 512
disjoint development rows, joint success >=0.85, and role-blind pruning of
unfinished shadow trials without behavior change. Clone that serialized state
into every arm and demand stratum; freeze shared biases and primitive weights
byte-identically.

Generate one matched set of 4,096 regime-1 experience rows and 512 evaluation
rows per seed. Reuse observations and nuisance bits across `m=0`, `m=1`, and
`m=2`; change only zero, one, or two hidden cue-conditioned mappings. Learners
receive anonymous terminals, legal action IDs, selected-action scores, graph
state and terminal return. They never receive demand, cue/action roles, mapping
changes, phase labels, correct actions or evaluation verdicts. Laboratory code
may use those fields only to generate return and evaluate frozen artifacts.

All arms use the same content-blind lifetime Algorithm-R reservoir of capacity
2,048 from the preceding package. No viewed row, trace, weight, topology or
threshold from seeds 20261901--20261920 enters these fresh learners.

## Exactly one changed scientific factor

The only scientific factor is the maximum number of concurrent temporary
challengers under the already frozen global causal-rent law. All rent arms keep:

- global mature capacity 32;
- proposal interval 128, review interval 512, minimum nomination support 16,
  minimum rent support 32 and 64 lifetime proposals per channel;
- residual-ranked candidate family and learner-local proposal evidence;
- predictive-rent cost 0.002, promotion threshold `>+0.01`, replacement margin
  `>0.01`, retirement threshold `<-0.01`, uncertainty and two-review death
  rules;
- terminal-only outcome credit, exploration, candidate/mature fast plasticity,
  clipping and frozen shared parameters;
- mature revalidation/retirement and the same reservoir evidence.

The arms are:

1. **fixed-8 ranked**: unchanged ceiling control from the preceding package.
2. **rent batch-1 ranked**: exact one-challenger mechanism replication.
3. **rent batch-2 ranked**: at most two concurrent temporary challengers.
4. **rent batch-4 ranked**: at most four concurrent temporary challengers.
5. **rent batch-4 shuffled**: identical to arm 4, except learner-local
   proposal ranks are shuffled as the nomination-selectivity control.

The mature capacity remains 32 in every rent arm. Temporary safety ceilings are
therefore 33, 34 and 36 for batch sizes 1, 2 and 4. This is not additional
deployable capacity: temporary candidates have no deployed root edge.

At each 128-episode opportunity, add at most one challenger if the configured
temporary allowance is not full. When review and proposal coincide, review the
existing batch first and then open the next batch. Thus all challengers receive
at least one full proposal interval of experience. At review, compute every
candidate's statistics from one pre-transition evidence snapshot, adjudicate
eligible challengers in descending rent with deterministic ID tie-breaking,
and apply the unchanged lease/replacement rule sequentially. For batch-1 this
is behaviorally identical to the closed mechanism. Batch size, its mechanical
safety ceiling and deterministic batch adjudication are the complete change.

## Common-experience shadows

For each seed/demand cell, replay the exact anonymous fixed-8-ranked acting
stream into non-acting batch-4 ranked and batch-4 shuffled shadow learners.
Compare their counterfactual rents under identical observations, selected
actions, returns and timing. This diagnoses nomination quality only and cannot
rescue a failed closed-loop gate.

## Measurements and frozen gates

Record the preceding package's complete evidence: phase-0 mastery and clone
parity; old/new success at 512/1024/2048/4096; row, action and observation
digests; mature/trial occupancy; lifecycle and rent histories; reservoir count
and digest; proposal opportunities/counts; shared hashes; clipping; trial-root
leakage; graph/update parity; action-score parity; and all ceilings. Report
changed-cue candidate-on/off effects separately from unchanged-cue, retention
and nuisance slices. Semantic roles remain post-hoc diagnostics only.

Development support requires every gate:

1. **Ceiling replication.** At `m=2`, fixed-8 ranked has median old and new
   success each >=0.85 and at least 16/20 seeds have both >=0.85.
2. **Batch-1 manipulation check.** Batch-1 preserves the bounded ecology:
   median final `m=2` mature occupancy is <=12 and it fails either median
   old/new >=0.85 or 16/20 joint mastery. Failure to reproduce this condition
   invalidates attribution; it does not support the hypothesis.
3. **Topology dose.** At `m=2`, median final mature occupancy is strictly
   increasing from batch-1 through batch-2 to batch-4, median batch-4 minus
   batch-1 is >=6, and at least 14/20 matched seeds satisfy the same strict
   ordering.
4. **Performance dose.** On minimum old/new success at `m=2`, batch-4 exceeds
   batch-1 in at least 14/20 seeds with median paired advantage >=0.15, and
   exceeds batch-2 in at least 12/20 seeds with positive median advantage.
5. **Fixed-capacity noninferiority.** Batch-4 ranked has median old and new
   success each >=0.85, at least 16/20 seeds have both >=0.85, and median paired
   minimum-success difference versus fixed-8 ranked is >=-0.05.
6. **Nomination selectivity.** Batch-4 ranked exceeds batch-4 shuffled on
   minimum old/new success in at least 14/20 `m=2` seeds with median paired
   advantage >=0.10. In common-experience shadows, ranked exceeds shuffled in
   mean positive counterfactual rent in at least 14/20 tasks with positive
   median advantage.
7. **Demand allocation.** Batch-4-ranked median mature occupancy is
   nondecreasing from `m=0` to `m=2`, at least 14/20 matched seeds satisfy that
   ordering, and median `m=2-m=0` occupancy is >=6.
8. **Low-demand compression.** At `m=0`, batch-4 ranked retains at least four
   fewer mature candidates in the median than fixed-8 ranked while median old
   and new success are each >=0.85.
9. **Safety and identity.** No safety ceiling binds as a rejected/skipped
   proposal; live and mature counts remain within their configured limits;
   shared hashes, checkpoints, manifests and budgets match; reservoir operation
   stays content-blind/bounded; no allocation record contains semantic fields;
   trials never enter deployed roots; and graph/update parity holds in every
   run.

## Predictions, kill criterion, budget and frozen transfer

Prediction: batch-1 reproduces the earlier undergrowth; batch-2 is intermediate;
batch-4 reaches the topology and performance neighborhood of fixed-8 ranked,
retains compression at `m=0`, and preserves ranked-over-shuffled selectivity.

Any failed gate is a negative completion. No batch size, cadence, threshold,
capacity, reservoir, plasticity, task distribution or gate may be tuned after
fresh rows are viewed. If occupancy rises without performance, the supported
next suspect is candidate/incumbent credit or plasticity, not more throughput.
If occupancy fails to rise, the supported next suspect is rent eligibility or
retention. Neither next package is automatic.

Compute/change budget: one bounded generalization of the existing controller,
one runner derived from the frozen predecessor, focused tests, a retired-seed
smoke test, full repository validation, then exactly 20 fresh matched seeds x 3
demands x 5 acting arms plus the diagnostic shadow cohort. Commit and push this
contract before mechanism changes; commit and push implementation/tests before
fresh execution; checkpoint each seed/demand cell independently.

Frozen transfer test: none. This is a generic-core developmental experiment,
not KRK evidence. Only a separately authorized, preregistered bridge may later
transfer a supported generic mechanism into the persistent from-scratch KRK
curriculum.
