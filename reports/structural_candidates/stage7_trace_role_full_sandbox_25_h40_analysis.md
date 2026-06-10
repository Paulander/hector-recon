# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 25
- No move: 0
- One-ply statuses: {'passed': 21, 'failed': 4}
- Conversion statuses: {'passed': 16, 'failed': 9}
- Playouts: {'mate': 16, 'max_plies': 9}
- Handoff gaps: 2
- Route conflicts: 0

## Successor Skills

- `krk.edge_trap_close` selected 14 times
- `krk.stage7_drive_repair` selected 9 times

## Failure Motifs

Failure classes:
- `selected_successor_miscalibrated`: 9

- `krk.box_shrink` via `krk.stage7_drive_repair` resulted in `max_plies` (count=9, gap=False, conflict=False)

Selected successor by outcome:
- `krk.edge_trap_close:mate`: 14
- `krk.stage7_drive_repair:max_plies`: 9

Visible eligible successors:
- `krk.stage0_finish`: 10
- `krk.box_shrink_to_drive_repair`: 9
- `krk.post_box_king_opposition_repair`: 4

## Semantic Alignment

Status counts:
- `reward_visible_fence_aligned_survived`: 10
- `reward_contract_mismatch`: 7
- `reward_visible_fence_aligned_broken_by_reply`: 6
- `reward_visible_fence_aligned_reply_not_checked`: 2

Conversion by semantic alignment:
- `reward_visible_fence_aligned_reply_not_checked`: {'mate': 2}
- `reward_contract_mismatch`: {'mate': 4, 'max_plies': 3}
- `reward_visible_fence_aligned_broken_by_reply`: {'max_plies': 6}
- `reward_visible_fence_aligned_survived`: {'mate': 10}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=mate`: 10
- `reward=true|visible_fence=true|fence_survived_reply=false|conversion=max_plies`: 6
- `reward=true|visible_fence=false|fence_survived_reply=false|conversion=mate`: 4
- `reward=true|visible_fence=false|fence_survived_reply=false|conversion=max_plies`: 3
- `reward=true|visible_fence=true|fence_survived_reply=not_checked|conversion=mate`: 2

Representative mismatch FENs:
- `reward_visible_fence_aligned_reply_not_checked`:
  - sample=0 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
  - sample=8 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
- `reward_contract_mismatch`:
  - sample=1 start=8/8/8/8/R7/8/2k1K3/8 w - - 0 1 move=a4e4 post_reply=8/8/8/8/4R3/2k5/4K3/8 w - - 2 2 result=max_plies
  - sample=2 start=8/8/8/8/4K3/R7/4k3/8 w - - 0 1 move=a3e3 post_reply=8/8/8/8/4K3/4R3/3k4/8 w - - 2 2 result=mate
  - sample=12 start=8/8/8/8/R7/8/2k1K3/8 w - - 0 1 move=a4e4 post_reply=8/8/8/8/4R3/2k5/4K3/8 w - - 2 2 result=max_plies
- `reward_visible_fence_aligned_broken_by_reply`:
  - sample=3 start=8/8/8/3k4/8/R7/8/3K4 w - - 0 1 move=a3a5 post_reply=8/8/8/R7/4k3/8/8/3K4 w - - 2 2 result=max_plies
  - sample=6 start=8/8/8/8/3k4/8/3K4/R7 w - - 0 1 move=a1d1 post_reply=8/8/8/2k5/8/8/3K4/3R4 w - - 2 2 result=max_plies
  - sample=9 start=8/8/8/8/3k4/8/3K4/R7 w - - 0 1 move=a1d1 post_reply=8/8/8/2k5/8/8/3K4/3R4 w - - 2 2 result=max_plies

## Role-Provider Support Adapter

- Adapter support fires: 16

Supported providers by outcome:
- `krk.edge_trap_close:mate`: 16

Supported moves by outcome:
- `e4d4:mate`: 16

## Shadow Candidates

- `repeated_conversion_failure`: 9
- `high_score_conversion_failure`: 9
- `reward_contract_mismatch`: 7

## Recommended Next Actions

- Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation.
- Inspect low-affordance post-reply states and consider a shadow stem for a dedicated continuation skill.
- Prioritize diagnostics for successor `unknown` because it appears in failed post-reply handoffs.
- Use `repeated_conversion_failure` as the first shadow-growth queue filter; do not create durable nodes yet.
