#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEMO_DIR="$ROOT_DIR/demos/experiments/endgame_handover_continuous"
WEIGHTS_DIR="$DEMO_DIR/weights_snapshot"

mkdir -p "$DEMO_DIR/_private"

echo "[1/2] Eval KQK (frozen weights pack):"
XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$ROOT_DIR/demos/persistent/kqk_persistent_demo.py" \
  --batch 200 \
  --consolidate \
  --consolidate-pack "$WEIGHTS_DIR/kqk_consol.json" \
  --consolidate-eta 0 \
  --consolidate-min-episodes 1000000 \
  --max-plies 150 \
  --trace-out "$DEMO_DIR/_private/kqk_eval_200.jsonl"

echo
echo "[2/2] Eval KPK (frozen weights pack; random positions):"
XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$ROOT_DIR/demos/persistent/kpk_persistent_demo.py" \
  --batch 200 \
  --consolidate \
  --consolidate-pack "$WEIGHTS_DIR/kpk_consol.json" \
  --consolidate-eta 0 \
  --consolidate-min-episodes 1000000 \
  --max-plies 120 \
  --trace-out "$DEMO_DIR/_private/kpk_eval_200.jsonl"

echo
echo "Wrote:"
echo "  $DEMO_DIR/_private/kqk_eval_200.jsonl"
echo "  $DEMO_DIR/_private/kpk_eval_200.jsonl"

