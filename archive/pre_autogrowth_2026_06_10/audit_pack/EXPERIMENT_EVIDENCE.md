# Experiment Evidence

Generated for external review of HEAD `2e0a570` (`Close selector behavior branch`).

This file extracts actual evidence from tests, reports, logs, and generated artifacts. If evidence is missing or weak, it says so.

## Fresh Test Output

Command run from repo root:

```text
uv run pytest
```

Result:

```text
1098 passed in 35.76s
```

This is good evidence that current tests pass. It is not evidence that the current branch solves arbitrary KRK. Many tests validate plumbing, report invariants, safety gates, and known quarantines.

## KRK Performance Evidence

### Entry and early curriculum

Evidence sources:

- `reports/krk_clean_retrain_retry1_result_v1.md`
- `reports/krk_clean_stack_post_replacement_validation_v0.md`
- `scripts/run_krk_triplet_pipeline.py`
- `tests/test_krk_triplet_pipeline.py`

Extracted evidence:

- Clean retry completed through Stage6 overlay and basic checks passed in `reports/krk_clean_retrain_retry1_result_v1.md`.
- The report records strong early checks, including KRK entry and Stage1 backchain success, and Stage6 h40 conversion passing in that run.
- `reports/krk_clean_stack_post_replacement_validation_v0.md` says the clean stack was adopted and validated after replacement/guardrail review.

Limit:

- This is not full KRK competence. The same report lineages keep Stage7 quarantined and Stage8 blocked.

### Stage7

Evidence sources:

- `reports/structural_candidates/stage7_pause_and_architecture_review.md`
- `reports/structural_candidates/stage7_post_decision_closure.md`
- `reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json`
- `reports/structural_candidates/stage7_clean_control_architecture_review_v0.md`
- `reports/structural_candidates/stage8_compare_base_stage7_box_50_h40_analysis.md`
- `reports/structural_candidates/stage8_opposition_guard_stage7_box_50_h40_analysis.md`

Extracted evidence:

- `reports/structural_candidates/stage7_clean_control_architecture_review_v0.md` records 46 clean candidates, 11 clean sequence success controls against a required threshold of 5, and bounded label playouts with mate count 3 and max_plies 7.
- The same report says this evidence is held-out/evaluation-only and does not authorize runtime behavior, promotion, or Stage8.
- The 50-h40 analyses record one-ply pass 38/50 and conversion pass 19/50, with 31/50 max_plies. They also record selected-successor miscalibration on 31 cases.
- `reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json` reclassifies `box_shrink` as a local evidence handoff trigger and says continuing standalone Stage7 work risks overfitting.

Conclusion:

- Stage7 has useful diagnostic/control evidence.
- Stage7 is not solved at HEAD.
- Stage7 is explicitly not promoted.

### Stage8

Evidence sources:

- `reports/structural_candidates/stage8_opposition_overlay_target_100_h40_analysis.md`
- `reports/structural_candidates/stage8_compare_base_stage7_box_50_h40_analysis.md`
- `reports/krk_stage8_training_readiness_review_v0.md`
- `tests/test_krk_stage8_training_readiness_review.py`

Extracted evidence:

- A targeted Stage8 opposition overlay target report records 100/100 one-ply and 100/100 conversion success.
- Broader/base Stage7-box 50-h40 analyses remain weak at 19/50 conversion and 31/50 max_plies.
- `reports/krk_stage8_training_readiness_review_v0.md` says Stage8 training is blocked pending a sequence-policy gate, Stage7 is not promoted, and runtime/selector/tablebase/topology changes are false.

Conclusion:

- The 100/100 targeted result is not accepted as sufficient evidence for Stage8 readiness.
- Current HEAD says Stage8 remains blocked.

## Selector and Strategy Arbitration Evidence

### Selector objective benchmark

Evidence sources:

- `reports/strategy_arbitration/krk_selector_objective_benchmark_review_packet_v2.md`
- `reports/strategy_arbitration/krk_selector_objective_runtime_review_packet_v0.md`
- `reports/current_agent_brief.md`

Extracted evidence:

- Best non-causal model: `combined_simple_rule`.
- Accuracy: 0.952.
- Safe-preservation recall: 1.0.
- Switch-contrast recall: 0.8.
- Abstain recall: 1.0.
- Runtime authorization rows: 0.

Conclusion:

- The selector objective benchmark is promising as a non-causal classifier/recommender.
- It is not authorized as runtime behavior.

### Selector behavior sandbox regression

Evidence sources:

- `reports/strategy_arbitration/krk_selector_behavior_regression_audit_v0.md`
- `reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.md`
- `reports/strategy_arbitration/krk_selector_behavior_continuation_regression_root_cause_v0.md`
- `reports/strategy_arbitration/krk_selector_behavior_branch_closure_v0.md`
- `tests/test_krk_selector_behavior_regression_audit.py`

Extracted evidence:

- A safe-control row regressed under the behavior sandbox.
- The regression involved a later h40 continuation switch, not the initial owner.
- The root cause report says the sandbox switched at ply 4 from a working fence/continuation path to an edge-trap path and lost continuation.
- The decision report quarantines selector behavior due to safe regression.
- The branch closure report says trace-only selector observability/recommendation artifacts may remain, but provider/move/score/routing/default/suppression changes are not authorized.

Conclusion:

- This is hard negative evidence against the current selector behavior path.
- It supports the current brief's decision to stop selector behavior work and return to broader strategy/sequence control-plane evidence.

## Protected Failure Contrast and Fresh Diversity Evidence

Evidence sources:

- `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_result_v0.md`
- `reports/strategy_arbitration/krk_protected_failure_contrast_additional_collection_decision_v1.md`
- `reports/strategy_arbitration/krk_selector_objective_fresh_diversity_review_packet_v0.md`
- `reports/current_agent_brief.md`

Extracted evidence:

- Protected plan-window collection produced 6 outputs and 0 unique failure candidates.
- The collection status is `collection_complete_underpowered`.
- The additional collection decision says another run is not worth running under the prior v0 framing because the six outputs were conversion-positive and the approval condition changed to Stage5/6-only diversity.
- Fresh diversity review records 8 attempted, 8 joined, 76 frames, 4 selected-failure visible-positive rows, and 4 safe-preservation rows.
- All relevant runtime/provider/score/routing deltas remain zero.

Conclusion:

- The protected contrast data is underpowered for causal selector/policy decisions.
- The fresh diversity data is useful for review, not runtime authorization.

## Curriculum Progression Evidence

Evidence sources:

- `reports/krk_clean_retrain_smoke_result_v0.md`
- `reports/krk_clean_retrain_run_result_v0.md`
- `reports/krk_clean_retrain_retry1_result_v1.md`
- `reports/krk_clean_retrain_retry1_guardrail_result_v1.md`
- `reports/krk_clean_stack_post_replacement_validation_v0.md`
- `reports/krk_full_suite_readiness_audit_v0.md`

Extracted evidence:

- Smoke run: plumbing passed but semantic smoke was too tiny.
- First full clean retrain: incomplete at Stage2A, no promotable checkpoint.
- Retry1: completed through Stage6 overlay and basic checks passed.
- Guardrail review: Stage6 overlay had partial guardrail issues and required quarantine/replacement logic.
- Clean stack post replacement: stack adopted and validated, but Stage7 remained quarantined and Stage8 blocked.
- Full suite readiness: runtime changes, label run, selector training, Stage7 promotion, and Stage8 training remain false.

Conclusion:

- There is real curriculum engineering and meaningful protected-stack progress.
- The evidence supports "progress toward KRK competence", not "KRK competence achieved".

## Handover Evidence

Evidence sources:

- `reports/Hector_Article_Draft.md`
- `reports/recon_long_term_architecture_roadmap.md`
- `reports/architecture_preservation_note.md`
- `tests/test_architecture_preservation.py`
- `src/recon_lite_chess/routing/*`
- `scripts/test_krk_landmark_progress.py`

Extracted evidence:

- The article draft claims autonomous handover and KPK/KQK-style structural maturation.
- The roadmap says `handoff_composition_v1` and the protected stack are validated, while Stage7 is not promoted.
- Architecture preservation tests verify that HandoffPacket, ShadowStemCandidate, SkillContractStats, and provider-promotion evidence remain non-causal unless promoted by explicit mechanisms.

Conclusion:

- Handoff observability and preservation are implemented.
- Current HEAD does not prove autonomous handover into robust KRK strategy. It proves a guarded handoff evidence path.

## Structural Growth Improving Play

Evidence sources:

- `reports/Hector_Article_Draft.md`
- `reports/structural_growth_lab_note.md`
- `reports/structural_candidates/*`
- `src/recon_lite_chess/triplets.py`
- `scripts/run_krk_triplet_pipeline.py`
- `scripts/test_krk_landmark_progress.py`

Extracted evidence:

- The article draft reports structural-growth and handover successes, especially outside the current Stage7/Stage8 blocked path.
- `reports/structural_growth_lab_note.md` says the growth monitor emits non-causal candidate records with credit 0 and no topology/routing/M3/M4 changes.
- Stage7 structural candidate work produced diagnostics and local successes but ended in quarantine/held-out status.

Conclusion:

- There is no strong accepted HEAD evidence that learned structural growth improves arbitrary KRK play.
- The current strongest structural-growth evidence is that the system can propose, represent, evaluate, quarantine, and preserve candidates without hidden runtime control.

## Regressions and Failed Experiments

- Selector behavior sandbox regressed a safe-control row and was quarantined.
- Stage7 direct/local repair failed to become promotable and was reclassified as a handoff/boundary signal.
- Stage8 targeted success did not survive readiness review because Stage7/sequence-policy conditions were not met.
- Protected failure-contrast collection was underpowered.
- Clean retrain first full run failed to produce a promotable checkpoint at Stage2A.
- Stage6 overlay required guardrail quarantine/replacement before clean stack acceptance.

## Missing Evidence

- No fresh, accepted full-KRK benchmark at HEAD showing robust mate conversion over broad random KRK positions.
- No accepted Stage7 promotion.
- No accepted Stage8 training run.
- No causal selector runtime authorization.
- No proof that fast plasticity plus slow consolidation are the main reason KRK performance improved.
- No proof that structural growth is learned rather than selected/designed through external scaffolding.
- No online gameplay-time topology mutation, by design.

## Evidence Bottom Line

The branch has strong evidence for test cleanliness, safety gates, report consistency, protected scaffolding, and identifying regressions before promotion. It has weaker evidence for the core research claim: learned structural growth producing measurable KRK competence. The current evidence supports a cautious continuation of the control-plane/candidate-generation path, not a claim that Hector/ReCoN has solved KRK.
