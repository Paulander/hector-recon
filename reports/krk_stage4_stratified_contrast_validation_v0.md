# KRK Stage 4 Stratified Contrast Validation v0

## Decision

- status: `stage4_stratified_contrast_validation_supports_first_move_ranking_gap`
- recommended_next_step: `stage4_stratified_first_move_contrast_review_packet`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`

## Summary

- variant_count: `4`
- candidate_row_count: `48`
- variant_status_counts: `{'first_move_ranking_gap_reproduced': 4}`
- gap_variant_count: `4`

## Variants

| variant | selected_move | selected_result | converting_count | status |
| --- | --- | --- | ---: | --- |
| identity | b8h8 | max_plies | 7 | first_move_ranking_gap_reproduced |
| mirror_files | g8a8 | max_plies | 7 | first_move_ranking_gap_reproduced |
| mirror_ranks | b1h1 | max_plies | 4 | first_move_ranking_gap_reproduced |
| rotate_180 | g1a1 | max_plies | 8 | first_move_ranking_gap_reproduced |

## Boundaries

- This is non-causal symmetry-stratified validation, not selector training.
- No runtime selector, score change, exact-state patch, Stage 7 promotion, or Stage 8 training is authorized.
