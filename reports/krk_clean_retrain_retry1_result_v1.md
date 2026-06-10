# KRK Clean Retrain Retry1 Result v1

This records the clean retry chain after the first full-run root stopped before producing the Stage 2A checkpoint.

## Decision

- status: `clean_retrain_retry1_completed_through_stage6_overlay_compose_basic_checks_passed`
- Stage 2A complete: `True`
- Stage 2B complete: `True`
- Stage 4 complete: `True`
- Stage 5 complete: `True`
- Stage 6 complete: `True`
- Stage 6 overlay composed: `True`
- Stage 7 remains quarantined: `True`
- Stage 8 remains blocked: `True`
- runtime behavior changed: `False`
- promoted by this artifact: `False`
- recommended next step: `run_dedicated_stage5_stage6_handoff_guardrail_artifacts_before_any_clean_checkpoint_promotion`

## Retry Root

```text
snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1
```

The retry root is separate from protected snapshots and from the first full-run root. No protected snapshot was overwritten.

## Stage Results

| Step | Result | Basic checks |
| --- | --- | --- |
| Stage 2A `edge_trap_close` | plateaued with best checkpoint, score `3.58228` | KRK entry `100/100`, Stage 1 backchain `100/100` |
| Stage 2B `edge_trap_enemy_between` | plateaued with best checkpoint, score `3.65102` | KRK entry `100/100`, Stage 1 backchain `100/100` |
| Stage 4 `edge_trap_wrong_tempo` | plateaued with best checkpoint, score `3.593` | KRK entry `100/100`, Stage 1 backchain `100/100` |
| Stage 5 `fence_established` | plateaued with best checkpoint, score `3.6025` | KRK entry `100/100`, Stage 1 backchain `100/100` |
| Stage 6 `drive_to_edge` | passed at cycle `9`, score `5.167125`, h40 conversion `passed` | KRK entry `100/100`, Stage 1 backchain `100/100` |
| Stage 6 overlay composition | composed fresh Stage 5 base + Stage 6 overlay | KRK entry `100/100`, Stage 1 backchain `100/100` |

Composed overlay topology:

```text
snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/topology/krk_entry_topology.json
nodes=390
edges=1088
```

## Interpretation

The clean curriculum is now executable through the current protected KRK stack in a fresh retry root. The early local stages plateau rather than conversion-pass, but they produce usable stage-best checkpoints, matching the historical adaptive pattern. Stage 6 passes the h40 handoff profile and the fresh overlay composition succeeds.

This artifact does not promote the retry checkpoint. It only establishes that the clean rebuild path can produce a fresh Stage 6 composed topology and pass basic entry/backchain checks.

## Remaining Validation Before Promotion

The following are still required before treating this retry root as a replacement for the existing protected stack:

- dedicated Stage 5 fence/handoff validation artifacts,
- dedicated Stage 6 drive/handoff validation artifacts,
- Stage 4 caveat/control comparison if the clean checkpoint is proposed as protected replacement,
- M1-M4 preservation tests,
- KPK→KQK bridge preservation tests,
- promotion/quarantine manifest review.

## Boundary

No runtime selector, score/routing change, provider suppression, topology mutation during gameplay, runtime DTM/tablebase lookup, Stage 7 promotion, or Stage 8 training was introduced.
