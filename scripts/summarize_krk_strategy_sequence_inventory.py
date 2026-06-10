#!/usr/bin/env python3
"""Replay-free inventory for KRK strategy ownership and sequence-policy evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_strategy_sequence_evidence_plan_v0.json")
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
CONTRAST_LABELS = Path("reports/krk_state_local_contrast_labels_v2.json")
CONTRAST_PROBE = Path("reports/krk_state_local_contrast_selector_probe_v2.json")
STAGE7_CONTROLS = Path("reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json")
STAGE7_CLEAN_REVIEW = Path("reports/structural_candidates/stage7_clean_control_architecture_review_v0.json")
OUT_JSON = Path("reports/krk_strategy_sequence_inventory_v0.json")
OUT_MD = Path("reports/krk_strategy_sequence_inventory_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_inventory() -> dict[str, Any]:
    _load(PLAN)
    frames = _load(RANKED_FRAMES)
    labels = _load(CONTRAST_LABELS)
    probe = _load(CONTRAST_PROBE)
    controls = _load(STAGE7_CONTROLS)
    clean_review = _load(STAGE7_CLEAN_REVIEW)

    frame_summary = frames.get("summary", {})
    label_summary = labels.get("summary", {})
    probe_summary = probe.get("summary", {})
    control_summary = controls.get("summary", {})
    control_acceptance = controls.get("acceptance", {})

    strategy_ready = (
        int(label_summary.get("usable_training_row_count", 0) or 0) >= 12
        and int((label_summary.get("training_contrast_label_counts") or {}).get("positive", 0) or 0) > 0
        and int((label_summary.get("training_contrast_label_counts") or {}).get("negative", 0) or 0) > 0
    )
    sequence_ready = bool(control_acceptance.get("clean_sequence_success_controls_met")) and bool(
        control_acceptance.get("clean_sequence_hard_negatives_met")
    )
    state_holdout_ready = (probe.get("decision") or {}).get("status") != "state_local_contrast_signal_not_ready"
    status = "replay_free_inventory_complete_sequence_gap_blocks_runtime"
    if strategy_ready and sequence_ready and state_holdout_ready:
        status = "replay_free_inventory_ready_for_review"
    elif not strategy_ready:
        status = "replay_free_inventory_strategy_ownership_gap"
    elif not state_holdout_ready:
        status = "replay_free_inventory_state_holdout_gap_blocks_runtime"
    elif not sequence_ready:
        status = "replay_free_inventory_sequence_policy_gap_blocks_runtime"

    return {
        "schema_version": "krk_strategy_sequence_inventory.v0",
        "causal_status": "non_causal_replay_free_inventory",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(PLAN),
            str(RANKED_FRAMES),
            str(CONTRAST_LABELS),
            str(CONTRAST_PROBE),
            str(STAGE7_CONTROLS),
            str(STAGE7_CLEAN_REVIEW),
        ],
        "strategy_ownership_inventory": {
            "ranked_frame_count": frame_summary.get("row_count"),
            "ranked_frame_training_rows": frame_summary.get("usable_training_row_count"),
            "ranked_frame_stage7_challenge_rows": frame_summary.get("stage7_challenge_row_count"),
            "state_local_contrast_rows": label_summary.get("row_count"),
            "state_local_training_rows": label_summary.get("usable_training_row_count"),
            "training_label_counts": label_summary.get("training_contrast_label_counts"),
            "provider_family_counts": label_summary.get("provider_family_counts"),
            "stage7_contrast_label_counts": label_summary.get("stage7_contrast_label_counts"),
            "state_holdout_probe_status": (probe.get("decision") or {}).get("status"),
            "ready_for_runtime_review": False,
        },
        "sequence_policy_inventory": {
            "clean_control_count": control_summary.get("control_count"),
            "role_counts": control_summary.get("role_counts"),
            "source_classification_counts": control_summary.get("source_classification_counts"),
            "success_controls_met": control_acceptance.get("clean_sequence_success_controls_met"),
            "hard_negatives_met": control_acceptance.get("clean_sequence_hard_negatives_met"),
            "stage7_clean_review_status": (clean_review.get("decision") or {}).get("status"),
            "ready_for_runtime_review": False,
        },
        "curriculum_boundary_inventory": {
            "stage7_is_held_out": True,
            "stage7_clean_control_collection_paused": True,
            "stage7_clean_review_recommendation": (clean_review.get("decision") or {}).get("recommended_next_step"),
        },
        "gap_summary": {
            "strategy_ownership_has_some_signal": strategy_ready,
            "strategy_ownership_state_holdout_ready": state_holdout_ready,
            "sequence_policy_has_clean_success_gap": not bool(
                control_acceptance.get("clean_sequence_success_controls_met")
            ),
            "sequence_policy_clean_gate_closed": sequence_ready,
            "state_holdout_gap_blocks_runtime": not state_holdout_ready,
            "runtime_work_allowed": False,
        },
        "decision": {
            "status": status,
            "recommended_next_step": (
                "review_state_holdout_signal_before_runtime_or_continue_protected_failure_contrast_gate"
                if not state_holdout_ready
                else "review_diverse_sequence_policy_controls_or_curriculum_boundary"
            ),
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy / Sequence Inventory v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Replay-free inventory of existing evidence for the split strategy-ownership and sequence-policy tracks.",
        "",
        "## Strategy Ownership",
        "",
    ]
    for key, value in payload["strategy_ownership_inventory"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Sequence Policy", ""])
    for key, value in payload["sequence_policy_inventory"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Gaps", ""])
    for key, value in payload["gap_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_inventory()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
