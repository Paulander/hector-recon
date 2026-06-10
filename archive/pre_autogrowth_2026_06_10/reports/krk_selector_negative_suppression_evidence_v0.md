# KRK Selector Negative Suppression Evidence v0

This replay-free audit explains why the two-stage benchmark is blocked on selector negative suppression.

## Label Balance

- `training_rows`: `12`
- `training_positive_count`: `9`
- `training_negative_count`: `3`
- `training_negative_state_count`: `1`
- `training_negative_stage_counts`: `{'stage6': 3}`
- `training_negative_provider_family_counts`: `{'edge_trap': 3}`
- `stage7_heldout_negative_count`: `8`
- `capacity_positive_count`: `11`
- `capacity_negative_count`: `5`
- `capacity_negative_state_count`: `2`
- `capacity_negative_stage_counts`: `{'stage6': 2, 'stage4': 3}`
- `capacity_negative_provider_family_counts`: `{'drive_to_edge': 1, 'fence_established': 1, 'edge_trap': 3}`

## Feature Overlap

- `all_training_normalized_score_values`: `[1.0]`
- `negative_training_feature_keys`: `[{'state_id': 'state.699f0003a511', 'provider_id': 'krk.edge_trap_close', 'feature_key': ['stage6', 'edge_trap', 'rank_1', 'score_high'], 'global_raw_score_rank': 1, 'provider_local_rank': 1, 'normalized_score': 1.0}, {'state_id': 'state.699f0003a511', 'provider_id': 'krk.edge_trap_enemy_between', 'feature_key': ['stage6', 'edge_trap', 'rank_1', 'score_high'], 'global_raw_score_rank': 3, 'provider_local_rank': 1, 'normalized_score': 1.0}, {'state_id': 'state.699f0003a511', 'provider_id': 'krk.edge_trap_wrong_tempo', 'feature_key': ['stage6', 'edge_trap', 'rank_1', 'score_high'], 'global_raw_score_rank': 2, 'provider_local_rank': 1, 'normalized_score': 1.0}]`
- `positive_training_feature_key_counts`: `{'stage5|edge_trap|rank_1|score_high': 4, 'stage5|stage0_basin|rank_1|score_high': 2, 'stage6|stage0_basin|rank_1|score_high': 3}`
- `negative_training_feature_key_counts`: `{'stage6|edge_trap|rank_1|score_high': 3}`

## Leave-State-Out Replay

- Objective: `stage_family_rank_score`
- False positives: `3`
- True negatives: `0`
- Negative suppression: `0.0`

## False Positive Rows

- state=`state.699f0003a511` stage=`stage6` provider=`krk.edge_trap_close` score=`1.0` feature_key=`['stage6', 'edge_trap', 'rank_1', 'score_high']` forced=`max_plies`
- state=`state.699f0003a511` stage=`stage6` provider=`krk.edge_trap_enemy_between` score=`1.0` feature_key=`['stage6', 'edge_trap', 'rank_1', 'score_high']` forced=`max_plies`
- state=`state.699f0003a511` stage=`stage6` provider=`krk.edge_trap_wrong_tempo` score=`1.0` feature_key=`['stage6', 'edge_trap', 'rank_1', 'score_high']` forced=`max_plies`

## Capacity Negative Controls

- state=`state.699f0003a511` stage=`stage6` provider=`krk.drive_to_edge` forced_move=`h7c7` existing=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- state=`state.699f0003a511` stage=`stage6` provider=`krk.fence_established` forced_move=`h7c7` existing=`['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo']`
- state=`state.b11124d658cf` stage=`stage4` provider=`krk.edge_trap_close` forced_move=`c8c7` existing=`['krk.stage0_basin']`
- state=`state.b11124d658cf` stage=`stage4` provider=`krk.edge_trap_wrong_tempo` forced_move=`c8c7` existing=`['krk.stage0_basin']`
- state=`state.b11124d658cf` stage=`stage4` provider=`krk.edge_trap_enemy_between` forced_move=`c8c7` existing=`['krk.stage0_basin']`

## Interpretation

- `primary`: `Negative suppression failure is real but the training negatives are underbalanced and concentrated.`
- `feature_gap`: `Current selector features mostly collapse to stage/family/rank/normalized-score buckets; normalized scores are all high, so current features cannot express why same-family candidates differ in capacity.`
- `data_gap`: `Protected negative-capacity controls exist but are not yet proposal-compatible or selector-training rows.`
- `directed_fix_class`: `non_causal_negative_balance_and_candidate_scoring_feature_fix_before_runtime`

## Decision

- `status`: `selector_negative_suppression_failure_confirmed`
- `recommended_next_step`: `design_non_causal_negative_suppression_feature_and_label_balance_fix`
- `runtime_work_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
