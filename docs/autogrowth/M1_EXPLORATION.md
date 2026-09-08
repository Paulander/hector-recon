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
