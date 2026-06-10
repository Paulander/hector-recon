# KRK Diverse Contrast Label Plan v1

This non-causal plan defines the next bounded contrast-label slice. It does not run labels or enable runtime behavior.

## Purpose

Collect a small, balanced, state-local provider contrast set that can test normalized selector objectives without relying on frame-level outcome labels.

## Label Budget

- `max_new_states`: `8`
- `max_forced_provider_labels`: `24`
- `horizon`: `40`
- `trace_failures_only`: `True`
- `diagnostic_caches`: `True`
- `parallel_workers_if_available`: `True`

## Strata

### `protected_stage4_wrong_tempo`

- Target states: `2`
- Provider families: `['stage0_basin', 'edge_trap', 'fence_established']`
- Purpose: add non-stage5/6 contrast and negative controls

### `protected_stage5_fence`

- Target states: `2`
- Provider families: `['stage0_basin', 'edge_trap', 'fence_established', 'drive_to_edge']`
- Purpose: separate fence finish from edge-trap alternatives

### `protected_stage6_drive`

- Target states: `2`
- Provider families: `['stage0_basin', 'drive_to_edge', 'edge_trap', 'fence_established']`
- Purpose: separate drive ownership from stage0 and edge/fence fallbacks

### `stage7_challenge_eval_only`

- Target states: `2`
- Provider families: `['stage0_basin', 'drive_to_edge', 'edge_trap', 'fence_established']`
- Purpose: held-out evaluation only; never training
- Training allowed: `False`

## Required Fields

- `state_id`
- `fen`
- `source_stage`
- `active_landmark_label`
- `provider_id`
- `provider_family`
- `provider_maturity`
- `provider_local_rank`
- `normalized_score`
- `forced_result_h40`
- `forced_plies`
- `forced_first_move`
- `frame_outcome`
- `label_channel=forced_provider_state_local_contrast`
- `stage7_challenge_row`
- `causal_status=non_causal`

## Success Criteria

- `at least 40 non-Stage7 contrast rows`
- `at least 3 provider families with positive and negative examples where possible`
- `negative labels not dominated by one repeated state/provider family`
- `leave-state-out negative_suppression improves over 0.0`
- `Stage7 rows remain held-out evaluation only`

## Stop Conditions

- `projected runtime exceeds practical bounded h40 label budget`
- `labels require runtime DTM/tablebase`
- `labeling starts tuning Stage7`
- `protected Stage5/6 behavior is modified`
- `proposal would become a runtime selector`

## Decision

- Status: `diverse_contrast_label_plan_ready`
- Recommended next step: `run_bounded_diverse_contrast_label_slice_if_budget_allows`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
