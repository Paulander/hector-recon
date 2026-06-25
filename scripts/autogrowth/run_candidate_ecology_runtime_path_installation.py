#!/usr/bin/env python3
"""Run TG29u candidate ecology runtime path installation diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    CandidateEcologyRuntimePathInstallationConfig,
    run_candidate_ecology_runtime_path_installation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29u_candidate_ecology_runtime_path_installation.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29u_candidate_ecology_runtime_path_installation.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29u_candidate_ecology_runtime_path_installation_progress.json")
    args = parser.parse_args()

    cfg = CandidateEcologyRuntimePathInstallationConfig(
        base=CandidateEcologyRuntimePathInstallationConfig().base.__class__(
            progress_output=args.progress_output,
        )
    )
    result = run_candidate_ecology_runtime_path_installation(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "ecology_runtime_path_installed",
        "mature_candidate_count",
        "mature_candidate_present_in_runtime_before_count",
        "mature_candidate_selected_before_count",
        "mature_candidate_present_in_runtime_after_count",
        "mature_candidate_selected_after_count",
        "ecology_runtime_candidate_selected_count",
        "mature_candidate_selected_count",
        "credited_candidate_selected_count",
        "decaying_candidate_selected_count",
        "pruned_candidate_selected_count",
        "targeted_episode_success_count",
        "targeted_episode_count",
        "decoy_correct_rejection_count",
        "decoy_false_handoff_count",
        "foundation_frozen",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
