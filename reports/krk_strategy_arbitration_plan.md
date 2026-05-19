# KRK Strategy Arbitration / Plan Selection Plan

## Purpose

Stage 7 `box_shrink` is paused as a local repair target.

The current evidence does not justify another Stage 7 runtime patch. Stage 7 remains:

```text
local_valid_composition_quarantined
```

The next architecture step is to move up one level:

```text
from fixing one local stage
to learning when each KRK strategy should own the position
```

The goal is to build a general KRK strategy arbitration / plan-selection layer that can learn from shared terminal-space context when to prefer:

- `stage0_basin`
- `edge_trap_close`
- `edge_trap_enemy_between`
- `edge_trap_wrong_tempo`
- `fence_established`
- `drive_to_edge`
- `box_shrink`
- plan capsule / post-box continuation
- future edge-net / king-support continuation

This is not a new runtime policy yet. It is an architecture and diagnostic plan.

## Motivation

The Stage 7 work revealed that local success is not enough.

`box_shrink` can be locally useful while still failing conversion. Near strategic boundaries, especially near the edge, `box_shrink` may stop being the right owner. The system may need to hand off to:

- fence / cut preservation
- edge-net pressure
- king support
- drive repair
- mate-basin finish
- plan capsule continuation

The curriculum created useful local providers. The missing layer may be:

```text
learned provider/strategy arbitration over shared terminal-space features
```

rather than another local `box_shrink` patch.

## Hard Invariants

The plan must preserve:

- No hidden Python controller.
- No runtime DTM/tablebase policy.
- No gameplay-time topology mutation.
- No Stage 7 promotion.
- No Stage 8 training from unresolved Stage 7.
- No broad Stage 7 support bonus / provider penalty / `stage0` suppression.
- No direct unsafe role-SCRIPT -> provider SUB edge.

The following remain non-causal evidence unless explicitly promoted into visible topology:

- `HandoffPacket`
- `SkillContractStats`
- `ShadowStemCandidate`
- `StructuralCandidate`
- `GrowthGovernor`
- provider-promotion events
- `PlanCapsuleSpec`

M1-M4 plasticity/consolidation semantics must remain intact.

Validated Stage 5/6 providers remain protected.

## Current Stage 7 Role

Stage 7 residuals become a challenge set, not the sole optimization target.

Stage 7 should be used to test whether a broader KRK strategy arbiter can correctly handle difficult post-box / near-edge / handoff-boundary cases.

The challenge set should include:

- 0926-like candidate-move family
- 069-like drive/fence arbitration families
- 2cc-like continuation families
- Plan Capsule owned-arbitration residuals
- `box_shrink` reward/contract mismatch cases
- known `stage0_basin` fallback failures

These should not be patched one-by-one unless a broader strategy-arbitration mechanism explains them.

## Core Concept

A strategy arbiter receives:

- terminal-space context
- provider proposals
- role/capsule context
- move-shape and post-move evidence
- history / recent handoff state

and predicts or supports:

```text
which strategy/provider/plan should own the next decision
```

It should not rely on raw provider scores being comparable across skills.

## StrategyProposalFrame

Introduce or formalize a non-causal record:

```text
StrategyProposalFrame
```

Fields:

- `schema_version`
- `state_id`
- `fen`
- `active_landmark_label`
- `provider_id`
- `skill_id`
- `provider_version`
- `move_uci`
- `raw_score`
- `provider_local_rank`
- `normalized_score`
- `source_terms`
- `role_licenses`
- `plan_capsule_context`
- `move_shape_terms`
- `post_move_terms`
- `safety_terms`
- `known_outcome_label`
- `shadow/failure labels`
- `causal_status = non_causal`

This is an evidence record, not a runtime controller.

## Terminal-Space Features

The dataset should record at least:

- `black_king_edge_distance`
- `black_king_edge_bucket`
- `box_area`
- `box_area_delta_possible`
- `box_area_relevance`
- `rook_safe`
- `fence_exists`
- `fence_stable`
- `cut_stable`
- `white_king_support_available`
- `white_king_can_improve_support`
- `enemy_king_mobility`
- `mate_in_one_available`
- `mate_basin_readiness`
- `edge_net_pressure_proxy`
- `corner_net_pressure_proxy`
- `stalemate_or_draw_risk`
- `plan_capsule_active`
- `recent_handoff_context`

Some terms may initially be proxies.

Important candidate terms:

- `box_area_relevance`
- `box_shrink_exit_condition`
- `edge_net_affordance`
- `king_support_conversion_affordance`
- `phase_boundary_near_edge`

These should be diagnostic first.

## Dataset v0

Build a non-causal dataset from existing artifacts first.

Include:

- Stage 5 successful fence/handoff states
- Stage 6 successful `drive_to_edge` states
- Stage 7 successful cases
- Stage 7 residual/failure families
- Stage 4 wrong-tempo debt cases if useful
- KPK->KQK bridge examples only as cross-domain sanity, not KRK arbiter training

Use existing labels where possible:

- conversion result
- forced-provider result
- candidate-move result
- legal-first result
- DTM diagnostic result
- shadow/failure class
- handoff/capsule state

Add new h40 labels only for small missing cells.

## Dataset v0 Performance Rules

- Small and stratified first.
- Use h40 as practical horizon.
- Use h80+ only for classification, not promotion.
- No exhaustive legal-first sweeps by default.
- Cap provider suggestions per state.
- Use diagnostic caches.
- Use parallel workers when available.
- Use thin traces.
- If a run projects to hours, stop and report missing evidence.

## Arbiter Tracks

### Track A - Visible Heuristic Arbiter

A non-causal baseline using explicit terms:

- edge distance
- box relevance
- fence/cut state
- king support
- mate-basin readiness
- draw/stalemate risk

Goal:

```text
Can simple visible terms explain when box_shrink should yield?
```

No runtime behavior.

### Track B - Provider-Ranking Arbiter

A learned non-causal ranking model over `StrategyProposalFrame` records.

Possible targets:

- conversion-positive provider
- provider that leads to handoff success
- provider that avoids shadow candidates
- provider that avoids stagnation/max_plies

Goal:

```text
Can the arbiter predict better provider ownership than raw global scores?
```

No runtime behavior initially.

### Track C - Plan-Selection Arbiter

A non-causal model that chooses between:

- single provider ownership
- bounded Plan Capsule commitment
- handoff to existing validated provider
- exit/abort of plan

Goal:

```text
Can plan commitment be selected only when it helps?
```

No runtime behavior initially.

### Track D - Curriculum Boundary Audit

Treat `box_shrink` as:

```text
local evidence + handoff trigger
```

rather than a standalone promoted stage.

Goal:

```text
Determine whether Stage 7 is a bad independent curriculum boundary.
```

Output may recommend:

```text
box_shrink remains local sensor/skill
but not promoted as independent owner
```

## Evaluation Questions

The first non-causal evaluation should answer:

1. Does raw provider score fail because provider scores are not comparable?
2. Does provider-local rank help?
3. Do visible terms predict when each provider should own?
4. Does `box_area_relevance` fall near the edge?
5. Do edge-net / king-support / fence terms dominate near the edge?
6. Are Stage 7 residuals better described as phase-boundary failures than box-shrink failures?
7. Are missing visible terms the main blocker?
8. Is the current training objective insufficient even with good features?
9. Should `box_shrink` be demoted to handoff evidence rather than promoted stage?

## Outputs For First Implementation Slice

Create:

```text
reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json
reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.json
reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.md
```

Optional:

```text
scripts/build_krk_strategy_arbitration_dataset.py
scripts/probe_krk_strategy_arbitration.py
tests/test_krk_strategy_arbitration_dataset.py
```

No runtime behavior changes.

## Decision Gate After Dataset v0

The probe should emit one of:

- `strategy_arbitration_promising`
- `missing_feature_first`
- `curriculum_boundary_likely`
- `continuation_capacity_dominant`
- `training_objective_dominant`
- `inconclusive_need_more_stratified_data`

Each status should recommend the next diagnostic class, not a causal patch.

## Future Sandbox Criteria

Only after offline evidence is strong, a sandbox arbiter may be considered.

A sandbox arbiter must be:

- default-off
- domain/profile scoped
- traceable
- visible-term justified
- guardrail validated
- unable to use DTM/tablebase at runtime
- unable to mutate topology during gameplay

Guardrails:

- Stage 6 `drive_to_edge`
- Stage 5 fence
- Stage 4 wrong-tempo debt with paired controls
- Stage 1 / KRK entry if cheap
- M1-M4 preservation
- KPK->KQK bridge sanity if relevant

## Relationship To Plasticity / Consolidation

The strategy arbiter should eventually connect to M3/M4:

```text
M3:
  temporary provider-arbitration adaptation

M4:
  slow consolidation of stable arbitration preferences

M5:
  structural promotion only after sandbox + guardrails
```

This plan does not alter M3/M4 now.

## Relationship To Structural Growth

This is a growth-governor-compatible path.

It avoids adding endless Stage 7 patches by moving from:

```text
local repair
```

to:

```text
strategy ownership learning
```

Stage 7 residuals remain useful as challenge cases.

## Stop Conditions

Stop and ask for review if:

- the probe becomes a runtime arbiter
- the probe starts changing defaults
- the probe uses DTM/tablebase at runtime
- the probe mutates topology during gameplay
- the probe requires hidden controller logic
- the probe cannot cite visible source terms
- the run becomes too slow
- the dataset is too Stage-7-only to generalize

## Recommended Next Step

Implement only the non-causal dataset/probe v0.

Do not implement a runtime arbiter.

Do not resume Stage 7 repair.

Do not train Stage 8.
