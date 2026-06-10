# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 25
- No move: 0
- One-ply statuses: {'passed': 21, 'failed': 4}
- Conversion statuses: {'passed': 19, 'failed': 6}
- Playouts: {'mate': 19, 'max_plies': 6}
- Handoff gaps: 2
- Route conflicts: 3

## Successor Skills

- `krk.edge_trap_close` selected 10 times
- `krk.stage0_basin` selected 6 times
- `krk.stage7_king_tempo` selected 4 times
- `krk.drive_to_edge` selected 3 times

## Failure Motifs

Failure classes:
- `selected_successor_miscalibrated`: 6

- `krk.box_shrink` via `krk.stage0_basin` resulted in `max_plies` (count=6, gap=False, conflict=False)

Selected successor by outcome:
- `krk.edge_trap_close:mate`: 10
- `krk.stage0_basin:max_plies`: 6
- `krk.stage7_king_tempo:mate`: 4
- `krk.drive_to_edge:mate`: 3

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
- `reward_contract_mismatch`: 9
- `reward_visible_fence_aligned_reply_not_checked`: 2

Conversion by semantic alignment:
- `reward_visible_fence_aligned_reply_not_checked`: {'mate': 2}
- `reward_contract_mismatch`: {'max_plies': 6, 'mate': 3}
- `reward_visible_fence_aligned_survived`: {'mate': 14}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=mate`: 14
- `reward=true|visible_fence=false|fence_survived_reply=false|conversion=max_plies`: 6
- `reward=true|visible_fence=false|fence_survived_reply=false|conversion=mate`: 3
- `reward=true|visible_fence=true|fence_survived_reply=not_checked|conversion=mate`: 2

Representative mismatch FENs:
- `reward_visible_fence_aligned_reply_not_checked`:
  - sample=0 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
  - sample=8 start=2k5/8/2K1R3/8/8/8/8/8 w - - 0 1 move=e6e8 post_reply=None result=mate
- `reward_contract_mismatch`:
  - sample=1 start=8/8/8/8/R7/8/2k1K3/8 w - - 0 1 move=a4h4 post_reply=8/8/8/8/7R/2k5/4K3/8 w - - 2 2 result=mate
  - sample=3 start=8/8/8/3k4/8/R7/8/3K4 w - - 0 1 move=a3a6 post_reply=8/8/R7/8/2k5/8/8/3K4 w - - 2 2 result=max_plies
  - sample=6 start=8/8/8/8/3k4/8/3K4/R7 w - - 0 1 move=a1a5 post_reply=8/8/8/R7/4k3/8/3K4/8 w - - 2 2 result=max_plies

## Role-Provider Support Adapter

- Adapter support fires: 9

Supported providers by outcome:
- `krk.drive_to_edge:mate`: 9

Supported moves by outcome:
- `e2e3:mate`: 9

## Shadow Candidates

- `reward_contract_mismatch`: 9
- `repeated_conversion_failure`: 6
- `high_score_conversion_failure`: 6

## Recommended Next Actions

- Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation.
- Inspect low-affordance post-reply states and consider a shadow stem for a dedicated continuation skill.
- Compare competing successor skills in route-conflict states before changing scoring or topology.
- Prioritize diagnostics for successor `unknown` because it appears in failed post-reply handoffs.
- Use `reward_contract_mismatch` as the first shadow-growth queue filter; do not create durable nodes yet.
