# KRK Visible Monitor Terms v0

This report extracts Tier 1 diagnostic monitor terms from existing strategy-arbitration artifacts. These terms are non-causal evidence only.

## Status

- Record count: `33`
- Terms: `['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists', 'box_area_no_longer_decision_relevant', 'post_plan_stagnation', 'local_provider_competition_failed']`
- True/false counts by term: `{'king_support_improves_after_move': {'True': 30, 'False': 3}, 'cut_or_fence_restored_after_move': {'True': 22, 'False': 11}, 'safe_repair_move_exists': {'True': 33}, 'box_area_no_longer_decision_relevant': {'False': 7, 'True': 26}, 'post_plan_stagnation': {'False': 29, 'True': 4}, 'local_provider_competition_failed': {'False': 31, 'True': 2}}`
- Scope counts: `{'candidate_move_or_current_state': 33, 'current_state': 88, 'trace_window': 33, 'decision_or_family': 33, 'post_move': 11}`
- Confidence counts: `{'extracted_from_existing_candidate_or_context_terms': 30, 'proxy_from_current_state_repair_availability': 22, 'expression_from_current_state_terms': 66, 'not_observed': 43, 'expression_from_provider_outcome_evidence': 33, 'extracted_from_trace_window': 2, 'proxy_from_failure_family_labels': 2}`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Term Definitions

- `king_support_improves_after_move`: candidate/current evidence that support improves, not merely exists.
- `cut_or_fence_restored_after_move`: candidate/post-move or repair-availability evidence that cut/fence can be restored.
- `safe_repair_move_exists`: bounded current-state expression combining repair availability, rook safety, and no known draw risk.
- `box_area_no_longer_decision_relevant`: owner-exit diagnostic when edge/box context suggests box shrink may no longer be the key decision axis.
- `post_plan_stagnation`: trace-window evidence that a plan/capsule/continuation context failed to progress.
- `local_provider_competition_failed`: decision/family evidence that raw local provider competition failed despite alternate conversion evidence.

## Sample Records

- `state.069e81a609ed` stage=`stage7` label=`box_shrink` outcome=`unknown` true_terms=`['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists']`
- `state.0926f12f8e8f` stage=`stage7` label=`box_shrink` outcome=`unknown` true_terms=`['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists', 'box_area_no_longer_decision_relevant']`
- `state.4a464b782ecb` stage=`stage7` label=`box_shrink` outcome=`unknown` true_terms=`['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists']`
- `state.4e34ad0b2f29` stage=`stage7` label=`box_shrink` outcome=`max_plies` true_terms=`['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists', 'post_plan_stagnation']`
- `state.b6796dfb62ff` stage=`stage7` label=`box_shrink` outcome=`max_plies` true_terms=`['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists', 'post_plan_stagnation']`
- `state.0afbf11aa123` stage=`stage7` label=`box_shrink` outcome=`max_plies` true_terms=`['cut_or_fence_restored_after_move', 'safe_repair_move_exists', 'box_area_no_longer_decision_relevant', 'post_plan_stagnation']`
- `state.38aed2f35911` stage=`stage7` label=`box_shrink` outcome=`max_plies` true_terms=`['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists', 'post_plan_stagnation']`
- `state.ac0b7ed500ea` stage=`stage7` label=`box_shrink` outcome=`max_plies` true_terms=`['king_support_improves_after_move', 'cut_or_fence_restored_after_move', 'safe_repair_move_exists', 'local_provider_competition_failed']`

## Constraints

No runtime terminal, causal affordance, runtime arbiter, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, topology mutation, or monitor-to-provider routing is authorized.
