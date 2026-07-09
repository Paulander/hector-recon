# Phase 3.21 Summary

Artifact: `reports/autogrowth/clean_slate_krk/phase3_21_addend_control_confirmed_audit/summary.json`

- Constructed conditional-gate move-flip proof passed.
- Two-arm guarded confirmation: Arm G confirmed 0/1/0/0/0; Arm L confirmed 1/0/0/0/0.
- Predicate-evaluation guard failures: 1264 dose-arm tests; most prior-looking confirmations are void, not inert or confirmed.
- Valid G-confirmed cell: seed20272932 `white_king_to_rook_after=2 AND white_rook_to_black_king_after=4`.
- Gate mechanism: `action_pattern_eligibility` over the same two action atoms.
- Validation: Arm G +2 wins at all doses; Arm L 0 at all doses for that cell.
- Heldout: cell is harmful, controlled ablation delta -6; run stops on `stage_b_mature_cell_gate_regression_vs_flat:20272932`.
- Addend-control reading: one Arm L nominee confirmed in seed20272931, so 3.19's empirical addend-inertness claim is retired as guard-confounded.
- Cross-rung survivors: 0.
- Recurring confirmed families: 0.
- Seed33 instability: not reproduced; final population stable with TRIAL 15, PROBATION 15, MATURE 0, PRUNED 786.
- Seed33 full fate log: `seed_20272933_population_unstable_fate_log.json`.
- Main interpretation: conditional gates can affect decisions, but current confirmation is mostly off-habitat and the one guarded mature gate is not heldout-safe.
