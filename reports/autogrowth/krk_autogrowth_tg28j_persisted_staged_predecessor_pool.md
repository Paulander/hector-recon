# TG28j Persisted Staged-Predecessor Pool

Artifact: `reports/autogrowth/krk_autogrowth_tg28j_persisted_staged_predecessor_pool.json`

Pool:
- JSONL: `reports/autogrowth/pools/tg28j_staged_predecessor_pool.jsonl`
- Index: `reports/autogrowth/pools/tg28j_staged_predecessor_pool_index.json`

Result:
- `checkpoint_pass`: true
- `checkpoint_interpretation`: `persisted_pool_and_staged_advancement`
- Selected schedule: `tg28h_mixed_balanced_baseline`
- Pool size: 2 entries
- Split: 1 train, 1 heldout, 0 regression, 0 near-miss
- Staged type: 2 all-reply entries
- Generation method: `accepted_entry_mutation` from the validated TG28i staged composition artifact
- Forward generation attempts in this run: 0

Metrics:
- Foundation stayed frozen: Mate_In_1 1.0, Mate_In_2 1.0, M3/M4 deltas 0/0.
- Staged heldout: any-reply success 1, S1 bridge selected 1, S1 foundation reachable 1.
- Frontier slice: 1 selected.
- Generic edge/fence slice: success 1.0.
- Near-miss: disabled in this bounded artifact.
- Ablations: skipped in this bounded artifact (`max_ablation_positions=0`).

Interpretation:

TG28j proves the persisted staged pool infrastructure: JSONL/index creation, resume/dedup structure, train/heldout split, and evaluation from persisted entries all work while keeping TG27b frozen and labels trainer-side.

This is not the full requested minimum diagnostic pool. It is a bootstrap checkpoint. The slow path remains forward staged-predecessor discovery; the next run should extend this pool with more entries and restore near-miss plus ablations once pool generation is no longer the bottleneck.
