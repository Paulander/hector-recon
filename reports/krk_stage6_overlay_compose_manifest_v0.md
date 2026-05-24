# KRK Stage 6 Overlay Compose Manifest v0

This manifest formalizes the missing replayable Stage 6 overlay composition step for the clean retrain checkpoint. It does not run composition.

## Decision

- status: `stage6_overlay_compose_manifest_ready_not_run`
- full_run_authorized_by_this_manifest: `False`
- compose_run_authorized_by_this_manifest: `False`
- stage7_remains_quarantined: `True`
- stage8_remains_blocked: `True`
- runtime_selector_allowed: `False`
- recommended_next_step: `review_manifest_then_run_only_after_fresh_stage5_stage6_artifacts_exist`

## Fresh Inputs

- frozen_base_topology: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/topology/krk_entry_topology.json`
- base_checkpoint: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline/best_by_stage/fence_established.pkl`
- overlay_learner: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/final_learner.pkl`
- overlay_checkpoint: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/best_by_stage/drive_to_edge.pkl`
- overlay_label: `drive_to_edge`

## Fresh Outputs

- composed_topology: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/topology/krk_entry_topology.json`
- stage6_candidate_eval: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/stage6_drive_overlay_300_seed7_h40.json`
- stage5_guardrail_eval: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/stage5_fence_overlay_300_seed7_h40.json`
- stage4_overlay_probe: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40.json`
- stage5_base_control: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/stage5_fence_stage5_base_control_300_seed7_h40.json`
- stage4_base_control: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/stage4_wrong_tempo_stage5_base_control_300_seed7_h40.json`
- promotion_eval: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/promotion_eval_stage6_overlay.json`

## Commands

- compile_overlay_topology:
  - `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/baseline_to_recon.py --base-topology snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/topology/krk_entry_topology.json --overlay-learner snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/final_learner.pkl --overlay-label drive_to_edge --base-provider-version stage5_validated_v1 --overlay-provider-version stage6_overlay_v1 --base-source-checkpoint snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage5_fence_handoff/baseline/best_by_stage/fence_established.pkl --overlay-source-checkpoint snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_drive_overlay_candidate/baseline/best_by_stage/drive_to_edge.pkl --validated-profile handoff_composition_v1 --output snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/topology/krk_entry_topology.json`
- promotion_eval:
  - `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/evaluate_provider_promotion.py --stage-artifact snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/stage6_drive_overlay_300_seed7_h40.json --guardrail-artifact snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/stage5_fence_overlay_300_seed7_h40.json --min-mate-rate 0.65 --max-max-plies-rate 0.25 --max-shadow-candidates 0 --json-output snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage6_overlay_composed/promotion_eval_stage6_overlay.json`
- validation:
  - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_architecture_preservation.py tests/test_routing_contracts.py tests/test_endgame_components.py`

## Current Reference Artifacts

- stage6_candidate: `{'path': 'snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage6_drive_overlay_300_seed7_h40.json', 'exists': True, 'playouts': {'mate': 300}, 'shadow_candidates': 0, 'total': 300}`
- stage5_guardrail: `{'path': 'snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_overlay_300_seed7_h40.json', 'exists': True, 'playouts': {'mate': 300}, 'shadow_candidates': 0, 'total': 300}`
- stage4_overlay_probe: `{'path': 'snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40.json', 'exists': True, 'playouts': {'mate': 247, 'max_plies': 53}, 'shadow_candidates': 106, 'total': 300}`
- promotion_eval: `{'schema_version': 'provider_promotion_eval.v1', 'promotion_status': 'promoted', 'stage': {'path': 'snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage6_drive_overlay_300_seed7_h40.json', 'label': 'drive_to_edge', 'total': 300, 'improved_rate': 1.0, 'worsened_rate': 0.0, 'mate_rate': 1.0, 'max_plies_rate': 0.0, 'shadow_candidates': 0, 'passed': True, 'failure_reasons': []}, 'guardrails': [{'path': 'snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_overlay_300_seed7_h40.json', 'label': 'fence_established', 'total': 300, 'improved_rate': 1.0, 'worsened_rate': 0.0, 'mate_rate': 1.0, 'max_plies_rate': 0.0, 'shadow_candidates': 0, 'passed': True, 'failure_reasons': []}], 'failures': []}`

## Acceptance Criteria

- `composed topology exists`
- `Stage 6 candidate evaluation meets promotion thresholds`
- `Stage 5 guardrail evaluation preserves protected behavior`
- `Stage 4 overlay probe no worse than Stage 5 base-control caveat`
- `promotion_eval promotion_status is promoted`
- `M1-M4 and bridge/routing preservation tests pass`
- `no Stage 7 promotion or Stage 8 training`

## Stop Conditions

- `compile command fails`
- `base or overlay checkpoint missing`
- `Stage 5 guardrail regresses`
- `Stage 4 caveat worsens relative to base control`
- `promotion eval fails`
- `runtime selector/scoring/routing behavior appears`
- `runtime DTM/tablebase use appears`
- `gameplay topology mutation appears`

## Boundary

The compose step preserves frozen-provider plus overlay discipline. It must not promote Stage 7, train Stage 8, add a selector, change runtime defaults, use runtime DTM/tablebase, or mutate topology during gameplay.
