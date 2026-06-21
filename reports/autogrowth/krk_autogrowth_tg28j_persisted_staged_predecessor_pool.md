# TG28j Persisted Staged-Predecessor Pool

Artifact: `reports/autogrowth/krk_autogrowth_tg28j_persisted_staged_predecessor_pool.json`

Pool:
- JSONL: `reports/autogrowth/pools/tg28j_staged_predecessor_pool.jsonl`
- Index: `reports/autogrowth/pools/tg28j_staged_predecessor_pool_index.json`

Current result:
- `checkpoint_pass`: true
- `checkpoint_interpretation`: `persisted_pool_and_staged_advancement`
- Selected schedule: `tg28h_mixed_balanced_baseline`
- Pool size: 8 entries
- Split: 4 train, 2 heldout, 2 regression, 0 near-miss
- Staged type: 8 all-reply entries
- Generation method: deterministic `accepted_entry_mutation` from the validated TG28i staged composition artifact plus legal symmetry mutations
- Forward generation attempts in this run: 0

Metrics:
- Foundation stayed frozen: Mate_In_1 1.0, Mate_In_2 1.0, M3/M4 deltas 0/0.
- Staged heldout: any-reply success 2, S1 bridge selected 2, S1 foundation reachable 2.
- Frontier slice: 1 selected.
- Generic edge/fence slice: success 1.0.
- Near-miss: disabled in this bounded artifact.
- Ablations: skipped in this bounded artifact (`max_ablation_positions=0`).

Interpretation:

TG28j proves the persisted staged pool infrastructure: JSONL/index creation, resume/dedup structure, train/heldout/regression split, deterministic accepted-entry mutation, and evaluation from persisted entries all work while keeping TG27b frozen and labels trainer-side.

This is still not the full requested minimum diagnostic pool because near-miss is absent and ablations are skipped. The slow path remains forward staged-predecessor discovery; the next run should add persisted staged near-misses and restore ablations before claiming scale.
