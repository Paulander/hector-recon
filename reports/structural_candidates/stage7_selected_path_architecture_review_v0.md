# Stage 7 Selected Path Architecture Review v0

Decision: `runtime_no_go_architecture_review_required`

This review closes the selected-path runtime-test follow-up. It does not authorize runtime behavior.

## Current Findings

- selected_failure_provider: `{'krk.stage0_basin': 4}`
- selected_failure_path_class_counts: `{'continuation_capacity_or_sequence_policy_gap': 2, 'strategy_ownership_gap_existing_provider_can_convert': 2}`
- abstention_selected_penalized_count: `0`
- split_target_probe_status: `split_targets_separable_but_source_biased_no_runtime`
- source_bias_detected: `True`

## Architecture Interpretation

- The failed runtime abstention selector was aimed at unsafe proposals, but the actual selected Stage 7 failure path is stage0_basin ownership.
- The selected failure path is not one homogeneous target: half is ownership misselection with an existing converting provider, and half is sequence/continuation capacity or model-expression gap.
- The split-target framing is useful offline, but existing sequence success controls come from prior sandbox artifacts and are not clean enough to authorize runtime behavior.
- A single penalty, provider boost, or support adapter would conflate distinct failure modes and likely overfit the Stage 7 lab.

## Recommended Next Work

- Status: `collect_clean_controls_or_review_before_runtime`
- Primary: Collect or recover clean non-sandbox Stage 7/post-box sequence controls and additional ownership-gap examples before any runtime selector/arbiter work.
- Secondary: If clean controls cannot be collected cheaply, pause Stage 7 implementation and review whether box_shrink should be treated as local evidence/handoff trigger rather than an independent owner.

Minimum clean-control requirements:

- successful post-box h40 controls not produced by a candidate repair sandbox
- paired max_plies hard negatives for the same or nearby post-box families
- protected Stage 5/6 examples where stage0_basin or edge/fence ownership is safe
- held-out family split separating ownership-gap from sequence-gap cases

## Blocked Actions

- `scale two-stage abstention selector`
- `increase abstention penalty`
- `implement runtime arbiter`
- `make internal terminals causal`
- `add Stage 7 support adapter`
- `promote Stage 7`
- `train Stage 8`
- `use runtime DTM/tablebase`

Next allowed slice: `non_causal_clean_control_collection_plan`
