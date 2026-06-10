#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EXP_DIR="$ROOT_DIR/demos/experiments/kpk_curriculum_benchmark"

echo "=== KPK Curriculum Benchmark: full pipeline ==="

"$EXP_DIR/generate_eval_sets.sh"
"$EXP_DIR/run_recon_curriculum.sh"
"$EXP_DIR/run_ppo_curriculum.sh"
"$EXP_DIR/run_heuristic_baseline.sh"

XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$EXP_DIR/summarize_results.py"

echo "Done."
echo "See:"
echo "  $EXP_DIR/outputs/latest_summary.json"
echo "  $EXP_DIR/outputs/latest_summary.md"
