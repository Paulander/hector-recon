# KRK Candidate Source Expansion Options v0

This review turns the source-gap manifest into non-causal next-step options. It does not authorize runtime behavior.

## Decision

- status: `candidate_source_expansion_options_review_complete_runtime_packet_required`
- runtime_changes_allowed: `False`
- selector_allowed: `False`
- recommended_next_step: `draft_exact_trace_enrichment_runtime_review_packet`
- preferred_next_review: `exact_trace_enrichment_within_existing_policy_cells`

## Summary

- exact_missing_positive_capacity_count: `21`
- policy_cell_covered_exact_missing_count: `15`
- policy_cell_missing_count: `6`
- gap_count_by_stage: `{'stage4': 6, 'stage5': 12, 'stage6': 3}`
- gap_count_by_family: `{'edge_trap': 12, 'stage0_basin': 9}`

## Options

- `exact_trace_enrichment_within_existing_policy_cells` scope=`stage5_stage6_current_refresh_policy_cells` supported_by_gap_count=`15` selector_allowed=`False` requires_review_packet=`True`
  Improve exact move/provider trace coverage where the reviewed policy cell is already visible but the exact capacity candidate is absent.
- `protected_stage4_scope_review` scope=`stage4_review_only` supported_by_gap_count=`6` selector_allowed=`False` requires_review_packet=`True`
  Decide whether Stage 4 should be eligible for observation-only candidate generation.
- `plan_sequence_candidate_trace_review` scope=`plan_capsule_sequence_candidates` supported_by_gap_count=`0` selector_allowed=`False` requires_review_packet=`True`
  Define separate observation frames for sequence/PlanCapsule candidates when provider-pack frames are insufficient.
- `selector_training` scope=`not_allowed` supported_by_gap_count=`0` selector_allowed=`False` requires_review_packet=`True`
  Out of scope because capacity/source gaps are not ownership labels.

## Required Before Runtime

- `new_review_packet`
- `default_off_scope`
- `candidate_count_bound`
- `default_off_equivalence`
- `no_score_delta`
- `no_selected_move_or_provider_delta`
- `no_stage7_training_rows`
- `no_selector_or_routing`
