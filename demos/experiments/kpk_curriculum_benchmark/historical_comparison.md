# Historical Paper Comparison (Exact Setup)

This is the comparison reported in the submitted AAAI paper version.

## ReCoN side

- Script family: `scripts/evolution_driver.py`
- Curriculum: KPK stage `0..7` (8-stage curriculum)
- Typical settings in paper text:
  - 10 cycles per stage
  - 100 games per cycle
  - total 8,000 games
- Structural maturation (stem cells/TRIAL) enabled in those runs.

## PPO side

- Script: `scripts/ppo_kpk_baseline.py`
- PPO trained on **Stage 7 only** (`--stage 7`), not sequential curriculum stages.
- Reported budgets:
  - 50k timesteps
  - 200k timesteps

## Reported results (paper)

- ReCoN: 97.0%
- PPO (50k): 26.3%
- PPO (200k): 35.9%

## Important caveat

This is not a strict apples-to-apples comparison because PPO was not curriculum-trained in the historical setup. The scripts in this folder provide a stricter curriculum-vs-curriculum benchmark.
