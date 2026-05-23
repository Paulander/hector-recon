# KRK CandidateMoveFrame Capacity Annotation v1

This replay-free review annotates observed CandidateMoveFrame rows against existing protected forced-capacity evidence. It is not selector training.

## Decision

- status: `candidate_move_capacity_annotation_partial_selector_blocked`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `bounded_candidate_move_capacity_label_manifest`

## Summary

- candidate_move_frame_count: 363
- protected_candidate_move_count: 292
- protected_annotated_candidate_move_count: 10
- protected_annotation_recall: `0.034`
- annotation_counts: `{'negative_capacity': 2, 'positive_capacity': 8, 'unannotated': 353}`
- annotation_counts_by_stage: `{'stage4': {'negative_capacity': 1, 'positive_capacity': 1, 'unannotated': 87}, 'stage5': {'positive_capacity': 6, 'unannotated': 118}, 'stage6': {'negative_capacity': 1, 'positive_capacity': 1, 'unannotated': 77}, 'stage7': {'unannotated': 71}}`
- matched_provider_ids: `{'krk.drive_to_edge': 1, 'krk.edge_trap_close': 3, 'krk.edge_trap_enemy_between': 3, 'krk.edge_trap_wrong_tempo': 3, 'krk.fence_established': 3, 'krk.stage0_basin': 3}`

## Interpretation

- replay_free_annotation_possible: `True`
- annotation_coverage_sufficient_for_selector_review: `False`
- capacity_labels_are_not_ownership_labels: `True`

## Boundary

The next step, if pursued, is a bounded non-causal label manifest for candidate-move capacity coverage. This artifact does not authorize selection or routing.
