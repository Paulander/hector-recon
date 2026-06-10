# KRK Strategy Arbiter Runtime Review Packet v1

This packet packages the current evidence for architecture review. It does not implement or authorize a runtime arbiter.

## Review Question

Should the project implement a default-off, traceable KRK strategy-arbiter sandbox using the v1 contract, or require additional non-causal evidence first?

## Current Stack

- Profile: `handoff_composition_v1`
- Stage 7 status: `local_valid_composition_quarantined`

- `stage1_backchain` status=`protected_solved_local_regression` solved=`True`
- `stage4_wrong_tempo` status=`protected_profile_solved_with_overlay_guardrail_caveat` solved=`True`
- `stage5_fence` status=`protected_solved_conversion_profile` solved=`True`
- `stage6_drive_overlay` status=`promoted_overlay_solved_against_stage5_guardrail` solved=`True`

## Evidence Summary

- `readiness_v3_status`: `selector_readiness_v3_sandbox_design_review_allowed`
- `default_off_design_status`: `default_off_strategy_arbiter_design_ready_for_external_review`
- `contrast_probe_status`: `strategy_owner_contrast_signal_present_selector_sandbox_blocked`
- `conversion_positive_provider_families`: `['drive_to_edge', 'edge_trap', 'fence_established']`
- `training_positive_label_count`: `13`
- `training_negative_label_count`: `11`
- `stage7_heldout_row_count`: `4`

## Review Options

### `approve_default_off_sandbox_implementation`

Allowed next step: `implement default-off trace-only or bounded-support sandbox according to the v1 contract`

Required conditions:
- `default-off equivalence tests are implemented before enabled tests`
- `Stage7 remains held out from training and tuning`
- `no runtime DTM/tablebase input`
- `no gameplay topology mutation`
- `every recommendation cites StrategyProposalFrame and provider metadata`

### `request_more_non_causal_evidence`

Allowed next step: `collect one bounded non-causal evidence slice identified by review`

Required conditions:
- `no runtime selector implementation`
- `no Stage7 repair`
- `no Stage8 training`
- `evidence gap must be specific and bounded`

### `reject_sandbox_path_for_now`

Allowed next step: `return to curriculum or sequence-policy architecture planning without runtime selector work`

Required conditions:
- `record rejection reason`
- `keep existing observability and evidence artifacts non-causal`

## Non-Negotiable Invariants

- `no hidden Python controller`
- `no runtime DTM/tablebase policy`
- `no gameplay-time topology mutation`
- `unpromoted StructuralCandidate/InternalTerminalSpec/PlanCapsuleSpec remain non-causal`
- `preserve M1-M4 plasticity/consolidation semantics`
- `validated Stage5/6 providers remain protected/frozen unless an explicit sandbox says otherwise`

## Decision

- Status: `runtime_review_packet_ready`
- Recommended next step: `external_architecture_review_decision`
- Implementation remains blocked until review.
