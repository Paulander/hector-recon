# KRK Normalized Selector Probe Review v1

This review gates the normalized selector objective before any further runtime test.

## Probe Summary

- `status`: `normalized_objective_probe_underpowered_fields_available`
- `benchmark_underpowered`: `True`
- `normalized_fields_available`: `True`
- `stage7_training_leakage`: `False`
- `best_provenance_objective`: `family_rank_score_bucket`
- `best_provenance_accuracy`: `0.8888888888888888`
- `family_maturity_baseline_accuracy`: `0.7962962962962963`
- `normalized_over_baseline_delta`: `0.09259259259259256`

## Interpretation

- `positive_signal`: family_rank_score_bucket improved over the family/maturity provenance baseline on existing provenance rows
- `readiness_blocker`: dataset is still small, balanced rows lack rank/score fields, and Stage7 is held out
- `runtime_conclusion`: not_runtime_ready

## Minimum Next Evidence

- `export ranked StrategyProposalFrame rows for balanced/protected controls`
- `keep selected/forced/same-move label channels separate`
- `include provider_local_rank and normalized_score in every new labeled row`
- `keep Stage7 residual rows held out as challenge/evaluation only`
- `rerun normalized objective probe before any runtime test`

## Decision

- Status: `normalized_selector_signal_promising_more_ranked_frames_required`
- Recommended next step: `build_ranked_strategy_proposal_frame_dataset_v1`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Blocked Next Steps

- `runtime_selector`
- `higher_additive_support_playout`
- `stage7_repair`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
