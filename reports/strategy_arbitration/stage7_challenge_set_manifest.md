# Stage 7 Challenge Set Manifest

This manifest is non-causal. Stage 7 residuals are held-out challenge cases for KRK strategy arbitration, not local repair targets.

## Status

- Stage 7 status: `local_valid_composition_quarantined`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
- Runtime behavior changed: `False`

## Summary

- Challenge families: `6`
- Evidence merge rows: `9`
- Strategy dataset records: `33`
- Evidence hypothesis labels: `{'missing_feature_candidate': 4, 'continuation_capacity_candidate': 4, 'training_objective_model_expression_candidate': 2, 'unresolved_without_new_continuation_policy': 4, 'bad_curriculum_boundary_candidate': 6, 'phase_boundary_candidate': 4, 'already_solved_by_existing_provider_if_arbitrated': 2, 'strategy_arbitration_candidate': 2}`

## Families

### 0926-like candidate-move family

- Family key: `0926_candidate_move`
- Tests hypotheses: `['missing_feature_ontology', 'strategy_arbitration_phase_boundary']`
- Known partial success: CandidateMoveFrame role identified exactly one visible matching move in the 0926 case.
- Rejected repair: Do not hardcode e4d3 or create state-hash move exceptions.
- Artifact presence: `{'stage7_0926_move_shape_role_candidate_audit.json': True, 'stage7_0926_candidate_move_layer_smoke.json': True}`

### 069-like drive/fence arbitration families

- Family key: `069_drive_fence`
- Tests hypotheses: `['strategy_arbitration_phase_boundary', 'bad_curriculum_boundary']`
- Known partial success: Drive/fence family-specific ownership repairs showed existing providers can solve some cases.
- Rejected repair: Do not revive broad drive support or broad score bonuses.
- Artifact presence: `{'stage7_069_drive_support_post_box_diagnosis.json': True, 'stage7_069_score_normalization_probe.json': True, 'stage7_drive_fence_family_balanced_summary.json': True}`

### 2cc-like post-box continuation families

- Family key: `2cc_post_box_continuation`
- Tests hypotheses: `['training_objective_model_expression', 'continuation_capacity']`
- Known partial success: DTM/top-k labels show theoretical signal, but learned capsule ownership still failed closed loop.
- Rejected repair: Do not use DTM/tablebase at runtime and do not tune Plan Capsule micro-parameters again.
- Artifact presence: `{'stage7_2cc_candidate_move_dtm_alignment.json': True, 'stage7_capsule_trajectory_fidelity_audit.json': True, 'stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json': True}`

### Plan Capsule owned-arbitration residuals

- Family key: `plan_capsule_owned_residuals`
- Tests hypotheses: `['continuation_capacity', 'training_objective_model_expression']`
- Known partial success: Plan Capsule entry/owned-window instrumentation made multi-ply failures inspectable.
- Rejected repair: Do not add another runtime Plan Capsule tweak from this checkpoint.
- Artifact presence: `{'stage7_plan_capsule_owned_failure_analysis_50_h40.json': True, 'stage7_expanded_ranked_capsule_phase1_replay_h40.json': True}`

### box_shrink reward/contract mismatch cases

- Family key: `reward_contract_mismatch`
- Tests hypotheses: `['missing_feature_ontology', 'bad_curriculum_boundary']`
- Known partial success: Growth Monitor / StructuralCandidate path captured mismatch evidence non-causally.
- Rejected repair: Do not promote Stage 7 from local reward confirmation alone.
- Artifact presence: `{'stage7_box_shrink_semantic_audit.json': True, 'stage7_box_shrink_candidates.json': True}`

### known stage0_basin fallback failures

- Family key: `stage0_fallback_failures`
- Tests hypotheses: `['strategy_arbitration_phase_boundary', 'bad_curriculum_boundary']`
- Known partial success: Evidence shows high-scoring fallback ownership can be wrong near post-box boundaries.
- Rejected repair: Do not add broad stage0 suppression.
- Artifact presence: `{'stage7_evidence_merge_table.json': True, 'stage7_unified_strategy_arbitration_dataset.json': True}`

## Global Rejected Paths

- stage7_runtime_repair
- support_adapter
- score_bonus_or_provider_penalty
- stage0_suppression
- plan_capsule_micro_tuning
- runtime_dtm_or_tablebase
- stage7_promotion
- stage8_training
