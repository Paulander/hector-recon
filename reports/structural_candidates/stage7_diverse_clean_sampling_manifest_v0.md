# Stage 7 Diverse Clean Sampling Manifest v0

Status: `stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval`

This is a reviewed label-run manifest only. It does not authorize execution by itself.

## Current Gap

- clean_sequence_success_controls_have: `2`
- clean_sequence_success_controls_required: `5`
- clean_sequence_hard_negatives_have: `8`
- sampling_overlap_detected: `True`

## Sampling Policy

- job_count: `8`
- max_total_samples: `64`
- unique_source_cell_count: `6`
- topology_exists: `True`
- h40 only
- Stage 7 labels are held-out challenge evidence, not training rows.
- Explicit approval is required before running.

## Jobs

- `stage7.diverse_clean.box_small.seed101.samples8.h40` sources=`['Box_Small']` seed=`101` samples=`8`
- `stage7.diverse_clean.box_medium.seed103.samples8.h40` sources=`['Box_Medium']` seed=`103` samples=`8`
- `stage7.diverse_clean.edge_fence_deep.seed107.samples8.h40` sources=`['Edge_Fence_Deep']` seed=`107` samples=`8`
- `stage7.diverse_clean.box_small_medium.seed109.samples8.h40` sources=`['Box_Small', 'Box_Medium']` seed=`109` samples=`8`
- `stage7.diverse_clean.box_medium_edge_deep.seed113.samples8.h40` sources=`['Box_Medium', 'Edge_Fence_Deep']` seed=`113` samples=`8`
- `stage7.diverse_clean.all_stage7_sources_a.seed127.samples8.h40` sources=`['Box_Small', 'Box_Medium', 'Edge_Fence_Deep']` seed=`127` samples=`8`
- `stage7.diverse_clean.all_stage7_sources_b.seed131.samples8.h40` sources=`['Box_Small', 'Box_Medium', 'Edge_Fence_Deep']` seed=`131` samples=`8`
- `stage7.diverse_clean.all_stage7_sources_c.seed137.samples8.h40` sources=`['Box_Small', 'Box_Medium', 'Edge_Fence_Deep']` seed=`137` samples=`8`

## Forbidden

- running_this_manifest_without_explicit_approval
- stage7_promotion
- stage8_training
- runtime_selector_or_arbiter
- stage7_support_adapter_or_score_bonus
- runtime_dtm_or_tablebase
- gameplay_topology_mutation
