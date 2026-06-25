#!/usr/bin/env python3
"""Run TG29s continuation evidence materialization diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import ContinuationEvidenceMaterializationConfig, run_continuation_evidence_materialization


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29s_continuation_evidence_materialization.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29s_continuation_evidence_materialization.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29s_continuation_evidence_materialization_progress.json")
    args = parser.parse_args()

    cfg = ContinuationEvidenceMaterializationConfig(
        base=ContinuationEvidenceMaterializationConfig().base.__class__(
            progress_output=args.progress_output,
        )
    )
    result = run_continuation_evidence_materialization(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "strong_continuation_positive_count",
        "partial_continuation_positive_count",
        "local_progress_only_count",
        "safe_low_progress_count",
        "misleading_positive_count",
        "continuation_label_too_broad",
        "materialized_continuation_candidate_count",
        "materialization_blocked_count",
        "targeted_episode_success_count",
        "targeted_episode_count",
        "foundation_frozen",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
