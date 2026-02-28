#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EXP_DIR="$ROOT_DIR/demos/experiments/kpk_curriculum_benchmark"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%d_%H%M%S)}"
RUN_DIR="$EXP_DIR/_private/recon/$RUN_ID"

TOPOLOGY="${TOPOLOGY:-topologies/kpk_legs_topology.json}"
START_STAGE="${START_STAGE:-0}"
END_STAGE="${END_STAGE:-7}"
GAMES_PER_CYCLE="${GAMES_PER_CYCLE:-100}"
CYCLES="${CYCLES:-10}"
WIN_THRESHOLD="${WIN_THRESHOLD:-0.9}"
STAGE_THRESHOLDS="${STAGE_THRESHOLDS:-}"
DISABLE_PACK_SPAWNS="${DISABLE_PACK_SPAWNS:-0}"
PERFECT_CYCLE_THRESHOLD="${PERFECT_CYCLE_THRESHOLD:-1.0}"
PERFECT_CYCLES_TO_ADVANCE="${PERFECT_CYCLES_TO_ADVANCE:-2}"
NEAR_THRESHOLD_EXTRA_MARGIN="${NEAR_THRESHOLD_EXTRA_MARGIN:-0.10}"
MAX_NEAR_THRESHOLD_EXTRA_CYCLES="${MAX_NEAR_THRESHOLD_EXTRA_CYCLES:-1}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

mkdir -p "$RUN_DIR"
cd "$ROOT_DIR"

if [[ "$TOPOLOGY" != /* ]]; then
  TOPOLOGY="$ROOT_DIR/$TOPOLOGY"
fi

echo "ReCoN curriculum run"
echo "  run_id:          $RUN_ID"
echo "  topology:        $TOPOLOGY"
echo "  stages:          $START_STAGE..$END_STAGE"
echo "  games_per_cycle: $GAMES_PER_CYCLE"
echo "  cycles:          $CYCLES"
echo "  win_threshold:   $WIN_THRESHOLD"
if [ -n "$STAGE_THRESHOLDS" ]; then
  echo "  stage_thresholds:$STAGE_THRESHOLDS"
fi
echo "  disable_packs:   $DISABLE_PACK_SPAWNS"
echo "  perfect_cycle_thr:$PERFECT_CYCLE_THRESHOLD"
echo "  perfect_cycles:  $PERFECT_CYCLES_TO_ADVANCE"
echo "  near_extra_margin:$NEAR_THRESHOLD_EXTRA_MARGIN"
echo "  near_extra_max:  $MAX_NEAR_THRESHOLD_EXTRA_CYCLES"

EXTRA_STAGE_THRESHOLD_ARGS=()
if [ -n "$STAGE_THRESHOLDS" ]; then
  EXTRA_STAGE_THRESHOLD_ARGS+=(--stage-thresholds "$STAGE_THRESHOLDS")
fi

XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache M5_DISABLE_PACK_SPAWNS="$DISABLE_PACK_SPAWNS" uv run python "$ROOT_DIR/scripts/evolution_driver.py" \
  --topology "$TOPOLOGY" \
  --stage "$START_STAGE" \
  --end-stage "$END_STAGE" \
  --games-per-cycle "$GAMES_PER_CYCLE" \
  --cycles "$CYCLES" \
  --win-threshold "$WIN_THRESHOLD" \
  --strict-stage-advance \
  --perfect-cycle-threshold "$PERFECT_CYCLE_THRESHOLD" \
  --perfect-cycles-to-advance "$PERFECT_CYCLES_TO_ADVANCE" \
  --near-threshold-extra-margin "$NEAR_THRESHOLD_EXTRA_MARGIN" \
  --max-near-threshold-extra-cycles "$MAX_NEAR_THRESHOLD_EXTRA_CYCLES" \
  "${EXTRA_STAGE_THRESHOLD_ARGS[@]}" \
  --run-name "$RUN_ID" \
  --output-dir "$RUN_DIR/reports" \
  $EXTRA_ARGS | tee "$RUN_DIR/recon_train.log"

GLOBAL_SNAP="$ROOT_DIR/snapshots/evolution/$RUN_ID"
GLOBAL_TRACE="$ROOT_DIR/traces/evolution/$RUN_ID"

if [ -d "$GLOBAL_SNAP" ]; then
  mkdir -p "$RUN_DIR/snapshots"
  cp -a "$GLOBAL_SNAP"/. "$RUN_DIR/snapshots/"
fi

if [ -d "$GLOBAL_TRACE" ]; then
  mkdir -p "$RUN_DIR/traces"
  cp -a "$GLOBAL_TRACE"/. "$RUN_DIR/traces/"
fi

GIT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
cat > "$RUN_DIR/run_manifest.json" <<EOF
{
  "run_id": "$RUN_ID",
  "topology": "$TOPOLOGY",
  "start_stage": $START_STAGE,
  "end_stage": $END_STAGE,
  "games_per_cycle": $GAMES_PER_CYCLE,
  "cycles": $CYCLES,
  "win_threshold": $WIN_THRESHOLD,
  "stage_thresholds": "$STAGE_THRESHOLDS",
  "disable_pack_spawns": $DISABLE_PACK_SPAWNS,
  "perfect_cycle_threshold": $PERFECT_CYCLE_THRESHOLD,
  "perfect_cycles_to_advance": $PERFECT_CYCLES_TO_ADVANCE,
  "near_threshold_extra_margin": $NEAR_THRESHOLD_EXTRA_MARGIN,
  "max_near_threshold_extra_cycles": $MAX_NEAR_THRESHOLD_EXTRA_CYCLES,
  "git_commit": "$GIT_COMMIT"
}
EOF

echo "Wrote $RUN_DIR/run_manifest.json"

echo "ReCoN outputs in: $RUN_DIR"
