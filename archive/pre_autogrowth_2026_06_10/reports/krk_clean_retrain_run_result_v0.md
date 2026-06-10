# KRK Clean Retrain Run Result v0

This records the approved full clean retrain attempt after the tiny smoke passed. It is a run-result artifact, not a promotion artifact.

## Decision

- status: `clean_retrain_full_run_incomplete_stage2a_no_promotable_checkpoint`
- full clean retrain complete: `False`
- Stage 2A complete: `False`
- Stage 2B/4/5/6 started: `False`
- Stage 6 overlay composed: `False`
- Stage 7 remains quarantined: `True`
- Stage 8 remains blocked: `True`
- runtime behavior changed: `False`
- recommended next step: `inspect_stage2a_training_stop_then_retry_stage2a_in_a_fresh_retry_root_or_fix_training_stop_condition`

## What Ran

The Stage 2A command from `reports/krk_clean_retrain_execution_manifest_v0.json` was launched under:

```text
snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline
```

The process wrote Stage 0, Stage 1, and Stage 2 edge-trap-close snapshots, then stopped before writing the required final or stage-best edge-trap-close checkpoint.

## Observed Outputs

- topology snapshot files: `40`
- Stage 0 mate-in-1 snapshots: `20`
- Stage 1 backchain snapshots: `10`
- Stage 2 edge-trap-close snapshots: `10`
- best-by-stage files written: `mate_in_1.pkl`, `stage0_basin.pkl`
- adaptive eval artifacts written for: `mate_in_1/cycle_0019`, `stage0_basin/cycle_0009`, `edge_trap_close/cycle_0009`

Missing required outputs:

- `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline/final_learner.pkl`
- `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/baseline/best_by_stage/edge_trap_close.pkl`
- `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0/stage2a_edge_trap_close/topology/krk_entry_topology.json`

## Partial Eval Summary

- `mate_in_1`: passed at cycle `19`, `100/100` mate found.
- `stage0_basin`: passed at cycle `9`, `100/100` improved and `100/100` optimal.
- `edge_trap_close`: adaptive eval learner/topology artifacts were written at cycle `9`, but the curriculum history did not record a completed stage-best checkpoint and no `edge_trap_close.pkl` was written.

## Interpretation

The clean retrain path is executable through early curriculum stages, and the smoke already confirmed command plumbing and topology compilation. The full run did not produce a promotable Stage 2A checkpoint, so the correct stop is before Stage 2B and later stages.

This is not a Stage 7 result and not a runtime-control result. It does not change protected Stage 5/6 snapshots and does not authorize any promotion.

## Boundary

No runtime behavior changed. No selector, score change, provider suppression, topology mutation, runtime DTM/tablebase lookup, Stage 7 promotion, or Stage 8 training was introduced.

Next retry should use a fresh retry root or first inspect/fix the Stage 2A training stop condition. Do not overwrite existing protected snapshots.
