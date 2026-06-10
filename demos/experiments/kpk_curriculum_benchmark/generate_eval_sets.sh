#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EXP_DIR="$ROOT_DIR/demos/experiments/kpk_curriculum_benchmark"

STAGES="${STAGES:-0,1,2,3,4,5,6,7}"
PER_STAGE="${PER_STAGE:-100}"
SEED="${SEED:-2026}"

echo "Generating eval FEN sets"
echo "  stages:    $STAGES"
echo "  per-stage: $PER_STAGE"
echo "  seed:      $SEED"

XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$EXP_DIR/generate_eval_sets.py" \
  --stages "$STAGES" \
  --per-stage "$PER_STAGE" \
  --seed "$SEED"
