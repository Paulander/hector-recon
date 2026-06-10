# KRK Candidate Proposal Quality Probe v1

This probe evaluates simple non-causal quality axes over known protected capacity rows. It is not selector training.

## Decision

- status: `proposal_quality_axes_insufficient_for_selector_review`
- selector_allowed: `False`
- recommended_next_step: `candidate_proposal_quality_decision_gate`

## Summary

- known_capacity_row_count: 38
- stage7_challenge_row_count: 111
- best_probe: `candidate_move_frame_source`
- best_probe_metrics: `{'known_row_count': 38, 'positive_count': 30, 'negative_count': 8, 'predicted_positive_count': 22, 'true_positive': 19, 'false_positive': 3, 'false_negative': 11, 'true_negative': 5, 'positive_precision': 0.8636363636363636, 'positive_recall': 0.6333333333333333, 'negative_suppression': 0.625, 'balanced_score': 0.6291666666666667}`

## Probe Results

- `candidate_move_frame_source`: precision=`0.864` recall=`0.633` negative_suppression=`0.625` balanced=`0.629`
- `validated_provider_pack_source`: precision=`0.688` recall=`0.367` negative_suppression=`0.375` balanced=`0.371`
- `has_post_or_safety_terms`: precision=`0.864` recall=`0.633` negative_suppression=`0.625` balanced=`0.629`
- `visible_density_at_or_above_median`: precision=`0.857` recall=`0.600` negative_suppression=`0.625` balanced=`0.613`
- `visible_density_at_or_above_upper_quartile`: precision=`0.875` recall=`0.467` negative_suppression=`0.750` balanced=`0.608`
- `distinct_from_selected_move`: precision=`0.839` recall=`0.867` negative_suppression=`0.375` balanced=`0.621`
- `same_selected_provider`: precision=`1.000` recall=`0.033` negative_suppression=`1.000` balanced=`0.517`
- `simple_quality_axis`: precision=`0.789` recall=`1.000` negative_suppression=`0.000` balanced=`0.500`

## Boundary

These probe results do not authorize a selector, scoring changes, guardrails, Stage 7 promotion, or Stage 8 training.
