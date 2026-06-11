#!/usr/bin/env python3
"""Run M12 KRK local ACTION arbitration checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import LocalArbitrationConfig, run_local_arbitration_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--candidate-count", type=int, default=12)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--activation-max-distance", type=float, default=1.5)
    parser.add_argument("--suppressor-max-distance", type=float, default=0.75)
    parser.add_argument("--eta-m3", type=float, default=0.08)
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m4_candidates.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m12_local_arbitration.json"),
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
        Path("reports/autogrowth/krk_autogrowth_m12_local_arbitration_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m12_local_arbitration.json")
        else args.output
    )
    result = run_local_arbitration_experiment(
        config=LocalArbitrationConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            candidate_path=str(candidate),
            candidate_count=min(args.candidate_count, 4) if args.smoke else args.candidate_count,
            horizon=int(args.horizon),
            activation_max_distance=float(args.activation_max_distance),
            suppressor_max_distance=float(args.suppressor_max_distance),
            eta_m3=float(args.eta_m3),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    metrics = payload["arms"]["local_action_arbitration"]
    selected = payload["arms"]["selected_candidate_unsuppressed"]
    decision = payload["decision"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "local_action_arbitration: "
        f"mates={metrics['mates']}/{metrics['total']} "
        f"rate={metrics['conversion_rate']:.3f} "
        f"selected={metrics['action_selected_count']} "
        f"changed_positions={metrics['action_changed_position_count']} "
        f"suppressed={metrics['suppressed_action_option_count']} "
        f"rook_loss={metrics['rook_losses']} "
        f"stalemate={metrics['stalemates']} "
        f"illegal={metrics['illegal_moves']} "
        f"vs_selected_rook_loss_delta={metrics['rook_losses'] - selected['rook_losses']} "
        f"decision={decision['status']}"
    )
    print(
        "structure: "
        f"actions={payload['local_recon_structure']['action_sibling_count']} "
        f"mediated={decision['move_choice_mediated_by_local_action_nodes']} "
        f"suppressor_active={decision['suppressor_mediated_sibling_inhibition']} "
        f"competence={decision['krk_competence_passed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
