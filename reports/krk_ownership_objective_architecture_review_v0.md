# KRK Ownership Objective Architecture Review v0

This review closes the latest ownership-evidence branch. It does not authorize runtime behavior, selector training, Stage 7 promotion, or Stage 8 training.

## Summary

- `ownership_rows`: `41`
- `converted_rows`: `31`
- `failed_rows`: `10`
- `stage7_rows`: `0`
- `non_stage0_rows`: `4`
- `best_objective`: `stage_provider_family@0.75`
- `best_negative_suppression`: `0.6`
- `best_positive_recall`: `0.5806451612903226`
- `best_balanced_objective`: `raw_score_bucket@0.75`
- `best_balanced_negative_suppression`: `0.2`
- `best_balanced_positive_recall`: `0.8064516129032258`
- `runtime_threshold_passed`: `False`
- `source_diversity_status`: `source_diversity_gap_blocks_runtime`

## Interpretation

- Labeling here means offline observation of what the current graph selected and whether that selected path converted; it is not hand-authoring a policy.
- Targeted source-diversity work recovered non-stage0 selected-owner evidence and proved current profile can preserve those owners.
- Targeted false-positive risk-cell labels added true ownership negatives, but the probe still cannot preserve safe owners and suppress unsafe owners simultaneously.
- The remaining blocker is objective structure: global row classification over sparse labels is too crude for ownership selection.
- The next principled objective should be state-local or paired: compare candidate owners within the same state/control context, preserve validated safe owners, and suppress only owners with direct same-context failure evidence.

## Recommended Next Design

- `status`: `state_local_paired_ownership_objective_design`
- `goal`: `separate safe-owner preservation from unsafe-owner suppression using same-state comparisons`
- `required_inputs`: `['normal_selected_owner_outcome', 'same_state_alternative_provider_capacity_when_available', 'provider_family_and_terminal_context', 'source_stage_and_active_landmark_scope', 'explicit abstain/no_selector_when_no_safe_pair evidence']`
- `forbidden_shortcuts`: `['global provider penalty', 'forced-capacity labels as direct ownership labels', 'Stage7 training rows', 'runtime selector before paired-objective review']`

## Decision

- `status`: `ownership_objective_requires_state_local_pairing_review`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `design_non_causal_state_local_paired_ownership_objective`
