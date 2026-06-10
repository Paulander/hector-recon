# KRK Abstention-First Selector Objective v0

This design responds to the selector failure mode: current probes select positives too easily and do not suppress negative ownership examples. It is non-causal and does not implement a runtime selector.

## Problem Statement

Current selector probes can recover many converting providers but fail to reject negative ownership examples. The next selector objective should first decide whether any proposed owner is safe enough to select; only then should it rank owners.

## Objective Components

- `ownership_abstention_gate` target=`reject unsafe or unsupported provider ownership` metric=`negative_suppression` minimum=`0.7`
- `owner_ranking_after_pass` target=`rank only proposals that pass the abstention gate` metric=`positive_precision` minimum=`0.75`
- `challenge_set_generalization` target=`do not train on Stage7 residuals; use them as held-out rejection/challenge examples` metric=`heldout_negative_suppression` minimum=`0.7`

## Data Requirements Before Runtime Review

- `minimum_training_rows`: `40`
- `minimum_negative_training_rows`: `12`
- `minimum_training_states`: `12`
- `required_stages`: `['stage4', 'stage5', 'stage6']`
- `stage7_training_rows`: `0`
- `heldout_stage7_rows_minimum`: `8`
- `required_splits`: `['leave_state_out', 'leave_stage_out_if_data_allows']`

## Evaluation Protocol

- Train/evaluate the abstention gate on protected Stage4/5/6 only.
- Measure negative_suppression before positive owner ranking.
- If abstention fails, no runtime selector review is allowed.
- If abstention passes, evaluate owner ranking on pass-filtered proposals.
- Evaluate Stage7 residuals only as held-out challenge rows.

## Decision

- Status: `abstention_first_selector_objective_defined`
- Recommended next step: `collect_or_reconstruct_protected_negative_controls_for_abstention_gate`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
