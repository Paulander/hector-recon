#!/usr/bin/env python3
"""Run TG26q native scheduler replay/heldout/equivalence audit."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    NativeSchedulerReplayAuditConfig,
    run_native_scheduler_replay_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26q_native_scheduler_replay_audit.json"))
    parser.add_argument("--replay-repetitions", type=int, default=50)
    parser.add_argument("--generated-mate1-heldout-count", type=int, default=12)
    parser.add_argument("--generated-mate2-heldout-count", type=int, default=6)
    parser.add_argument("--max-ticks", type=int, default=80)
    parser.add_argument("--max-samples", type=int, default=16)
    parser.add_argument("--no-symmetries", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26q_native_scheduler_replay_audit_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26q_native_scheduler_replay_audit.json")
        else args.output
    )
    config = NativeSchedulerReplayAuditConfig(
        replay_repetitions=2 if args.smoke else args.replay_repetitions,
        include_symmetries=not args.no_symmetries,
        max_ticks=args.max_ticks,
        max_samples=args.max_samples,
        generated_mate1_heldout_count=2 if args.smoke else args.generated_mate1_heldout_count,
        generated_mate2_heldout_count=1 if args.smoke else args.generated_mate2_heldout_count,
        equivalence_mate1_positions=1,
        equivalence_mate2_positions=0 if args.smoke else 1,
    )
    result = run_native_scheduler_replay_audit(config=config)
    path = result.write_json(output)
    payload = result.to_dict()
    final = payload["replay"]["final"]
    print(f"wrote {path}")
    print(
        "replay_final",
        "mate1",
        final.get("mate1_correct"),
        "/",
        final.get("mate1_total"),
        "mate2",
        final.get("mate2_conversions"),
        "/",
        final.get("mate2_total"),
        "same_graph_second_moves",
        final.get("same_graph_second_move_count"),
    )
    print(
        "generated_heldout",
        "mate1",
        payload["generated_heldout"]["mate1"]["correct_count"],
        "/",
        payload["generated_heldout"]["mate1"]["position_count"],
        "mate2",
        payload["generated_heldout"]["mate2"]["conversion_count"],
        "/",
        payload["generated_heldout"]["mate2"]["position_count"],
    )
    print("scheduler_mismatches", payload["scheduler_equivalence"]["mismatch_count"])
    print("checkpoint_pass", payload["decision"]["checkpoint_pass"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
