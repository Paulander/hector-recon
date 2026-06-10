# KRK Abstention Safe-Preservation Label Review v0

This review explains the context-feature abstention blocker as a label-semantics issue. It is design/evidence only and does not authorize runtime selector behavior.

## Summary

- `row_count`: `51`
- `label_source_distribution`: `{'forced_provider_conversion': {'safe_owner': 23, 'unsafe_owner': 5}, 'selected_playout_success': {'safe_owner': 11, 'unsafe_owner': 12}}`
- `best_context_objective`: `king_support_provider_family`
- `best_negative_suppression`: `0.8235294117647058`
- `best_safe_preservation`: `0.6470588235294118`
- `false_positive_count`: `12`
- `false_positive_forced_provider_conversion_examples`: `8`
- `false_positive_by_provider_family`: `{'edge_trap': 11, 'stage0_basin': 1}`
- `false_positive_by_label_source_kind`: `{'forced_provider_conversion': 8, 'selected_playout_success': 4}`

## Findings

- `forced_provider_conversion and selected_playout_success labels should not be treated as identical abstention targets`: False positives include known-safe forced-provider conversions, especially Stage 5 edge-trap owners. Implication: An abstention gate needs to preserve validated provider conversions even when context looks risky.
- `king-support context is useful for unsafe-owner recall but too aggressive as a one-stage rejection rule`: It reaches high negative suppression but misses safe-preservation threshold. Implication: Use it as a risk feature inside a two-stage objective, not as a runtime decision rule.
- `repair/phase monitor signatures are ambiguous`: They occur in both failed and successful protected contexts. Implication: Future labels need companion semantics: repair needed, repair possible, and repair-preserves-conversion should be separated.

## Proposed Non-Causal Objective

- Name: `two_stage_abstention_preservation_objective_v0`
- Stage 1 goal: preserve validated safe owners
- Stage 2 goal: suppress unsafe owners after preservation filter
- Required separations: `['forced_provider_conversion vs selected_playout_success', 'provider_can_convert_if_forced vs normal_selected_provider_failed', 'repair_needed_monitor vs repair_preserves_conversion', 'white_king_support_bucket risk vs validated edge_trap safe ownership']`

## Runtime Blocks

- Do not turn king-support bucket into a causal abstention terminal.
- Do not suppress edge-trap ownership from this evidence.
- Do not use monitor signatures as direct runtime rejections.

## Decision

- Status: `safe_preservation_requires_two_stage_label_semantics`
- Recommended next step: `design_or_probe_two_stage_abstention_objective_non_causal`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
