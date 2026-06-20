# TG28g Full Frontier Validation + Near-Miss Audit

TG28g validates the TG28f full-config foundation-backed bridge-frontier runway without broadening KRK or unfreezing the TG27b foundation.

- Artifact: `reports/autogrowth/krk_autogrowth_tg28g_full_frontier_validation_near_miss.json`
- Checkpoint pass: `true`
- Interpretation: `full_frontier_validated_with_clean_near_miss_and_dependency_audit`

## Result

The TG28f full pool is intact and hash-aligned:

- pool entries: 16
- train / heldout / regression: 8 / 4 / 4
- foundation hash matches: 16/16
- cache hash matches: 16/16
- anchor overlap: 0
- mutation-lineage overlap: 0
- exact canonical overlap: 0
- geometry-bucket overlap: 0

Foundation remained frozen and stable:

- Mate_In_1 sanity: 1.0
- Mate_In_2 sanity: 1.0
- cache/live mismatches: 0
- foundation M3/M4 deltas during training: 0/0
- foundation M3/M4 deltas during eval: 0/0

Frontier heldout remains clean:

- selected moves: 4/4
- reply-envelope foundation reachable: 4/4
- foundation handoff conversions: 4
- same-graph continuations: 4
- rook blunders: 0
- stalemate avoidance: 1.0

## Dependency Audit

The TG28f residual no-reply-envelope ablation was traced to an instrumentation gap: the cache-backed candidate path did not actually disable reply-envelope queries for the `disable_reply_envelope_foundation_checks` mask.

TG28g applies the repair and reruns the arm:

- residual no-reply-envelope selections: 0
- residual classification: `none`
- bridge overreach: 0
- edge-only false positives: 0

Required ablations now collapse selected frontier behavior:

- foundation-response terminals masked: 0 selected
- bridge-pressure terminals masked: 0 selected
- reply-envelope checks disabled: 0 selected
- frozen Mate_In_2 foundation quorum masked: 0 selected
- actuator terminals masked: 0 selected

## Near-Miss And Generic Edge

Near-miss negatives:

- near-miss candidates scored: 48
- near-miss selected: 0
- false positives: 0
- rejection rate: 1.0
- failure bucket: `safe_candidates_exist_but_no_foundation_response`

Generic edge/fence regression remains separate from frontier competence:

- generic selected moves: 1/8
- generic edge/fence success rate: 0.125
- generic foundation handoff conversions: 1
- generic rook blunders: 0
- generic stalemate avoidance: 1.0

## Interpretation

TG28g validates the TG28f full foundation-backed frontier runway and removes the residual ablation caveat. It does not prove broad generic edge/fence competence. Generic edge/fence remains mostly null, which is acceptable here because the slice is a safety regression check, not the main advancement criterion.

Next checkpoint can cautiously scale the frontier pool or run a controlled mixed curriculum, but filtered frontier, unfiltered edge/fence, and boundary/near-miss metrics must remain separate.
