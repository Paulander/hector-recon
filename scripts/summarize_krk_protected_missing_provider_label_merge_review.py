#!/usr/bin/env python3
"""Review whether protected missing-provider labels merged into contrast rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LABELS = Path("reports/krk_protected_missing_provider_capacity_labels_v0.json")
CONTRAST = Path("reports/krk_state_local_contrast_labels_v2.json")
OUT_JSON = Path("reports/krk_protected_missing_provider_label_merge_review_v0.json")
OUT_MD = Path("reports/krk_protected_missing_provider_label_merge_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    labels_payload = _load(LABELS)
    contrast = _load(CONTRAST)
    if labels_payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("protected labels must remain non-causal")
    if contrast.get("causal_status") != "non_causal_state_local_contrast_dataset":
        raise ValueError("contrast dataset must remain non-causal")

    protected_labels = list(labels_payload.get("labels") or [])
    matched_job_ids = {
        str(row.get("source_label_job_id"))
        for row in contrast.get("rows") or []
        if str(row.get("source_label_job_id") or "").startswith("job.krk.protected_missing_provider.")
    }
    protected_job_ids = {str(label.get("job_id")) for label in protected_labels}
    unmatched = [label for label in protected_labels if str(label.get("job_id")) not in matched_job_ids]
    matched = [label for label in protected_labels if str(label.get("job_id")) in matched_job_ids]
    status = "protected_missing_provider_labels_merged"
    recommendation = "refresh_strategy_sequence_inventory_after_merge"
    if not matched and protected_labels:
        status = "protected_missing_provider_labels_unmatched_by_current_proposal_frames"
        recommendation = "review_ranked_proposal_frame_coverage_for_protected_missing_provider_states"
    elif unmatched:
        status = "protected_missing_provider_labels_partially_matched"
        recommendation = "review_unmatched_protected_label_keys_before_runtime_work"

    payload = {
        "schema_version": "krk_protected_missing_provider_label_merge_review.v0",
        "causal_status": "non_causal_merge_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(LABELS), str(CONTRAST)],
        "summary": {
            "protected_label_count": len(protected_labels),
            "matched_protected_label_count": len(matched),
            "unmatched_protected_label_count": len(unmatched),
            "matched_result_counts": dict(Counter(str(label.get("result")) for label in matched)),
            "unmatched_result_counts": dict(Counter(str(label.get("result")) for label in unmatched)),
            "unmatched_stage_counts": dict(Counter(str(label.get("source_stage")) for label in unmatched)),
            "unmatched_provider_counts": dict(Counter(str(label.get("provider_id")) for label in unmatched)),
            "stage7_label_count": sum(1 for label in protected_labels if label.get("source_stage") == "stage7"),
        },
        "unmatched_label_refs": [
            {
                "job_id": label.get("job_id"),
                "state_id": label.get("state_id"),
                "source_stage": label.get("source_stage"),
                "provider_id": label.get("provider_id"),
                "result": label.get("result"),
                "plies": label.get("plies"),
            }
            for label in unmatched
        ],
        "decision": {
            "status": status,
            "recommended_next_step": recommendation,
            "runtime_work_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_review(payload)
    return payload


def validate_review(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_label_count"] != 0:
        raise ValueError("Stage 7 labels must remain excluded")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Missing-Provider Label Merge Review v0",
        "",
        "This replay-free review checks whether the protected missing-provider labels joined to ranked proposal frames.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Unmatched Labels", ""])
    for item in payload["unmatched_label_refs"]:
        lines.append(
            f"- `{item['job_id']}` stage=`{item['source_stage']}` provider=`{item['provider_id']}` "
            f"result=`{item['result']}` plies=`{item['plies']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
