# KRK Clean Retrain Execution Manifest v0

This manifest makes the clean rebuild path executable without overwriting protected snapshots. It does not run training.

## Decision

- status: `clean_retrain_execution_manifest_ready_not_run`
- full run authorized by this manifest: `False`
- Stage 7 remains quarantined: `True`
- Stage 8 remains blocked: `True`
- runtime selector allowed: `False`
- recommended next step: `review_manifest_then_optionally_run_stage2a_smoke_or_full_clean_retrain`

## Preflight

- fresh_output_root_required: `True`
- fresh_output_root_exists_now: `False`
- must_not_overwrite_protected_snapshots: `True`
- full_run_started_by_this_manifest: `False`
- requires_human_review_before_long_run: `True`
- checkpoint_plan_status: `clean_curriculum_checkpoint_plan_ready_full_run_requires_review`

## Execution Steps

### stage2a_edge_trap_close

- stage label: `stage2_edge_trap_close`
- purpose: Fresh Stage 0/1 plus edge-trap-close foundation from zero.
- execution status: `not_run_by_manifest`
- prerequisites: `[]`
- historical source manifest: `snapshots/krk_triplet_pipeline/adaptive_krk_stage2a_fixed2/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/topology/krk_entry_topology.json`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline/best_by_stage/edge_trap_close.pkl`
- commands:
  - `.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 40 --stage1-cycles 20 --samples-per-cycle 150 --output-dir snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline --save-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline/final_learner.pkl --device cpu --seed 7 --snapshot-every 1 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 2 --landmark-cycles 10 --stage1-position-mode mate_in_2 --adaptive-curriculum --eval-every 5 --patience 3 --min-cycles-per-stage 10 --max-cycles-per-stage 80 --adaptive-eval-samples 100 --stage0-balance-corners`
  - `.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/topology/krk_entry_topology.json`
  - `.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/topology/krk_entry_topology.json --samples 100`
  - `.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline/final_learner.pkl --samples 100 --seed 7 --stage-filter 1 --position-mode mate_in_2`
- stop if:
  - `command exits nonzero`
  - `expected output missing`
  - `protected validation regression`
  - `Stage 7 training/promotion appears`
  - `Stage 8 training appears`

### stage2b_enemy_between

- stage label: `stage3_edge_trap_enemy_between`
- purpose: Fresh enemy-between edge-trap continuation using the fresh Stage 2A provider.
- execution status: `not_run_by_manifest`
- prerequisites: `['stage2a_edge_trap_close']`
- historical source manifest: `snapshots/krk_triplet_pipeline/adaptive_krk_stage2b_only/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/topology/krk_entry_topology.json`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/baseline/best_by_stage/edge_trap_enemy_between.pkl`
- commands:
  - `.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 0 --stage1-cycles 0 --samples-per-cycle 150 --output-dir snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/baseline --save-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/baseline/final_learner.pkl --device cpu --seed 7 --snapshot-every 1 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 3 --landmark-cycles 10 --stage1-position-mode mate_in_2 --adaptive-curriculum --eval-every 5 --patience 3 --min-cycles-per-stage 10 --max-cycles-per-stage 80 --adaptive-eval-samples 100 --stage0-balance-corners --start-curriculum-stage 3 --load-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline/best_by_stage/edge_trap_close.pkl --adaptive-playout-max-plies 0`
  - `.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/topology/krk_entry_topology.json`
  - `.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/topology/krk_entry_topology.json --samples 100`
  - `.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/baseline/final_learner.pkl --samples 100 --seed 7 --stage-filter 1 --position-mode mate_in_2`
- stop if:
  - `command exits nonzero`
  - `expected output missing`
  - `protected validation regression`
  - `Stage 7 training/promotion appears`
  - `Stage 8 training appears`

### stage4_wrong_tempo

- stage label: `stage4_edge_trap_wrong_tempo`
- purpose: Fresh wrong-tempo profile using the fresh Stage 2B provider.
- execution status: `not_run_by_manifest`
- prerequisites: `['stage2b_enemy_between']`
- historical source manifest: `snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/topology/krk_entry_topology.json`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/baseline/best_by_stage/edge_trap_wrong_tempo.pkl`
- commands:
  - `.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 0 --stage1-cycles 0 --samples-per-cycle 150 --output-dir snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/baseline --save-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/baseline/final_learner.pkl --device cpu --seed 7 --snapshot-every 1 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 4 --landmark-cycles 10 --stage1-position-mode mate_in_2 --adaptive-curriculum --eval-every 5 --patience 3 --min-cycles-per-stage 10 --max-cycles-per-stage 80 --adaptive-eval-samples 100 --stage0-balance-corners --start-curriculum-stage 4 --load-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2b_enemy_between/baseline/best_by_stage/edge_trap_enemy_between.pkl --adaptive-playout-max-plies 0`
  - `.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/topology/krk_entry_topology.json`
  - `.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/topology/krk_entry_topology.json --samples 100`
  - `.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/baseline/final_learner.pkl --samples 100 --seed 7 --stage-filter 1 --position-mode mate_in_2`
- stop if:
  - `command exits nonzero`
  - `expected output missing`
  - `protected validation regression`
  - `Stage 7 training/promotion appears`
  - `Stage 8 training appears`

### stage5_fence_handoff

- stage label: `stage5_fence_established`
- purpose: Fresh protected fence/handoff provider using the fresh Stage 4 provider.
- execution status: `not_run_by_manifest`
- prerequisites: `['stage4_wrong_tempo']`
- historical source manifest: `snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/topology/krk_entry_topology.json`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline/best_by_stage/fence_established.pkl`
- commands:
  - `.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 0 --stage1-cycles 0 --samples-per-cycle 150 --output-dir snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline --save-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline/final_learner.pkl --device cpu --seed 7 --snapshot-every 1 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 5 --landmark-cycles 10 --stage1-position-mode mate_in_2 --adaptive-curriculum --eval-every 5 --patience 3 --min-cycles-per-stage 10 --max-cycles-per-stage 80 --adaptive-eval-samples 100 --stage0-balance-corners --start-curriculum-stage 5 --load-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage4_wrong_tempo/baseline/best_by_stage/edge_trap_wrong_tempo.pkl --adaptive-playout-max-plies 0`
  - `.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/topology/krk_entry_topology.json`
  - `.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/topology/krk_entry_topology.json --samples 100`
  - `.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline/final_learner.pkl --samples 100 --seed 7 --stage-filter 1 --position-mode mate_in_2`
- stop if:
  - `command exits nonzero`
  - `expected output missing`
  - `protected validation regression`
  - `Stage 7 training/promotion appears`
  - `Stage 8 training appears`

### stage6_drive_overlay_candidate

- stage label: `stage6_drive_to_edge`
- purpose: Fresh Stage 6 drive provider using handoff_composition_v1 and the fresh Stage 5 provider.
- execution status: `not_run_by_manifest`
- prerequisites: `['stage5_fence_handoff']`
- historical source manifest: `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/topology/krk_entry_topology.json`
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/best_by_stage/drive_to_edge.pkl`
- commands:
  - `.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 0 --stage1-cycles 0 --samples-per-cycle 150 --output-dir snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline --save-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/final_learner.pkl --device auto --seed 7 --snapshot-every 1 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 6 --landmark-cycles 10 --stage1-position-mode mate_in_2 --adaptive-curriculum --eval-every 5 --patience 3 --min-cycles-per-stage 10 --max-cycles-per-stage 80 --adaptive-eval-samples 200 --stage0-balance-corners --start-curriculum-stage 6 --load-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline/best_by_stage/fence_established.pkl --adaptive-playout-max-plies 40 --adaptive-composition-profile handoff_composition_v1 --adaptive-use-profile-validation-defaults --adaptive-stagnation-breaker-king-support-bonus 2.0`
  - `.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/topology/krk_entry_topology.json`
  - `.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/topology/krk_entry_topology.json --samples 100`
  - `.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/final_learner.pkl --samples 100 --seed 7 --stage-filter 1 --position-mode mate_in_2`
- stop if:
  - `command exits nonzero`
  - `expected output missing`
  - `protected validation regression`
  - `Stage 7 training/promotion appears`
  - `Stage 8 training appears`

### stage6_overlay_composition_review

- stage label: `stage6_overlay_composed`
- purpose: Compose fresh Stage 6 overlay with fresh protected Stage 5 base after training artifacts exist.
- execution status: `requires_dedicated_compose_script_or_manual_review`
- prerequisites: `['stage5_fence_handoff', 'stage6_drive_overlay_candidate']`
- readiness note: Current repo has a composed overlay artifact but no replayable compose run_manifest; this step needs a small compose-manifest package before execution.
- expected outputs:
  - `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/topology/krk_entry_topology.json`
- commands:
  - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_architecture_preservation.py tests/test_routing_contracts.py`
- stop if:
  - `dedicated compose path is ambiguous`
  - `Stage 5 provider preservation cannot be verified`
  - `Stage 4 guardrail caveat worsens`

## Final Validation Commands

- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_krk_strategy_arbitration_dataset.py tests/test_krk_ownership_selection_recovery.py`
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_architecture_preservation.py tests/test_routing_contracts.py tests/test_endgame_components.py`
- `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_krk_candidate_generation_refresh_sandbox_v0.py`
- `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/analyze_krk_candidate_generation_refresh_coverage_v0.py`

## Global Stop Conditions

- `any command projects to hours without explicit run approval`
- `fresh output root already exists with non-manifest-owned files`
- `protected Stage 5/6 behavior regresses`
- `M1-M4 preservation tests fail`
- `KPK->KQK bridge preservation fails`
- `Stage 7 training/promotion appears`
- `Stage 8 training appears`
- `runtime DTM/tablebase use appears`
- `candidate-generation observation affects selection/scoring/routing`

## Boundary

This manifest preserves the current architecture boundaries: no Stage 7 promotion, no Stage 8 training, no selector, no score/routing changes, no runtime DTM/tablebase, and no gameplay-time topology mutation. Candidate-generation observation remains diagnostic only.
