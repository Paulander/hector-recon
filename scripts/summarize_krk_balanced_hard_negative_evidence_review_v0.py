#!/usr/bin/env python3
"""Summarize balanced hard-negative evidence after two bounded label slices."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LABELS_V0 = Path("reports/krk_balanced_hard_negative_labels_v0.json")
LABELS_V1 = Path("reports/krk_balanced_hard_negative_labels_v1.json")
TARGETS_V2 = Path("reports/krk_hard_negative_selector_target_dataset_v2.json")
ABLATION_V2 = Path("reports/krk_hard_negative_selector_feature_ablation_v2.json")
OUT_JSON = Path("reports/krk_balanced_hard_negative_evidence_review_v0.json")
OUT_MD = Path("reports/krk_balanced_hard_negative_evidence_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    labels_v0 = _load(LABELS_V0)
    labels_v1 = _load(LABELS_V1)
    targets = _load(TARGETS_V2)
    ablation = _load(ABLATION_V2)
    for payload in (labels_v0, labels_v1):
        if payload.get("causal_status") != "non_causal_label_run":
            raise ValueError("label runs must remain non-causal")
    if targets.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("target dataset must remain non-causal")
    if ablation.get("causal_status") != "non_causal_feature_ablation":
        raise ValueError("ablation must remain non-causal")
    best = ablation.get("best_result") or {}
    target_summary = targets.get("summary") or {}
    label_summaries = [labels_v0.get("summary") or {}, labels_v1.get("summary") or {}]
    total_label_count = sum(int(summary.get("label_count") or 0) for summary in label_summaries)
    total_new_negatives = sum(int(summary.get("negative_capacity_count") or 0) for summary in label_summaries)
    total_new_positives = sum(int(summary.get("positive_capacity_count") or 0) for summary in label_summaries)
    status = "balanced_hard_negative_signal_promising_but_underpowered"
    recommended_next_step = "review_label_semantics_or_design_stronger_selector_features_before_more_label_jobs"
    payload = {
        "schema_version": "krk_balanced_hard_negative_evidence_review.v0",
        "causal_status": "non_causal_evidence_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(LABELS_V0), str(LABELS_V1), str(TARGETS_V2), str(ABLATION_V2)],
        "summary": {
            "new_label_count": total_label_count,
            "new_positive_capacity_count": total_new_positives,
            "new_negative_capacity_count": total_new_negatives,
            "expanded_row_count": target_summary.get("row_count"),
            "expanded_positive_context_count": (target_summary.get("target_kind_counts") or {}).get(
                "positive_capacity_context"
            ),
            "expanded_hard_negative_count": (target_summary.get("target_kind_counts") or {}).get(
                "hard_negative_capacity"
            ),
            "expanded_hard_negative_state_count": target_summary.get("hard_negative_state_count"),
            "stage7_row_count": target_summary.get("stage7_row_count"),
            "best_objective": best.get("objective"),
            "best_negative_suppression": best.get("negative_suppression"),
            "best_positive_recall": best.get("positive_recall"),
            "underpowered": (ablation.get("summary") or {}).get("underpowered"),
        },
        "interpretation": {
            "what_was_fixed": (
                "The original evidence defect was real: hard negatives expanded from five rows to nine rows, "
                "and protected rows expanded to forty without Stage 7 training rows."
            ),
            "what_remains_blocked": (
                "The label set is still hard-negative sparse and state-narrow. A simple offline rule now has "
                "nonzero suppression, but the evidence is not robust enough for selector training or runtime use."
            ),
            "why_not_more_blind_labels": (
                "The second bounded slice produced only one hard negative from twelve jobs. More blind forced-provider "
                "labels are likely inefficient unless guided by sharper semantics or candidate features."
            ),
        },
        "decision": {
            "status": status,
            "recommended_next_step": recommended_next_step,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "more_blind_label_farming_recommended": False,
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
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Balanced Hard-Negative Evidence Review v0",
        "",
        "Review after two bounded protected hard-negative label slices.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
