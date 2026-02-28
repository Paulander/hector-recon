# KPK Curriculum Benchmark (PPO vs ReCoN vs Heuristic)

This experiment folder is a self-contained benchmark harness for the reviewer request:

1. PPO with curriculum training over KPK stages
2. ReCoN with curriculum training over the same stage indices
3. A simple hand-written heuristic baseline

It also preserves the exact historical paper comparison context (Stage 7 PPO-only vs ReCoN curriculum) so you can report both:
- historical apples-to-oranges baseline (as submitted),
- updated apples-to-apples curriculum benchmark.

## Historical comparison used in the paper

See `historical_comparison.md`.

Short version:
- ReCoN: 8-stage KPK curriculum (`scripts/evolution_driver.py`, stage 0..7)
- PPO: `scripts/ppo_kpk_baseline.py` trained on Stage 7 only (50k and 200k timesteps)
- Reported numbers: 97.0% (ReCoN), 26.3% (PPO-50k), 35.9% (PPO-200k)

## Folder layout

- `run_recon_curriculum.sh` - trains ReCoN curriculum and snapshots artifacts locally
- `run_ppo_curriculum.sh` - trains PPO sequentially through stage list
- `run_heuristic_baseline.sh` - evaluates a simple rule-based KPK policy
- `run_all.sh` - runs the full benchmark pipeline
- `generate_eval_sets.sh` - creates deterministic eval FEN sets
- `run_ppo_curriculum.py` - PPO curriculum training/eval implementation
- `run_heuristic_baseline.py` - heuristic eval implementation
- `kpk_stage_env.py` - stage-aware Gym environment for PPO/evaluation
- `benchmark_common.py` - shared stage/FEN/config utilities
- `summarize_results.py` - merges method outputs into one comparison table/json
- `STEM_CELL_MECHANISM.md` - concise explanation of the exact M5/stem-cell mode used here
- `_private/` - intermediate artifacts (models, traces, snapshots, logs)
- `outputs/` - benchmark summaries for presentation/reporting

## Quick start

```bash
./demos/experiments/kpk_curriculum_benchmark/run_all.sh
```

Prerequisites:
- ReCoN run: project default `uv` env
- PPO run: `stable-baselines3` + `gymnasium` installed in the same env
  - `uv pip install stable-baselines3 gymnasium`

Artifacts:
- `demos/experiments/kpk_curriculum_benchmark/outputs/latest_summary.json`
- `demos/experiments/kpk_curriculum_benchmark/outputs/latest_summary.md`

## Individual runs

Generate deterministic evaluation FENs:

```bash
./demos/experiments/kpk_curriculum_benchmark/generate_eval_sets.sh
```

Run ReCoN curriculum:

```bash
./demos/experiments/kpk_curriculum_benchmark/run_recon_curriculum.sh
```

Run PPO curriculum:

```bash
./demos/experiments/kpk_curriculum_benchmark/run_ppo_curriculum.sh
```

Run heuristic baseline:

```bash
./demos/experiments/kpk_curriculum_benchmark/run_heuristic_baseline.sh
```

Rebuild merged summary:

```bash
XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python \
  demos/experiments/kpk_curriculum_benchmark/summarize_results.py
```

## Notes

- Default stage list is `0,1,2,3,4,5,6,7` to align with the paper's 8-stage KPK curriculum framing.
- Eval sets are deterministic and shared across methods.
- ReCoN wrapper copies global `snapshots/evolution/<run_name>` and `traces/evolution/<run_name>` into this folder to keep the experiment self-contained.
- Stage progression is strict by default in wrappers:
  - ReCoN uses `--strict-stage-advance` in `evolution_driver.py`.
  - PPO wrapper enables `--strict-stage-advance` unless `STRICT_STAGE_ADVANCE=0`.
  - Both use a threshold of `0.9` by default (override via `WIN_THRESHOLD` for ReCoN and `ADVANCE_THRESHOLD` for PPO).
- PPO wrapper supports fairness controls similar to ReCoN:
  - `CYCLES_PER_STAGE`, `PERFECT_EVAL_THRESHOLD`, `PERFECT_EVALS_TO_ADVANCE`
  - `NEAR_THRESHOLD_EXTRA_MARGIN`, `MAX_NEAR_THRESHOLD_EXTRA_CYCLES`
- ReCoN wrapper supports extra controls:
  - `START_STAGE` / `END_STAGE` to run a subset (default `0..7`).
  - `DISABLE_STEM_CELLS=1` for a true no-stem ablation (no stem manager at all).
  - `DISABLE_PACK_SPAWNS=1` to disable template pack spawning (`M5_DISABLE_PACK_SPAWNS=1`).
  - `STAGE_THRESHOLDS="0-4:1.0,5-7:0.8"` (or `"0-4:100%,5-7:80%"`) for per-stage win thresholds.
  - `PERFECT_CYCLES_TO_ADVANCE=2` + `PERFECT_CYCLE_THRESHOLD=1.0` for early stage exit on repeated perfect cycles.
  - `NEAR_THRESHOLD_EXTRA_MARGIN=0.10` + `MAX_NEAR_THRESHOLD_EXTRA_CYCLES=1` for one bonus cycle when just below threshold.
