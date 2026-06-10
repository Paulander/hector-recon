# Stage 6 Overlay Validation Manifest

This manifest records the current validated KRK overlay checkpoint. It is an experimental composition profile, not the universal Hector default policy.

## Profile

```text
composition_profile: handoff_composition_v1
profile_status: experimental
domain: KRK
default_policy: false
overlay_provider_version: stage6_overlay_v1
base_provider_version: stage5_validated_v1
```

## Inputs

```text
frozen_base_topology:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json

base_checkpoint:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl

overlay_learner:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/final_learner.pkl

overlay_checkpoint:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/best_by_stage/drive_to_edge.pkl

overlay_label:
  drive_to_edge
```

## Composed Topology

```text
path:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json

composition_mode:
  frozen_base_plus_overlay

nodes:
  286

edges:
  866

frozen_base_provider_count:
  102

overlay_provider_count:
  10

overlay_actuators_added:
  actuator_34
  actuator_35
  actuator_36
```

## Validation Artifacts

```text
stage6_candidate:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage6_drive_overlay_300_seed7_h40.json
  result: 300 mate / 0 max_plies
  shadow_candidates: 0

stage5_guardrail:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_overlay_300_seed7_h40.json
  result: 300 mate / 0 max_plies
  shadow_candidates: 0

stage5_base_control:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_stage5_base_control_300_seed7_h40.json
  result: 300 mate / 0 max_plies

stage4_overlay_probe:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40.json
  result: 247 mate / 53 max_plies

stage4_base_control:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage4_wrong_tempo_stage5_base_control_300_seed7_h40.json
  result: 247 mate / 53 max_plies

promotion_eval:
  snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json
  result: promotion_status = promoted

cross_domain_bridge_check:
  command: uv run python tests/test_subgraph_delegation.py
  result: all tests passed
  checks:
    KPK direct promotion
    KQK direct move selection
    pre-promotion KQK execution veto
    KPK promotion handoff packet
    post-promotion KQK route eligibility
    KQK continuation move
```

## Interpretation

The monolithic Stage 6 topology solved Stage 6 but regressed earlier Stage 5 conversion. The overlay topology preserves the validated Stage 5 provider pack and adds only the Stage 6 `drive_to_edge` provider as an additive overlay.

The Stage 6 overlay is promoted against the current protected Stage 5 guardrail. It should not be treated as a monolithic replacement topology.

The Stage 4 wrong-tempo 40-ply probe fails identically on the overlay and the frozen Stage 5 base control. That is not evidence of overlay interference; it is a separate Stage 4 horizon/guardrail-definition diagnostic.

The KPK to KQK bridge remains valid under the current routing-contract instrumentation: KQK approach can be visible before promotion, but execution remains vetoed until queen material exists; the promotion handoff packet is trace-only and does not cause routing by itself.

## Reproduction Commands

Compile overlay topology:

```bash
uv run python scripts/baseline_to_recon.py \
  --base-topology snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json \
  --overlay-learner snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/final_learner.pkl \
  --overlay-label drive_to_edge \
  --base-provider-version stage5_validated_v1 \
  --overlay-provider-version stage6_overlay_v1 \
  --base-source-checkpoint snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl \
  --overlay-source-checkpoint snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/best_by_stage/drive_to_edge.pkl \
  --validated-profile handoff_composition_v1 \
  --output snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json
```

Evaluate promotion against the protected Stage 5 guardrail:

```bash
uv run python scripts/evaluate_provider_promotion.py \
  --stage-artifact snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage6_drive_overlay_300_seed7_h40.json \
  --guardrail-artifact snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_overlay_300_seed7_h40.json \
  --min-mate-rate 0.65 \
  --max-max-plies-rate 0.25 \
  --max-shadow-candidates 0 \
  --json-output snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json
```

## Next Use

Use this overlay pattern for later KRK curriculum stages:

```text
validated provider pack
  + new stage overlay provider
  + guardrail-aware promotion evaluation
```

Do not promote a later-stage monolithic topology if it regresses protected prior-stage guardrails.
