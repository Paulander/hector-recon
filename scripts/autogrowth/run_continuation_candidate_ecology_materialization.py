#!/usr/bin/env python3
"""Run TG29t continuation candidate ecology materialization diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ContinuationCandidateEcologyMaterializationConfig,
    run_continuation_candidate_ecology_materialization,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29t_continuation_candidate_ecology_materialization.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29t_continuation_candidate_ecology_materialization.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29t_continuation_candidate_ecology_materialization_progress.json")
    parser.add_argument("--cycles", type=int, default=25)
    args = parser.parse_args()

    cfg = ContinuationCandidateEcologyMaterializationConfig(
        base=ContinuationCandidateEcologyMaterializationConfig().base.__class__(
            progress_output=args.progress_output,
        ),
        ecology_cycle_count=args.cycles,
    )
    result = run_continuation_candidate_ecology_materialization(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "spawned_candidate_count",
        "safe_candidate_count",
        "candidate_credit_event_count",
        "candidate_debt_event_count",
        "candidate_decay_event_count",
        "candidate_credited_count",
        "candidate_mature_count",
        "candidate_decaying_count",
        "candidate_pruned_count",
        "targeted_episode_success_count",
        "targeted_episode_count",
        "decoy_correct_rejection_count",
        "decoy_false_handoff_count",
        "foundation_frozen",
        "trainer_side_exploration_used_in_final_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
