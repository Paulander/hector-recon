# KRK Strategy / Sequence Evidence Plan v0

Status: `strategy_sequence_evidence_plan_defined`

Collect enough non-causal evidence to evaluate strategy ownership and multi-step sequence policy without resuming Stage 7 local repair.

## Tracks

- `strategy_ownership`: stage7_usage=`held_out_challenge_only` targets=`{'protected_states': 12, 'max_forced_provider_labels': 36, 'min_positive_provider_families': 3, 'min_negative_provider_families': 2}`
- `sequence_policy`: stage7_usage=`evaluation_only_no_training_rows` targets=`{'clean_success_controls': 8, 'hard_negative_controls': 8, 'heldout_stage7_challenge_rows': 4}`
- `curriculum_boundary`: stage7_usage=`held_out_boundary_probe` targets=`{'phase_boundary_examples': 8, 'box_shrink_exit_examples': 4}`

## Collection Phases

- `replay_free_inventory`: Join existing ranked proposal frames, forced-provider labels, and sequence controls before any new run.
- `bounded_manifest_only`: If gaps remain, write a concrete h40 label manifest with topology/provider bindings before executing.
- `reviewed_label_execution`: Execute only after manifest review; trace failures only and keep Stage 7 out of training rows.
- `state_heldout_probe`: Probe ownership and sequence signals with state/family holdout; report source bias explicitly.

## Readiness Before Runtime

- `protected Stage 4/5/6 coverage`
- `no Stage 7 training leakage`
- `provider-family diversity across positives and negatives`
- `state-heldout performance above simple provenance/rank baselines`
- `negative suppression measured`
- `sequence-policy controls not sourced only from Stage 7 repair artifacts`
- `source-bias audit passes`
- `default-off runtime design review passes separately`

## Blocked Actions

- `runtime selector implementation`
- `Stage 7 repair or promotion`
- `Stage 8 training`
- `unreviewed label execution`
- `runtime DTM/tablebase use`
- `gameplay-time topology mutation`

Recommended next step: `run_replay_free_strategy_sequence_inventory`
