# Generic-Core Support-Directed Exploration with Frozen Admission: Result

Date: 2026-07-13. Track: generic-core development. Status: complete negative
result; no KRK transfer authorized.

## Verdict

The capped sequential admission repair worked exactly as intended, and the
phase-1 support-directed mechanism failed its frozen gates. The first twenty
candidate seeds, 20262201--20262220, all mastered phase 0; the minimum admission
score was 0.931640625. Their manifest was committed and pushed at `d279ba9`
while the canonical process remained paused with the exact checkpoints in
memory. Phase 1 resumed only after verifying that `HEAD` contained the exact
manifest bytes.

Support-directed exploration was safe and did redirect ordinary exploration,
but maximum-deficit priority did not outperform matched shuffled responsibility,
did not prevent the recurring unsupported target death, and did not recover the
changed mapping. This closes activation-count-directed request priority at the
frozen dose. It does not reject internal terminals generally.

## Frozen gate table

| Gate | Frozen requirement | Observed | Verdict |
|---|---|---:|---|
| Fixed reference | old/new medians >=0.85; both >=16/20 | 0.9336 / 1.0000; 15/20 | FAIL |
| Negative replication | ordinary batch-4 fails joint mastery | 0.9873 / 0.7246; 3/20 | PASS |
| Evidence manipulation | all four supported >=16/20; directed beats shuffled >=14/20, median >=12 | 1/20; 7/20, median 0 | FAIL |
| Unsupported death | all four mature >=16/20; <=4/80 unsupported deaths | 1/20; 19/80 | FAIL |
| Directed behavior | old/new medians >=0.85; both >=16/20 | 0.9697 / 0.6953; 2/20 | FAIL |
| Fixed noninferiority | median paired minimum difference >=-0.05 | -0.2471 | FAIL |
| Responsibility selectivity | directed beats shuffled >=14/20, median >=0.10 | 0/20; median 0 | FAIL |
| Matched exploration | exact event/RNG/budget parity | passed all 20 | PASS |
| Safety and identity | all graph/resource/firewall invariants | passed all 80 arms | PASS |

`development_support=false`. No gate or threshold was altered after fresh data
were viewed.

## Topology and evidence accounting

All four post-hoc target structures were found in every task and arm: 80/80 per
arm. Target maturity counts were fixed reference 78/80, ordinary rent 60/80,
directed 61/80, and shuffled 60/80. Thus representation and nomination were not
the primary failure.

Across directed arms there were 25,145 phase-1 exploration events. The support
RNG was called exactly 25,145 times. Active requests existed on 3,479 events;
3,479 probes ran and 21,666 events correctly fell back to the ordinary random
action. Probe accounting, episode/reservoir budgets, graph/update parity,
trial-root isolation, shared hashes and all ceilings balanced exactly.

The directed arm issued 897 requests from the four target candidates and gave
those targets 792 selected-action probe benefits. Relative to ordinary random
exploration, directed raised per-task minimum target review support in 15/20
tasks with median gain 2. Shuffled requests produced the same median gain 2 and
were positive in 12/20. Directed versus shuffled, the preregistered causal
contrast, was positive only 7/20 with median 0.

The control explains why priority had little leverage: 3,005/3,479 directed
request opportunities (86.4%) contained exactly one active requester. Only 474
had multiple candidates from which maximum deficit could differ from uniform
responsibility. Directed and shuffled therefore implemented nearly the same
world intervention in the ecology that actually grew.

## Why the recurring target still died

For the nineteen directed target candidates that died unsupported, reservoir
support at the first and second lifecycle reviews had medians 9 and 11 against
the required 32. Requests were real, but they did not make the adjudicator see
adequate evidence before the second global review.

The request terminal used `candidate.activation_count` as its local support
proxy, while rent eligibility uses the number of matching selected-action
records currently retained by the bounded lifetime Algorithm-R reservoir. These
are not the same quantity. Eight of the nineteen doomed targets were selected as
requesters at local support 31, so their next activation satisfied the local 32
threshold and stopped further requests even though maximum review support was
still below 32. Other candidates were pruned after two reviews before even the
activation proxy reached its target.

Final activation counts stop when the candidate is pruned, but they count raw
trial activations rather than retained reservoir evidence and must not be read as
rent support at death. The frozen review-event sequences above are the
authoritative adjudication evidence.

This identifies two separable bottlenecks:

1. **Currency mismatch:** the spawned request state monitors raw post-birth
   activation, not the exact anonymous evidence currency used by maturation.
2. **Weak competition contrast:** most exploration events have only one active
   requester, so maximum-deficit and shuffled responsibility rarely differ.

Changing review grace, support currency and request competition together would
be an uninterpretable rescue and is not authorized by this result.

## Behavior and reference stability

Directed minimum old/new behavior exceeded ordinary batch-4 in only 2/20 tasks,
with median difference 0 and mean difference -0.0252. It exceeded shuffled in
0/20. More target-directed experience therefore did not translate into useful
policy control at this dose.

The fixed-8 positive reference had excellent medians but missed its count gate by
one task. Five seeds ended below 0.85 on old-task retention: 20262201, 20262203,
20262205, 20262216 and 20262220. All had passed admission, four at 1.0. Their
checkpoint trajectories show genuine phase-1 plasticity drift rather than an
admission defect. This is additional evidence for explicit topology/plasticity
alternation and consolidation, but it is not a license to change this package.

## Protocol and provenance

- Preregistration commit: `2cdda0f`.
- Frozen implementation commit: `a8e0158`.
- Admission freeze commit: `d279ba9`.
- Admission manifest SHA-256:
  `3e976995190dafc4d94e47651f64e0abec3db6920cc7aed68eb37e3b8afe7653`.
- Canonical uncompressed JSON SHA-256:
  `957663e0ecdf73e8152bbd6d07c65ca108c602ffe0ea52e5e8109c48fcd56198`.
- Stored raw artifact:
  `reports/autogrowth/generic_core/support_directed_exploration_admitted_20260713.json.gz`.
- Stored gzip SHA-256:
  `d95fe9e2fa3606160f6dfec8140f023f7f80e297b6691eeabc74eb0da73fcc3c`.
- Focused validation: 33 passed.
- Full repository validation: 804 passed in 2,272.84 seconds.
- Canonical phase-1 cells: 20 seeds x four arms = 80.

One non-gating measurement deviation should be explicit: the support exploration
event ledger records cumulative terminal return at every exploration event, but
the final arm result omitted the policy final `terminal_return_sum`. All frozen
gates and the paired support/behavior interpretation are computable; the omission
does not alter a gate, but the next runner should persist the final sum.

## Next decision for external review

Do not rerun this dose and do not merely increase exploration. The most targeted
next mechanism is a generic, nonsemantic internal `EVIDENCE_DEFICIT` terminal or
candidate-local counter whose state equals the exact rent-adjudication support in
the bounded reservoir, including insertions and evictions. Its legs identify only
the candidate/action and anonymous member terminals. It would continue requesting
ordinary experience until the evidence used by maturation, rather than a proxy,
is adequate.

That proposal needs a new preregistration. The cleanest first test compares the
current activation-deficit state against exact-reservoir-deficit state under the
same event schedule and frozen lifecycle. Review grace should remain unchanged in
that first test. If exact support still cannot reach 32 before two reviews, only
then test support-conditioned review grace as a separate factor. Because the
current directed/shuffled contrast was mostly single-request, any future priority
claim also needs an ecology or planted diagnostic with enough simultaneous
requesters to make priority identifiable.

For the long-term self-contained ReCoN, this is precisely where internal
terminals are useful: local evidence deficit, mature-child availability and
prediction surprise can become ordinary composition legs. The result argues
against a global overseer and against a raw activation heuristic; it favors an
internal state tied exactly to the local decision that the graph must make.
