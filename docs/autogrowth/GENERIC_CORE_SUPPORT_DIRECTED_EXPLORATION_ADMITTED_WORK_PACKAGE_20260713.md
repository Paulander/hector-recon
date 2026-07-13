# Generic-Core Support-Directed Exploration with Frozen Admission

Date: 2026-07-13. Track: generic-core development. Status: PI-authorized and
frozen before implementation or fresh execution.

## Basis, hypothesis and strongest null

The first support-directed package stopped before phase 1 because one of twenty
fixed fresh checkpoints failed the common phase-0 mastery boundary. Nineteen
passed; seed 20262109 scored 0.8203125 on the anonymous key decision while its
door decision was perfect. The evidence-request mechanism was never enabled, so
that artifact neither supports nor rejects its hypothesis.

This package changes only upstream cohort admission. It conditions the phase-1
comparison on independently demonstrated child-task readiness, as the curriculum
doctrine requires. The phase-1 learner, arms, mechanism, budgets, measurements
and gates remain those frozen in the predecessor.

Hypothesis: among checkpoints that have independently mastered the old task,
allowing an active trial composite to allocate an exploration event that would
already occur will supply missing action-conditioned evidence, mature all four
target structures, and recover the changed mapping without damaging retention.

Strongest null: directed requests do not improve minimum target support,
unsupported deaths, maturity or behavior over shuffled responsibility; or they
consume unequal exploration/resources. Failure to acquire twenty eligible base
checkpoints inside the capped candidate pool is a separate admission abort and
leaves the phase-1 hypothesis untested.

## Fresh candidate pool and sequential admission

Candidate seeds are exactly 20262201--20262240 in ascending order. None may have
been used in prior development. For each candidate, generate the same anonymous
key-door task and train phase 0 for 4,096 episodes. Evaluate the 512-row old-task
development pool, then quiesce unfinished trials without another observation.

A candidate is admitted if and only if all three upstream conditions hold:

1. old-task joint success is at least 0.85;
2. zero trial candidates remain after quiescence;
3. deployed behavior is byte-identical before and after quiescence.

Attempt candidates in ascending order and stop as soon as twenty are admitted.
Report every attempted seed, result, checkpoint hash and all row-manifest hashes.
If fewer than twenty pass by seed 20262240, stop before phase 1. Rejected seeds
are never replaced based on phase-1 data because no phase-1 arm is allowed to run
until admission is complete.

This conditioning criterion is upstream and outcome-independent with respect to
the new mapping. It does not inspect target candidates, changed-task performance,
arm behavior or phase-1 rewards. All attempted candidate seeds and manifests are
retired after this package.

## Mandatory manifest freeze boundary

The canonical process retains the twenty admitted policy objects in memory,
writes a separate admission manifest, and pauses before cloning or consuming any
phase-1 experience. The manifest records attempted/admitted/rejected seeds,
checkpoint hashes, row hashes, admission rule, runner hash and implementation
hashes. Commit and push that manifest for external audit while the process is
paused. Resume only after the push succeeds. The final artifact must record the
admission-manifest SHA-256 and freeze commit.

A canonical run without this pause/commit boundary is invalid. Do not reconstruct
or retrain admitted checkpoints after the manifest is observed.

## Phase-1 learner and exactly one scientific factor

For every admitted checkpoint, use only hardest anonymous demand m=2. Clone the
complete checkpoint into four arms:

1. **fixed-8 ranked** -- successful positive reference;
2. **rent batch-4 ranked** -- negative-mechanism replication with ordinary
   random exploration;
3. **rent batch-4 support-directed** -- an existing active trial requests the
   legal action with greatest local evidence deficit;
4. **rent batch-4 support-shuffled** -- the same request set and event schedule,
   but a uniform request ignores deficit magnitude.

The only phase-1 factor is allocation of already scheduled exploration actions.
Exploration rate, event timing/count, shared weights, proposal family, nomination,
rent, review cadence, lifecycle thresholds, capacity and learning rates remain
identical to the predecessor. Each admitted seed uses 4,096 matched phase-1
experience rows and 512 old/512 new evaluation rows.

The request emitter is the existing trial composite with two anonymous terminal
member legs. On an exploration event only, enumerate active legal positive-deficit
trials. Directed chooses among maximum deficits; shuffled chooses uniformly among
all requests using the same one-draw local RNG budget. No request retains the
ordinary random action. Trials never affect greedy scores or deployed roots.
Requests create no reward, confirmation, rent or maturity; they only choose which
ordinary action receives ordinary experienced outcome.

## Information firewall and measurements

The learner may receive active anonymous terminals, legal actions, graph and
candidate-local state, selected scores, terminal return and local counters. It
must not receive cue meaning, action role, changed mapping, correct action,
target identity, evaluation result, cohort label or demand.

Preserve every predecessor measurement: phase-0 mastery/quiescence, clone and
shared hashes, old/new checkpoints at 512/1024/2048/4096, all action/observation
and exploration digests, support-RNG calls, request/probe/fallback ledgers,
candidate trajectories, reservoir support, proposal/review/rent/lifecycle events,
action margins as diagnostics only, occupancy, clipping, graph/update parity,
trial-root isolation, resource ceilings and post-hoc four-target reconstruction.
Record all non-target candidates as well.

## Frozen phase-1 gates

Development support requires every gate, unchanged from the predecessor:

1. Fixed reference: median old and new success each at least 0.85 and at least
   16/20 tasks master both.
2. Negative replication: ordinary rent batch-4 fails that same joint criterion.
3. Evidence manipulation: directed has all four targets reach reservoir support
   at least 32 in at least 16/20 tasks; its per-task minimum exceeds shuffled in
   at least 14/20 with median paired advantage at least 12.
4. Unsupported death: at least 16/20 directed tasks mature all four targets and
   no more than 4/80 directed targets die unsupported.
5. Behavior: directed median old/new each at least 0.85 and at least 16/20 master
   both.
6. Fixed noninferiority: median paired minimum old/new directed-minus-fixed is
   at least -0.05.
7. Responsibility selectivity: directed exceeds shuffled minimum old/new in at
   least 14/20 tasks with median advantage at least 0.10.
8. Matched exploration: directed/shuffled have identical event counts/timing,
   support-RNG calls, episode/reservoir budgets and exploration rate.
9. Safety and identity: shared hashes, clones/manifests, probe accounting,
   semantic firewall, trial isolation, graph parity and ceilings all pass in all
   80 arms.

## Kill criteria, budget and transfer

Any failed phase-1 gate is a negative completion. Do not tune admission threshold,
candidate cap, support target, request eligibility, exploration, rent, topology,
task distribution or gates after fresh data are viewed. An admission abort does
not authorize another seed extension. If target support rises but rent fails,
individual versus cooperative rent is the next separate question. If targets
mature but behavior does not improve, action competition/plasticity is next. If
support does not rise, local request allocation is falsified at this dose.

Budget: one admission-aware runner and tests; bounded retired-seed smoke; full
repository validation; commit/push implementation; one canonical candidate
admission process with mandatory manifest pause/commit/push; then at most twenty
admitted checkpoints times four phase-1 arms. No KRK transfer occurs in this
package.
