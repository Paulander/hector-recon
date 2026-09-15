# Context-compatible growth: completed comparison

2026-09-14. Protocol: [OWNER_COMPATIBILITY.md](OWNER_COMPATIBILITY.md), committed
at `eb1f0db5` before play; execution followed the passing checks at `1f97242c`.
Branch `codex/context-owned-decisions`; no external publication.

**The local contradiction check prevented all nine impossible new births in
these runs, reduced graph cost, and preserved both observed learning trajectories
exactly. It did not fix the remaining acquisition or retention failures.**

These are results on the existing 16-row Boolean development task, not chess
mastery or broader retention evidence. Both saved event 640 sources were reused.
Each arm received 1,280 additional actual training actions on the unchanged
mostly-B then mostly-A fivefold schedule. Both arms used adaptive owner splitting;
the sole configured difference was compatibility.enabled.

| Seed | Initial score | Final score, both arms | Physical nodes: control → check | Parameters | Registered expression definitions | Impossible births: control → check |
|---|---:|---:|---:|---:|---:|---:|
|10|8/16|11/16|473 →403|42 →35|87 →76|7 →0|
|11|6/16|14/16|557 →531|46 →44|97 →93|2 →0|

Both pairs finished with four owners, three splits and maximum expression depth 4.
Physical nodes fell 14.8% and 4.7% respectively. Parameter, expression-definition
and execution-node counts describe different things; none is a count of
independently discovered chess concepts. No duplicate merging occurred.

## What the check actually did

The organism checks only its own immutable route C, the proposed expression F,
and declared typed sensor domains. It rejects when C AND F is proven impossible.
For example, seed 10's owner 6 already requires x=true and y=true. At event 1088,
its proposed x=false reader was rejected before any nodes or weights were created.
No observations, frequency thresholds, phase labels, correct-action targets or
alternative-action rewards entered this decision.

There were 15 and 14 raw proposals per arm, with exactly matching proposal sequences,
owner visits, opportunity schedules and final proposal/exploration RNG states.
Five already-seen proposals were skipped across each two-seed condition. Of the
remaining 24, the enabled check admitted 15 and rejected 9. No replacement draws,
parameter-ceiling skips, graph-budget rejections or inconclusive checks occurred.
Every admitted new condition later participated in actual credit in these runs;
participation alone does not establish behavioral usefulness.

Checks consumed 145 declared-domain assignments and 2,480 node/child evaluation
operations in total, taking about 0.00385 s. These are logical assignments, not
environment interactions. Nine scoped proofs were cached; this experiment had
no repeated rejection requiring a cache hit. Cache scope/invalidation, bounded
eviction, typed domains, OR/exactly-one semantics and unknown-permits-trial are
covered by mechanism tests. Future changed/noisy/temporal predicates need explicit
semantics; the current proof does not silently generalize to those readers.

## Behavior and retention

Across both pairs, all 2,560 paired training actions and rewards match. Predictions,
active expression sequences, credit denominators and per-weight updates also
match exactly after accounting for changed condition storage IDs. All 40 paired
full evaluations match, not merely their scores. The disabled extension separately
reproduces every original adaptive control state and training record from the
previous fivefold run. Its logging does not alter that learner.

The prior failures therefore persist unchanged:

- Seed 10 loses/relearns B row 6 at event 1472, then loses A rows 8/9 at 1536 and still
  misses them at the endpoint. Final A/B scores are 5/8 and 6/8.
- Seed 11 repeatedly swaps A rows 4/12 and ends failing 4 while solving 12. Its final
  A/B scores are 6/8 and 8/8.
- Both actors retain their mostly-B-boundary B successes at the final endpoint.
  This is not uninterrupted retention, as seed 10's temporary B loss shows.

Why unchanged behavior is plausible: if C·F is always zero, its weighted term
adds zero to action support and never enters the active-credit denominator.
Avoiding that birth saves structure without altering those calculations. This
is not a universal trajectory-invariance theorem: resource ceilings, changed
proposal opportunities or other developmental interactions could later matter.

## Verification, resources and continuation

Status **complete**, no retry. All 5,120 training actions, 1,280 scheduled evaluation
actions and1,280 frozen reproduction actions completed: 7,680 actual environment
actions overall. The original immutable-block verifier passed all 80 blocks and 84
new checkpoints, plus both byte-identical source payload copies were preserved.
All 74 execution-source hashes match their snapshots; all 63 original learner/core
files remain unchanged. All 284 distinct tests passed in this increment, including
13 new tests and all 221 required legacy tests. Repeated new tests are counted once.

Runtime 1,312.882 s (21m53s); peak RSS 41,216 KiB (40.25 MiB), one CPU, under the 2 GiB
and 1,800 s worker limits. The independent 1,830 s guard was not needed. Recorded
training/block/evaluation time was 244.44 →227.25 s for seed 10 and 329.11 →318.06 s
for seed 11. These sequential timings include checkpoint/recorder costs and are
descriptive, not a replicated speed benchmark. No process remains running.

Keep this check as the experimental reference for avoiding contradictory births.
The next proposal should target useful structure *within* compatible contexts,
with separate controls for proposal quality and development opportunities. Do not
turn this result into a blanket ban on state-only or rare unobserved definitions,
or a reason to merge duplicate credit, freeze weights, clean inherited conditions,
or add replacement draws. Those are different interventions. Local nomination
and compatibility are supplied generic developmental laws, not a graph-learned
development controller. No further experiment or publication was launched.

Evidence: `snapshots/autogrowth/owner-compatibility-20260914/`,
`reports/autogrowth/development/OWNER_COMPATIBILITY_ANALYSIS_20260914.json`, and
`reports/autogrowth/development/OWNER_COMPATIBILITY_CHECKS_20260914.json`.
