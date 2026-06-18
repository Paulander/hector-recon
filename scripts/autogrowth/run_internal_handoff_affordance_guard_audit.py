#!/usr/bin/env python3
"""Run TG26w internal handoff affordance guard audit."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    InternalHandoffAffordanceConfig,
    run_internal_handoff_affordance_guard_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26w_internal_handoff_affordance_guard_audit.json"))
    parser.add_argument("--mate1-train-count", type=int, default=12)
    parser.add_argument("--mate1-heldout-count", type=int, default=6)
    parser.add_argument("--mate2-train-count", type=int, default=6)
    parser.add_argument("--mate2-heldout-count", type=int, default=3)
    parser.add_argument("--guardless-probe-position-count", type=int, default=1)
    parser.add_argument("--max-ticks", type=int, default=30)
    parser.add_argument("--max-samples", type=int, default=24)
    parser.add_argument("--max-shared-atom-candidates-per-choice", type=int, default=3)
    parser.add_argument("--shared-atom-min-overlap", type=int, default=6)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26w_internal_handoff_affordance_guard_audit_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26w_internal_handoff_affordance_guard_audit.json")
        else args.output
    )
    cfg = InternalHandoffAffordanceConfig(
        mate1_train_count=4 if args.smoke else args.mate1_train_count,
        mate1_heldout_count=2 if args.smoke else args.mate1_heldout_count,
        mate2_train_count=1 if args.smoke else args.mate2_train_count,
        mate2_heldout_count=1 if args.smoke else args.mate2_heldout_count,
        guardless_probe_position_count=1 if args.smoke else args.guardless_probe_position_count,
        max_ticks=args.max_ticks,
        max_samples=args.max_samples,
        max_shared_atom_candidates_per_choice=2 if args.smoke else args.max_shared_atom_candidates_per_choice,
        shared_atom_min_overlap=args.shared_atom_min_overlap,
        equivalence_count=1 if args.smoke else 4,
    )
    result = run_internal_handoff_affordance_guard_audit(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "guarded_conversion_rate",
        "guardless_probe_conversion_rate",
        "internal_handoff_conversion_rate",
        "internal_handoff_first_move_success_rate",
        "internal_handoff_same_graph_second_move_count",
        "guard_used_during_runtime_choice",
        "validator_skip_used_during_internal_handoff_eval",
        "fully_evaluated_candidate_count",
        "skipped_candidate_count",
        "internal_gate_approved_candidate_count",
        "internal_gate_rejected_candidate_count",
        "false_positive_internal_gate_count",
        "false_negative_internal_gate_count",
        "materialized_mate2_quorum_confirmed_count",
        "scheduler_equivalence_mismatch_count",
        "failure_mode",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

