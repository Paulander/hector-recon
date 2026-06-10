# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 25
- No move: 0
- One-ply statuses: {'failed': 13, 'passed': 12}
- Conversion statuses: {'passed': 13, 'failed': 12}
- Playouts: {'mate': 13, 'max_plies': 12}
- Handoff gaps: 0
- Route conflicts: 0

## Successor Skills

- `krk.stage7_king_tempo` selected 25 times

## Failure Motifs

Failure classes:
- `selected_successor_miscalibrated`: 12

- `krk.box_shrink` via `krk.stage7_king_tempo` resulted in `max_plies` (count=12, gap=False, conflict=False)

Selected successor by outcome:
- `krk.stage7_king_tempo:mate`: 13
- `krk.stage7_king_tempo:max_plies`: 12

Visible eligible successors:
- `krk.edge_rook_transfer_recovery`: 25
- `krk.fence_maintenance`: 25
- `krk.fence_repair`: 25
- `krk.rook_transfer_after_fence`: 25

## Semantic Alignment

Status counts:
- `reward_visible_fence_aligned_survived`: 25

Conversion by semantic alignment:
- `reward_visible_fence_aligned_survived`: {'mate': 13, 'max_plies': 12}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=mate`: 13
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=max_plies`: 12

## Shadow Candidates

- `repeated_conversion_failure`: 12
- `high_score_conversion_failure`: 12

## Recommended Next Actions

- Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation.
- Use `repeated_conversion_failure` as the first shadow-growth queue filter; do not create durable nodes yet.
