# KRK Strategy Monitor Records v0

This extraction is replay-free and non-causal. It converts typed feature candidates into StrategyMonitorRecord evidence over existing strategy-arbitration records.

## Status

- Monitor definitions: `5`
- Rejected definitions: `1`
- Monitor records: `108`
- Records by monitor type: `{'PhaseBoundaryMonitor': 52, 'OwnerExitMonitor': 25, 'RepairNeededMonitor': 22, 'PlanSelectionNeededMonitor': 9}`
- Records by active landmark label: `{'box_shrink': 23, 'fence_established': 30, 'drive_to_edge': 35, 'wrong_tempo_control': 20}`
- Records by associated outcome: `{'unknown': 9, 'max_plies': 60, 'mate': 39}`
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Monitor Definitions

### edge_net_affordance

- Monitor type: `PhaseBoundaryMonitor`
- Candidate: `cand.krk.strategy.edge_net_affordance.v0`
- Promotion status: `proposed`
- Confidence: `0.480`
- Source terms: `['black_king_edge_bucket == at_edge', 'edge_net_pressure_proxy', 'edge_trap_shape_available', 'corner_net_pressure_proxy', 'rook_safe']`
- Missing terms: `['safe_edge_net_tighten_move_exists', 'king_support_conversion_affordance', 'draw_risk_absent']`
- Notes: matches successful and failed edge states similarly; not a positive affordance yet

### box_shrink_exit_condition

- Monitor type: `OwnerExitMonitor`
- Candidate: `cand.krk.strategy.box_shrink_exit_condition.v0`
- Promotion status: `proposed`
- Confidence: `0.500`
- Source terms: `['box_area_relevance == low', 'black_king_edge_bucket == at_edge', 'edge_net_pressure_proxy', 'mate_basin_readiness']`
- Missing terms: `['active_landmark_label == box_shrink', 'edge_net_affordance', 'mate_basin_readiness']`
- Notes: mixed success/failure near edge; potential owner-release signal, not provider boost

### phase_boundary_near_edge

- Monitor type: `PhaseBoundaryMonitor`
- Candidate: `cand.krk.strategy.phase_boundary_near_edge.v0`
- Promotion status: `proposed`
- Confidence: `0.480`
- Source terms: `['black_king_edge_bucket in {at_edge, near_edge}', 'box_area_relevance in {low, medium}', 'edge_net_pressure_proxy or fence_exists']`
- Missing terms: `['box_area_relevance', 'edge_net_pressure_proxy', 'current_owner', 'successful_next_provider']`
- Notes: near-edge context is broadly cross-stage and mixed-outcome

### fence_or_cut_repair_affordance

- Monitor type: `RepairNeededMonitor`
- Candidate: `cand.krk.strategy.fence_or_cut_repair_affordance.v0`
- Promotion status: `proposed`
- Confidence: `0.842`
- Source terms: `['fence_exists', 'not fence_stable', 'not cut_stable', 'rook_safe']`
- Missing terms: `['repair_or_reestablish_cut_available', 'rook_safe_after_repair', 'box_area_not_expanded_after_reply']`
- Notes: failure-correlated; currently better as repair-pressure evidence than positive affordance

### plan_selection_needed

- Monitor type: `PlanSelectionNeededMonitor`
- Candidate: `cand.krk.strategy.plan_selection_needed.v0`
- Promotion status: `monitoring_only`
- Confidence: `1.000`
- Source terms: `['stage7 residual', 'no visible heuristic hit', 'post_box continuation / capsule context', 'current_graph_h40 == max_plies']`
- Missing terms: `['plan_capsule_context', 'handoff_success_after_plan', 'post_plan_stagnation']`
- Notes: stage7-only failure-oriented term; useful as a monitor, not a move-support affordance

## Rejected Definitions

- `king_support_conversion_affordance`: `too broad / reject`; matches nearly all records and is not separable enough as currently defined

## Outcomes By Monitor Type

- `PhaseBoundaryMonitor`: `{'unknown': 2, 'max_plies': 26, 'mate': 24}`
- `OwnerExitMonitor`: `{'unknown': 1, 'mate': 12, 'max_plies': 12}`
- `RepairNeededMonitor`: `{'unknown': 3, 'max_plies': 16, 'mate': 3}`
- `PlanSelectionNeededMonitor`: `{'unknown': 3, 'max_plies': 6}`

## Answers

- Monitor activations are Stage7-only: `False`
- Repair and plan monitors are failure-oriented: `True`
- Records authorize runtime behavior: `False`
- Next step: `architecture_review_or_targeted_companion_term_design`

No runtime arbiter, causal terminal, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, or topology mutation is authorized by these records.
