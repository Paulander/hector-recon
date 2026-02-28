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
