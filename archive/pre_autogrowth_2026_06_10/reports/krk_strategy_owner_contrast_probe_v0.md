# KRK Strategy Owner Contrast Probe v0

This is a non-causal probe over protected and held-out strategy-owner contrast labels. It does not train or run a selector.

## Metrics

- Rows: `13`
- Training rows: `9`
- Held-out rows: `4`
- Training positives: `13`
- Training negatives: `11`
- Training provider family rates: `{'drive_to_edge': {'total': 2, 'positive': 2, 'negative': 0, 'positive_rate': 1.0}, 'edge_trap': {'total': 19, 'positive': 8, 'negative': 11, 'positive_rate': 0.4211}, 'fence_established': {'total': 3, 'positive': 3, 'negative': 0, 'positive_rate': 1.0}}`
- Held-out provider family rates: `{'drive_to_edge': {'total': 4, 'positive': 1, 'negative': 3, 'positive_rate': 0.25}, 'edge_trap': {'total': 12, 'positive': 0, 'negative': 12, 'positive_rate': 0.0}, 'fence_established': {'total': 4, 'positive': 1, 'negative': 3, 'positive_rate': 0.25}, 'stage0_basin': {'total': 4, 'positive': 0, 'negative': 4, 'positive_rate': 0.0}}`
- Selected training provider families: `['edge_trap']`
- Readiness blockers: `['insufficient_selected_provider_family_diversity']`

## Findings

- `protected_conversion_positive_provider_diversity_present`
- `protected_label_balance_present`
- `selected_provider_family_diversity_still_missing`
- `heldout_stage7_contains_unresolved_all_negative_rows`

## Decision

- Status: `strategy_owner_contrast_signal_present_selector_sandbox_blocked`
- Recommended next step: `architecture_review_selector_readiness_after_contrast_probe`
- Runtime arbiter and selector sandbox remain blocked.
