# KRK CandidateMoveFrame Capacity Annotation v2

This merges the bounded candidate-move capacity label run back into the observation-frame annotation view.

## Decision

- status: `candidate_move_capacity_annotation_improved_but_selector_blocked`
- selector_allowed: `False`
- recommended_next_step: `candidate_generation_label_blocker_review`

## Summary

- candidate_move_frame_count: 363
- protected_candidate_move_count: 292
- protected_annotated_candidate_move_count: 22
- protected_annotation_recall: `0.075`
- annotation_counts: `{'negative_capacity': 3, 'positive_capacity': 19, 'unannotated': 341}`
- annotation_counts_by_stage: `{'stage4': {'negative_capacity': 1, 'positive_capacity': 5, 'unannotated': 83}, 'stage5': {'positive_capacity': 10, 'unannotated': 114}, 'stage6': {'negative_capacity': 2, 'positive_capacity': 4, 'unannotated': 73}, 'stage7': {'unannotated': 71}}`
- matched_annotation_source_counts: `{'reports/krk_protected_provider_coverage_frames_v0.json': 16, 'reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.json': 12}`

## Boundary

The merged labels improve coverage but remain capacity evidence only. They do not authorize selector training or runtime behavior.
