# KRK Clean Retrain Retry1 Guardrail Result v1

This records the dedicated Stage 5/6 handoff guardrail check for the fresh retry1 clean retrain topology.

## Decision

- status: `clean_retrain_retry1_stage6_overlay_quarantined_guardrails_partial`
- promotion status: `quarantine`
- Stage 6 target passed: `False`
- Stage 5 overlay conversion preserved: `True`
- Stage 5 overlay regressed vs fresh base control: `False`
- Stage 4 overlay probe run: `False`
- retry1 can replace protected stack: `False`
- Stage 7 remains quarantined: `True`
- Stage 8 remains blocked: `True`
- runtime behavior changed: `False`
- recommended next step: `inspect_retry1_stage6_candidate_quality_before_any_retrain_or_promotion_retry`

## Artifacts

```text
stage6_candidate:
  snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage6_drive_overlay_300_seed7_h40.json

stage5_overlay_guardrail:
  snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage5_fence_overlay_300_seed7_h40.json

stage5_fresh_base_control:
  snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage5_fence_stage5_base_control_300_seed7_h40.json

promotion_eval:
  snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/promotion_eval_stage6_overlay.json
```

## Results

| Artifact | Mate | Max plies | Shadow | One-ply | Conversion |
| --- | ---: | ---: | ---: | --- | --- |
| Stage 6 `drive_to_edge` candidate | 217/300 | 83/300 | 166 | failed | failed |
| Stage 5 overlay guardrail | 300/300 | 0/300 | 0 | failed | passed |
| Stage 5 fresh base control | 256/300 | 44/300 | 88 | failed | failed |

Promotion failure:

```text
stage6 max_plies_rate = 0.277 > 0.250
stage6 shadow_candidates = 166 > 0
```

The Stage 5 overlay guardrail fails local one-ply reward thresholds, but it does not regress conversion relative to the fresh Stage 5 base control. The overlay improves Stage 5 conversion by `+0.1467` mate-rate, removes `44` max-plies failures, and removes `88` shadow candidates relative to the fresh base control.

## Interpretation

The retry1 clean chain is executable through Stage 6 composition, but it does not produce a replacement-quality protected Stage 6 overlay. The target Stage 6 h40 conversion is below the existing protected overlay, and shadow growth pressure is high.

This is not a reason to promote or replace the existing protected stack. It is evidence that clean retraining is possible, but the clean Stage 5/6 checkpoint quality is not yet equivalent to the protected historical stack.

Stage 4 overlay probing was intentionally not run because the Stage 6 target already failed promotion thresholds.

## Boundary

No runtime selector, score/routing change, provider suppression, topology mutation during gameplay, runtime DTM/tablebase lookup, Stage 7 promotion, or Stage 8 training was introduced.
