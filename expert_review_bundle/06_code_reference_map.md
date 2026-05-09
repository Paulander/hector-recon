# Code Reference Map

These are the most relevant repo files if the expert wants implementation-level context.

## Core Curriculum And Rewards

`src/recon_lite_chess/training/krk_landmarks.py`

Defines:

- KRK landmark labels.
- Stage order from edge traps through full KRK.
- Source curriculum stages per label.
- Target lower-stage goal labels.
- Rich KRK landmark reward functions.
- Reward families such as `edge_trap`, `fence_established`, `drive_to_edge`, `box_shrink`, `opposition_tempo`, `full_krk`.

Most relevant concepts:

- `LANDMARK_LABELS`
- `KRK_LANDMARK_STAGE_SPECS`
- `reward_family_for_label`
- `landmark_reward`
- `worst_reply_reward`

## Adaptive Curriculum Criteria

`src/recon_lite_chess/training/adaptive_curriculum.py`

Defines:

- `StagePassCriteria`
- `AdaptiveStageSpec`
- `StageEvalResult`
- `stage_score`
- `evaluate_pass_criteria`
- `make_eval_result`
- `record_curriculum_event`

Important design detail:

- The code separates local one-ply pass from conversion/playout pass.
- A stage can pass as a local skill while conversion remains separately tracked.

## Training Driver

`scripts/train_baseline_krk_chain.py`

Defines the main baseline learner curriculum:

- Stage 0 mate-in-1.
- Stage 1 backchain to mate basin.
- Landmark stages after Stage 1.
- Adaptive eval loop.
- Best checkpoint saving.
- Foundation protection during pruning.
- Goal memory seeding.

Important CLI flags:

- `--load-learner`
- `--feature-set krk_rich_v1`
- `--adaptive-curriculum`
- `--start-curriculum-stage`
- `--max-curriculum-stage`
- `--adaptive-playout-max-plies`
- `--min-cycles-per-stage`
- `--max-cycles-per-stage`
- `--patience`

## Pipeline Runner

`scripts/run_krk_triplet_pipeline.py`

Wraps:

1. train baseline learner,
2. compile learner to ReCoN topology,
3. run basic KRK entry test,
4. run Stage 1 backchain regression test,
5. write run manifest.

## Compiler

`scripts/baseline_to_recon.py`

Compiles the learned baseline into explicit ReCoN topology JSON.

Current output style:

- root entry node,
- hub node,
- learned actuator legs,
- child sensor terminals,
- `SUB/POR/RET` style graph structure,
- stage and curriculum metadata on learned legs.

## Landmark Evaluation

`scripts/test_krk_landmark_progress.py`

Evaluates a compiled topology on landmark curriculum positions.

Supports:

- label filtering,
- stage filtering,
- adversarial black replies,
- playout evaluation,
- debug failure logging,
- debug playout traces in current local changes.

## Runtime Terminals

`src/recon_lite_chess/krk_baseline_nodes.py`

Defines runtime sensor/actuator terminal behavior for compiled baseline topology.

Important current concern:

- Actuator scoring combines local landmark reward, goal progress, mate/draw/rook-loss penalties, and optional black-reply lookahead.

## Tests

`tests/test_krk_landmarks.py`

Covers:

- reward direction for edge/fence/box/opposition-like concepts,
- split edge trap labels,
- source stage mapping,
- black reply selection behavior.
