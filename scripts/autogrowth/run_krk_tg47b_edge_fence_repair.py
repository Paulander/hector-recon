#!/usr/bin/env python3
"""Run TG47b clean edge/fence repair diagnostic."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import CleanEdgeFenceStageConfig, run_clean_edge_fence_stage


DEFAULT_OUTPUT_DIR = "reports/autogrowth/clean_slate_krk/tg47b_edge_fence_repair"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-extension", action="store_true", help="required guard; create a clean child extension")
    parser.add_argument("--seed", type=int, default=20260629)
    parser.add_argument("--edge-fence-train-count", type=int, default=900)
    parser.add_argument("--edge-fence-heldout-count", type=int, default=300)
    parser.add_argument("--edge-fence-regression-count", type=int, default=180)
    parser.add_argument("--decoy-count", type=int, default=180)
    parser.add_argument("--hard-decoy-count", type=int, default=180)
    parser.add_argument("--stage-play-episode-count", type=int, default=120)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-scale-label", default=None)
    args = parser.parse_args()
    if not args.fresh_extension:
        raise SystemExit("TG47b requires --fresh-extension")

    output_dir = args.output_dir
    config = CleanEdgeFenceStageConfig(
        checkpoint_name="TG47b_edge_fence_repair",
        schema_version="krk_tg47b_edge_fence_repair.v0",
        progress_schema_version="krk_tg47b_edge_fence_repair_progress.v0",
        run_scale_label=args.run_scale_label or _run_scale_label(args),
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg47b_edge_fence_repair.json",
        progress_path=f"{output_dir}/krk_tg47b_edge_fence_repair_progress.json",
        markdown_path=f"{output_dir}/krk_tg47b_edge_fence_repair.md",
        train_trace_path=f"{output_dir}/pools/tg47b_train_traces.jsonl.gz",
        eval_trace_path=f"{output_dir}/pools/tg47b_eval_traces.jsonl.gz",
        failure_pool_path=f"{output_dir}/pools/tg47b_failure_pool.jsonl.gz",
        online_trace_path=f"{output_dir}/pools/tg47b_online_episodes.jsonl.gz",
        m4_audit_log_path=f"{output_dir}/pools/tg47b_m4_audit.jsonl.gz",
        graph_summary_path=f"{output_dir}/pools/tg47b_graph_summary.json",
        promoted_edge_fence_artifact_path=f"{output_dir}/promoted_tg47b_edge_fence.json",
        seed=args.seed,
        edge_fence_train_count=args.edge_fence_train_count,
        edge_fence_heldout_count=args.edge_fence_heldout_count,
        edge_fence_regression_count=args.edge_fence_regression_count,
        decoy_count=args.decoy_count,
        hard_decoy_count=args.hard_decoy_count,
        stage_play_episode_count=args.stage_play_episode_count,
        fresh_extension=True,
    )
    result = run_clean_edge_fence_stage(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


def _run_scale_label(args: argparse.Namespace) -> str:
    defaults = {
        "edge_fence_train_count": 900,
        "edge_fence_heldout_count": 300,
        "edge_fence_regression_count": 180,
        "decoy_count": 180,
        "hard_decoy_count": 180,
        "stage_play_episode_count": 120,
    }
    for key, default in defaults.items():
        if getattr(args, key) < default:
            return "smoke"
    return "configured"


if __name__ == "__main__":
    main()
