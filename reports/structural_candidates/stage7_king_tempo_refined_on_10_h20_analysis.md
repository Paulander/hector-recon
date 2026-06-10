# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 10
- No move: 0
- One-ply statuses: {'passed': 7, 'failed': 3}
- Conversion statuses: {'failed': 10}
- Playouts: {'max_plies': 10}
- Handoff gaps: 0
- Route conflicts: 0

## Successor Skills

- `krk.stage7_king_tempo` selected 10 times

## Failure Motifs

Failure classes:
- `selected_successor_miscalibrated`: 10

- `krk.box_shrink` via `krk.stage7_king_tempo` resulted in `max_plies` (count=10, gap=False, conflict=False)

Selected successor by outcome:
- `krk.stage7_king_tempo:max_plies`: 10

Visible eligible successors:
- `krk.edge_rook_transfer_recovery`: 10
- `krk.fence_maintenance`: 10
- `krk.fence_repair`: 10
- `krk.rook_transfer_after_fence`: 10

## Semantic Alignment

Status counts:
- `reward_visible_fence_aligned_survived`: 10

Conversion by semantic alignment:
- `reward_visible_fence_aligned_survived`: {'max_plies': 10}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=max_plies`: 10

## Shadow Candidates

- `repeated_conversion_failure`: 10
- `high_score_conversion_failure`: 10

## Recommended Next Actions

- Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation.
- Use `repeated_conversion_failure` as the first shadow-growth queue filter; do not create durable nodes yet.
