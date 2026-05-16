# KRK Handoff Analysis

- Sources: 1
- Total evaluated: 100
- No move: 0
- One-ply statuses: {'failed': 51, 'passed': 49}
- Conversion statuses: {'passed': 100}
- Playouts: {'mate': 100}
- Handoff gaps: 0
- Route conflicts: 0

## Successor Skills

- `krk.stage7_king_tempo` selected 73 times

## Failure Motifs

- No failed post-reply or conversion motifs found.

Selected successor by outcome:
- `krk.stage7_king_tempo:mate`: 73

Visible eligible successors:
- `krk.edge_rook_transfer_recovery`: 73
- `krk.fence_maintenance`: 73
- `krk.fence_repair`: 73
- `krk.rook_transfer_after_fence`: 73

## Semantic Alignment

Status counts:
- `reward_visible_fence_aligned_survived`: 100

Conversion by semantic alignment:
- `reward_visible_fence_aligned_survived`: {'mate': 100}

Reward/contract/reply/conversion confusion matrix:
- `reward=true|visible_fence=true|fence_survived_reply=true|conversion=mate`: 100

## Shadow Candidates

- No shadow candidates found.

## Recommended Next Actions

- No handoff bottleneck found in these diagnostics; run a larger conversion sample.
