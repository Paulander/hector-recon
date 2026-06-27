# TG31 Child Boundary Coverage Scale and Shadow Stability

- checkpoint_pass: `True`
- interpretation: `child_boundary_coverage_scaled_shadow_online_stability_clean`
- expanded pool: `512` entries, `512` unique FENs
- split train/heldout/regression/decoy: `192` / `128` / `96` / `96`
- selected child arm: `child_boundary_plus_foundation_response`
- heldout/regression coverage: `0.171875` / `0.104167`
- worst-seed heldout coverage: `0.09375`
- decoy false handoff: `0`
- shadow child used: `True`
- long_run_short_finish_reason: `all_arms_completed_early`

Interpretation: TG31 is a shadow-only boundary coverage stability diagnostic. It does not adopt the child branch into main runtime.
