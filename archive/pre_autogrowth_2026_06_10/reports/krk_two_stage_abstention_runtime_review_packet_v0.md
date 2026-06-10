# KRK Two-Stage Abstention Runtime Review Packet v0

This packet summarizes the first offline abstention result that clears both review thresholds. It does not implement or authorize runtime selector behavior.

## Accepted Evidence

- `row_count`: `51`
- `state_count`: `15`
- `stage_counts`: `{'stage4': 9, 'stage5': 24, 'stage6': 18}`
- `threshold_passing_objective_count`: `12`
- `best_objective_id`: `king_support_provider_family__preserve_monitor_provider_family__u0.45_p0.5`
- `best_negative_suppression`: `0.7058823529411765`
- `best_safe_preservation`: `0.8529411764705882`
- `best_accuracy`: `0.803921568627451`
- `best_error_counts`: `{'false_negative_unsafe_owner_allowed': 5, 'false_positive_safe_owner_rejected': 5, 'true_negative_safe_owner_allowed': 29, 'true_positive_unsafe_owner_rejected': 12}`

## Why This Is Different

- Earlier additive support and one-stage context objectives either failed to move ownership or over-rejected safe owners.
- The two-stage objective explicitly separates safe-owner preservation from unsafe-owner suppression.
- The best threshold-passing objective clears both offline review thresholds on protected Stage 4/5/6 rows and keeps Stage 7 out of training.

## Remaining Risks

- The evidence is still small: 51 rows across 15 states.
- The features include FEN-derived proxy context and monitor signatures; these must be exposed as visible trace/state if ever used causally.
- Stage 7 remains a held-out challenge and is not solved by this packet.
- This packet does not prove guardrail safety under runtime arbitration.
- A runtime selector could still perturb protected provider ownership if not strictly default-off and scoped.

## Future Sandbox Requirements If Approved

- `default_off_flag_required`
- `default_off_equivalence_required_before_enabled_smoke`
- `visible_trace_metadata_for_preserve_score_and_unsafe_score`
- `no_runtime_dtm_or_tablebase`
- `no_gameplay_topology_mutation`
- `no_stage7_training_or_promotion`
- `protected_stage4_stage5_stage6_guardrails_before_any_promotion_discussion`
- `M1_M4_preservation_suite_before_any_promotion_discussion`

## Review Question

Should the next slice implement a strictly default-off two-stage abstention selector sandbox using the threshold-passing objective, with default-off equivalence and trace-only first?

## Decision

- Status: `two_stage_abstention_review_ready_implementation_blocked`
- Recommended next step: `explicit_review_before_default_off_runtime_selector_implementation`
- Implementation allowed by this packet: `False`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
