# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 25
- No move: 0
- One-ply statuses: {'passed': 16, 'failed': 9}
- Conversion statuses: {'passed': 15, 'failed': 10}
- Playouts: {'mate': 15, 'max_plies': 10}
- Handoff gaps: 2
- Route conflicts: 0

## Successor Skills

- `krk.edge_trap_close` selected 10 times
- `krk.stage7_drive_repair` selected 9 times
- `krk.stage7_king_tempo` selected 4 times

## Failure Motifs

Failure classes:
- `selected_successor_miscalibrated`: 9

- `krk.box_shrink` via `krk.stage7_drive_repair` resulted in `max_plies` (count=6, gap=False, conflict=False)
- `krk.box_shrink` via `krk.stage7_king_tempo` resulted in `max_plies` (count=4, gap=False, conflict=False)

Selected successor by outcome:
- `krk.edge_trap_close:mate`: 10
- `krk.stage7_drive_repair:max_plies`: 6
- `krk.stage7_king_tempo:max_plies`: 4
- `krk.stage7_drive_repair:mate`: 3

Visible eligible successors:
- `krk.stage0_finish`: 10
- `krk.box_shrink_to_drive_repair`: 9
- `krk.edge_rook_transfer_recovery`: 4
- `krk.fence_maintenance`: 4
- `krk.fence_repair`: 4
- `krk.rook_transfer_after_fence`: 4

## Semantic Alignment

Status counts:
- `reward_visible_fence_aligned_survived`: 14
- `reward_contract_mismatch`: 5
- `neither_reward_nor_visible_contract`: 4
- `reward_visible_fence_aligned_reply_not_checked`: 2

Conversion by semantic alignment:
- `reward_visible_fence_aligned_reply_not_checked`: {'mate': 2}
- `neither_reward_nor_visible_contract`: {'mate': 3, 'max_plies': 1}
- `reward_visible_fence_aligned_survived`: {'mate': 10, 'max_plies': 4}
- `reward_contract_mismatch`: {'max_plies': 5}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=mate`: 10
- `reward=true|visible_fence=false|fence_survived_reply=false|conversion=max_plies`: 5
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=max_plies`: 4
- `reward=false|visible_fence=false|fence_survived_reply=false|conversion=mate`: 3
- `reward=true|visible_fence=true|fence_survived_reply=not_checked|conversion=mate`: 2
- `reward=false|visible_fence=false|fence_survived_reply=false|conversion=max_plies`: 1

Representative mismatch FENs:
- `reward_visible_fence_aligned_reply_not_checked`:
  - sample=0 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
  - sample=8 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
- `neither_reward_nor_visible_contract`:
  - sample=1 start=8/8/8/8/R7/8/2k1K3/8 w - - 0 1 move=a4a8 post_reply=R7/8/8/8/8/2k5/4K3/8 w - - 2 2 result=mate
  - sample=3 start=8/8/8/3k4/8/R7/8/3K4 w - - 0 1 move=a3a8 post_reply=R7/8/8/8/3k4/8/8/3K4 w - - 2 2 result=max_plies
  - sample=12 start=8/8/8/8/R7/8/2k1K3/8 w - - 0 1 move=a4a8 post_reply=R7/8/8/8/8/2k5/4K3/8 w - - 2 2 result=mate
- `reward_contract_mismatch`:
  - sample=6 start=8/8/8/8/3k4/8/3K4/R7 w - - 0 1 move=a1a8 post_reply=R7/8/8/8/2k5/8/3K4/8 w - - 2 2 result=max_plies
  - sample=9 start=8/8/8/8/3k4/8/3K4/R7 w - - 0 1 move=a1a8 post_reply=R7/8/8/8/2k5/8/3K4/8 w - - 2 2 result=max_plies
  - sample=11 start=8/8/8/8/3k4/8/3K4/R7 w - - 0 1 move=a1a8 post_reply=R7/8/8/8/2k5/8/3K4/8 w - - 2 2 result=max_plies

## Shadow Candidates

- `repeated_conversion_failure`: 9
- `high_score_conversion_failure`: 9
- `reward_contract_mismatch`: 5

## Recommended Next Actions

- Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation.
- Inspect low-affordance post-reply states and consider a shadow stem for a dedicated continuation skill.
- Prioritize diagnostics for successor `krk.stage7_drive_repair` because it appears in failed post-reply handoffs.
- Use `repeated_conversion_failure` as the first shadow-growth queue filter; do not create durable nodes yet.
