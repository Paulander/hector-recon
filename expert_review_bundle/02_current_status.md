# Current Status

## Latest Clean Run

Latest clean artifact:

`snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/`

Copied artifacts in this review bundle:

- `stage5_fence_clean_run_manifest.json`
- `stage5_fence_clean_curriculum_history.json`
- `stage5_fence_conversion_debug.json`

## Current Learned State

The latest clean Stage 5 learner has:

- 25 sensors.
- 21 mature sensors.
- 34 actuators.
- 2 mate-in-1 goal memories.
- Compiled topology: 260 nodes, 786 edges.
- Feature set: `krk_rich_v1`.
- Training device: CPU.

Compiled topology path in repo:

`snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json`

Learner path in repo:

`snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/final_learner.pkl`

Best Stage 5 checkpoint:

`snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl`

## Current Curriculum Stages

Successful or partially successful stages:

- `mate_in_1`: Stage 0.
- `stage0_basin`: Stage 1 backchain toward mate-in-1.
- `edge_trap_close`: Stage 2A.
- `edge_trap_enemy_between`: Stage 2B.
- `edge_trap_wrong_tempo`: Stage 2C.
- `fence_established`: Stage 5.

Planned next KRK stages:

- `drive_to_edge`.
- `box_shrink`.
- `opposition_tempo`.
- `full_krk`.

## Key Metrics

From the latest clean Stage 5 local evaluation:

- Total: 100.
- Improved: 100.
- Optimal: 100.
- Worsened: 0.
- Average reward: about `0.1025`.

Stage 1 regression on the same final topology:

- Improved: 100/100.
- Optimal: 100/100.
- Worsened: 0/100.

Narrow KRK entry mate test:

- Mate found: 100/100.

Important conversion eval:

- Local `fence_established` one-ply skill: 100% improved and optimal.
- Adversarial playout from fence positions: about 30 mate / 70 draw in a saved eval.

## Interpretation

The current bottleneck is not local KRK move selection. Local one-ply landmark skills are working.

The current bottleneck is robust handoff/conversion:

- After a local skill succeeds, which subgraph should activate next?
- How does the graph know whether to continue fence, drive, edge trap, tempo, box shrink, or mate basin?
- How should skills learned in one local curriculum become reusable in a full-game setting?

This is why the expert review should focus on affordance routing, subgraph composition, handoff, meta terminals, online spawning, pruning, and transfer.
