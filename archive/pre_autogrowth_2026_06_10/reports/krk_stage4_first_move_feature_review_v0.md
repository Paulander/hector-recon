# KRK Stage 4 First-Move Feature Review v0

## Decision

- status: `stage4_first_move_feature_contrast_found_single_state`
- recommended_next_step: `synthetic_or_stratified_stage4_contrast_validation`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`

## Summary

- row_count: `12`
- success_count: `7`
- failure_count: `5`
- single_state_only: `true`

## Interpretation

- The selected failed move is separable from several converting first moves by simple visible move-shape terms.
- The evidence is one repeated state only, so these terms are not runtime-ready and should not be treated as general selector labels.
- The safest next step is synthetic/stratified contrast validation or a sequence-policy review, not an exact-state patch.

## Candidate Terms

- candidate_positive_terms: `['king_destination_c_file', 'rook_mid_rank8_cut_candidate']`
- candidate_failure_terms: `['king_destination_a7', 'rook_far_rank8_drift_candidate']`

## Boolean Feature Summary

| feature | true_count | true_success | true_failure | true_success_precision |
| --- | ---: | ---: | ---: | ---: |
| king_destination_a7 | 1 | 0 | 1 | 0.000 |
| king_destination_c_file | 3 | 3 | 0 | 1.000 |
| rook_far_rank8_drift_candidate | 4 | 0 | 4 | 0.000 |
| rook_mid_rank8_cut_candidate | 3 | 3 | 0 | 1.000 |
| king_move | 5 | 4 | 1 | 0.800 |
| king_destination_rank7_or_8 | 4 | 3 | 1 | 0.750 |
| rook_rank8_destination | 7 | 3 | 4 | 0.429 |

## Boundaries

- These are single-state visible contrast terms, not runtime terminals or selector labels.
- No exact-state patch, selector training, score change, Stage 7 promotion, or Stage 8 training is authorized.
