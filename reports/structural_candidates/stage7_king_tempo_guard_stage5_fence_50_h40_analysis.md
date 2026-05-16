# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 50
- No move: 0
- One-ply statuses: {'passed': 50}
- Conversion statuses: {'passed': 50}
- Playouts: {'mate': 50}
- Handoff gaps: 0
- Route conflicts: 25

## Successor Skills

- `krk.edge_trap_close` selected 32 times
- `krk.stage7_king_tempo` selected 18 times

## Failure Motifs

- No failed post-reply or conversion motifs found.

Selected successor by outcome:
- `krk.edge_trap_close:mate`: 32
- `krk.stage7_king_tempo:mate`: 18

Visible eligible successors:
- `krk.edge_rook_transfer_recovery`: 43
- `krk.rook_transfer_after_fence`: 43
- `krk.fence_maintenance`: 37
- `krk.fence_repair`: 37
- `krk.stage0_finish`: 7
- `krk.edge_trap_close_recovery`: 6

## Semantic Alignment

Status counts:
- `reward_visible_fence_aligned_survived`: 50

Conversion by semantic alignment:
- `reward_visible_fence_aligned_survived`: {'mate': 50}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=mate`: 50

## Shadow Candidates

- No shadow candidates found.

## Recommended Next Actions

- Compare competing successor skills in route-conflict states before changing scoring or topology.
