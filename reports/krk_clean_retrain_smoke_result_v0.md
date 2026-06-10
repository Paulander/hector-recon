# KRK Clean Retrain Smoke Result v0

This records the tiny command-plumbing smoke run. It does not validate the full curriculum.

## Decision

- status: `clean_retrain_smoke_plumbing_passed_semantic_smoke_too_tiny`
- full run authorized by this artifact: `False`
- runtime selector allowed: `False`
- recommended next step: `run_full_clean_retrain_or_create_larger_semantic_smoke`

## Summary

- smoke root: `snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_smoke/stage2a_edge_trap_close_smoke`
- train command exit code: `0`
- compile command exit code: `0`
- parse command exit code: `0`
- learner written: `True`
- topology written: `True`
- topology node count: `81`
- topology edge count: `160`
- Stage 1 skipped: `True`
- command plumbing validated: `True`
- curriculum semantics validated: `False`

## Interpretation

The smoke confirms fresh output paths, training command execution, compiler execution, and topology JSON parsing. Stage 1 skipped because the smoke used only 1 Stage 0 cycle, 1 Stage 1 cycle, and 8 samples per cycle. That is acceptable for plumbing but not meaningful as a curriculum validation.

## Boundary

No runtime behavior changed. No selector, Stage 7 promotion, Stage 8 training, runtime DTM/tablebase use, or gameplay-time topology mutation was introduced.
