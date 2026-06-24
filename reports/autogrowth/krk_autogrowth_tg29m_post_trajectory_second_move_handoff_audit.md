# TG29m Post-Trajectory Second-Move Handoff Audit

- checkpoint_pass: `True`
- interpretation: `second_move_handoff_repair_pass`
- repair_applied: `True`
- S1 failure before/after: `second_move_bridge_candidate_exists_but_lost_selection` / `none`
- second move before/after: `f6e6` / `d3c4`
- max2 success: `2` / `2`
- max3 success: `2` / `2`
- safety rook/illegal/stalemate: `0` / `0` / `0`
- repair ablation causal: `True`

Interpretation: TG29m audits the S1 second move after the repaired TG29l trajectory prefix. It does not broaden KRK.
