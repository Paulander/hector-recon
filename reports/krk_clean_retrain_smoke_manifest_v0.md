# KRK Clean Retrain Smoke Manifest v0

This is a tiny command-plumbing smoke manifest. It does not run training and is not a full curriculum validation.

## Decision

- status: `clean_retrain_smoke_manifest_ready_not_run`
- smoke_run_authorized_by_this_manifest: `False`
- full_run_authorized_by_this_manifest: `False`
- safe_to_request_smoke_run_approval: `True`
- runtime_selector_allowed: `False`
- recommended_next_step: `request_explicit_smoke_run_approval`

## Smoke Scope

- purpose: `command_plumbing_only`
- stage_scope: `['stage0_mate_in_1', 'stage1_backchain']`
- samples_per_cycle: `8`
- stage0_cycles: `1`
- stage1_cycles: `1`
- max_curriculum_stage: `1`
- stage7_rows: `0`
- stage8_training: `False`

## Commands

- train_smoke: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/train_baseline_krk_chain.py --stage0-cycles 1 --stage1-cycles 1 --samples-per-cycle 8 --output-dir snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_smoke/stage2a_edge_trap_close_smoke/baseline --save-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_smoke/stage2a_edge_trap_close_smoke/baseline/final_learner.pkl --device cpu --seed 7 --snapshot-every 0 --min-mature-for-goals 6 --feature-set krk_rich_v1 --max-curriculum-stage 1 --stage1-position-mode mate_in_2 --stage0-balance-corners`
- compile_topology: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/baseline_to_recon.py --learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_smoke/stage2a_edge_trap_close_smoke/baseline/final_learner.pkl --output snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_smoke/stage2a_edge_trap_close_smoke/topology/krk_entry_topology.json`
- parse_topology: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c import json, pathlib; p=pathlib.Path('snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_smoke/stage2a_edge_trap_close_smoke/topology/krk_entry_topology.json'); d=json.loads(p.read_text()); assert 'nodes' in d and 'edges' in d`

## Blockers

- `none`

## Boundary

The smoke scope excludes Stage 7 and Stage 8, does not enable candidate-generation observation as causal behavior, and does not authorize the full clean retrain.
