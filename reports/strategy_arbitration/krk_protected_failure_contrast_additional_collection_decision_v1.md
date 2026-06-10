# KRK Protected Failure-Contrast Additional Collection Decision v1

Status: `protected_failure_contrast_collection_not_worth_running`

The conditional approval for one additional bounded protected failure-contrast
collection was not consumed.

## Rationale

- The currently reviewed v0 manifest is the already-spent manifest.
- All six expected v0 outputs already exist.
- The prior collection produced six `conversion_positive` outputs and zero new failure rows.
- The v0 manifest includes Stage 4 rows, while the current approval requires protected Stage 5/6-only scope unless a review explicitly says otherwise.
- The current gate exposes review only; no collection command is available.

## Next Gate

Before any additional collection, author and review a fresh bounded Stage 5/6-only
diversity manifest. It should avoid prior seed frames and target new protected
states, switch-contrast rows, provider-family diversity, Stage 5/6 balance, and
progress-window failure contrast.

Runtime selector, routing/scoring/default changes, provider suppression, Stage 7
promotion, Stage 8 training, runtime DTM/tablebase, gameplay-time topology
mutation, and hidden controllers remain blocked.
