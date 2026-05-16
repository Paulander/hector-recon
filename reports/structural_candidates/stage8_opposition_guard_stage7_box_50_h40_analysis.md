# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 50
- No move: 0
- One-ply statuses: {'passed': 38, 'failed': 12}
- Conversion statuses: {'failed': 31, 'passed': 19}
- Playouts: {'max_plies': 31, 'mate': 19}
- Handoff gaps: 4
- Route conflicts: 0

## Successor Skills

- `krk.stage0_basin` selected 25 times
- `krk.edge_trap_close` selected 15 times
- `krk.stage7_king_tempo` selected 6 times

## Failure Motifs

Failure classes:
- `selected_successor_miscalibrated`: 31

- `krk.box_shrink` via `krk.stage0_basin` resulted in `max_plies` (count=25, gap=False, conflict=False)
- `krk.box_shrink` via `krk.stage7_king_tempo` resulted in `max_plies` (count=6, gap=False, conflict=False)

Selected successor by outcome:
- `krk.stage0_basin:max_plies`: 25
- `krk.edge_trap_close:mate`: 15
- `krk.stage7_king_tempo:max_plies`: 6

Visible eligible successors:
- `krk.box_shrink_to_drive_repair`: 25
- `krk.stage0_finish`: 15
- `krk.edge_rook_transfer_recovery`: 6
- `krk.fence_maintenance`: 6
- `krk.fence_repair`: 6
- `krk.rook_transfer_after_fence`: 6

## Semantic Alignment

Status counts:
- `reward_contract_mismatch`: 25
- `reward_visible_fence_aligned_survived`: 21
- `reward_visible_fence_aligned_reply_not_checked`: 4

Conversion by semantic alignment:
- `reward_visible_fence_aligned_reply_not_checked`: {'mate': 4}
- `reward_contract_mismatch`: {'max_plies': 25}
- `reward_visible_fence_aligned_survived`: {'mate': 15, 'max_plies': 6}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=false|fence_survived_reply=false|conversion=max_plies`: 25
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=mate`: 15
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=max_plies`: 6
- `reward=true|visible_fence=true|fence_survived_reply=not_checked|conversion=mate`: 4

Representative mismatch FENs:
- `reward_visible_fence_aligned_reply_not_checked`:
  - sample=0 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
  - sample=8 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
  - sample=38 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
- `reward_contract_mismatch`:
  - sample=1 start=8/8/8/8/R7/8/2k1K3/8 w - - 0 1 move=a4h4 post_reply=8/8/8/8/7R/2k5/4K3/8 w - - 2 2 result=max_plies
  - sample=3 start=8/8/8/3k4/8/R7/8/3K4 w - - 0 1 move=a3a6 post_reply=8/8/R7/8/2k5/8/8/3K4 w - - 2 2 result=max_plies
  - sample=6 start=8/8/8/8/3k4/8/3K4/R7 w - - 0 1 move=a1a5 post_reply=8/8/8/R7/4k3/8/3K4/8 w - - 2 2 result=max_plies

## Shadow Candidates

- `repeated_conversion_failure`: 31
- `high_score_conversion_failure`: 31
- `reward_contract_mismatch`: 25

## Recommended Next Actions

- Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation.
- Inspect low-affordance post-reply states and consider a shadow stem for a dedicated continuation skill.
- Prioritize diagnostics for successor `unknown` because it appears in failed post-reply handoffs.
- Use `repeated_conversion_failure` as the first shadow-growth queue filter; do not create durable nodes yet.
