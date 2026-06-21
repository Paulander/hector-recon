# TG28h Controlled Mixed Frontier + Generic Edge/Fence Curriculum

TG28h trains/evaluates one frozen-foundation native graph across three trainer-side streams:

- full-config foundation-backed bridge-frontier examples from the TG28f pool;
- generic TG28a-style edge/fence positions;
- near-miss foundation-negative examples.

Stream labels remain trainer-side only. Runtime choices remain graph-mediated.

## Result

- Artifact: `reports/autogrowth/krk_autogrowth_tg28h_controlled_mixed_frontier_edge_curriculum.json`
- Checkpoint pass: `true`
- Interpretation: `mixed_curriculum_preserved_frontier_and_improved_generic_edge`
- Selected schedule: `mixed_balanced`

Foundation stayed frozen and stable:

- Mate_In_1 sanity: 1.0
- Mate_In_2 sanity: 1.0
- cache/live mismatches: 0
- foundation M3/M4 deltas during training: 0/0
- foundation M3/M4 deltas during eval: 0/0

Selected mixed schedule:

- frontier selected: 4/4
- frontier reply-envelope foundation reachable: 4/4
- frontier handoff conversions: 4
- frontier same-graph continuations: 4
- near-miss selected: 0/8
- near-miss false positives: 0
- generic selected: 8/8
- generic edge/fence success: 1.0
- generic confinement improvement: 1.0
- generic black-king mobility reduction: 0.875
- generic rook blunders: 0
- generic stalemate avoidance: 1.0

Relative to TG28g:

- frontier drop: 0
- near-miss false-positive increase: 0
- generic edge/fence success improvement: +0.875

## Schedule Comparison

- `frontier_only`: frontier 4/4, generic success 0.875, near-miss false positives 0.
- `generic_edge_only`: frontier 3/4, generic success 1.0, near-miss false positives 0.
- `mixed_balanced`: frontier 4/4, generic success 1.0, near-miss false positives 0.
- `mixed_frontier_then_edge`: frontier 4/4, generic success 1.0, near-miss false positives 0.
- `mixed_edge_then_frontier`: frontier 4/4, generic success 1.0, near-miss false positives 0.
- `mixed_with_near_miss_replay`: frontier 4/4, generic success 0.875, near-miss false positives 0.

`mixed_balanced` was selected because it preserved frontier handoff, rejected near misses, and improved generic edge/fence behavior.

## Ablations

Bounded ablations on the selected schedule show the expected dependency pattern:

- masking foundation-response terminals collapses frontier selection;
- masking bridge-pressure terminals collapses frontier selection;
- disabling reply-envelope checks collapses frontier selection;
- masking frozen Mate_In_2 foundation quorum collapses frontier selection;
- masking edge/fence terminals collapses generic edge success;
- masking action-delta, internal-attention, safety/veto, or actuator terminals collapses both selected behavior on the ablation slice.

## Interpretation

This is a controlled mixed-curriculum pass, not broad KRK competence. It shows the current graph can preserve foundation-backed bridge handoff while recovering useful generic edge/fence behavior on a bounded slice, without near-miss overgeneralization or safety regression.

Next checkpoint can run a short staged rollout:

generic edge/fence move -> bridge-frontier move -> frozen foundation continuation.
