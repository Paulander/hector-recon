# KRK Clean Curriculum Checkpoint Plan v0

This is a readiness and execution-plan artifact. It does not launch a full retrain and does not change runtime behavior.

## Decision

- status: `clean_curriculum_checkpoint_plan_ready_full_run_requires_review`
- Stage 7 remains quarantined: `True`
- Stage 8 remains blocked: `True`
- runtime selector allowed: `False`
- recommended next step: `write_explicit_clean_retrain_execution_manifest_before_any_long_run`

## Validated Stack

- profile: `handoff_composition_v1`
- protected/base component: `stage1_backchain`
- protected/base component: `stage5_fence_handoff`
- protected/base component: `stage6_drive_to_edge_overlay`
- protected/base component: `kpk_to_kqk_bridge_preservation`
- Stage 4 status: `mostly_clean_with_separate_h40_overlay_control_caveat`
- Stage 7 status: `local_valid_composition_quarantined_held_out_challenge`
- Stage 8 status: `blocked_until_stage7_or_broader_control_plane_review`

## Command Sequence

### stage1_foundation_clean

- purpose: `Train/rebuild Stage 0/1 foundation from zero.`
- source manifest: `snapshots/krk_triplet_pipeline/stage1_clean/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/stage1_clean/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/stage1_clean/topology/krk_entry_topology.json`
- commands:
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 20 --stage1-cycles 10 --samples-per-cycle 100 --output-dir snapshots/krk_triplet_pipeline/stage1_clean/baseline --save-learner snapshots/krk_triplet_pipeline/stage1_clean/baseline/final_learner.pkl --device cpu --seed 7 --snapshot-every 1 --stage1-position-mode mate_in_2 --stage0-balance-corners`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/stage1_clean/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/stage1_clean/topology/krk_entry_topology.json`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/stage1_clean/topology/krk_entry_topology.json --samples 50`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/stage1_clean/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/stage1_clean/baseline/final_learner.pkl --samples 50 --seed 7 --stage-filter 1 --position-mode mate_in_2`

### stage4_wrong_tempo_profile

- purpose: `Train/rebuild wrong-tempo / edge-trap profile from the prior clean provider.`
- source manifest: `snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/topology/krk_entry_topology.json`
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/best_by_stage/edge_trap_wrong_tempo.pkl`
- commands:
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 0 --stage1-cycles 0 --samples-per-cycle 150 --output-dir snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline --save-learner snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/final_learner.pkl --device cpu --seed 7 --snapshot-every 1 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 4 --start-curriculum-stage 4 --landmark-cycles 10 --stage1-position-mode mate_in_2 --load-learner snapshots/krk_triplet_pipeline/adaptive_krk_stage2b_only/baseline/best_by_stage/edge_trap_enemy_between.pkl --adaptive-curriculum --eval-every 5 --patience 3 --min-cycles-per-stage 10 --max-cycles-per-stage 80 --adaptive-eval-samples 100 --adaptive-playout-max-plies 0 --stage0-balance-corners`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/topology/krk_entry_topology.json`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/topology/krk_entry_topology.json --samples 100`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/final_learner.pkl --samples 100 --seed 7 --stage-filter 1 --position-mode mate_in_2`

### stage5_fence_handoff

- purpose: `Train/rebuild protected fence/handoff component.`
- source manifest: `snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json`
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl`
- commands:
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 0 --stage1-cycles 0 --samples-per-cycle 150 --output-dir snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline --save-learner snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/final_learner.pkl --device cpu --seed 7 --snapshot-every 1 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 5 --start-curriculum-stage 5 --landmark-cycles 10 --stage1-position-mode mate_in_2 --load-learner snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/best_by_stage/edge_trap_wrong_tempo.pkl --adaptive-curriculum --eval-every 5 --patience 3 --min-cycles-per-stage 10 --max-cycles-per-stage 80 --adaptive-eval-samples 100 --adaptive-playout-max-plies 0 --stage0-balance-corners`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json --samples 100`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/final_learner.pkl --samples 100 --seed 7 --stage-filter 1 --position-mode mate_in_2`

### stage6_drive_overlay

- purpose: `Train/rebuild Stage 6 drive overlay against handoff_composition_v1.`
- source manifest: `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/run_manifest.json`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/final_learner.pkl`
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/topology/krk_entry_topology.json`
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/best_by_stage/drive_to_edge.pkl`
- commands:
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/train_baseline_krk_chain.py --stage0-cycles 0 --stage1-cycles 0 --samples-per-cycle 150 --output-dir snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline --save-learner snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/final_learner.pkl --device auto --seed 7 --snapshot-every 1 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 6 --start-curriculum-stage 6 --landmark-cycles 10 --stage1-position-mode mate_in_2 --load-learner snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl --adaptive-curriculum --eval-every 5 --patience 3 --min-cycles-per-stage 10 --max-cycles-per-stage 80 --adaptive-eval-samples 200 --adaptive-playout-max-plies 40 --adaptive-composition-profile handoff_composition_v1 --adaptive-use-profile-validation-defaults --adaptive-stagnation-breaker-king-support-bonus 2.0 --stage0-balance-corners`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/topology/krk_entry_topology.json`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/test_krk_entry.py --topology snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/topology/krk_entry_topology.json --samples 100`
  - `/home/banquo/recon-lite/.venv/bin/python3 scripts/test_stage1_backchain.py --topology snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/topology/krk_entry_topology.json --learner snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/final_learner.pkl --samples 100 --seed 7 --stage-filter 1 --position-mode mate_in_2`

### stage6_overlay_composition

- purpose: `Compose Stage 6 overlay with protected Stage 5 base and validate preservation.`
- readiness note: `Existing composed overlay artifact has no run_manifest; preserve current artifact paths until a dedicated compose script is formalized.`
- expected outputs:
  - `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json`
- commands:
  - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_architecture_preservation.py tests/test_routing_contracts.py`

## Stage Checkpoints

- `stage1`: local/backchain foundation (protected_if_clean_retrain_matches_current_stage1_guardrails)
- `stage4`: wrong-tempo / edge-trap profile (protected_with_existing_h40_overlay_control_caveat)
- `stage5`: fence/handoff protected base (protected_base_provider_pack)
- `stage6`: drive_to_edge overlay (overlay_preserved_if_stage5_and_stage4_guardrails_hold)
- `stage7`: held-out challenge / local evidence / handoff trigger (do_not_promote)

## Candidate-Generation Observation

- include in normal clean training: `False`
- include in diagnostic validation: `True`
- allowed effect: `trace_or_candidate_generation_frames_only`
- selector allowed: `False`

## Validation Commands

- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_krk_strategy_arbitration_dataset.py tests/test_krk_ownership_selection_recovery.py`
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_architecture_preservation.py tests/test_routing_contracts.py tests/test_endgame_components.py`
- `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_krk_candidate_generation_refresh_sandbox_v0.py`
- `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/analyze_krk_candidate_generation_refresh_coverage_v0.py`

## Readiness Review

- can run full clean curriculum now: `False`
- reason: commands and artifacts are identified, but a full run may be long and should start from an explicit execution manifest with output paths to avoid overwriting protected snapshots
- can run tiny smoke now: `True`
- estimated runtime class: `full_retrain_likely_long; smoke_tests_short`
- missing/stale items:
  - `full_clean_retrain_not_launched_in_this_slice_requires_explicit_manifest_review`
- invalid run conditions:
  - `overwriting protected snapshots without a new output directory`
  - `training Stage 8`
  - `promoting Stage 7`
  - `using runtime DTM/tablebase`
  - `enabling observation sandboxes as causal selectors`

## Boundary

This plan keeps Stage 7 as a held-out challenge, keeps Stage 8 blocked, and keeps candidate-generation observation separate from selector ownership labels. A full clean retrain should be launched only from a separate execution manifest with fresh output paths.
