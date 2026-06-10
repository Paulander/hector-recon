# KRK Two-Stage Abstention Runtime Go/No-Go v0

Decision: `no_go_for_scaling_or_promotion`

Allowed status: keep the default-off runtime-test code and artifacts. Do not scale, promote, or tune this selector now.

## Evidence

- Default-off equivalence passed: `reports/krk_two_stage_abstention_default_off_equivalence_v0.json`
- Protected enabled smoke passed without behavior delta: `reports/krk_two_stage_abstention_enabled_smoke_v0.json`
- Stage 7 challenge smoke did not improve target conversion: `reports/krk_two_stage_abstention_stage7_challenge_smoke_v0.json`

## Why Keep It

- Default-off behavior is equivalent on the protected Stage 5 sample.
- Enabled protected-control smoke produced no paired metric delta or shadow regression.
- Selector evidence is visible and bounded to already materialized suggestions.
- Rollback tag exists: `pre-two-stage-abstention-runtime`

## Why Not Scale It

- The selector did not select or suppress the actual chosen move in protected or Stage 7 smoke.
- Stage 7 challenge conversion stayed at `{"max_plies": 2, "mate": 1}`.
- Scaling larger validation now would mostly measure a no-op selector path.
- Raising penalties would not help when penalized suggestions are not selected.

## Recommendation

Do not scale, promote, or tune this two-stage abstention selector now. Keep it as a reversible default-off runtime-test scaffold. The next architecture class should return to strategy ownership or sequence-policy design before another runtime selector attempt.

Stage 7 remains `local_valid_composition_quarantined`; Stage 8 remains blocked.
