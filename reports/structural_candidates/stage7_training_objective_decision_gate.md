# Stage 7 Training-Objective Decision Gate

This report turns the offline benchmark into a hard decision. It is non-causal and does not implement a runtime repair.

## Decision

- Selected outcome: `model_expression_gap_persists_stage7_micro_work_stops`
- Recommended action class: `stop_stage7_micro_work_pending_architecture_review`
- Rationale: Simple ranked/pairwise objectives underperform, internal monitor features do not improve the visible baseline, and oracle ceiling remains high.
- Stage 7 status: `local_valid_composition_quarantined`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Supporting Evidence

- `benchmark_status=model_expression_gap_persists`
- `ranked_top1_improvement=-0.16748768472906406`
- `visible_top1_improvement=0.12561576354679804`
- `internal_monitor_top1_improvement_over_visible=0.0`
- `current_hard_negative_rate=0.2857142857142857`
- `ranked_hard_negative_rate=0.7931034482758621`
- `internal_hard_negative_rate=0.5`
- `oracle_top1=1.0`

## Stop Conditions Reaffirmed

- `no_runtime_repairs`
- `no_stage7_promotion`
- `no_stage8_training`
- `no_runtime_dtm_or_tablebase`
- `no_gameplay_topology_mutation`
- `no_internal_terminal_causal_use`
- `no_new_broad_diagnostic_branch_without_explicit_review`

## Blocked Next Steps

- `implement_runtime_repair`
- `promote_stage7`
- `train_stage8`
- `make_internal_terminals_causal`
- `add_runtime_terminal_topology`
- `use_runtime_dtm_or_tablebase`
- `mutate_topology_during_gameplay`
- `start_broad_diagnostic_branch_without_review`
