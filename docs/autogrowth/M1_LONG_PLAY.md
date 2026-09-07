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

## Completed result — 2026-09-07

The protocol and implementation were published before play at
`b2bf6d44317eca1d8aa1f50434c9b239f75d2698`. All **199 required branch tests passed**.
All **19,968 declared actual moves** completed in one attempt: **16,896 rewarded
training moves** (12,599 mates) and **3,072 frozen evaluation moves**. Per-seed
times were 3,358.905–3,535.321 seconds, within the 4,800-second caps. No timeout,
retry, extension, new diagnostic transitions or final-test access occurred.
The [public aggregate](../../reports/autogrowth/development/M1_LONG_PLAY_20260907.json)
contains the complete manifest, outcomes, lifecycle counts and checkpoint hashes.

Development mates out of 128; event 1,280 is inherited, all later columns are new:

| Seed | 1,280 | 1,536 | 2,048 | 3,072 | 4,096 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4 | 128 | 128 | 124 | 126 | 128 |
| 5 | 128 | 128 | 128 | 128 | 128 |
| 6 | 128 | 128 | 128 | 128 | 128 |
| 7 | 103 | 103 | 103 | 123 | 126 |
| 8 | 125 | 128 | 128 | 128 | 128 |
| 9 | 111 | 111 | 111 | 111 | 111 |

Two actors improved, four tied, none finished with a lower total. Mean success
rose from **94.14% to 97.53%** (+26 mates across six actors). Relative to the
initial row outcomes there were **28 gains and two losses**, both losses in seed
7. A nondecreasing final score does not mean every old success was retained.
Four final actors solved all 25 development symmetry orbits; seed 7 solved 24,
seed 9 remained at 18.

Seed 7's long plateau ended without changing a learner mechanism or rate. Seed
8 gained its final three mates early and retained them at every measured point.
Seed 4 temporarily lost six distinct initially solved rows across the observed
milestones, then recovered all of them. Seed 7 temporarily lost five initially
solved rows and recovered three. Across actors, 712 of the 723 initially solved
seed/row pairs remained solved at every observed milestone; 721 were solved at
the final endpoint. These observations do not establish stability between
measurements or attribute recovery to slow consolidation.

Seed 9 kept exactly the same solved/failed row partition at every observation,
despite **235 additional births and 237 retirements**. This is a persistent
behavioral plateau, not an inactive learner or proof of its ultimate limit.
Across actors, new births ranged 165–305, retirements 166–304, final live
conditions 62–64 and final physical vertices 2,389–2,692. Ordinary turnover and
weight updates continued together; this study does not isolate their effects.

Every source endpoint, inherited configuration and schedule prefix matched.
All 24 evaluated payloads were independently loaded and checked against their
full reported snapshots; all six final pointers restored. Evaluations preserved
learned state and completed shadow histories stayed unchanged. All **162 private
checkpoint payloads** were retained, including the temporary regressions, in a
verified archive (SHA256
`9c8e6ac1850a2ea1cdb9caa76928bbe1c6fa4a1da5dbd432cca3d1aee6f01532`).

**What this changes:** longer ordinary experience can improve another weak
history and recover a temporary regression. The fixed 0.3 learning rate is still
not an identified cause. No learner mechanism, feature, reward, oracle, authored
composition or coach-side intervention was introduced. Random proposal plus
outcome learning remains distinct from demonstrated adaptive structural
selection. Reused development results do not establish general M1 mastery,
competence estimation, strategic handover or a world model.

**Next bounded target:** use the existing offline representation/ranking checks
on seed 9's initial and final saved actors to ask whether the persistent failures
are constrained by their current compositions/shared ordering, or leave room for
weight-only improvement. Include seed 7's initial/final actors as the improving
comparison; declare that scope before executing it. Do not feed diagnostic labels
or fitted weights back, silently extend this closed study, or add a new controller.
The result should select one subsequent ordinary-play comparison of an existing
budget or learning setting, if justified; it need not promise a complete causal
diagnosis. Do not require perfect scores on these viewed rows before the separate
small child-competence/delegation experiment.

Broader positional coverage also remains necessary. The pool generator currently
uses its seed for both sampling and symmetry-orbit partition assignment. A new
seed alone can therefore move old training orbits into a new evaluation split.
Preserve the original partition seed (20260905), exclude already viewed
development orbits when constructing a fresh development set, and leave the final
test partition unopened. No new pool was generated in this study. Main retains
its unchanged production learner and original 96-condition default; 64 remains a
provisional experimental profile.
