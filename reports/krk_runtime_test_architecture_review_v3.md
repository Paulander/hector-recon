# KRK Runtime-Test Architecture Review v3

This review decides what to do after the bounded runtime-test selector evidence. It is non-causal and does not authorize a runtime selector.

## Accepted Findings

- Default-off observability and reporting infrastructure is useful and safe.
- Broad additive support is not a viable scaling mechanism.
- Normalized/provenance selector objectives are not runtime-ready.
- Diverse contrast labels confirm Stage7 residual providers remain max_plies under forced ownership.
- Protected non-Stage7 training evidence is still too sparse and positive-heavy.
- The best current contrast selector has negative_suppression=0.0.

## Runtime Readiness

- Runtime selector ready: `False`
- Runtime internal terminal ready: `False`
- Runtime Stage 7 repair ready: `False`
- Reason: No candidate can suppress known negative ownership examples in leave-state-out evaluation.

## Next Options

- `A` targeted_negative_control_evidence: Collect or reconstruct protected Stage4/5/6 negative ownership labels with the same semantics as positives.
- `B` selector_objective_redesign: Redesign the selector target around abstention/risk detection before ownership selection.
- `C` pause_runtime_selector_track: Stop selector work and return to broader curriculum integration / provider-capacity planning.

## Recommended Next Class

- Status: `design_abstention_first_selector_objective`
- Rationale: The blocker is not selecting positives; it is failing to suppress negatives. Before collecting more expensive labels or implementing runtime behavior, define a selector objective that can abstain/reject unsafe ownership using non-causal protected controls.
- Implementation allowed: `design_only`
- Next artifacts: `['reports/krk_abstention_first_selector_objective_v0.json', 'reports/krk_abstention_first_selector_objective_v0.md']`

## Blocked Next Steps

`['runtime_selector', 'stage7_repair', 'stage7_promotion', 'stage8_training', 'runtime_dtm_or_tablebase', 'gameplay_topology_mutation', 'm3_m4_arbitration_update']`
