# Longer ordinary M1 play: progress and retention

Protocol declared before new outcomes. Continue **all six** final 64-condition
actors from the completed capacity replication at
`6039510925b7329196cb0ec692ec3bd8d7c5a104`. Their event-1,280 development scores
were 128, 128, 128, 103, 125 and 111 for seeds 4–9. These are inherited endpoint
results, not new evaluation moves or a reason to choose a subset of seeds.

The question is whether ordinary continued learning improves weaker histories
and preserves stronger ones. Earlier short plateaus could end abruptly, but a
perfect intermediate score could also regress. Neither observation establishes
that the learning rate is too small or too large.

## Fixed continuation

- Start from the exact published final private checkpoint for each seed. Verify
  its source, transport hash, event count, complete learned-state snapshot and
  unchanged configuration. Do not replace a weaker endpoint with an earlier one.
- Continue from **1,280 to 4,096** training decisions: **2,816 new rewarded moves
  per actor**, using the same deterministic shuffled training schedule. Its first
  1,280 entries must match the inherited schedule exactly.
- Every actor retains max_conditions=64, learning_rate=0.3, exploration=0.25,
  births_per_episode=2, grace_episodes=256, prune_weight=0.02 and all other saved
  settings. Normal random births, pruning and edge learning remain active. No
  nominee, controller, feature, learning law or goal-value interface is added.
- The unchanged graph requests ordinary input terminals, selects an opaque
  binding, and requests its output terminal. The unchanged M1 coach returns only
  the submitted action's scalar outcome: +1 for actual mate, -1 for M1 failure.
  No diagnostic labels, successor scores, fitted weights or action answers enter.
- Train in fixed **128-decision blocks**. Evaluate on the same 128 development
  rows at **1,536, 2,048, 3,072 and 4,096**, with learning/exploration disabled.
  Actually restore every evaluation checkpoint before continuing. No evaluation
  score changes the next block, seed inclusion, settings or final endpoint.
- Same 256-position training pool and 128-position development pool, verified
  against the completed replication's hashes. No pool replacement or final-test
  access. No new diagnostic alternative transitions in this study.
- **16,896 training + 3,072 evaluation = 19,968 new actual moves.** The inherited
  experience and baseline evaluation are not counted again. Six seed workers,
  **4,800 seconds per seed**, one attempt. No automatic retry, extension or resume.
  A timeout/error preserves completed outputs and checkpoints, and identifies
  the unfinished unit whose additional actual moves may be uncertain.
- Save a new private initial checkpoint and every block/evaluation boundary.
  Preserve the original source files, unsuccessful episodes and all endpoints.
  No trained state enters git. Main's production learner/defaults stay unchanged.

## Report and interpretation

Report each seed's complete five-point score trajectory, including the inherited
1,280 baseline. Primary: final mates minus that baseline for each seed. Secondary:
gained and lost rows between consecutive milestones and relative to baseline;
solved symmetry orbits; actual training mates; ordinary births/retirements; graph
cost and runtime. Record whether initially solved rows stay solved across every
**observed milestone**, without claiming stability between observations. Do not
substitute the best intermediate checkpoint for the declared final result.

These are continued, development-selected histories on already viewed positions.
This is not another causal 32/64 comparison or a learning-rate experiment, since
neither budget nor rate varies here. Even all six reaching 128/128 would not prove
general M1 mastery, adaptive structural selection, useful consolidation or learned
handover. Fresh positions and deliberate final-test evaluation remain separate.

If the weaker histories improve while stronger ones remain effective, the next
question is broader positional coverage and a frozen evaluation profile. If
material regressions or plateaus persist, preserve the affected states and choose
one supported attribution question before modifying a mechanism or rate. Do not
infer a need for a retention controller or an authored chess composition. The
small independently trained child-competence/delegation task remains separate.

## Run and verification

Python 3.12, chess 1.11.2, numpy 2.3.5; the launcher fixes hash seed 0 and numerical
library threads to one. The source checkpoint bundle and public aggregate from
the preceding replication are required:

```bash
python scripts/autogrowth/run_m1_long_play.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --reference reports/autogrowth/development/M1_CAPACITY_REPLICATION_20260907.json \
  --private-source snapshots/autogrowth/m1-capacity-replication-seeds4-9 \
  --output reports/autogrowth/runs/m1-long-play-seeds4-9 \
  --private snapshots/autogrowth/m1-long-play-seeds4-9 \
  --episodes 4096 --evaluate-at 1536 2048 3072 4096 \
  --block 128 --workers 6 --wall-seconds 4800
```

For an extracted checkpoint archive, point `--private-source` at its `private`
directory and `--pool` at its `pool` directory. The new focused tests verify the
exact source endpoint, actual move accounting, terminal-only observations,
unchanged source files and configuration, schedule continuity, evaluation/reload
equivalence to uninterrupted training, and interruption accounting. Run the
required full branch suite in `AGENTS.md` before the declared experiment.
