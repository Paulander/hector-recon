# Stage 7 Clean h40 Label Manifest v0

Status: `bounded_clean_h40_label_manifest_ready`

Bounded non-causal label manifest to fill clean Stage 7 sequence-control gaps. This is a data-labeling job only; it does not enable any runtime repair.

## Current Gap

- clean_sequence_success_controls_have: `2`
- clean_sequence_success_controls_required: `5`
- clean_sequence_success_controls_gap: `3`
- clean_sequence_hard_negatives_have: `8`

## Job

- job_id: `stage7.clean_h40.seed17.samples10.v0`
- samples: `10`
- horizon: `40`
- seed: `17`
- output: `reports/structural_candidates/stage7_clean_h40_label_run_seed17_10_h40.json`

Command:

```bash
uv run python scripts/test_krk_landmark_progress.py --topology snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json --label box_shrink --samples 10 --seed 17 --playout-max-plies 40 --composition-profile handoff_composition_v1 --enable-diagnostic-caches --early-stop-stable-suggestions 2 --json-output reports/structural_candidates/stage7_clean_h40_label_run_seed17_10_h40.json --no-json-stdout
```

Forbidden flags:

- `--enable-stage7-king-tempo`
- `--enable-stage7-drive-repair`
- `--enable-stage7-post-king-tempo`
- `--enable-stage7-post-box-continuation`
- `--enable-stage7-learned-post-box-continuation`
- `--enable-stage7-post-box-frozen-model-candidate`
- `--enable-stage7-plan-capsule`
- `--enable-candidate-move-layer`
- `--enable-stage7-king-support-fence-stabilizer`
- `--enable-krk-strategy-arbiter-sandbox`
- `--enable-krk-two-stage-abstention-selector`

Next step: `run_single_bounded_clean_h40_label_job`
