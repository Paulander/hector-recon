# Native intrinsic KRK — resume, composition, and causal-consolidation audit

Date: 2026-07-11  
Branch: `codex/native-krk-resume-composition`  
Scope: work after the authoritative balanced R0/R1 audit on `codex/native-from-scratch-krk`.

## Executive verdict

The project is materially closer to a self-contained, self-growing ReCoN, but R1 (Mate-in-2) and KRK are not solved.

The strongest result remains the clean-slate high-resolution foundation: one root and no learned topology reaches 16/16 R0 validation plus 16/16 regression at epoch 8. The inherited 48-position R1 run remains the strongest behavioral R1 result: mature-child bootstrap reached 8/16 validation and 5/16 regression, while no-bootstrap stayed 0/16 and 0/16.

This branch adds exact R1 resume, a certified frozen-child cache, real graph-native composite circuits, outcome-native candidate mining, matched-random candidate selection, structural/equilibration/consolidation epochs, paired causal credit, and MATURE-only held-out influence.

The first structural smoke was a useful null. Four candidates were created, but all were activation-equivalent aliases of one negative rook-danger region. Across two consolidation epochs every candidate produced 0 paired helps, 0 paired hurts, and 32 neutral interventions; none matured. Full held-out was 0/16 validation and 1/16 regression versus no-bootstrap 0/16 and 0/16. This does not show that composition is useless. It shows that proposal diversity and arm attribution were inadequate.

## Standing doctrine

The central curriculum is:

1. Start from an empty learned graph.
2. Train R0 Mate-in-1 to joint 100% on disjoint high-resolution validation and regression.
3. Freeze the mature R0 child.
4. Train R1 from executed actions and mature-child successor value, never correct-move labels.
5. Let structural candidates explore during training.
6. Promote only after paired causal intervention; mask TRIAL candidates from held-out evaluation.
7. Advance only at joint 100%, with R0 retained.
8. Repeat outward so reaching a mature inner manifold supplies intrinsic successor value.

This curriculum is central. Low-resolution or orientation-unbalanced foundation pools have repeatedly produced false diagnoses.

## Inherited baseline

From `NATIVE_INTRINSIC_KRK_RUN_BRIEF_20260711.md`:

| Arm | R0 val | R0 reg | R1 val | R1 reg | R0 retained |
|---|---:|---:|---:|---:|---:|
| full intrinsic, 48 R1 train / 240 epochs | 16/16 | 16/16 | 8/16 | 5/16 | 16/16 |
| no bootstrap | same frozen R0 | same frozen R0 | 0/16 | 0/16 | 16/16 |

That established real causal value from the mature R0 child, but did not close R1. Most failures were premature checks instead of nearby quiet setup moves; the rest were wrong quiet offsets or king-approach squares.

## Implementation checkpoints

| Commit | Change |
|---|---|
| `830dc4c` | Atomic exact-fingerprint R1 snapshots, resume, predicate-safe pickle, interruption parity |
| `cd27652` | Frozen-policy child certificate and semantics-preserving dispatch cache |
| `daeeb6f` | Native stem-cell composite circuits and separate correlation/intervention lifecycle |
| `0dc48cb` | Deterministic selective outcome-native composite miner |
| `a264dca` | Opt-in structural epochs with snapshot persistence |
| `dd4bc36` | Support-matched identity-random composite controls |
| `76b8d16` | Paired intervention, consolidation, and MATURE-only held-out masking |
| `071d078` | Reproducible proposal bounds on the CLI |

The post-smoke correction deduplicates observed activation signatures and balances bounded proposals across positive affordance and negative suppressor valence.

## Snapshot and performance evidence

Snapshot parity is exact for counters, validation/regression/retention, learned graph audit, and intrinsic-credit state after interrupt/resume.

The frozen-child cache takes its first answer from the live graph, requires the exact frozen child triplet set and policy token, rechecks legality, re-executes the move in the chess world, and falls back to live formal confirmation. Held-out validation stays live-formal.

A 200-hit microbenchmark was about 399× faster (4.014 s to 0.010 s). A repeated-query full-arm test has exact semantic parity. A one-epoch real-pool run had no repeated successors and therefore correctly showed parity but no speedup (~291 s versus ~294 s).

The historical TG26 indexed scheduler remains active; this cache complements the earlier active-node/early-exit work.

## Structural-consolidation smoke

Compact artifact: `reports/autogrowth/native_from_scratch/r1_structural_consolidation_smoke_seed_20260719_compact.json`.

Configuration:

- proven R0 seed 20260719;
- R0 48/16/16 balanced across edges and corners;
- prior 40 R0 development positions and D4 orbits excluded;
- R1 engineering slice 16/16/16 balanced;
- proposal at epoch 20;
- consolidation at epochs 30 and 40;
- four candidates;
- frozen-policy child cache;
- no R0 replay;
- held-out MATURE-only.

| Arm | R1 val | R1 reg | R0 retained | Handoffs | Duration |
|---|---:|---:|---:|---:|---:|
| structural full intrinsic | 0/16 | 1/16 | 16/16 | 66 | 4,084 s |
| no bootstrap | 0/16 | 0/16 | 16/16 | 0 | 636 s |

R0 reached 16/16 plus 16/16 at epoch 8. Four composites were proposed at epoch 20. Each had seven parent triplets and the same firing signature despite different member IDs. Their generic meanings were variants of rook adjacent to the black king, rook attacked after the move, and king-to-rook distance two.

Each candidate accumulated correlation evidence but paired behavior was fully neutral:

- epoch 30: 0 help / 0 hurt / 16 neutral per candidate;
- epoch 40 cumulative: 0 help / 0 hurt / 32 neutral per candidate;
- XP stayed 50;
- state stayed TRIAL;
- mature count stayed zero.

TRIAL masking therefore worked: no merely correlated candidate entered held-out policy.

A preceding 24/8/8 R0 smoke transiently reached 8/8 validation but stayed 6/8 regression and later fell to 7/8 validation. R1 correctly did not run. This repeats the lesson that foundation resolution cannot be casually reduced.

## What this work initially missed

1. Foundation resolution was treated as a small engineering detail. It is a first-order scientific variable.
2. Continuing plasticity after mastery caused regressions; immediate joint validation/regression freeze is correct.
3. Mature-child value existed before arbitration fully consumed learned hierarchy-edge credit.
4. Old corner/orientation history was consulted too late.
5. Indexed scheduling did not remove repeated child-query cost.
6. A shared composite SCRIPT violated ReCoN’s single-parent SCRIPT law. The correct topology shares lifecycle identity but creates one SCRIPT circuit per parent.
7. Adding composite evidence to the primitive normalization denominator could cancel its effect.
8. The scheduler could exit before an attached composite settled.
9. TRIAL composites could have contaminated held-out claims; they are now masked.
10. Top-k ranking spent all slots on activation-equivalent aliases.
11. The smoke lacked a no-composite child-bootstrap arm and a materialized matched-random arm, so the 1/16 regression result cannot be attributed specifically to composition.

## What improved

- Empty-start and outcome-only boundaries are explicit and tested.
- The R0 child is frozen, scoped, formally grounded, and behavior-changing.
- Structural growth is real ReCoN topology.
- Relevance, correlation, causal intervention, XP, survival, and maturity remain separate.
- Candidates can learn during exploration but cannot affect held-out gates until causal maturity.
- Every long arm is independently resumable.
- Candidate failures now produce inspectable evidence.
- All implementation commits are pushed for external audit.

Focused suites reached 37 tests after cache work and 44–46 tests after composition/consolidation. The latest focused consolidation suite passed 46 tests in 121.45 s. Syntax compilation and `git diff --check` passed.

## Corrected proposal replay

Applying activation-signature and valence diversity to the completed snapshot yields four distinct generic regions:

- negative: check while king support is two Manhattan squares away;
- negative: rook adjacent/attacked danger;
- positive: king-support L-shape / knight-distance geometry;
- positive: reduction of a black-king escape neighbor under a generic side relation.

This is much closer to the audited chess failure—premature check versus quiet supported setup—without naming a correct move, stage, edge, corner, or mate rule to the learner. It is post-smoke diagnostic evidence only; it has not been trained or causally validated.

## Immediate next work package

1. Keep activation-signature and valence diversity.
2. Add independently resumable child-bootstrap arms from one frozen R0:
   - no composite;
   - outcome-ranked distinct composites;
   - support/population-matched random composites.
3. Checkpoint each candidate’s paired intervention separately.
4. Cache only formally invariant subqueries during intervention evaluation.
5. Run a bounded corrected smoke. Require nonzero proposal diversity, paired discordance before maturity, no TRIAL held-out influence, exact R0 retention, and ranked improvement over matched random before interpreting selectivity.
6. Only then preregister fresh high-resolution R1 train/structural-validation/validation/regression pools and multiple seeds.
7. Do not advance to R2 until fresh R1 validation and regression are both 100%.

## Mid/long-term route

After R1, expand outward through quiet fence establishment, king approach, same-side rook tempo, edge drive, and mate. Use episode trajectories and eligibility traces for multi-ply stages. Treat mature-child successor value as the intrinsic “known good state” signal. Keep rook loss and stalemate as generic high-priority veto outcomes. Alternate bounded structural, equilibration, consolidation, and promote/prune phases.

Tune depth/age/activity-dependent plasticity only through preregistered ablations. Add LAG/temporal terminals once static composition is causally useful. Use imagination/virtual frames for internal child queries and later prediction error while preserving real-world outcome grounding.

## Publication outlook

A publishable result remains plausible but unproven.

Already real:

- empty learned graph to perfect held-out R0;
- causal mature-child benefit at R1;
- persistent topology and intrinsic credit;
- graph-native autonomous candidate materialization;
- causal maturity boundary and durable experiments.

Still required:

- selective composites that improve held-out behavior over matched controls;
- 100% fresh R1 closure;
- outward multi-ply curriculum closure;
- multi-seed preregistration;
- full KRK without runtime tablebase/DTM, correct-move provider, learner-visible stage labels, or external selector shortcuts.
