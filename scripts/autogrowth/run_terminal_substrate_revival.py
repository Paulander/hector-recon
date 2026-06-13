#!/usr/bin/env python3
"""Run TG26h FeatureHub / terminal substrate revival checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import TerminalSubstrateConfig, run_terminal_substrate_revival


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260612)
    parser.add_argument("--mate1-train-count", type=int, default=300)
    parser.add_argument("--mate1-heldout-count", type=int, default=100)
    parser.add_argument("--mate1-mirror-count", type=int, default=40)
    parser.add_argument("--mate2-train-count", type=int, default=300)
    parser.add_argument("--mate2-heldout-count", type=int, default=100)
    parser.add_argument("--disable-mate2", action="store_true")
    parser.add_argument("--max-generation-attempts", type=int, default=500_000)
    parser.add_argument("--eta-m3", type=float, default=0.10)
    parser.add_argument("--rich-feature-credit-scale", type=float, default=0.25)
    parser.add_argument("--mate1-pass-threshold", type=float, default=0.95)
    parser.add_argument("--mate2-pass-threshold", type=float, default=0.80)
    parser.add_argument("--max-samples", type=int, default=12)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg26h_terminal_substrate_revival.json"),
    )
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    default_output = Path("reports/autogrowth/krk_autogrowth_tg26h_terminal_substrate_revival.json")
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26h_terminal_substrate_revival_smoke.json")
        if args.smoke and args.output == default_output
        else args.output
    )
    result = run_terminal_substrate_revival(
        config=TerminalSubstrateConfig(
            seed=args.seed,
            mate1_train_count=60 if args.smoke else args.mate1_train_count,
            mate1_heldout_count=24 if args.smoke else args.mate1_heldout_count,
            mate1_mirror_count=16 if args.smoke else args.mate1_mirror_count,
            mate2_train_count=12 if args.smoke else args.mate2_train_count,
            mate2_heldout_count=6 if args.smoke else args.mate2_heldout_count,
            mate2_enabled=not args.disable_mate2,
            max_generation_attempts=min(args.max_generation_attempts, 80_000)
            if args.smoke
            else args.max_generation_attempts,
            eta_m3=args.eta_m3,
            rich_feature_credit_scale=args.rich_feature_credit_scale,
            mate1_pass_threshold=args.mate1_pass_threshold,
            mate2_pass_threshold=args.mate2_pass_threshold,
            max_samples=args.max_samples,
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    terminal = payload["terminal_native"]
    decision = payload["decision"]
    mate1 = terminal["mate1"]["heldout"]
    mate2 = terminal["mate2"]
    print(f"wrote {path}")
    print(
        "terminal mate1: "
        f"accuracy={mate1['accuracy']:.3f} "
        f"correct={mate1['correct_count']}/{mate1['position_count']} "
        f"activation={mate1['candidate_activation_rate']:.3f} "
        f"wrong_suppression={mate1['wrong_action_suppression_rate']:.3f} "
        f"m3_updates={terminal['mate1']['m3_update_count']} "
        f"m4={terminal['mate1']['m4_consolidation_event_count']}"
    )
    if mate2.get("enabled"):
        heldout = mate2["heldout"]
        print(
            "terminal mate2: "
            f"first_success={heldout['first_move_success_rate']:.3f} "
            f"conversion={heldout['conversion_rate']:.3f} "
            f"reply_coverage={heldout['forced_mate_reply_coverage']:.3f} "
            f"m4={mate2['m4_consolidation_event_count']}"
        )
    else:
        print(f"terminal mate2: skipped reason={mate2['reason']}")
    print(
        "decision: "
        f"status={decision['status']} "
        f"terminal_ready_edge_fence={decision['terminal_native_ready_for_edge_fence_rerun']} "
        f"action_ranker={decision['action_ranker_claim_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
