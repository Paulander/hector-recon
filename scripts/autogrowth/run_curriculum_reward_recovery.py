#!/usr/bin/env python3
"""Run TG24 KRK curriculum reward recovery checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import CurriculumRewardRecoveryConfig, run_curriculum_reward_recovery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--min-support", type=int, default=1)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--horizons", type=int, nargs="+", default=[40, 80])
    parser.add_argument("--min-sequence-credit", type=float, default=0.10)
    parser.add_argument("--activation-max-distance", type=float, default=0.5)
    parser.add_argument("--after-max-distance", type=float, default=1.5)
    parser.add_argument("--chain-max-distance", type=float, default=1.5)
    parser.add_argument("--max-chain-edges", type=int, default=64)
    parser.add_argument("--chain-request-bonus", type=float, default=0.75)
    parser.add_argument("--eta-m3", type=float, default=0.08)
    parser.add_argument("--lag-negative-threshold", type=int, default=1)
    parser.add_argument("--curriculum-probe-per-stage", type=int, default=1)
    parser.add_argument("--max-rollout-samples", type=int, default=8)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg24_curriculum_reward_recovery.json"),
    )
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    default_output = Path("reports/autogrowth/krk_autogrowth_tg24_curriculum_reward_recovery.json")
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg24_curriculum_reward_recovery_smoke.json")
        if args.smoke and args.output == default_output
        else args.output
    )
    horizons = tuple(int(item) for item in ([min(args.horizons)] if args.smoke else args.horizons))
    result = run_curriculum_reward_recovery(
        config=CurriculumRewardRecoveryConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            min_support=args.min_support,
            max_candidates=min(args.max_candidates, 4) if args.smoke else args.max_candidates,
            horizons=horizons,
            min_sequence_credit=float(args.min_sequence_credit),
            activation_max_distance=float(args.activation_max_distance),
            after_max_distance=float(args.after_max_distance),
            chain_max_distance=float(args.chain_max_distance),
            max_chain_edges=int(args.max_chain_edges),
            chain_request_bonus=float(args.chain_request_bonus),
            eta_m3=float(args.eta_m3),
            lag_negative_threshold=int(args.lag_negative_threshold),
            curriculum_probe_per_stage=min(args.curriculum_probe_per_stage, 1) if args.smoke else args.curriculum_probe_per_stage,
            max_rollout_samples=int(args.max_rollout_samples),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    primary = str(payload["decision"]["primary_horizon"])
    baseline = payload["heldout_metrics"][primary]["baseline"]
    candidate = payload["heldout_metrics"][primary]["continuation_retry_on"]
    paired = payload["heldout_metrics"][primary]["paired_deltas"]["baseline_vs_candidate_on"]
    yoked = payload["heldout_metrics"][primary]["paired_deltas"]["baseline_vs_yoked_random"]
    decision = payload["decision"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "curriculum_reward_recovery: "
        f"candidates={payload['retry_runtime']['candidate_count']} "
        f"chain_edges={payload['retry_runtime']['chain_edge_count']} "
        f"tg18_tg23_used_old_reward="
        f"{payload['audit']['current_autogrowth_tg18_tg23_use']['uses_krk_curriculum_reward_or_stage_generation']}"
    )
    print(
        f"h{primary}: "
        f"baseline_mates={baseline['mates']}/{baseline['total']} "
        f"candidate_mates={candidate['mates']}/{candidate['total']} "
        f"graded_delta={paired['graded_credit_delta_sum']} "
        f"progress_delta={paired['non_terminal_progress_delta_sum']} "
        f"yoked_graded_delta={yoked['graded_credit_delta_sum']} "
        f"rook_loss_regressions={paired['rook_loss_regression_count']} "
        f"confinement_regressions={paired['confinement_regression_count']}"
    )
    print(
        "decision: "
        f"status={decision['status']} "
        f"non_win_reward_no_longer_flat={decision['non_win_reward_no_longer_flat_in_tg24_metrics']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
