#!/usr/bin/env python3
"""Review Stage 7 clean-control sampling diversity after the bounded label job."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECOVERY = Path("reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json")
RUN_REVIEW = Path("reports/structural_candidates/stage7_clean_h40_label_run_review_v0.json")
PLAN = Path("reports/structural_candidates/stage7_clean_control_collection_plan_v0.json")
OUT_JSON = Path("reports/structural_candidates/stage7_clean_control_sampling_review_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_clean_control_sampling_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    recovery = _load(RECOVERY)
    run_review = _load(RUN_REVIEW)
    _load(PLAN)
    role_counts = recovery.get("summary", {}).get("role_counts") or {}
    success_have = int(role_counts.get("clean_sequence_success_control", 0) or 0)
    negative_have = int(role_counts.get("clean_sequence_hard_negative", 0) or 0)
    success_required = int(
        recovery.get("acceptance", {}).get("clean_sequence_success_controls_required", 5) or 5
    )
    run_mates = int(run_review.get("summary", {}).get("run_mate_count", 0) or 0)
    recovered_from_run = int(run_review.get("summary", {}).get("recovered_from_run", 0) or 0)
    status = "clean_success_collection_blocked_by_sampling_overlap"
    next_step = "architecture_review_before_more_stage7_clean_labels"
    if success_have >= success_required:
        status = "clean_success_collection_requirement_met"
        next_step = "build_clean_selected_path_dataset_and_source_bias_audit"
    elif run_mates > 0 and recovered_from_run == 0:
        status = "clean_success_collection_blocked_by_sampling_overlap"
        next_step = "architecture_review_before_more_stage7_clean_labels"
    return {
        "schema_version": "stage7_clean_control_sampling_review.v0",
        "causal_status": "non_causal_sampling_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN), str(RECOVERY), str(RUN_REVIEW)],
        "summary": {
            "clean_sequence_success_controls_have": success_have,
            "clean_sequence_success_controls_required": success_required,
            "clean_sequence_hard_negatives_have": negative_have,
            "bounded_label_run_mates": run_mates,
            "bounded_label_run_novel_controls": recovered_from_run,
            "sampling_overlap_detected": run_mates > 0 and recovered_from_run == 0,
            "runtime_work_allowed": False,
        },
        "interpretation": [
            "Current replay-free clean artifacts provide enough h40 hard negatives but too few unique clean mate controls.",
            "The single bounded current-default h40 label job produced mates but no novel de-duplicated clean controls.",
            "Blindly running more Stage 7 current-default labels risks spending time on duplicate curriculum positions rather than resolving the architecture question.",
        ],
        "allowed_next_options": [
            {
                "option_id": "reviewed_diverse_clean_sampling_manifest",
                "description": "Design a new manifest with explicit disjoint source-stage/position diversity and a hard cap before any additional labels.",
                "runtime_behavior_allowed": False,
            },
            {
                "option_id": "stage7_curriculum_boundary_review",
                "description": "Stop clean-control collection and review whether box_shrink should remain a held-out boundary/challenge rather than a standalone stage.",
                "runtime_behavior_allowed": False,
            },
        ],
        "blocked_next_steps": [
            "unreviewed additional Stage 7 label runs",
            "runtime selector or arbiter changes",
            "Stage 7 repair, support adapter, score bonus, or provider penalty",
            "Stage 7 promotion",
            "Stage 8 training",
        ],
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Clean Control Sampling Review v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Non-causal review of clean Stage 7 control collection after the bounded h40 label job.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed Next Options", ""])
    for item in payload["allowed_next_options"]:
        lines.append(f"- `{item['option_id']}`: {item['description']}")
    lines.extend(["", "## Blocked Next Steps", ""])
    for item in payload["blocked_next_steps"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
