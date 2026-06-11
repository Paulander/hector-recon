#!/usr/bin/env python3
"""Run M8 multi-candidate KRK autogrowth training."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import GrowthTrainingConfig, train_growth_candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--candidate-count", type=int, default=8)
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--train-horizon", type=int, default=40)
    parser.add_argument("--eval-horizon", type=int, default=40)
    parser.add_argument("--activation-max-distance", type=float, default=1.5)
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m4_candidates.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m8_training.json"),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use smoke candidate artifact and tiny deterministic data.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidate = (
        Path("reports/autogrowth/krk_autogrowth_m4_candidates_smoke.json")
        if args.smoke and args.candidate == Path("reports/autogrowth/krk_autogrowth_m4_candidates.json")
        else args.candidate
    )
    output = (
        Path("reports/autogrowth/krk_autogrowth_m8_training_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m8_training.json")
        else args.output
    )
    result = train_growth_candidates(
        config=GrowthTrainingConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            candidate_path=str(candidate),
            candidate_count=min(args.candidate_count, 4) if args.smoke else args.candidate_count,
            cycles=min(args.cycles, 2) if args.smoke else args.cycles,
            train_horizon=min(args.train_horizon, 20) if args.smoke else args.train_horizon,
            eval_horizon=min(args.eval_horizon, 40) if args.smoke else args.eval_horizon,
            activation_max_distance=args.activation_max_distance,
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    summary = payload["summary"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "summary: "
        f"spawned={summary['candidate_nodes_spawned']} "
        f"mature={summary['mature_candidate_count']} "
        f"quarantined={summary['quarantined_candidate_count']} "
        f"m3_updates={summary['m3_update_count']} "
        f"heldout_candidate={summary['heldout_selected_candidate_key']} "
        f"heldout_decision={summary['heldout_decision']}"
    )
    heldout = payload["heldout"]
    if heldout.get("trained_candidate"):
        metrics = heldout["trained_candidate"]
        safety = heldout["safety"]
        print(
            "heldout: "
            f"mates={metrics['mates']}/{metrics['total']} "
            f"activations={metrics['candidate_activated_position_count']} "
            f"changed={metrics['candidate_behavior_changed_position_count']} "
            f"rook_loss={metrics['rook_losses']} "
            f"blunder_regressions={safety['blunder_regression_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
