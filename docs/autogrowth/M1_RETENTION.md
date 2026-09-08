# M1 retention: saved structure and actual credit

Protocol declared before execution, following the exploration result at
`37e064ecbd6203163c8376c5a0882ed8070dbcae`. Seed 9 learned its entire old corner
failure family but lost four previously solved rows (one other orbit). Both
exploration rates ended with the same outcome partition. This attribution asks
whether current structure can retain both alternatives and how recorded credit
and structural changes account for the lost ordering. No learner changes.

## Fixed scope

- Use only the existing 256 training and 128 development positions. Final-test
  rows remain unopened. Grade every legal alternative once in the isolated
  laboratory: **7,039 transitions**. These answers never enter a learner.
- Restore and formally replay five saved actors: seed 9 at 0.25/events **4,096,
  4,608 and 6,144**; seed 9 at 0.50/event **6,144**; and recovered seed 7 at
  0.25/event **6,144**. Each acts once on every training/development row with
  learning and exploration disabled: **1,920 frozen actor moves**.
- Total **8,959 diagnostic executions, zero training moves, zero learner update
  calls**. One process, **2,400 seconds**, one attempt, no automatic retry or
  extension. Preserve completed reports and exact counts on interruption.
- Check the formal graph's supports and choices against the saved Boolean
  conditions and weights; reproduce historical development outcomes and digests.
  Check ranking feasibility on each split and their **combined union**. A feasible
  union is one shared set of possible weights, still not learned or generalizing
  performance. Discard all fitted coefficients. Use exact tie-aware checks when
  strict feasibility fails; numerical uncertainty stays explicit.
- Numerically inspect all 17 saved 128-decision boundaries for both seed 9 arms,
  without further actor actions. Track development rows **6, 9, 15 and 105**,
  orbit **10,54,0**. Separate changed retained weights, removed contributions and
  new definitions on fixed winning/finally-chosen comparisons. This is arithmetic
  attribution, not a counterfactual no-growth training experiment.

## Actual credit accounting

Use the two complete logs of actually submitted training actions and observed
rewards from events 4,096–6,143. The logged action selects which measurement vector
to examine; **only its recorded reward** enters the arithmetic. Never use a
laboratory grade as a substitute, select an alternative, call actor `act` or
`observe`, generate new experience or save an updated organism.

Reconstruct the existing one-step numerical update:
`delta = learning_rate * (observed_reward - selected_support) / (1 + active_count)`.
Add delta to the bias and each confirmed condition's fast weight. Reconstruct
the existing bias fast/slow transfer. Condition definitions, birth times and
request-count retirement times come from persistent saved history, not a new
proposal/pruning law. This is an audit calculation in separate Python numbers.

The complete live definition set and all fast/slow weights must match **every
subsequent saved boundary** within absolute 1e-8. If not, do not make an attribution
claim. Never deploy the reconstructed numbers or treat them as a trained policy.
Group actual credit to a representative lost position's fixed comparison by
time block, geometric family and reward sign. Track all four positions at saved
boundaries; a representative's credit explanation is not automatically proof
for every transformed choice. Keep the contribution of removals separate.

This can establish which actual updates and retirements account for a score
change. It does not establish what would happen under different actions,
retirements, weights or learning laws. Preserving a fixed action log while changing
policy would not be a valid on-policy comparison.

## Tests and execution

New focused tests cover numerical reconstruction through births and retirements,
both exploration rates, no environment transitions or learner updates during
credit accounting, rejection of incomplete/corrupted reward logs, joint-set
conflicts hidden by separate feasibility checks, trusted checkpoint identity and
terminal-only formal replay. Run the required full branch suite before execution.

```bash
python scripts/autogrowth/diagnose_m1_retention.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --reference reports/autogrowth/development/M1_EXPLORATION_20260908.json \
  --private snapshots/autogrowth/m1-exploration-seeds479 \
  --output reports/autogrowth/runs/m1-retention-seeds79 \
  --wall-seconds 2400
```

Use Python 3.12, chess 1.11.2, numpy 2.3.5 and the existing SciPy installation,
hash seed 0 and single-thread numerical libraries. No runtime/learner source
changes or new trained payloads. The independent expert prompt accompanies this
study but does not supply a training rule or override its declared protocol.

The next learning experiment must follow the result: distinguish lack of current
capacity from reward-credit interference before selecting one generic correction
and a matched actual-play control. Do not assume more hierarchy, more exploration,
a global freeze, a corner detector or a retention controller is the answer.

## Completed result — 2026-09-08

Protocol/code were published at `fd5df7b966b8ec8bd797d18a1da94a56e4accb7e`
before execution. **221 tests passed** in 213.44 seconds. The single diagnostic
attempt completed in **778.02 seconds**: exactly 7,039 laboratory transitions and
1,920 frozen actor moves, **zero training and zero learner update calls**.
All 120 source payloads, six action logs and six other source files retain their
pre-run hashes. No new trained payloads or final-test access. Detailed evidence:
[`M1_RETENTION_20260908.json`](../../reports/autogrowth/development/M1_RETENTION_20260908.json).

### Capacity remained available

| Actor | Training step | Train / 256 | Development / 128 | One shared perfect ranking on all 384 rows exists |
| --- | ---: | ---: | ---: | --- |
| Seed 9, exploration .25 | 4,096 | 236 | 111 | Yes |
| Seed 9, exploration .25 | 4,608 | 253 | 122 | Yes |
| Seed 9, exploration .25 | 6,144 | 254 | 124 | Yes |
| Seed 9, exploration .50 | 6,144 | 254 | 124 | Yes |
| Seed 7, exploration .25 | 6,144 | 256 | 128 | Yes |

All formal supports/choices and historical development results reproduced.
Each joint feasibility result verifies 6,655 strict win-over-loss constraints;
each row has exactly one winning action. Coefficients were discarded. Unlike the
earlier separate-split result, this establishes representational room for both
alternatives with ONE weight vector at every inspected endpoint. It does not
establish what training will converge to, or capacity between these endpoints.

Seed 9's final failures in both arms are the same four development rows plus
training rows **118 and 230**, orbit `10,62,0`. The training pair was initially
solved. Each received eight actual attempts in this continuation; .25 produced
four and three wins respectively. Thus this is not solely absence of practice,
although the development orbit itself remains absent from training. All six
final failures choose a checking rook move that leaves one legal escape. The
training-pair margins are -0.00108/.25 and -0.03713/.50; development margins
are -0.15925 and -0.13366. No rank/file precedence bug or formal-choice error.

### Actual credit explains the decline

Both 2,048-event logs reconstruct every live fast/slow weight and condition
lifetime at all **32 subsequent saved boundaries**, with maximum weight error
**8.89e-16**. No learner method or actor action was invoked for this calculation.
The representative comparison is development row 6's winning move against its
final chosen losing move. Positive margin favours the win:

| Exploration | Initial margin | Final margin | Accumulated actual credit | Contribution removed at actual retirement times |
| --- | ---: | ---: | ---: | ---: |
| .25 | +0.85216 | -0.15925 | -0.99701 | -0.01439 |
| .50 | +0.85216 | -0.13366 | -0.92437 | -0.06145 |

The two rightmost columns sum to the margin change. They distinguish actual
updates from removal at the time it happened. This is different from an endpoint
decomposition into retained, removed and newly born definitions: for .25 those
terms are -0.62465, -0.03339 and -0.35338. Both identities are valid; do not mix
their terms. New definitions also received credit. Their existence and later
weight changes are not independent causal interventions.

Grouping the ACTUAL update contributions by the position that produced feedback:

| Source of recorded feedback | .25 target-margin contribution | .50 target-margin contribution |
| --- | ---: | ---: |
| Corner (1,2), the target's geometric family | +5.25905 | +5.09721 |
| Corner (2,1), the formerly failed family | -8.19954 | -8.25057 |
| All aligned-two positions, including corners | +1.94348 | +2.22899 |
| Total credit | -0.99701 | -0.92437 |

These are cumulative contributions with cancellation, not independent effect
sizes or counterfactual performance. In .25, successful (2,1) moves alone
contributed -7.74158 to this comparison. The FIRST positive-to-negative crossing
occurred after a real successful (2,1) move at event 4,378 (completed count 4,379):
+0.18272 to -0.09640. For .50 the first crossing is likewise a successful (2,1)
move, event 4,584: +0.22406 to -0.04066. Neither step is a pruning boundary;
births start at zero weight. These particular crossings are actual shared-weight
interference, not removal of a useful node.

There are 27/.25 and 49/.50 sign crossings of this fixed pair. A positive pair
margin need not beat every other alternative, so do not call all crossings policy
recoveries. The saved full-choice calculation DOES show all four development
rows recovered at **5,888** in .25, then failed again at 6,016 and 6,144. The
old 4,608/5,120/6,144 evaluation cadence missed that recovery. In .50, the rows
are still solved at 4,480 and fail at every inspected boundary from 4,608 onward.
Saved-boundary outcomes agree across all four rows; per-event credit was computed
for the declared representative, not separately for every transformed action.

Large negative contributions involve broad target-file alignment conditions and
compositions containing them, while successful older-family experience supplies
opposing credit. There is also functional overlap: conditions 93, 124 and 364
have different definitions, but all three reduce to target-file alignment when
king separation is (1,2) or (2,1). The report includes the four-case symbolic
truth table, using their saved definitions. This is local equivalence in those
contexts, not global redundancy or proof that deduplication will help.
These descriptions are interpretations after learning. Do not
mask these definitions, promote their opposites or feed their IDs/family labels
back into training. Their harmful contribution on one target does not establish
that they are globally harmful or should be removed.

### Interpretation and next experiment

The current evidence supports **interference through shared condition weights**,
with retention and generalization still unstable despite expressible solutions.
It does not support “a missing corner node,” “pruning erased the skill,” or
“rewards never reached it” as the main explanation for this representative loss.
No new chess competence was trained in this study. Recovered seed 7 demonstrates
an actual 256/256 + 128/128 saved policy on these examined rows, not general M1
mastery or proof that seed 9's update law will converge.

Next propose one bounded ordinary-play comparison from the **4,096 checkpoints**:
keep exploration .25, cap 64, normal growth/pruning and all learning mechanisms;
compare the existing **0.3 learning rate with 0.1** across seeds 4/7/9. Declare
budgets and measurement points before play. Use new actual actions/rewards,
never replay a fixed transcript as training. Track acquisition of the old misses,
retention of prior successes, overall train/development performance and turnover.
Changing the rate can change future policy and topology; do not claim identical
later structures or use frozen-log arithmetic as its counterfactual control.

This tests a minimal step-size explanation before adding a controller. The
smaller rate is a hypothesis, not a fix already established: it could merely
delay acquisition, preserve an inferior policy, or leave systematic interference
unchanged. If it does, examine the selected-action prediction objective and
generic context-specific credit/factoring next. Broader orbit coverage remains
necessary but is a separate intervention, preserving original split assignment.
No global freeze, coach-guided retention, pattern targeting or authored corner
composition. [Independent expert prompt](RETENTION_EXPERT_PROMPT.md) invites
criticism of both this interpretation and the proposed next test.
