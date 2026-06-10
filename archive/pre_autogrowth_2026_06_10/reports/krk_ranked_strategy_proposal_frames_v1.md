# KRK Ranked Strategy Proposal Frames v1

This replay-free dataset exports existing `StrategyProposalFrame` records with ranks and normalized scores. Frame labels are context only; they do not make each proposal a positive owner.

## Summary

- `row_count`: `87`
- `frame_count`: `22`
- `usable_training_row_count`: `42`
- `stage7_challenge_row_count`: `45`
- `outcome_counts`: `{'unknown': 21, 'max_plies': 52, 'mate': 14}`
- `label_counts`: `{'None': 21, 'frame_failure': 52, 'frame_success': 14}`
- `provider_family_counts`: `{'stage0_basin': 22, 'box_shrink': 3, 'fence_established': 7, 'edge_trap': 48, 'drive_to_edge': 7}`
- `source_stage_counts`: `{'stage7': 45, 'stage5': 16, 'stage6': 20, 'stage4': 6}`
- `rows_missing_provider_local_rank`: `0`
- `rows_missing_normalized_score`: `0`

## Decision

- Status: `ranked_strategy_proposal_frames_exported`
- Recommended next step: `probe_ranked_strategy_proposal_frames_v1`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
