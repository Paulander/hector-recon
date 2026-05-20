#!/usr/bin/env python3
"""Close the Stage 7 clean-control collection branch with an architecture review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/structural_candidates/stage7_clean_artifact_manifest_v0.json")
RECOVERY = Path("reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json")
RUN_REVIEW = Path("reports/structural_candidates/stage7_clean_h40_label_run_review_v0.json")
SAMPLING_REVIEW = Path("reports/structural_candidates/stage7_clean_control_sampling_review_v0.json")
OUT_JSON = Path("reports/structural_candidates/stage7_clean_control_architecture_review_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_clean_control_architecture_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    manifest = _load(MANIFEST)
    recovery = _load(RECOVERY)
    run_review = _load(RUN_REVIEW)
    sampling = _load(SAMPLING_REVIEW)
    role_counts = recovery.get("summary", {}).get("role_counts") or {}
    success_have = int(role_counts.get("clean_sequence_success_control", 0) or 0)
    hard_negative_have = int(role_counts.get("clean_sequence_hard_negative", 0) or 0)
    success_required = int(recovery.get("acceptance", {}).get("clean_sequence_success_controls_required", 5) or 5)
    evidence = {
        "clean_candidate_count": manifest.get("summary", {}).get("clean_candidate_count"),
        "clean_sequence_success_controls": success_have,
        "clean_sequence_success_required": success_required,
        "clean_sequence_hard_negatives": hard_negative_have,
        "bounded_label_run_playouts": run_review.get("run", {}).get("playouts"),
        "bounded_label_run_novel_controls": run_review.get("summary", {}).get("recovered_from_run"),
        "sampling_overlap_detected": sampling.get("summary", {}).get("sampling_overlap_detected"),
    }
    success_gap_open = success_have < success_required
    sampling_overlap = bool(evidence["sampling_overlap_detected"])
    status = "stage7_clean_control_collection_paused_architecture_review_required"
    next_step = "return_to_broader_krk_strategy_or_sequence_architecture_review"
    return {
        "schema_version": "stage7_clean_control_architecture_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(RECOVERY), str(RUN_REVIEW), str(SAMPLING_REVIEW)],
        "evidence": evidence,
        "conclusions": [
            "Stage 7 clean hard negatives are available, but clean success controls remain below the minimum threshold.",
            "A bounded current-default h40 label job produced mates but no novel de-duplicated controls, indicating sampling overlap in the current curriculum slice.",
            "More unreviewed Stage 7 label runs are unlikely to be a principled next step and risk re-entering Stage 7 micro-work.",
            "Runtime selector/arbiter work remains blocked by insufficient clean Stage 7 success-control evidence and unresolved curriculum-boundary concerns.",
        ],
        "recommended_paths": [
            {
                "path_id": "broader_krk_strategy_sequence_architecture_review",
                "description": "Use Stage 7 as a held-out challenge while designing broader KRK strategy ownership / sequence-policy evidence across stages.",
                "preferred": True,
                "runtime_behavior_allowed": False,
            },
            {
                "path_id": "reviewed_diverse_stage7_sampling_manifest",
                "description": "Only if more Stage 7 data is essential, design explicit disjoint source-stage/position sampling before any further labels.",
                "preferred": False,
                "runtime_behavior_allowed": False,
            },
        ],
        "blocked_next_steps": [
            "unreviewed additional Stage 7 h40 labels",
            "Stage 7 runtime repair",
            "Stage 7 promotion",
            "Stage 8 training from unresolved Stage 7",
            "runtime selector/arbiter implementation from this evidence",
            "support bonus or provider penalty tuning",
        ],
        "decision": {
            "status": status,
            "recommended_next_step": next_step if success_gap_open or sampling_overlap else "build_clean_selected_path_dataset",
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Clean Control Architecture Review v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Non-causal closure review for the Stage 7 clean-control collection branch.",
        "",
        "## Evidence",
        "",
    ]
    for key, value in payload["evidence"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Conclusions", ""])
    for item in payload["conclusions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Paths", ""])
    for item in payload["recommended_paths"]:
        lines.append(f"- `{item['path_id']}`: {item['description']} preferred=`{item['preferred']}`")
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
