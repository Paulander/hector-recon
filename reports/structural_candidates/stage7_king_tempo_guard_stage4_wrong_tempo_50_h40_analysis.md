# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 50
- No move: 0
- One-ply statuses: {'passed': 50}
- Conversion statuses: {'passed': 43, 'failed': 7}
- Playouts: {'mate': 43, 'max_plies': 7}
- Handoff gaps: 0
- Route conflicts: 0

## Successor Skills

- `krk.stage0_basin` selected 37 times
- `krk.edge_trap_close` selected 10 times
- `krk.stage7_king_tempo` selected 3 times

## Failure Motifs

Failure classes:
- `selected_successor_miscalibrated`: 7

- `krk.edge_trap_wrong_tempo` via `krk.stage0_basin` resulted in `max_plies` (count=7, gap=False, conflict=False)

Selected successor by outcome:
- `krk.stage0_basin:mate`: 30
- `krk.edge_trap_close:mate`: 10
- `krk.stage0_basin:max_plies`: 7
- `krk.stage7_king_tempo:mate`: 3

Visible eligible successors:
- `krk.edge_rook_transfer_recovery`: 40
- `krk.rook_transfer_after_fence`: 40
- `krk.edge_trap_close_recovery`: 29
- `krk.fence_maintenance`: 11
- `krk.fence_repair`: 11
- `krk.stage0_finish`: 10

## Semantic Alignment

Status counts:
- `reward_visible_fence_aligned_survived`: 50

Conversion by semantic alignment:
- `reward_visible_fence_aligned_survived`: {'mate': 43, 'max_plies': 7}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=mate`: 43
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=max_plies`: 7

## Shadow Candidates

- `repeated_conversion_failure`: 7
- `high_score_conversion_failure`: 7

## Recommended Next Actions

- Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation.
- Use `repeated_conversion_failure` as the first shadow-growth queue filter; do not create durable nodes yet.
