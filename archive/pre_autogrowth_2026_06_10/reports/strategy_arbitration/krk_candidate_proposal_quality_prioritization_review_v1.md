# KRK Candidate Proposal Quality / Prioritization Review v1

This review follows the observation sandbox and bounded candidate-move labels. It is non-causal and does not authorize selection.

## Decision

- status: `proposal_quality_prioritization_review_ready`
- selector_allowed: `False`
- recommended_next_step: `build_non_causal_candidate_proposal_quality_dataset`

## Evidence Summary

- observation_frame_count: 569
- candidate_move_frame_count: 363
- protected_annotated_candidate_move_count: 22
- protected_annotation_recall: `0.075`
- bounded_label_count: 12
- bounded_label_positive_capacity_count: 11
- bounded_label_negative_capacity_count: 1
- missing_expected_sources: `['broader_strategy_candidate', 'plan_capsule_sequence_candidate']`

## Diagnosis

- `candidate_generator_is_visible_but_too_broad_and_underannotated`

## Why Not More Blind Labels

- bounded labels found many positives but only raised protected annotation recall to 0.075
- observation emits hundreds of candidate moves, so unprioritized labeling scales poorly
- capacity labels remain candidate-generation evidence, not ownership labels
- negative-capacity provider-pack candidates remain present

## Quality Axes

- `source_channel`: separate validated_provider_pack, candidate_move_frame, plan_capsule_sequence_candidate, and broader_strategy_candidate before ranking
- `visible_term_density`: prioritize candidates with meaningful move_shape/post_move/safety/source terms over low-information legal moves
- `safety_floor`: separate legal-safe candidate generation from conversion-capacity evidence
- `known_capacity_contrast`: use existing positive/negative capacity labels as offline quality calibration only
- `duplicate_or_selected_move_relation`: distinguish current selected move, same-move provider alternatives, and distinct alternatives
- `stage_and_protection_scope`: Stage 4/5/6 protected candidates may train coverage diagnostics; Stage 7 remains held-out challenge

## Forbidden Next Steps

- `runtime_selector`
- `score_changes`
- `provider_routing`
- `guardrail_campaign`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `hidden_python_controller`
- `more_blind_label_farming_without_quality_prioritization`
