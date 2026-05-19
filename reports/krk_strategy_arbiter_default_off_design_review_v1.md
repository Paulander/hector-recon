# KRK Strategy Arbiter Default-Off Design Review v1

This is a design-review artifact only. It does not implement a runtime arbiter or selector sandbox.

## Readiness v3 Summary

- Passed checks: `['proposal_family_diversity', 'conversion_positive_provider_diversity', 'label_balance', 'protected_stage_coverage', 'stage7_heldout_boundary']`
- Diagnostic-only checks: `['current_selected_provider_diversity']`
- Hard blockers: `[]`

## Future Sandbox Contract

- Sandbox id: `sandbox.krk.strategy_arbiter_v1`
- Default enabled: `False`

Allowed inputs:
- `StrategyProposalFrame records`
- `provider provenance and maturity metadata`
- `visible terminal-space context terms`
- `InternalTerminalSpec-derived non-causal monitor evidence only if promoted to visible runtime evidence in a future review`
- `plan-capsule observation metadata only as trace evidence`

Forbidden inputs:
- `runtime DTM/tablebase lookup`
- `state hash exceptions`
- `hidden Python controller state`
- `unpromoted StructuralCandidate as causal input`
- `unpromoted InternalTerminalSpec as causal input`
- `unpromoted PlanCapsuleSpec as causal input`

Required default-off tests before runtime code:
- `baseline vs flag-present-default-off selected first move equivalence`
- `selected provider equivalence`
- `local one-ply result equivalence`
- `conversion result equivalence on protected smoke`
- `shadow candidate equivalence where available`
- `no no-move/illegal/draw regression`
- `no observation metadata emitted when disabled`

## Open Risks

- `selected_provider_stage0_dominance` status=`diagnostic_only_pre_sandbox_promotion_risk`: Current selected-provider diversity remains poor; v3 treats this as the failure mode to test, not as a design-review blocker.
- `stage7_overfit` status=`must_hold_out`: Stage7 rows remain challenge cases and must not become training rows for a selector.
- `forced_vs_selected_label_semantics` status=`must_keep_separate`: Forced conversion labels can justify candidate ownership contrast, but they are not the same as selected-playout success labels.

## Decision

- Status: `default_off_strategy_arbiter_design_ready_for_external_review`
- Recommended next step: `external_architecture_review_before_runtime_sandbox`
- Runtime arbiter implementation remains blocked.
- Selector sandbox implementation remains blocked.
