# KRK State-Local Paired Selector Runtime Proxy Review Packet v1

This packet is review-only and does not authorize implementation.

- status: `runtime_review_ready_progress_window_scope_only`
- selected proxy: `conservative_safe_preservation_gated_proxy`
- review scope: `default_off_progress_window_selected_owner_failure_risk_monitor`
- implementation allowed by this packet: `False`

## Translation Blocker

The passing v1 evidence is progress-window based. It supports a future monitor/reconsideration sandbox review, not an initial pre-decision selector based only on one-ply move shape.

## Requirements

- `default_off_explicit_flag_required`
- `default_off_equivalence_required`
- `trace_every_proxy_firing`
- `proxy_metadata_must_not_directly_request_provider`
- `protected_stage4_stage5_stage6_guardrails_required`
- `stage7_heldout_challenge_required`
- `m1_m4_preservation_required`
- `rollback_tag_required_before_any_runtime_test`
