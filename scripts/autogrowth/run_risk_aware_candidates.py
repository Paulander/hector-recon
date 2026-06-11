#!/usr/bin/env python3
"""Run M13 risk-aware candidate generation plus local arbitration."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import RiskAwareCandidateConfig, run_risk_aware_candidate_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--min-support", type=int, default=3)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--min-candidate-credit", type=float, default=0.05)
    parser.add_argument("--activation-max-distance", type=float, default=1.5)
    parser.add_argument("--suppressor-max-distance", type=float, default=0.75)
    parser.add_argument("--eta-m3", type=float, default=0.08)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m13_risk_aware_candidates.json"),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use tiny deterministic train/heldout split.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = (
        Path("reports/autogrowth/krk_autogrowth_m13_risk_aware_candidates_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m13_risk_aware_candidates.json")
        else args.output
    )
    result = run_risk_aware_candidate_experiment(
        config=RiskAwareCandidateConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            min_support=args.min_support,
            max_candidates=min(args.max_candidates, 4) if args.smoke else args.max_candidates,
            horizon=int(args.horizon),
            min_candidate_credit=float(args.min_candidate_credit),
            activation_max_distance=float(args.activation_max_distance),
            suppressor_max_distance=float(args.suppressor_max_distance),
            eta_m3=float(args.eta_m3),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    arbitration = payload["local_arbitration_result"]
    metrics = arbitration.get("arms", {}).get("local_action_arbitration", {})
    decision = payload["decision"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "risk_generation: "
        f"candidates={payload['generation_summary']['candidate_count']} "
        f"actions_considered={payload['generation_summary']['total_legal_white_actions_considered']} "
        f"rejected_negative={payload['generation_summary']['rejected_negative_projection_count']}"
    )
    print(
        "local_arbitration: "
        f"mates={metrics.get('mates', 0)}/{metrics.get('total', 0)} "
        f"selected={metrics.get('action_selected_count', 0)} "
        f"rook_loss={metrics.get('rook_losses', 0)} "
        f"decision={decision['status']} "
        f"competence={decision['krk_competence_passed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
