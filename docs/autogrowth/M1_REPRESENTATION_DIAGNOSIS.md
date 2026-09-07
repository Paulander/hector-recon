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

## Completed result — 2026-09-07

The original protocol/implementation was published at `c6997362`; the separately
declared tie-aware follow-up at `ec8323f9`. The original run completed in
1,136.752 seconds within its 1,200-second cap, with all 10,111 declared executions.
The follow-up completed its separate 7,039 laboratory transitions within 180
seconds. Combined: **3,072 frozen actor moves, 14,078 laboratory transitions,
zero training moves**. All 73 focused tests passed before the subsequent capacity
probe was added. No retries, shortened results or final-test access occurred.
The [aggregate evidence](../../reports/autogrowth/development/M1_REPRESENTATION_DIAGNOSIS_20260907.json)
contains both protocols, counts, split results and elementary contradiction
certificates. No learned weights or alternative-action dataset is published.

All eight actors reproduced their exact development actions and outcomes. All
sixteen split evaluations preserved learned state and matched formal support and
choice to the declared Boolean/weight calculation. No formal implementation bug
was found. Within each examined position, neither the complete schema nor the
existing reader predicates collapsed a winning and losing alternative. This is a
local finding; it does not prove universal sufficiency of the feature space.

| Seed | Actor | Saved event | Development mates | Local signature/tie upper bound |
| --- | --- | ---: | ---: | ---: |
| 2 | No addition | 384 | 121 | 123 |
| 2 | No addition | 1,024 | 124 | 124 |
| 2 | Ranked | 384 | 98 | 123 |
| 2 | Ranked | 1,024 | 124 | 124 |
| 3 | No addition | 384 | 66 | 128 |
| 3 | No addition | 1,024 | 66 | 128 |
| 3 | Ranked | 384 | 66 | 128 |
| 3 | Ranked | 1,024 | 66 | 128 |

Seed 2's final four development failures cannot be repaired by changing the
existing weights: compositions alias the relevant alternatives and the existing
tie selects the failing representative. Seed 3 has no such within-position gate
alias. Its 128 upper bound is not an attainable-score certificate: a single set
of shared weights must also work across positions.

The [tie-aware follow-up](M1_RANKING_CERTIFICATE.md) closes that qualification.
Every saved graph has an explicit contradictory pair of weight requirements on
both splits. Some shared gate-weight difference must be positive in one case and
nonpositive in another (or a zero difference must be positive). Thus **none of
these particular fixed graphs can solve its whole examined split by weight
changes alone**, even using its existing tie rule. For seed 3 this proves a
capacity limitation, not that 66 is its best achievable score. It does not
attribute every error to structure or identify a universally correct birth law.

This rules out treating the remaining problem as merely a learning-rate tune or
a chess-rule fix. It motivates a small test of the current growth budget before
inventing another mechanism. See [M1_CAPACITY_PROBE.md](M1_CAPACITY_PROBE.md): restore
identical saved no-addition actors, compare 32 versus 64 allowed conditions, and
let the unchanged generic birth/credit laws receive matched actual chess play.
That probe supplies no particular reader, composition, answer or fitted weight.
