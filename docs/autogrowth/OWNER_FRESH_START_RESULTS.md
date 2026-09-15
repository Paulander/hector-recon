# Fresh owner-local learning: completed comparison

2026-09-15. Fixed protocol: [OWNER_FRESH_START.md](OWNER_FRESH_START.md), committed
before play as local `b5c75d442cad18b66de55dc2946096fae9ef8601` and published with
the identical tree as remote `e3cf9a31f1a276eeb4dbe0252f2202825501a297`.

**All six fresh runs completed. Residual-ranked birth selection finishes44/48
versus41/48 for random selection across three seeds. It improves two seeds and
worsens one; retention remains imperfect. No split-timing knob was introduced.**

**Scope: these are all16 states of a four-bit Boolean task, not mate-in-one
chess positions. No new chess performance was measured in this experiment.**
See [OWNER_FRESH_FAILURES.md](OWNER_FRESH_FAILURES.md) for the task definition,
growth/weight-update distinction and the subsequent read-only failure audit.

The user asked to start new networks from the beginning. Each learner therefore
starts with zero completed actions, one untrained owner, zero-valued learned
bias, no learned scoring features and no imported checkpoint. A generic unbound
request site keeps the initial graph formally valid without inspecting the
environment. The actual catalog and measurements are read only by terminals.
The existing ownership and exploration rules apply from action zero.

This differs from the preceding study's conversion after640 flat training
actions. It is a fresh acquisition comparison, not an otherwise identical
warm-start replication. "Stronger learned starting policies" meant already
acquired useful behavior, which is a separate retention question. Some fresh
arms naturally solve all eight A rows by640, but this protocol does not select
or extend prefixes using a maturity score.

## Matched outcomes

Each new seed receives random/current and residual/current arms. Both train
for1,920 actions:640 A,640 mostly B,640 mostly A, with the same seed-specific
fixed task order. Both retain the same24-candidate pool, compatibility gate,
25% random eligibility path, local64-visit clock, four-owner limit, credit,
pruning and current split/birth schedule. Evaluation uses disposable clones.

| Selection | Seed12 | Seed13 | Seed14 | Total | Final physical nodes, seeds12/13/14 | Final parameters |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Random | 15/16 | 12/16 | 14/16 | 41/48 | 335 /335 /343 | 28 /28 /28 |
| Residual-ranked | 14/16 | 14/16 | 16/16 | 44/48 | 333 /335 /339 | 28 /28 /27 |

Only ranked seed14 reaches16/16. It first does so at768 actions and stays perfect
at every subsequent64-action checkpoint through1920, including the return to
mostly-A training. This does not establish behavior between measured checkpoints.
Final A scores are8/8 in all six arms; endpoint differences are entirely B.

Ranking makes14,19 and19 evidence-ranked selections in seeds12/13/14; the remaining
10,5 and5 use the random/fallback path. Every arm accepts24 births and finishes
with four owners. Ranked seed14 prunes one condition; all other arms prune none.
There are no allocation-budget rejections. Physical counts include the formal
observer branches and execution instances, not just learned concepts.

## Retention must be measured separately

References below are rows actually correct at the declared phase boundaries,
not the initial chance-level successes. Full row histories are in the JSON report.

| Seed / selection | A correct at640 | Fewest of those A rows retained after640 | B correct at1280 | Those B rows retained at1920 | Fewest retained after1280 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 12 random | 5 | 3 | 7 | 7 | 7 |
| 12 ranked | 7 | 3 | 7 | 6 | 6 |
| 13 random | 8 | 7 | 5 | 4 | 4 |
| 13 ranked | 8 | 8 | 6 | 6 | 6 |
| 14 random | 5 | 2 | 8 | 6 | 5 |
| 14 ranked | 8 | 8 | 8 | 8 | 8 |

Seed12's ranked arm loses boundary B row11, while its matched random arm retains
all seven boundary successes. Random seed13 loses B row6; its ranked partner
retains all six boundary B successes and all eight boundary A successes at every
subsequent scheduled checkpoint. Random seed14 loses B rows14/15 at endpoint and
temporarily retains only five of the original eight; ranking retains all eight.
All A losses recover by endpoint, which should not erase the transient losses.
The three-seed aggregate supports further investigation, not a universal fix.

## Fresh-start development exposes an existing delay

All six learners split at actions64,191 and192, exhausting the four-owner budget
before any ordinary scoring-feature birth. Child visit counts start at zero,
and a successful split uses that owner's development opportunity. The first
ordinary feature arrives at443 in seed12 and439 in seeds13/14, once a child has
its own64 observations. Scores stay8/16 through the448 checkpoint. The new
conditions start at zero and learn only from subsequent activations.

In this cohort the paired split routes and owner exposures remain matched;
final leaf visits range430–435. Initial A-only exposure cannot support a split
on the never-varying context coordinate. The local rule chooses available
supported variation, including nuisance variation, without a task oracle.
This is evidence about the current startup sequence and sample cost. There is
no delayed-split control here, so it does not show that delaying splitting would
improve final performance. The user's suggestion remains a later experiment;
no timing, maturity or resolution knob was added to these runs.

One ranked seed12 birth receives no subsequent live credit. It is the condition
`coordinate2=True AND coordinate4=False`, born at1475 in owner6. Its own probe
history contains47 earlier confirmations, so lack of later credit is not proof
of impossibility. The other143 births receive actual live credit. Probe evidence,
live credit and semantic usefulness are different measurements; no diagnostic
repair or rare-condition exclusion was applied.

## Locality and verification

The learner receives the declared typed schema, state-coordinate scope and
generic configuration at construction. During learning it receives formal
selected-binding confirmations and the matching actual scalar outcome. Split
nomination, birth selection and retirement use the active owner's internal
history. Resource ceilings constrain allocation; they do not identify useful
routes. No task rule, phase label, alternate-action reward, externally fitted
weight, evaluation score or graph-wide performance controller enters growth.
The supplied generic Python law is not itself a graph-learned controller.

All11,520 training actions,2,976 scheduled evaluation actions and2,976 frozen
reproduction actions complete:17,472 actual environment actions,180 blocks and
186 checkpoints. The verifier checks immutable submissions/credits, scalar
credit arithmetic, complete manifests, restored ownership, every owner's full
candidate residual history and all scheduled evaluations. Initial paired state
and final exploration RNG equality pass. No old checkpoint payload is imported.

All79 runtime-source hashes match their saved snapshots, including all76
unchanged files from the preceding study. All52 focused tests pass, including
six fresh-start cases. Preflight failures exposed an empty formal request root
and an invalid assumption that re-pickling preserves byte identity; both were
corrected before cohort play. Initial graphs retain a generic unbound child and
verification compares complete restored state, while stored payload checksums
remain exact. No cohort retry, continuation or parameter change occurred.

Runtime875.678s (14m36s); peak RSS40,772KiB (39.82MiB), one CPU, inside the fixed
2GiB and3600s worker limits. No training process remains running. The machine-
readable summary and checks are in `reports/autogrowth/development/` under
`OWNER_FRESH_START_20260915.json` and `OWNER_FRESH_START_CHECKS_20260915.json`.

The private work branch contains this experiment and its evidence. Main remains
unchanged. Keep random nomination as the control; ranked/current remains a
promising experimental option. A separate mature-policy retention study and
any change to splitting, protection, merging or reuse still need their own
defined comparison. The current fresh-start protocol is closed.
