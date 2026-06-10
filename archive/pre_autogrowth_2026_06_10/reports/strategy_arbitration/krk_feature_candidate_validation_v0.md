# KRK Feature Candidate Validation v0

This report validates and types the six missing-feature candidates from the KRK strategy-arbitration audit. It is replay-free and non-causal.

## Status

- Source decision: `missing_feature_first`
- Candidate count: `6`
- Typed counts: `{'needs refinement / companion terms': 2, 'too broad / reject': 1, 'exit condition': 1, 'risk/failure monitor': 1, 'growth-pressure/internal monitor': 1}`
- Causal recommendation counts: `{'sandbox-blocked': 4, 'needs-more-evidence': 1, 'non-causal only': 1}`
- Sandbox-ready candidates: `[]`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Overall Conclusion

No candidate is causal-ready. The current candidates are useful as monitors, exit/handoff hypotheses, or scoped ontology candidates, but their current predicates are either mixed-outcome, failure-correlated, Stage7-only, or too broad.

## Candidate Typing

### cand.krk.strategy.edge_net_affordance.v0

- Target concept: `edge_net_affordance`
- Matching records: `26`
- Result distribution: `{'unknown': 1, 'max_plies': 13, 'mate': 12}`
- Mate precision: `0.480`
- Max-plies/failure precision: `0.520`
- Source-stage distribution: `{'stage7': 2, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Stage 7-only precision: `{'matching_record_count': 2, 'result_distribution': {'unknown': 1, 'max_plies': 1}, 'mate_precision': 0.0, 'failure_precision': 1.0, 'unknown_count': 1}`
- Cross-stage generality: `{'label': 'cross_stage_broad', 'source_stage_count': 4, 'non_stage7_matching_count': 24}`
- Associated with: `both`
- Typed as: `needs refinement / companion terms`
- Causal recommendation: `sandbox-blocked`
- Rationale: matches successful and failed edge states similarly; not a positive affordance yet
- Suggested refinement terms: `['separate edge-net pressure from edge-net action availability', 'require specific net-tightening or safe checking/cut move existence']`
- Required scope/companion terms: `['safe_edge_net_tighten_move_exists', 'king_support_conversion_affordance', 'draw_risk_absent']`

### cand.krk.strategy.king_support_conversion_affordance.v0

- Target concept: `king_support_conversion_affordance`
- Matching records: `33`
- Result distribution: `{'unknown': 3, 'max_plies': 18, 'mate': 12}`
- Mate precision: `0.400`
- Max-plies/failure precision: `0.600`
- Source-stage distribution: `{'stage7': 9, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Stage 7-only precision: `{'matching_record_count': 9, 'result_distribution': {'unknown': 3, 'max_plies': 6}, 'mate_precision': 0.0, 'failure_precision': 1.0, 'unknown_count': 3}`
- Cross-stage generality: `{'label': 'cross_stage_broad', 'source_stage_count': 4, 'non_stage7_matching_count': 24}`
- Associated with: `both`
- Typed as: `too broad / reject`
- Causal recommendation: `sandbox-blocked`
- Rationale: matches nearly all records and is not separable enough as currently defined
- Suggested refinement terms: `['split static support availability from action-relevant support improvement', 'require move-level king-support improvement or provider ownership label']`
- Required scope/companion terms: `['king_support_improvement_move_exists', 'white_king_distance_to_enemy_decreases_after_move']`

### cand.krk.strategy.box_shrink_exit_condition.v0

- Target concept: `box_shrink_exit_condition`
- Matching records: `25`
- Result distribution: `{'unknown': 1, 'mate': 12, 'max_plies': 12}`
- Mate precision: `0.500`
- Max-plies/failure precision: `0.500`
- Source-stage distribution: `{'stage7': 1, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Stage 7-only precision: `{'matching_record_count': 1, 'result_distribution': {'unknown': 1}, 'mate_precision': None, 'failure_precision': None, 'unknown_count': 1}`
- Cross-stage generality: `{'label': 'cross_stage_broad', 'source_stage_count': 4, 'non_stage7_matching_count': 24}`
- Associated with: `both`
- Typed as: `exit condition`
- Causal recommendation: `needs-more-evidence`
- Rationale: mixed success/failure near edge; potential owner-release signal, not provider boost
- Suggested refinement terms: `['distinguish box-shrink exit from edge-net success', 'add current owner and next-provider success labels']`
- Required scope/companion terms: `['active_landmark_label == box_shrink', 'edge_net_affordance', 'mate_basin_readiness']`

### cand.krk.strategy.phase_boundary_near_edge.v0

- Target concept: `phase_boundary_near_edge`
- Matching records: `26`
- Result distribution: `{'unknown': 1, 'max_plies': 13, 'mate': 12}`
- Mate precision: `0.480`
- Max-plies/failure precision: `0.520`
- Source-stage distribution: `{'stage7': 2, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Stage 7-only precision: `{'matching_record_count': 2, 'result_distribution': {'unknown': 1, 'max_plies': 1}, 'mate_precision': 0.0, 'failure_precision': 1.0, 'unknown_count': 1}`
- Cross-stage generality: `{'label': 'cross_stage_broad', 'source_stage_count': 4, 'non_stage7_matching_count': 24}`
- Associated with: `both`
- Typed as: `needs refinement / companion terms`
- Causal recommendation: `sandbox-blocked`
- Rationale: near-edge context is broadly cross-stage and mixed-outcome
- Suggested refinement terms: `['add owner-specific phase-boundary labels', 'pair edge bucket with box relevance and edge-net pressure']`
- Required scope/companion terms: `['box_area_relevance', 'edge_net_pressure_proxy', 'current_owner', 'successful_next_provider']`

### cand.krk.strategy.fence_or_cut_repair_affordance.v0

- Target concept: `fence_or_cut_repair_affordance`
- Matching records: `22`
- Result distribution: `{'unknown': 3, 'max_plies': 16, 'mate': 3}`
- Mate precision: `0.158`
- Max-plies/failure precision: `0.842`
- Source-stage distribution: `{'stage7': 9, 'stage5': 6, 'stage6': 5, 'stage4': 2}`
- Stage 7-only precision: `{'matching_record_count': 9, 'result_distribution': {'unknown': 3, 'max_plies': 6}, 'mate_precision': 0.0, 'failure_precision': 1.0, 'unknown_count': 3}`
- Cross-stage generality: `{'label': 'cross_stage_broad', 'source_stage_count': 4, 'non_stage7_matching_count': 13}`
- Associated with: `failure`
- Typed as: `risk/failure monitor`
- Causal recommendation: `sandbox-blocked`
- Rationale: failure-correlated; currently better as repair-pressure evidence than positive affordance
- Suggested refinement terms: `['split broken-fence detection from safe repair availability', 'require explicit repair move existence before calling it an affordance']`
- Required scope/companion terms: `['repair_or_reestablish_cut_available', 'rook_safe_after_repair', 'box_area_not_expanded_after_reply']`

### cand.krk.strategy.plan_selection_needed.v0

- Target concept: `plan_selection_needed`
- Matching records: `9`
- Result distribution: `{'unknown': 3, 'max_plies': 6}`
- Mate precision: `0.000`
- Max-plies/failure precision: `1.000`
- Source-stage distribution: `{'stage7': 9}`
- Stage 7-only precision: `{'matching_record_count': 9, 'result_distribution': {'unknown': 3, 'max_plies': 6}, 'mate_precision': 0.0, 'failure_precision': 1.0, 'unknown_count': 3}`
- Cross-stage generality: `{'label': 'stage7_only', 'source_stage_count': 1, 'non_stage7_matching_count': 0}`
- Associated with: `failure`
- Typed as: `growth-pressure/internal monitor`
- Causal recommendation: `non-causal only`
- Rationale: stage7-only failure-oriented term; useful as a monitor, not a move-support affordance
- Suggested refinement terms: `['separate plan-entry marker from plan-policy quality', 'add post-plan handoff success/failure companion label']`
- Required scope/companion terms: `['plan_capsule_context', 'handoff_success_after_plan', 'post_plan_stagnation']`

## Next Step

architecture_review_or_refine_companion_terms_before_any_runtime_sandbox

No runtime arbiter, causal terminal, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, or topology mutation is authorized by this report.
