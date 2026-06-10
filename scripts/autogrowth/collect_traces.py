#!/usr/bin/env python3
"""Collect KRK Autogrowth v0 M4 train traces for later graph mining."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import TraceCollectionConfig, collect_trace_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m4_traces.json"),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use a tiny deterministic train split for quick local validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    train_count = 20 if args.smoke else args.train_count
    horizon = 12 if args.smoke else args.horizon
    output = (
        Path("reports/autogrowth/krk_autogrowth_m4_traces_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m4_traces.json")
        else args.output
    )
    result = collect_trace_records(
        config=TraceCollectionConfig(
            seed=args.seed,
            train_count=train_count,
            horizon=horizon,
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    summary = payload["summary"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "summary: "
        f"records={summary['trace_record_count']} "
        f"train={summary['train_position_count']} "
        f"horizon={summary['horizon']} "
        f"outcomes={summary['terminal_outcomes']} "
        f"repetitions={summary['repetition_events']} "
        f"repeated_white_actions={summary['repeated_white_action_events']} "
        f"action_vitality={summary['action_vitality_rate']:.3f}"
    )
    print(
        "causal_guard: "
        f"behavior_change_applied={summary['behavior_change_applied']} "
        f"candidate_behavior_enabled={summary['candidate_behavior_enabled']} "
        f"runtime_tablebase_or_dtm_move_source={summary['runtime_tablebase_or_dtm_move_source']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
