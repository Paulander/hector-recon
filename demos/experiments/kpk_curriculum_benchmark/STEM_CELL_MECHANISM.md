# Stem Cell Mechanism in This Benchmark

This benchmark uses the legacy/production KPK M5 path from `scripts/evolution_driver.py`, not the newer "fully discovered actuators/subgoals" setup.

## What is fixed (predefined)

- Core KPK control skeleton is predefined in topology:
  - `kpk_detect -> kpk_execute -> kpk_finish -> kpk_wait`
  - move production is already implemented by predefined actuator logic (legs + arbiter / selector path).
- End condition and environment are predefined (KPK win by promotion/checkmate, draw/timeouts).

In other words: this setup does **not** discover the whole policy stack from scratch.

## What stem cells do here

Stem cells are used as **structural feature discoverers** and optional pack injectors:

1. **Online phase**
   - Games are played.
   - Tick/reward traces are collected.
   - Candidate patterns get XP and can transition toward TRIAL.

2. **Structural phase (M5)**
   - Spikes/high-impact moments are mined from traces.
   - Some cells are promoted/hoisted to TRIAL structures.
   - Optional template packs (AND/OR/goal packs) are injected for additional gating/feature pathways.

3. **Persistence**
   - New topology snapshot is saved per cycle and inherited by later cycles/stages.

### Optional benchmark switch

- Set `DISABLE_PACK_SPAWNS=1` in `run_recon_curriculum.sh` to disable template pack spawning while keeping the base stem-cell loop active.

## Practical interpretation

- This is best described as:
  - **fixed action machinery + learned structural auxiliaries**
  - not "pure bottom-up discovery of actuators and goals."

- That is exactly why this benchmark is useful for baseline fairness:
  - it measures sample efficiency/competence under a semi-structured ReCoN regime,
  - while PPO baseline remains a flat RL policy.

## Difference vs your newer deep experiments

Your newer line of work pushes toward:

- discovering/chaining subgoals more autonomously,
- reducing hardcoded routing/actuator priors,
- deeper recursively-grown topologies as primary control, not just augmentation.

This benchmark does **not** fully represent that newer "pure/deep" objective; it represents the earlier stage used for paper-comparable KPK performance experiments.
