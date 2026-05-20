# Stage 7 Selected Path Target Probe v0

Decision: `split_targets_separable_but_source_biased_no_runtime`

This is a non-causal offline probe. It does not authorize runtime behavior.

## Summary

- row_count: `30`
- ownership_row_count: `14`
- sequence_row_count: `16`
- ownership_state_count: `10`
- sequence_state_count: `16`
- sequence_source_counts: `{'gap_or_unqualified': 2, 'sandbox_sourced_replay_free_success_control': 14}`
- source_bias_detected: `True`

## Ownership Target

- `local_provider_competition_failed`: precision=`1.0`, recall=`1.0`, tp=`2`, fp=`0`, fn=`0`
- `selected_owner_failed_h40`: precision=`1.0`, recall=`1.0`, tp=`2`, fp=`0`, fn=`0`
- `alternative_provider_known_conversion_h40`: precision=`1.0`, recall=`1.0`, tp=`2`, fp=`0`, fn=`0`

Ownership positives separate from protected safe controls, but there are only two Stage 7 positives.

## Sequence Target

- `post_plan_stagnation`: precision=`1.0`, recall=`1.0`, tp=`2`, fp=`0`, fn=`0`
- `forced_providers_h40_no_mate`: precision=`1.0`, recall=`1.0`, tp=`2`, fp=`0`, fn=`0`
- `legal_first_h40_no_mate`: precision=`1.0`, recall=`1.0`, tp=`2`, fp=`0`, fn=`0`

Sequence gap rows separate from recovered success controls, but recovered controls are prior-sandbox-sourced and may encode artifact/source bias.

## Decision

- Recommended next step: `architecture_review_or_collect_clean_sequence_controls_before_runtime`
- Why: The split target framing is useful, but existing evidence is too small and source-biased to justify runtime behavior.

Blocked runtime work:

- `runtime arbiter`
- `abstention selector tuning`
- `plan capsule runtime repair`
- `Stage 7 promotion`
- `Stage 8 training`
