# KRK Selected Provider Diversity Sampling Manifest Review v0

This review authorizes at most a bounded selection-only observation scan. It does not run playout labels, implement a selector, promote Stage 7, or train Stage 8.

## Summary

- Jobs: `20`
- Jobs by stage: `{'stage4': 10, 'stage5': 6, 'stage6': 4}`
- Stage 7 jobs: `0`
- Violations: `[]`
- Observations allowed: `True`

## Bounds

- Selection only: `True`
- Playout labels: `False`
- Max jobs: `45`
- Per-stage max: `15`

## Decision

- Status: `selected_provider_diversity_sampling_manifest_review_passed`
- Recommended next step: `run_bounded_selected_provider_observation_scan`
- Runtime arbiter and selector sandbox remain blocked.
