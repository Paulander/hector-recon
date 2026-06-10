# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 50
- No move: 0
- One-ply statuses: {'passed': 40, 'failed': 10}
- Conversion statuses: {'passed': 50}
- Playouts: {'mate': 50}
- Handoff gaps: 0
- Route conflicts: 10

## Successor Skills

- `krk.stage0_basin` selected 40 times
- `krk.edge_trap_close` selected 10 times

## Failure Motifs

- No failed post-reply or conversion motifs found.

Selected successor by outcome:
- `krk.stage0_basin:mate`: 40
- `krk.edge_trap_close:mate`: 10

Visible eligible successors:
- `krk.edge_rook_transfer_recovery`: 50
- `krk.rook_transfer_after_fence`: 50
- `krk.edge_trap_close_recovery`: 40
- `krk.fence_maintenance`: 10
- `krk.fence_repair`: 10

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
