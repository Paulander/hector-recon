# KRK Selector Readiness v2 Plan

This design-only plan tightens selector-readiness criteria after the out-of-sample controls showed strong guardrail conversion but weak selector evidence.

## Purpose

Prevent future selector sandbox reviews from treating guardrail-positive, single-provider evidence as strategy-arbitration evidence.

## Requirements

- `label_balance`: Protected-control labels must include enough positive and negative examples per target semantics. Minimum: `{'overall_positive_count': 6, 'overall_negative_count': 6, 'min_positive_negative_ratio': 0.5}`
- `provider_diversity`: Selected and candidate provider evidence must not be dominated by one provider family. Minimum: `{'distinct_selected_provider_families': 3, 'max_selected_provider_family_dominance': 0.7, 'distinct_conversion_positive_provider_families': 2}`
- `label_semantics_split`: Evaluate selected playout, forced-provider conversion, and same-move compatibility separately. Minimum: `{'selected_playout_rows': 12, 'forced_provider_rows': 12, 'same_move_compatibility_rows_if_available': 4}`
- `stage_coverage`: Protected controls must span Stage 4, Stage 5, and Stage 6 without using Stage 7 training rows. Minimum: `{'stage4_rows': 4, 'stage5_rows': 4, 'stage6_rows': 4, 'stage7_training_rows': 0}`
- `held_out_challenge_boundary`: Stage 7 residuals remain held-out challenge cases unless explicitly reclassified by architecture review. Minimum: `{'stage7_training_rows': 0, 'stage7_runtime_repair_allowed': False}`
- `selector_outperforms_non_selector_baselines`: A proposed selector must beat provider-prior/stage-prior/simple-score baselines on held-out protected controls. Minimum: `{'held_out_positive_hit_rate_margin': 0.1, 'guardrail_regression_allowed': False}`

## Current Blockers

- `class_imbalance`
- `selected_provider_family_dominance`
- `insufficient_non_stage0_conversion_positive_ownership_examples`
- `same_move_compatibility_not_executed_in_bounded_out_of_sample_run`

## Next Allowed Evidence Slice

- Name: `strategy_owner_contrast_dataset_v0`
- Status: `non_causal_only`
- Goal: Find or collect small protected-control states where multiple providers are plausible and non-stage0 provider ownership has conversion evidence.

## Decision

- Status: `selector_readiness_v2_defined_runtime_sandbox_blocked`
- Recommended next step: `build_non_causal_strategy_owner_contrast_dataset_v0`
- Runtime arbiter and selector sandbox remain blocked.
