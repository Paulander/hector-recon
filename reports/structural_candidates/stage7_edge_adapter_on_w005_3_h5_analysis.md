# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 3
- No move: 0
- One-ply statuses: {'failed': 2, 'passed': 1}
- Conversion statuses: {'failed': 3}
- Playouts: {'max_plies': 3}
- Handoff gaps: 0
- Route conflicts: 0

## Successor Skills

- `krk.stage0_basin` selected 3 times

## Failure Motifs

Failure classes:
- `selected_successor_miscalibrated`: 3

- `krk.box_shrink` via `krk.stage0_basin` resulted in `max_plies` (count=3, gap=False, conflict=False)

Selected successor by outcome:
- `krk.stage0_basin:max_plies`: 3

Visible eligible successors:
- `krk.edge_rook_transfer_recovery`: 3
- `krk.fence_maintenance`: 3
- `krk.fence_repair`: 3
- `krk.rook_transfer_after_fence`: 3

## Semantic Alignment

Status counts:
- `reward_visible_fence_aligned_survived`: 3

Conversion by semantic alignment:
- `reward_visible_fence_aligned_survived`: {'max_plies': 3}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=max_plies`: 3

## Role-Provider Support Adapter

- Adapter support fires: 8

Supported providers by outcome:
- `krk.edge_trap_close:max_plies`: 8

Supported moves by outcome:
- `a7d7:max_plies`: 8

## Shadow Candidates

- `repeated_conversion_failure`: 3
- `high_score_conversion_failure`: 3

## Recommended Next Actions

- Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation.
- Use `repeated_conversion_failure` as the first shadow-growth queue filter; do not create durable nodes yet.
