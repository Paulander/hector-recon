# KRK Selector Behavior Continuation Regression Root Cause v0

This report is diagnostic-only. It does not change production behavior or unquarantine selector_behavior.

## Minimal Reproduction

- row_id: `joined_trace_ownership_4`
- state_id: `state.2c1d6da27ea1`
- fen: `5k2/R7/8/8/8/8/4K3/8 w - - 2 2`
- active_landmark_label: `fence_established`
- rng_seed: `40`
- black_policy: `adversarial`
- max_plies: `40`
- max_ticks: `200`
- suggestion_limit: `10`
- early_stop_stable_suggestions: `2`
- command: `uv run python scripts/diagnose_krk_selector_behavior_continuation_regression_v0.py`

## Observed vs Expected

- expected_control_result: `{'result': 'mate', 'plies': 17, 'basis': 'protected validation default-off h40 outcome'}`
- control_result: `{'result': 'mate', 'plies': 17, 'engine_decision_count': 9}`
- selector_observability_only_result: `{'result': 'mate', 'plies': 17, 'engine_decision_count': 9}`
- selector_behavior_enabled_result: `{'result': 'max_plies', 'plies': 40, 'engine_decision_count': 20}`
- selector_behavior_enabled_no_cache_result: `{'result': 'max_plies', 'plies': 40, 'engine_decision_count': 20}`
- expected_behavior: `Selector behavior remains quarantined. If enabled diagnostically, it should not turn a protected safe-control mate into max_plies.`
- observed_behavior: `The first protected-row decision is preserve/no-op, but a later h40 continuation state triggers switch_to_visible_alternative and the playout enters a non-mating rook/king loop.`

## First Divergence

- ply: `4`
- differing_fields: `['move', 'selected_provider', 'resulting_fen']`
- control: `e8a8 / krk.fence_established`
- enabled: `e8b8 / krk.edge_trap_close`
- behavior_action: `switch_to_visible_alternative`
- replacement: `krk.edge_trap_close / e8b8`

## Root Cause

- summary: The regression is caused by a deterministic later h40 continuation switch, not by the protected row's first selector decision. Enabling selector_behavior activates recommendation application at every white decision in play_to_mate. At ply 4 it applies a prefer_visible_alternative recommendation and replaces the ranked fence-established move e8a8 with edge_trap_close move e8b8. That legal switch loses the mating continuation and creates a loop.
- suspected_invariant_violation: Visible positive-capacity alternatives are being treated as sufficient to override a safe ranked continuation move during h40, even when the row is a protected safe-preservation control and no runtime-visible outcome proof supports the override.
- why_not_first_row_switch: At ply 0 the behavior action is no_op with recommendation preserve_selected_owner. The first move remains a7a8 in both runs. The first behavior switch appears at white ply 4.

## Affected Code Paths

- safe/control behavior: `['scripts/test_krk_landmark_progress.py::play_to_mate', 'scripts/test_krk_landmark_progress.py::choose_move_details', 'ranked selected_suggestion is used directly']` - control_default_off selects e8a8 via krk.fence_established at ply 4 and mates in 17 plies
- selector observability only: `['play_to_mate', 'choose_move_details', '_krk_selector_objective_recommendation_for_observation', 'recommendation recorded but not applied']` - selector_observability_only records prefer_visible_alternative at ply 4 but still selects e8a8 and mates in 17
- selector_behavior enabled behavior: `['play_to_mate', 'choose_move_details', '_krk_selector_objective_recommendation_for_observation', '_krk_selector_behavior_sandbox_choice', 'replacement_suggestion becomes selected_suggestion']` - selector_behavior_enabled_cached switches e8a8/krk.fence_established to e8b8/krk.edge_trap_close at ply 4

## Hypotheses

- continuation-state mutation: `against_hidden_mutation_for_move_induced_state_change`; for: The enabled path changes the legal move at ply 4, so subsequent positions differ by normal chess state transition.; against: No topology mutation, DTM/tablebase lookup, illegal move, or out-of-band board mutation is observed; the divergence follows the selected legal replacement move.
- selector arbitration state leaking across rows: `unlikely`; for: No positive evidence.; against: The minimal reproduction uses a single row with a fresh graph and engine per variant, and no-cache behavior reproduces the same max_plies regression.
- h40-specific heuristic interaction: `primary_cause`; for: The first-row decision is preserve/no-op. The failing switch is only encountered during h40 continuation at ply 4, where near-edge medium-box/far-support terms recommend a visible alternative.; against: The recommendation is deterministic and not limited to h40 code, but h40 is the first validation path that exposes the downstream effect of later continuation switches.
- candidate ordering instability: `unlikely`; for: The behavior selector uses current suggestion order to choose the first visible alternative not equal to the original selection.; against: The suggestion order is stable across control and enabled traces. The selected replacement is deterministic: original e8a8 entries are skipped, then the first e8b8 edge_trap_close entry is chosen.
- unsafe fallback behavior: `contributing_invariant_gap`; for: The switch logic has no continuation safety check and no fallback to the ranked selected move when the visible alternative has lower score/progress evidence in the current state.; against: The switch is bounded to an already-visible suggestion; it does not create candidates or route directly.
- cache/reuse contamination: `unlikely`; for: No positive evidence.; against: selector_behavior_enabled_cached and selector_behavior_enabled_no_cache both choose e8b8 at ply 4 and both hit max_plies.
- another invariant violation: `safe_continuation_preservation_invariant_missing`; for: A protected safe-control h40 playout permits a later prefer_visible_alternative switch from a safe fence-established choice to an edge-trap alternative using capacity evidence rather than ownership/outcome evidence.; against: The diagnostic confirms capacity labels were not treated as ownership labels; the issue is insufficient causal evidence for safe continuation switching, not a label field mix-up.

## Recommended Fix Plan

- Keep selector_behavior quarantined.
- Add continuation-level selector behavior trace capture for every h40 white decision.
- Create a separate diagnostic-only shadow veto that records when a switch would override a safe ranked continuation move; do not change production behavior.
- Review runtime-visible safe-continuation proxies before any veto implementation; do not use offline ownership labels or capacity labels as ownership.
- Require protected h40 validation to show zero safe-control regressions and positive target improvements before any future unquarantine review.
- If a fix is later proposed, gate it behind an explicit non-production diagnostic flag first and prove default-off equivalence.

## Risks Of Fixing

- A broad safe-preservation veto may erase the two observed target improvements.
- Using offline row classes or capacity labels at runtime would violate label semantics.
- A term-specific veto based only on this row may overfit and miss other continuation regressions.
- Adding h40 outcome checks to runtime would violate the no runtime DTM/tablebase/outcome-probe constraint.

## Tests Required Before Unquarantine

- current selector behavior regression audit tests
- current protected selector behavior sandbox validation tests
- new continuation root-cause diagnostic tests
- protected h40 validation with full continuation selector decision trace
- default-off equivalence
- zero score/routing/topology/DTM deltas
- zero Stage7 promotion and zero Stage8/selector training rows
- full repository test suite
