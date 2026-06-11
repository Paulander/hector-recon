#!/usr/bin/env python3
"""Run M11 KRK local suppressor checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import LocalSuppressorConfig, run_local_suppressor_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--activation-max-distance", type=float, default=1.5)
    parser.add_argument("--suppressor-max-distance", type=float, default=0.75)
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m4_candidates.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m11_local_suppressor.json"),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use smoke candidate artifact and tiny deterministic train/heldout split.",
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
        Path("reports/autogrowth/krk_autogrowth_m11_local_suppressor_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m11_local_suppressor.json")
        else args.output
    )
    result = run_local_suppressor_experiment(
        config=LocalSuppressorConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            candidate_path=str(candidate),
            horizon=int(args.horizon),
            activation_max_distance=float(args.activation_max_distance),
            suppressor_max_distance=float(args.suppressor_max_distance),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    suppressor = payload["arms"]["local_suppressor"]
    candidate_metrics = payload["arms"]["candidate_unsuppressed"]
    decision = payload["decision"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(f"candidate={payload['candidate']['candidate_key']}")
    print(
        "local_suppressor: "
        f"mates={suppressor['mates']}/{suppressor['total']} "
        f"rate={suppressor['conversion_rate']:.3f} "
        f"triggers={suppressor['suppressor_trigger_count']} "
        f"suppressed={suppressor['suppressed_sibling_action_count']} "
        f"rook_loss={suppressor['rook_losses']} "
        f"stalemate={suppressor['stalemates']} "
        f"illegal={suppressor['illegal_moves']} "
        f"horizon_no_mate={suppressor['horizon_no_mate']} "
        f"vs_candidate_rook_loss_delta={suppressor['rook_losses'] - candidate_metrics['rook_losses']} "
        f"decision={decision['status']}"
    )
    print(
        "stem_cell: "
        f"state={decision['stem_cell_state']} "
        f"survival={decision['candidate_survival_decision']} "
        f"mediated={decision['behavior_mediated_by_stem_cell_trial_structure']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
