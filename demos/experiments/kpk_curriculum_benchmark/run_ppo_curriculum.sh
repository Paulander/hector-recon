#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EXP_DIR="$ROOT_DIR/demos/experiments/kpk_curriculum_benchmark"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%d_%H%M%S)}"
RUN_DIR="$EXP_DIR/_private/ppo/$RUN_ID"

STAGES="${STAGES:-0,1,2,3,4,5,6,7}"
TIMESTEPS="${TIMESTEPS:-50000}"
EVAL_PER_STAGE="${EVAL_PER_STAGE:-100}"
MAX_MOVES="${MAX_MOVES:-100}"
SEED="${SEED:-42}"
EVAL_SEED="${EVAL_SEED:-2026}"

mkdir -p "$RUN_DIR"

echo "PPO curriculum run"
echo "  run_id:         $RUN_ID"
echo "  stages:         $STAGES"
echo "  timesteps:      $TIMESTEPS"
echo "  eval_per_stage: $EVAL_PER_STAGE"
echo "  max_moves:      $MAX_MOVES"

XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$EXP_DIR/run_ppo_curriculum.py" \
  --stages "$STAGES" \
  --timesteps-per-stage "$TIMESTEPS" \
  --eval-per-stage "$EVAL_PER_STAGE" \
  --max-moves "$MAX_MOVES" \
  --seed "$SEED" \
  --eval-seed "$EVAL_SEED" \
  --output-dir "$RUN_DIR"

echo "Wrote $RUN_DIR/ppo_curriculum_results.json"
