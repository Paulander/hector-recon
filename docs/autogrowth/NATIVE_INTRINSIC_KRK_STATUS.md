# Native Intrinsic KRK Status

Date: 2026-07-11

This ledger is subordinate to the central doctrine in
`KRK_INTRINSIC_CURRICULUM_LEDGER.md`: one persistent ecology, empty learned
start, outcome-only grounding, mature-child value, and 100% disjoint gates before
advancing outward.

## Current single-seed gate boundary

R0 (Mate-in-1) is the furthest rung to pass the current bounded single-seed
gate. The planned multi-seed/final certification has not been run.

- Empty learned state was audited before episode one: one generic root, zero
  learned triplets, zero trainable learned edges, zero learned weights.
- Training used content-blind round-robin legal actions and actual world
  transitions only. No mating move set or recognizer verdict entered credit.
- On the 24/8/8 run, R0 first reached joint 8/8 validation and 8/8 regression at
  epoch 40, with zero null, illegal, stalemate, or rook-loss selections.
- The mature R0 competence has terminal grounding, a positive enabled/disabled
  intervention, and deterministic clone parity.

Artifact:
`reports/autogrowth/native_from_scratch/r0_joint_freeze_24_8_8_seed_20260710.json`.

R1 (Mate-in-2) is not certified and must not advance to R2.

## R1 evidence through hierarchy-credit integration

| Run | Full intrinsic | No bootstrap | Child ablation | R0 retention |
|---|---:|---:|---:|---:|
| 24 epochs, no replay | validation 0/4; regression 1/4 | 0/4; 0/4 | 0/4; 0/4 | 5/8 full; 7/8 controls |
| 24 epochs, 8 R0 replay/epoch | validation 0/4; regression 1/4 | 0/4; 1/4 | 0/4; 1/4 | 6/8 full; 8/8 controls |
| 24 epochs, memoized mature-response replay | validation 0/4; regression 1/4 | 0/4; 0/4 | 0/4; 0/4 | 6/8 full; 8/8 controls |
| 24 epochs, frozen R0, flat root, zero replay | validation 0/4; regression 0/4 | 0/4; 0/4 | not run (redundant) | 7/8 both |
| 24 epochs, frozen R0, mature-child priority | validation 0/4; regression 0/4 | 0/4; 0/4 | not run (redundant) | 8/8 both |

| Later fixed-pool run | Full intrinsic | No bootstrap | R0 retention |
|---|---:|---:|---:|
| 120 epochs, child priority, edge credit not scored | validation 0/4; regression 0/4 | 0/4; 0/4 | 8/8 both |
| 24 epochs, hierarchy-edge score after R0 freeze | validation 0/4; regression 0/4 | 0/4; 0/4 | 8/8 both |
| 120 epochs, hierarchy-edge score after R0 freeze | validation 0/4; regression 1/4 | 0/4; 0/4 | 8/8 both |
| 240 epochs, hierarchy-edge score after R0 freeze | validation 2/4; regression 2/4 | 0/4; 0/4 | 8/8 both |
| 480 epochs, hierarchy-edge score after R0 freeze | validation 2/4; regression 4/4 | 0/4; 0/4 | 8/8 both |

The intrinsic arm produced real mature-child handoffs and changed behavior, but
did not improve heldout R1 conversion. Replay protected R0 completely in both
controls, while child-value updates still damaged two retained R0 cases. This
isolated a real integration defect: M3 depth decay existed in the competence
value engine, but native graph M3 continued rewriting consolidated shared R0
sensor weights during R1.

Freezing all R0 parameters removed the arm-specific loss but did not restore the
last retained case: both frozen arms scored 7/8. This separates parameter
forgetting from routing interference. Newly grown R1 candidates can still
compete on R0 states when every competence is flattened under one root.

Mature-child priority restored both arms to 8/8 with zero replay. The child
controls only after its own frozen subgraph selects and virtually verifies an
available move; no stage label or solution move chooses the branch.

The initial 120-epoch hierarchy run exposed a policy-consumption defect. The
full arm's R1 competence reached fast value 1.0 from 161 mature-child handoffs,
while the no-bootstrap control fell to -0.736, yet heldout moves were identical.
M3 was learning per-triplet SUB-edge credit, but native action scoring consumed
only shared terminal local weights.

Hierarchy-edge scoring is now activated only after R0 reaches joint mastery and
is frozen. Enabling it during R0 itself failed the R0 gate (6/8 validation,
7/8 regression), confirming that structural degrees of freedom must be staged.
At the R1 boundary, exact candidate-SCRIPT-to-shared-terminal edges are scored;
a regression test covers shared atoms with multiple parents.

The fixed-pool dose response is causal: 24 epochs changed value but not heldout
behavior; 120 produced one regression conversion; 240 produced 2/4 validation
and 2/4 regression; 480 produced 2/4 validation and 4/4 regression. Every
no-bootstrap control remained 0/4 and every R0 retention probe remained 8/8.
This is native outcome-grounded heldout R1 transfer, but it is not the
preregistered joint 100% gate and R1 remains uncertified.

The two stable 480-epoch validation misses are adjacent rook-placement errors:
c8c2 instead of c8c1 and b1b6 instead of b1b5. Both selected moves are premature
checks; both correct moves are quiet setup moves. A post-hoc atom audit shows
identical before-features but explicit, non-aliased gives-check and
escape-availability differences. The graph can represent the distinction; the
eight-position R1 pool did not teach sufficient selectivity.

Artifacts:

- `r0_r1_virtual_frame_smoke_seed_20260710.json`
- `r0_r1_virtual_replay24_seed_20260710.json`
- `r0_r1_cached_replay24_seed_20260711.json`
- `r0_r1_frozen24_seed_20260711.json`
- `r0_r1_hierarchical24_v2_seed_20260711.json`
- `r0_r1_hierarchical120_v2_seed_20260711.json`
- `r0_r1_edge_visible24_seed_20260711.json`
- `r0_r1_phase_edge_visible24_seed_20260711.json`
- `r0_r1_phase_edge_visible120_seed_20260711.json`
- `r0_r1_phase_edge_visible240_seed_20260711.json`
- `r0_r1_phase_edge_visible480_seed_20260711.json`

All are under `reports/autogrowth/native_from_scratch/`.

## Corrections now implemented

1. R0 replay memory stores only the mature graph's own selected experiences.
   Every replay hit is formally reconfirmed and its move is re-executed in the
   chess world. It is not a teacher move cache.
2. Existing R0 node and edge parameters can be frozen at joint mastery while
   nodes and edges grown afterward remain plastic.
3. R0 child requests during R1 are scoped to the frozen R0 triplet snapshot;
   newly grown R1 candidates cannot impersonate or perturb the child competence.
4. Frozen child dispatch memory memoizes the child graph response, but every hit
   still live-confirms the exact ReCoN branch and re-executes the virtual move.
5. Reply exposure is round-robin per training position and first action. This
   removes the prior correlation between first-move and reply scheduling.
6. The redundant third R1 control is off by default. The previous no-bootstrap
   and child-ablation implementations were behaviorally identical.
7. Every arm checkpoints independently, and a reproducible CLI now exists at
   `scripts/autogrowth/run_native_intrinsic_curriculum.py`.
8. Slow-success quorum semantics are explicit on native SCRIPT nodes
   (`k_of_n`, k=1). Legacy authored OR semantics remain unchanged; the Phase-2
   Mate-in-2 scheduler regression suite passes.
9. Per-triplet hierarchy-edge credit is consumed by action scoring only after
   R0 joint mastery and parameter freezing. Shared atoms use the exact current
   triplet SCRIPT parent, not an ambiguous first-parent lookup.

## Performance interpretation

The TG26 indexed native scheduler is already active. The earlier Phase-2 speedup
(remembered as roughly 45-70x) came from early exit plus dispatch/caching around
child continuation checks. It was only partly applicable to this runner:
training replay was still recomputing full move arbitration for every remembered
R0 example. Memoized graph response plus live branch confirmation removes that
avoidable scan. Frozen-child dispatch applies the same idea to repeated virtual
successor queries without changing their semantics.

The same-seed three-arm run fell from about 75 minutes to 24m19s (3.1x
end-to-end). Each arm's 192 replay episodes took 7.1-7.5 seconds, with zero
formal-confirmation failures and zero cached/world outcome mismatches. The full
intrinsic arm reproduced exactly; the controls changed one 1/4 regression
conversion because frozen-response replay intentionally differs from replaying a
policy that is allowed to drift during rehearsal.

The eight R1 training positions expose 16-22 legal first actions each, usually
with only one forced Mate-in-2 action. Increasing epochs alone improved transfer,
but validation plateaued at 2/4 from epoch 200 through 480. The bottleneck is now
experience diversity and quiet-setup selectivity, not raw exposure count.

## Next gates

The next bounded experiment expands the R1 training pool beyond eight positions,
with deliberate diversity in quiet setup versus premature checking contexts.
Keep the empty start, outcome-only credit, frozen R0 snapshot, child-priority
routing, disjoint validation/regression, and no-bootstrap control unchanged.
Preregister pool sizes and a fixed epoch cap before running; do not tune on the
two heldout misses. Require 100% on both fresh validation and regression, 100%
R0 retention, and a positive causal effect before certifying R1 or opening R2.

No result below joint 100% is a curriculum promotion.
