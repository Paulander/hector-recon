#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <num_games>"
  echo "Example: $0 500"
  exit 1
fi

NUM_GAMES="$1"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEMO_DIR="$ROOT_DIR/demos/experiments/endgame_handover_continuous"
WEIGHTS_DIR="$DEMO_DIR/weights_snapshot"

mkdir -p "$DEMO_DIR/_private"

echo "Training router on near-promotion KPK positions:"
echo "  games: $NUM_GAMES"
echo "  weights: $WEIGHTS_DIR"
echo

XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$ROOT_DIR/demos/persistent/full_game_train.py" \
  --batch "$NUM_GAMES" \
  --fen-file "$DEMO_DIR/data/near_promo.fens" \
  --max-moves 80 \
  --timeout-loss \
  --weights-dir "$WEIGHTS_DIR" \
  --router-mode learned_affordance \
  --router-epsilon 0.05 \
  --plasticity \
  --consolidate \
  --consolidate-pack "$DEMO_DIR/_private/fullgame_router_consol.json" \
  --output-json "$DEMO_DIR/_private/bridge_train_stats.json" \
  --trace-out "$DEMO_DIR/_private/bridge_train_trace.jsonl"

echo
echo "Wrote:"
echo "  $DEMO_DIR/_private/fullgame_router_consol.json"
echo "  $DEMO_DIR/_private/bridge_train_stats.json"
echo "  $DEMO_DIR/_private/bridge_train_trace.jsonl"

