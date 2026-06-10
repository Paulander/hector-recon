# KRK Selected-Owner Failure-Risk Evidence v1

## Summary

- rows: `48`
- Stage 7 readiness rows: `0`
- selector-training rows: `0`
- split counts: `{'discovery_proxy_dataset': 40, 'independent_validation_label': 8}`
- target counts: `{'safe_preservation': 40, 'failure_risk': 8}`
- alternative live proposal rows: `5`
- progress-window trace rows: `6`
- progress-window failure rows: `6`

## Evidence Tracks

- `visible_competing_proposal`: `sparse_or_missing_for_alternatives`. Ranked proposal frames mostly expose the selected owner; forced alternatives are usually offline labels, not live proposals.
- `progress_window`: `available_when_selected_owner_trace_exists`. Progress-window evidence is visible only after the selected owner has already run; it is monitor evidence, not an initial pre-decision selector input.

## Boundary

This evidence is non-causal. Forced-provider outcomes and selected-owner outcomes are labels only; they are not runtime inputs.
