# KRK Ownership Selection Labeling Review v0

This review closes the current ownership-label expansion slice. It is non-causal evidence only: no runtime selector, arbiter, candidate generator, terminal, topology mutation, Stage 7 promotion, or Stage 8 training was added.

## What Labeling Means Here

“Labeling” is not hand-authoring a chess policy. The label is an offline observation of the current graph:

- Which provider normal routing selected.
- Which move it selected.
- Whether the h40 playout converted.
- Failure trace evidence only when the selected playout failed.

The human-authored part is the measurement protocol, sampling bounds, safety constraints, and artifact schema. The policy result is produced by the current graph and the offline harness. These labels remain evidence for later review, not causal runtime rules.

## Evidence Added

- First diversity label slice: `20` protected jobs, `16` selected-owner converted, `4` selected-owner failed.
- Second fresh-seed diversity slice: `18` protected jobs, `15` selected-owner converted, `3` selected-owner failed.
- Deduplicated ownership dataset v2: `34` protected rows, `25` converted / `9` failed.
- Stage 7 rows: `0`.
- Selector training rows: `0`.

The second fresh-seed slice produced useful raw observations, but no new deduplicated state/provider rows. That is a sampling-overlap signal and a reason to stop blind label farming.

## Probe Result

The best ownership probe remains underpowered:

- Objective: `stage_provider_family@0.75`.
- Negative suppression: `0.556`.
- Positive recall: `0.56`.
- Accuracy: `0.559`.

That is not enough for selector training or runtime review.

## Decision

Status:

```text
ownership_labels_improved_but_selector_runtime_blocked
```

Recommended next step:

```text
review_sampling_source_diversity_and_ownership_feature_semantics_before_more_labels
```

Runtime selector/arbiter/candidate-generator work remains blocked.
