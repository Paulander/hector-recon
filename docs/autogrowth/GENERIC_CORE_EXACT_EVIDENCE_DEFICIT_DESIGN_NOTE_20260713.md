# Generic-Core Exact Evidence-Deficit Internal State: Design Note

Date: 2026-07-13. Status: superseded in part by the accepted architectural
decision and frozen graph-internal work package. Retained as provenance for the
completed negative result.

## Motivation from the completed experiment

The admitted support-directed result found all 80 target candidates and executed
3,479 directed probes safely, but 19/80 targets died unsupported. Median exact
reservoir support at their first and second reviews was 9 and 11 against required
32. Eight doomed targets reached local activation support 31 and received the
next activation that ended their request deficit, while exact retained support
remained inadequate.

The current request state therefore asks the right qualitative question with the
wrong quantitative currency. `CompositeCandidate.activation_count` is the count
of selected-action observations while a trial predicate is active. Causal-rent
support is the count of matching action/member records currently retained in a
bounded lifetime Algorithm-R reservoir. Insertions, later replacements and
evictions make those quantities diverge.

This note specifies how an exact local state could be implemented without chess
semantics, a global evaluator, repeated reservoir scans or changed randomness.
It deliberately does not change review grace, exploration rate, rent thresholds
or topology.

## Candidate-local kernel

Add a candidate-local counter, provisionally `rent_evidence_support`, whose
contract is exactly:

> the number of current reservoir records whose selected action is this
> candidate channel, whose legal-action set has at least two actions, and whose
> active anonymous atom set contains every immutable candidate member.

The match predicate is already the structural support predicate inside
`candidate_rent_stats`; factor it into one shared helper so lifecycle review and
the local counter cannot drift semantically.

Change `LifetimeDecisionReservoir.add` to return a content-blind mutation record:

- the inserted `LifetimeDecisionRecord`;
- the evicted record, or `None` when the reservoir grows or Algorithm R rejects
  the insertion;
- the retained index when relevant for audit.

This return value must not add an RNG call or change Algorithm-R selection. On
every retained insertion/eviction, update support for each live candidate by
adding the inserted match and subtracting the evicted match. With the current
hard ceiling of 36 live candidates and two decisions per episode, this is bounded
O(36) local bookkeeping per retained record rather than O(2,048 x candidates)
rescanning on every exploration event.

When a candidate is first proposed, initialize its exact support with one scan of
the current bounded reservoir. Candidate members are immutable and its action is
fixed by channel ownership, so subsequent mutation deltas are sufficient. Freeze
the counter when a candidate is pruned; initialize and maintain it for trials and
mature candidates only.

At proposal, every review, each saved checkpoint and finalization, assert that
the incremental counter equals a fresh full scan. Any mismatch is a hard invariant
failure. The existing `candidate_rent_stats.support` remains the adjudicator and
must equal the local counter; the counter does not grant rent or maturity.

## Internal-terminal interpretation

The original note proposed using the exact counter directly before optionally
materializing it. External review correctly rejected that boundary. The first
causal test must materialize a first-class generic internal terminal associated
with the candidate, with the exact counter as its measurement backend:

- it fires only while the candidate is live and exact support is below threshold;
- its legs identify the owning candidate/action channel and the candidate’s
  anonymous member terminals;
- it exposes no cue, regime, role, correctness, target identity or evaluation
  result;
- it cannot enter exploitative action roots by default;
- it may request an already scheduled exploration event but creates no reward,
  confirmation, rent or maturity.

This is local knowledge, not a central overseer. Each candidate receives only the
state of its own evidence ledger, maintained from the same anonymous experiences
that will adjudicate it.

A later generic vocabulary may include `CHILD_VALUE_AVAILABLE`,
`PREDICTION_SURPRISE` and `CONSOLIDATION_READY`, but adding those in the same test
would confound the support-currency question.

## Required tests before any new experiment

1. Algorithm-R mutation return preserves exact prior reservoir contents, hashes,
   replacement counts and RNG-call counts for fixed seeds.
2. Incremental support equals full-scan support after append, rejected insertion,
   matching replacement, nonmatching replacement and matching eviction.
3. Candidate birth initializes exact support from records that predate birth,
   matching current causal-rent semantics.
4. Pruned candidates stop requesting and cannot affect greedy scores or roots.
5. Exact-deficit and activation-deficit arms have identical exploration event
   timing and main RNG streams.
6. No-request fallback remains the pre-drawn ordinary random action.
7. Snapshot/clone/restore retains the exact counter and parity.
8. A planted multi-request diagnostic creates unequal deficits often enough that
   maximum-deficit and shuffled responsibility make measurably different choices.
9. Full repository validation passes before any new seed is touched.

## Proposed next scientific factor

A new preregistration should compare support currency, not silently repair the
completed package. A defensible arm set is:

1. fixed-8 positive reference;
2. ordinary batch-4 negative replication;
3. current activation-deficit directed requests;
4. exact-reservoir-deficit directed requests;
5. exact-reservoir-deficit shuffled responsibility.

All use the same exploration-event schedule, local RNG budget, proposal ecology,
review cadence, two-review grace, capacity, rent and outcome learning. The primary
manipulation is exact versus proxy support. Exact directed must first raise the
per-task minimum exact support and reduce unsupported deaths relative to current
activation-directed. Priority selectivity versus exact shuffled is a distinct
secondary claim and should only bind if the planted/matched ecology proves enough
multi-request opportunities.

Do not raise exploration, extend review grace or lower support 32 in this test.
If exact deficit still leaves candidates below 32 at the second review, that is
clean evidence for a later support-conditioned grace experiment. If exact support
reaches 32 but candidates fail rent, the next question is individual versus
cooperative causal contribution. If candidates mature without behavior, action
competition/plasticity is next.

## Reference-stability issue

The fixed-8 reference reached median old/new 0.9336/1.0 but only 15/20 tasks
mastered both. Five admitted old-task policies drifted below 0.85 during phase-1
plasticity. A future contract must retain this reference gate or separately
preregister a stability mechanism; it must not lower the count after observing
15/20. Exact evidence support does not solve retention drift.

This strengthens the case for the alternating structural/equilibration/
consolidation schedule in the long-term graph. It does not authorize freezing
all learning in the next support-currency test, because that would remove the
new-task adaptation being measured.

## Performance and implementation boundary

No new semantic node family is necessary for the first causal kernel. Returning
reservoir mutations and maintaining at most 36 counters should be substantially
cheaper than the current candidate-rent full scan, which remains necessary only
at review and invariant checkpoints. The earlier repository speedups do not
remove this logical distinction: caching helps repeated evaluation, while this
counter prevents an avoidable scan on every decision.

Implementation should remain generic in `recon_lite`; the key-door runner may
only select arms and measure post-hoc targets. Native KRK transfer remains closed
until a separately frozen generic experiment supports the exact local state and
R1 still must pass before R2 opens.
