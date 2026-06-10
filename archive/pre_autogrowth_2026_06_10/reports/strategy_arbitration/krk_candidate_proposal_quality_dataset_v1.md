# KRK Candidate Proposal Quality Dataset v1

This dataset joins observation-only candidate frames with non-causal capacity/quality annotations. It does not train or select.

## Decision

- status: `candidate_proposal_quality_dataset_ready_for_probe`
- selector_allowed: `False`
- recommended_next_step: `probe_candidate_proposal_quality_axes`

## Summary

- row_count: 569
- row_count_by_candidate_source: `{'candidate_move_frame': 363, 'validated_provider_pack': 206}`
- row_count_by_quality_bucket: `{'held_out_challenge': 111, 'known_negative': 8, 'known_positive': 30, 'unknown_unqualified': 150, 'unknown_with_visible_terms': 270}`
- row_count_by_capacity_evidence: `{'held_out_challenge': 111, 'negative_capacity': 8, 'positive_capacity': 30, 'unknown_capacity': 420}`
- quality_probe_row_count: 38
- stage7_challenge_row_count: 111

## Boundary

Rows are capacity/quality evidence, not selector labels. Stage 7 rows are held-out challenge rows only.
