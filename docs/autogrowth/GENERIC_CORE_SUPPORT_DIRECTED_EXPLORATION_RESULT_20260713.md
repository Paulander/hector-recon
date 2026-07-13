# Generic-Core Support-Directed Exploration Result

Date: 2026-07-13. Track: generic-core development. Status: completed
phase-0 admission abort; phase-1 hypothesis untested.

## Verdict

The frozen execution stopped correctly at the shared phase-0 boundary. Nineteen
of twenty fresh checkpoints met the required development threshold, but seed
20262109 scored 0.8203125 against the frozen minimum 0.85. No fresh checkpoint
entered any of the four phase-1 arms. This artifact is therefore neither
support nor a scientific negative result for support-directed exploration.

The failure was isolated to the anonymous key decision. On the failing seed,
door accuracy was 1.0, key accuracy and joint success were both 0.8203125, and
quiescence pruned three unfinished trials with byte-identical deployed behavior
before and after. The proposed evidence-request mechanism targets the later
door-action composition problem and was never enabled.

## Immutable execution record

- Frozen implementation commit: `3d2d03cc24afffe73903810091dad448f9fa8c57`.
- Fresh seeds touched exactly once: 20262101--20262120.
- Phase-0 training: 4,096 episodes per seed.
- Phase-0 development: 512 rows per seed.
- Threshold: joint success at least 0.85, zero surviving trials, unchanged
  behavior after quiescence.
- Passed: 19/20; median joint success 1.0.
- Failed: seed 20262109 at 0.8203125 joint, 0.8203125 key, 1.0 door.
- All 20 quiescence checks had zero surviving trials and unchanged behavior.
- Phase-1 episodes consumed by any arm: zero.
- Raw artifact:
  `reports/autogrowth/generic_core/support_directed_exploration_20260713.json`.
- Raw artifact SHA-256:
  `7893d1f7f277a6c6b3c255b3ffd473c7543b5239383d158bb7a4073430ca4619`.

The runner, focused tests and bounded retired-seed smoke passed before fresh
execution. The complete repository suite passed 796 tests in 2,263.11 seconds.
The smoke passed clone, shared-state, capacity, role-blindness, graph/update,
trial-root, exploration-timing and cumulative probe-accounting invariants.

## Interpretation

This is an upstream curriculum-readiness failure. The common base learner had
not mastered one fresh task, so comparing bridge mechanisms from that state
would mix failure to learn the child skill with failure to acquire evidence for
a new composition. Stopping is consistent with the central curriculum doctrine:
a mature child manifold must exist before it can serve as a local goal or handoff
for the next stage.

The result also prevents a misleading rescue. Replacing seed 20262109, lowering
the threshold, proceeding with 19 tasks, or increasing its phase-0 experience
after seeing the row would all change the frozen sampling or admission rule.
None was done. The touched seed and its generated manifests are retired from
future development evidence.

## Next decision, requiring a new preregistration

The cleanest next design is an upstream, outcome-independent admission protocol:
use new seeds, train phase 0 identically, and admit seeds sequentially until 20
checkpoints meet the already established 0.85 mastery/quiescence rule. Declare a
maximum number of attempted seeds and report every rejection and the admission
rate. Freeze the 20 admitted checkpoint hashes and all phase-1 manifests before
any phase-1 arm runs. Because admission uses only the old task before the new
mapping is trained or evaluated, it separates child-skill readiness from the
bridge hypothesis without selecting on the phase-1 result.

A more expensive alternative is to preregister a larger common phase-0 budget
on entirely new seeds. That tests a different base learner and must not be
presented as continuation of this frozen experiment. Proceeding with 19 tasks or
changing the threshold post hoc is not an acceptable option.

## Relation to self-contained ReCoN and internal terminals

The current implementation is a deliberately narrow precursor to internal
terminals: an existing trial composite, using only its anonymous terminal-member
legs and local activation deficit, can request allocation of an exploration
event that would happen anyway. It cannot affect greedy scores, create reward,
or grant itself maturity. Ordinary experienced outcome remains the arbiter.

This fresh abort provides no evidence about whether those local requests work.
If a new admitted-checkpoint experiment supports the mechanism, the justified
next abstraction is a generic spawned internal terminal for local states such as
under-supported hypothesis, mature-child availability and prediction surprise.
Those signals can then become ordinary composition legs. Introducing that node
family before the narrow causal test would still confound representation with
experience allocation.
