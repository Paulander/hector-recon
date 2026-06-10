# Curriculum, Growth, And Artifacts

## Training Pipeline

Main scripts in the repo:

- `scripts/train_baseline_krk_chain.py`
- `scripts/run_krk_triplet_pipeline.py`
- `scripts/baseline_to_recon.py`
- `scripts/test_krk_landmark_progress.py`
- `scripts/test_stage1_backchain.py`
- `scripts/test_krk_entry.py`

Important code modules:

- `src/recon_lite_chess/training/krk_landmarks.py`
- `src/recon_lite_chess/training/adaptive_curriculum.py`
- `src/recon_lite_chess/krk_baseline_nodes.py`

## Current Feature Set

The richer KRK feature set is called:

`krk_rich_v1`

It includes concepts such as:

- enemy king edge distance,
- white/black king distance,
- rook safety,
- cut/fence state,
- box area,
- box minimum side,
- opposition,
- can mate now,
- checkmate/stalemate/draw indicators.

## Landmark Rewards

Current landmark labels include:

- `edge_trap`
- `edge_trap_close`
- `edge_trap_enemy_between`
- `edge_trap_wrong_tempo`
- `fence_established`
- `drive_to_edge`
- `box_shrink`
- `opposition_tempo`
- `full_krk`

The split edge-trap labels currently share an `edge_trap` reward family.

## Adaptive Curriculum

The trainer supports adaptive stages:

- `--adaptive-curriculum`
- `--eval-every`
- `--patience`
- `--min-cycles-per-stage`
- `--max-cycles-per-stage`
- `--start-curriculum-stage`
- `--max-curriculum-stage`
- `--adaptive-playout-max-plies`

It saves:

- `final_learner.pkl`
- `best_learner.pkl`
- `best_by_stage/<label>.pkl`
- `curriculum_history.json`
- `run_manifest.json`

## Current Pass Criteria Concept

The code distinguishes:

- local/one-ply stage pass,
- conversion/playout pass.

This distinction matters because local skill success can be high while full playout success is low.

## Topology Compilation

The baseline learner is compiled to a ReCoN JSON topology by:

`scripts/baseline_to_recon.py`

Each verified actuator/sensor leg becomes explicit graph structure. The output topology is inspectable and can be animated.

Current topology sizes are modest:

- Stage 1 presentation: 236 nodes, 740 edges.
- Stage 2C clean: 242 nodes, 760 edges.
- Stage 5 clean: 260 nodes, 786 edges.
- Older noisy Stage 5 run: 494 nodes, 1540 edges.

This is not yet large enough to be a storage problem. Future full-growth animation may need delta/topology-change exports rather than full topology snapshots per game.

## Current Concern

If every skill is learned as an isolated stage-local leg, the graph may not compose well.

The likely missing layer is a routing/affordance mechanism that reads the current board and internal terminal space, then activates the correct subgraph or requests exploration.
