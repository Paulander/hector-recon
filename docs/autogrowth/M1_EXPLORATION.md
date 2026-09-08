# M1 exploration comparison

Protocol declared before new play. Follow the completed failure diagnosis at
`ff71baaaf85d46dc2f394e9aeab2df6f77c34d57`. The stalled seed 9 already admits a
perfect ranking on each examined split, but has not learned it. Actual successful
experience in the corner family was not recoverable from old aggregate logs.
This tests the existing exploration parameter, not a new learner mechanism.

## Fixed experiment

- Restore final event-4,096 actors from the completed long-play reference
  `a21473e7b818271fbd5424204ea83d49c2d550f8`: seeds **4, 7 and 9**, respectively
  strong retention reference, improving actor and stalled actor. Inherited
  development scores are **128, 126 and 111 / 128**. These are selected histories.
- Clone each endpoint into **exploration 0.25 and 0.50**. Only this saved config
  field changes. Keep learning_rate=0.3, max_conditions=64, births_per_episode=2,
  grace_episodes=256, prune_weight=0.02, normal growth/pruning and all other
  settings. Do not attach a nominee, freeze topology or add a chess feature.
- Continue every arm from **4,096 to 6,144**, **2,048 additional rewarded moves**.
  Use the original deterministic shuffled 256-position training schedule and
  verify its complete inherited prefix. Each row has eight more opportunities.
  No diagnosed-family oversampling or schedule adaptation.
- Evaluate all 128 existing development rows at **4,608, 5,120 and 6,144** with
  learning/exploration disabled. Reuse the inherited baseline without replay.
  Save every **128-decision block** and actually reload each evaluated checkpoint.
  No score selects endpoints, checkpoints, arms or further play.
- **12,288 training + 2,304 evaluation = 14,592 actual moves**. No laboratory
  alternative transitions and no final-test access. **Six worker processes**,
  **3,600 seconds per arm**, one attempt. No automatic retry, extension or resume.
  Preserve failed/partial action logs and checkpoints with explicit accounting.
- Both arms have identical initial exploration/birth RNG states and exercise
  opportunities. They do **not** have per-event matched exploration randomness:
  the unchanged implementation draws a random action only when its exploration
  coin succeeds, so rates can shift later draws. Do not quietly change that law
  for coupling or claim identical later RNG streams. Lifecycle divergence can
  also change proposal opportunities. The paired treatment includes these effects.

## Information and evidence

The unchanged graph observes only feature terminals and executes its selected
opaque binding through its actuator terminal. The unchanged coach returns only
the actual action-bound scalar reward (+1 observed mate, -1 M1 failure).

The runner appends event, pool index, actual submitted action, reward, reason and
real-move count **after** action and feedback. Logs never enter the organism or
coach, and contain no alternative-action grades, graph features or family label.
They are private evidence, retained with the checkpoints. Family classification
and counts run only after the experiment, without any further chess transitions.
An interrupted log may lag at most the in-flight action; preserve the bounded
pending-unit uncertainty rather than silently replaying it.

Primary: each seed's final development difference, 0.50 minus 0.25. Report every
milestone, gains/losses against the inherited baseline and between paired arms,
and fully solved symmetry orbits. Secondary: actual training wins/opportunities
by family and fixed interval; how many distinct positions yielded a win; birth,
retirement and graph cost. Extra exploration naturally changes training success;
judge learned behavior with exploration disabled at the fixed evaluations.

Separate outcome possibilities: extra successful experience with later policy
improvement; extra wins without retained improvement; or no useful extra wins.
None alone proves a complete causal credit explanation. No learned symmetry
sharing, adaptive structural selection, general M1 mastery or handover claim.
Do not promote 0.50 to the default from three selected histories. A supported
next experiment may examine selected-action credit; do not author a corner rule.

The user's compactness/reuse discussion is a further structural milestone, not
a new treatment here. Current random births create shallow one-to-three-reader
conditions; arbitrary learned factoring and symmetry sharing remain unproved.
The old edge precedence is also absent from this terminal adapter: file/rank
are separate coordinates and both corner edge flags can confirm simultaneously.

## Run and tests

Use Python 3.12, chess 1.11.2, numpy 2.3.5, hash seed 0 and numerical-library
threads one, as in the source runs. Run the full required branch suite first.
New focused tests check sole-field treatment, source/schedule rejection,
terminal-only measurement and exact real-move accounting, logger equivalence to
ordinary learning, checkpoint/reload continuity, partial-log retention and
serial/parallel agreement. The only existing runner change is an optional
training-loop callback; its default remains the previous ordinary loop. No
learner, feature, reward or formal-engine source changes.

```bash
python scripts/autogrowth/run_m1_exploration.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --reference reports/autogrowth/development/M1_LONG_PLAY_20260907.json \
  --private-source snapshots/autogrowth/m1-long-play-seeds4-9 \
  --output reports/autogrowth/runs/m1-exploration-seeds479 \
  --private snapshots/autogrowth/m1-exploration-seeds479 \
  --seeds 4 7 9 --episodes 6144 --evaluate-at 4608 5120 6144 \
  --block 128 --workers 6 --wall-seconds 3600
```

## Completed result — 2026-09-08

The protocol and implementation were published before play at
`ea188d30a464e684f8ca79e0871e95e305e3fc9e`. All **215 required branch tests passed**
in 202.65 seconds, including exact logger/ordinary-loop agreement at both rates
and serial/parallel agreement. All **14,592 actual moves** completed in one
attempt: **12,288 training** (7,994 mates) and **2,304 evaluation**. Each arm took
1,150.333–1,280.069 seconds, below its 3,600-second cap. No retry, extension,
alternative-action grading or final-test access occurred. Full evidence is in the
[public aggregate](../../reports/autogrowth/development/M1_EXPLORATION_20260908.json).

Development mates out of 128; event 4,096 is inherited:

| Seed | Exploration | 4,096 | 4,608 | 5,120 | 6,144 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4 | 0.25 | 128 | 128 | 128 | 128 |
| 4 | 0.50 | 128 | 128 | 128 | 128 |
| 7 | 0.25 | 126 | 126 | 128 | 128 |
| 7 | 0.50 | 126 | 120 | 128 | 128 |
| 9 | 0.25 | 111 | 122 | 124 | 124 |
| 9 | 0.50 | 111 | 120 | 124 | 124 |

**Every final pair ties, including its exact solved/failed row partition.** At
the first evaluation, higher exploration loses six paired mates for seed 7 and
two for seed 9; the second and final evaluations tie. This provides no measured
final-score reason to increase exploration. It does not establish equivalence on
other histories or optimality of either setting, particularly with ceiling scores.
Initial RNG states matched, but later conditional draws can diverge as declared.

### Learning occurred, and the residual failure changed

Seed 7 recovered its two old lost rows and finished with all 25 development
symmetry orbits solved in both arms. Its 0.50 arm temporarily lost six additional
previously solved rows, all in corner (2,1), then recovered all eight failures by
5,120. Seed 4 retained every development success at every measured milestone in
both arms. Neither observation proves continuous stability or slow consolidation.

Seed 9's net gain of 13 consists of **17 gained rows and four lost rows** in each
arm. It learned **all** of its formerly failing corner (2,1) family. Its four
final failures are new losses in corner (1,2), present at every new evaluation.
They are development rows **6, 9, 15 and 105**, all one symmetry orbit
**`10,54,0`**; for example White king b3 / rook g7 / Black king a1. Final family
scores are **86/86 aligned, 21/25 corner (1,2), 17/17 corner (2,1)**. Thus 124 does
not mean four remnants of the old 17-case failure. Both arms finish with 24 of
25 development orbits completely solved.

This confirms further learning of the historically difficult family under the
existing terminal/growth/credit path. No corner predicate or authored strategy was
added. It also confirms incomplete retention within these selected histories.
It does not identify whether the four new losses arise from weight interference,
retired distinctions, generalization to this orbit or their interaction.

### What actual experience shows

Both arms received eight appearances of every training row. Seed 9's actual
successful actions, classified only after all play finished:

| Training family | Opportunities per arm | Wins at 0.25 | Wins at 0.50 |
| --- | ---: | ---: | ---: |
| Aligned kings, separation two | 1,656 | 1,314 | 925 |
| Corner (1,2), containing the new development-loss family | 232 | 167 | 130 |
| Corner (2,1), the old failure family | 160 | 106 | 67 |

Every training position in both corner families produced at least one successful
action in each seed 9 arm. Training/development orbits are disjoint: this does
not mean the particular lost development orbit was trained or successfully
executed. Nor do historical wins establish the final training policy's score.

Within this continuation, the first logged corner (2,1) win occurs at event 4,351
for 0.25 and 4,341 for 0.50. In the first 512-decision interval, the arms then
accumulate 18 versus six wins in that family; totals become 106 versus 67 by the
endpoint. These are actual successes, not all guaranteed exploratory choices:
the logs do not label the internal exploration coin. More exploration did not
produce more total successful experience here. Across all three seeds, 0.25
recorded **4,695/6,144** training mates versus **3,299/6,144** for 0.50. Exploration
can displace already successful actions; training success and evaluated policy
quality are distinct measures. The earlier prefix still has no per-action logs.

Normal structural turnover continued. New births/retirements were 178/179 versus
136/137 for seed 4, 66/64 versus 90/89 for seed 7, and 140/138 versus 124/122 for
seed 9. Final live populations were 63–64. Survival and these counts do not prove
adaptive proposal selection, causal maturity, minimality or learned reuse.

### Integrity and retained evidence

All configurations and inherited states matched; only exploration differed.
Completed shadow histories stayed unchanged. Every block's action/outcome digest
was reconstructed from its post-feedback log and matched the runner's counts.
All **18 evaluated payloads** were independently verified against their complete
reported snapshots; all six final pointers restored. All **162 source payload
hashes** stayed unchanged. No post-play analysis made additional chess moves.

The first post-play check found two leftover final-evaluation pending markers for
seed 7. Both arms already had complete endpoint reports and progress records.
The exact saved payloads, full logs and move counts independently verified their
completion. The markers are retained and explicitly reconciled in the aggregate;
no action was replayed and no extra move budget was inferred from stale markers.
Their persistence is a bookkeeping issue, not evidence of failed learning or an
established formal-engine defect. Do not use a marker alone to resume a finished
arm; reconcile it with committed progress and payload identity first.

All **120 new immutable checkpoints** and all six actual-action logs are preserved
in a verified private archive, SHA256
`11dd7015e1a1f7cd9988bdb262835821b8fb1aee03d3357c203e6e83be1f4b6e`.
Trained payloads remain outside git. The final test remains unopened.

### Next bounded target

Keep **0.25 as the unchanged working exploration setting**; this comparison gives
no benefit for promoting 0.50. The closed run must not be extended automatically.
The next focused attribution is **loss of the other corner alternative during
learning**: use the saved seed 9 trajectories and actual-reward logs to examine
the four newly lost rows, with seed 7's recovered actor as reference. First check
whether the current saved conditions can support retaining both alternatives;
then examine selected-action credit and changed/retired contributions. The old
event-4,096 capacity result does not automatically survive later turnover.

Declare the analysis and any new actor/laboratory transitions before executing
it. Preserve every outcome; do not replay logged actions as training, supply a
corner rule, use a fitted solution, freeze all growth or introduce a retention
controller by assumption. Substantial positive family experience rules out a
simple family-wide absence of successes in this continuation, but it does not
prove which local learning law needs correction. Broader orbit coverage, generic
reuse/simplification and tiny independently trained child-competence/delegation
remain distinct milestones. Perfect viewed M1 is not their universal prerequisite.
Main retains its stable learner and original 96-condition default; 64 remains a
provisional experimental profile.
