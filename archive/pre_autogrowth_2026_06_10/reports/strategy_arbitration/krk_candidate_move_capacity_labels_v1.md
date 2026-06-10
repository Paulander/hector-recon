# KRK CandidateMoveFrame Capacity Labels v1

Bounded protected-only offline labels for observed candidate moves. These labels are capacity evidence, not runtime ownership labels.

## Decision

- status: `bounded_candidate_move_capacity_labels_completed`
- selector_allowed: `False`
- guardrails_allowed: `False`
- recommended_next_step: `merge_candidate_move_capacity_labels_and_refresh_annotation`

## Summary

- label_count: 12
- result_counts: `{'mate': 11, 'max_plies': 1}`
- capacity_label_counts: `{'negative_capacity': 1, 'positive_capacity': 11}`
- result_counts_by_stage: `{'stage4:mate': 4, 'stage5:mate': 4, 'stage6:mate': 3, 'stage6:max_plies': 1}`
- stage7_label_count: 0
- wall_time_seconds: `27.939`

## Labels

- `cmcap.v1.001` stage=`stage4` move=`e5e8` result=`mate` capacity=`positive_capacity` total_plies=`5`
- `cmcap.v1.002` stage=`stage5` move=`h7h8` result=`mate` capacity=`positive_capacity` total_plies=`5`
- `cmcap.v1.003` stage=`stage6` move=`a1a8` result=`mate` capacity=`positive_capacity` total_plies=`7`
- `cmcap.v1.004` stage=`stage4` move=`e5h5` result=`mate` capacity=`positive_capacity` total_plies=`5`
- `cmcap.v1.005` stage=`stage5` move=`e7g7` result=`mate` capacity=`positive_capacity` total_plies=`5`
- `cmcap.v1.006` stage=`stage6` move=`a1a8` result=`max_plies` capacity=`negative_capacity` total_plies=`40`
- `cmcap.v1.007` stage=`stage4` move=`e5e7` result=`mate` capacity=`positive_capacity` total_plies=`7`
- `cmcap.v1.008` stage=`stage5` move=`h7a7` result=`mate` capacity=`positive_capacity` total_plies=`17`
- `cmcap.v1.009` stage=`stage6` move=`a1c1` result=`mate` capacity=`positive_capacity` total_plies=`7`
- `cmcap.v1.010` stage=`stage4` move=`e5g5` result=`mate` capacity=`positive_capacity` total_plies=`7`
- `cmcap.v1.011` stage=`stage5` move=`h7b7` result=`mate` capacity=`positive_capacity` total_plies=`23`
- `cmcap.v1.012` stage=`stage6` move=`a1a7` result=`mate` capacity=`positive_capacity` total_plies=`7`

## Boundary

These labels do not authorize selector training, routing, guardrails, Stage 7 promotion, or Stage 8 training.
