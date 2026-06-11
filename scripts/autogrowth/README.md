# Autogrowth Scripts

This directory is reserved for the active `KRK Autogrowth v0` implementation.

Planned scripts:

- `run_baseline.py`: evaluate protected baseline and sham-growth arms.
- `collect_traces.py`: collect train-only M4 before/action/after traces.
- `mine_triplet_candidates.py`: mine M4 trace-derived candidate records for M5 sandboxing.
- `run_growth_sandbox.py`: run one mined candidate in sandbox-only ReCoN topology.
- `run_autogrowth_experiment.py`: write the full three-arm v0 result and threshold decision.
- `run_growth_training.py`: run M8 multi-candidate lifecycle training.
- `generate_krk_positions.py`
- `evaluate_krk_competence.py`

Keep these scripts focused on executable learning/evaluation loops. Do not add review-packet writers here.
