# Saved M1 representation diagnosis

Protocol declared before outcomes, from `ea74d8fff85409336a8e9c302a28941006ca7cb7`.
This is an offline investigation of the completed ordinary-M1 experiment. It
does not train an actor or change any runtime mechanism, feature or reward.

## Question and fixed scope

Seeds 2 and 3, roles no addition and ranked addition, saved endpoints 384 and
1,024: eight actors. Seed 2 is the recovered reference; seed 3 is the persistent
weak case. Use all 256 training-pool and 128 development-pool positions in their
existing file order. Do not open the final test or select a checkpoint by score.

First, in the offline laboratory only, read each legal binding's declared
coordinates through the existing leaf reader implementation. Grade every legal
alternative once on an independent board copy. These labels are never supplied
to an actor, never saved as a training dataset, and never used to choose a
deployed action. This is the same permitted environment outcome test used to
curate M1 exercises, separated from the unchanged opaque coach.

For each frozen actor, compare three signatures: the complete declared schema,
the reader predicates it actually grew, and their current Boolean compositions.
Count winning/losing alternatives that look identical. Using the existing
reverse-lexical slot tiebreak, identify rows where every signature class would
select a failing representative. No weights on those signatures can solve such a
row. The resulting per-row upper bound need not be jointly attainable by one
global weight vector; it is not a trained score or a new selector.

Replay the actor normally on every position with learning disabled. Independently
check that its formal support and chosen action match the declared Boolean gates
and learned SUR weights. Require exact reproduction of historical development
outcomes/actions and unchanged learned state. Only the graph executes the actor's
move; the mathematical comparison observes and checks it afterwards.

An additional offline linear feasibility check asks whether weights could rank
**every** winning option strictly above every failing one. Feasible solutions are
checked directly for their margins, then discarded. Infeasibility is not proof
that no successful policy exists: one of several wins may suffice, or a favorable
tie may work. These fitted comparison weights never enter an actor or report.
The diagnostic uses [SciPy's linear-programming interface](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html),
with unrestricted signed coefficients, a unit margin and HiGHS. This dependency
is confined to the diagnostic; it is not a learner mechanism.

## Resources and separation

- **7,039 laboratory alternative transitions:** 4,669 train-pool and 2,370
  development-pool legal alternatives, each graded once and shared only by the
  offline analyses.
- **3,072 frozen actor moves:** eight actors times 384 positions.
- **10,111 total explicit move executions; zero training moves.**
- One process, **1,200-second cap**, no retry or automatic extension.
- Original source, dependency, pool and checkpoint hashes must match before
  loading saved trusted state. Record diagnostic source and SciPy versions too.
- Retain completed actor reports and a failure record if interrupted; never
  publish a shortened run as complete. Report any unreturned in-flight action.
- Publish aggregates only. No boards, action lists, trained weights, offline
  fitted weights or alternative-action datasets enter git or a policy.

The source is `src/recon_lite_chess/experiments/m1_representation.py`; the runtime
and existing experiments do not import it. The eight focused checks cover Boolean
semantics (including exactly-one for three-reader XOR), signature/tiebreak bounds,
joint Boolean expressivity, discarded fitted coefficients, actual move accounting,
terminal-only reads, disabled learning, source rejection before unpickling, and
the time cap. The standard terminal/coach/formal-choice checks accompany them.

```bash
PYTHONHASHSEED=0 PYTHONPATH=src:libs/recon-lite/src \
python scripts/autogrowth/diagnose_m1_representation.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --reference reports/autogrowth/development/ORDINARY_M1_CONTINUATION_20260907.json \
  --previous reports/autogrowth/runs/ordinary-m1-seeds123 \
  --private snapshots/autogrowth/ordinary-m1-seeds123 \
  --output reports/autogrowth/runs/m1-representation-diagnosis \
  --wall-seconds 1200
```

## Decision after evidence

A formal computation mismatch justifies fixing that implementation defect and
retesting. Representation collisions justify investigating a generic birth or
composition correction, not supplying the missing chess answer. Distinguishable
options with poor learned ordering motivate a credit/optimization investigation;
they do not by themselves identify a particular update-law bug. Do not force a
mechanism tweak if this run only locates, rather than resolves, the cause.
