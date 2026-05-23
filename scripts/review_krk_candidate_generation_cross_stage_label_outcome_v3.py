#!/usr/bin/env python3
"""Review outcome of cross-stage capacity labels for candidate generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRE_PROBE = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_after_labels.json"
)
LABELS = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_labels_v3.json"
)
POST_PROBE = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_cross_stage_labels.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_label_outcome_review_v3.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_label_outcome_review_v3.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _metrics(probe: dict[str, Any]) -> dict[str, Any]:
    summary = probe.get("summary") or {}
    best = summary.get("best_non_oracle_metrics") or {}
    leave_stage = summary.get("leave_stage_out_aggregate") or {}
    return {
        "capacity_row_count": summary.get("capacity_row_count"),
        "capacity_label_counts": summary.get("capacity_label_counts"),
        "best_policy": summary.get("best_non_oracle_policy"),
        "best_positive_recall": best.get("positive_recall"),
        "best_positive_precision": best.get("positive_precision"),
        "best_negative_suppression": best.get("negative_suppression"),
        "best_balanced_recall_risk": best.get("balanced_recall_risk"),
        "leave_stage_positive_recall": leave_stage.get("positive_recall"),
        "leave_stage_negative_suppression": leave_stage.get("negative_suppression"),
        "leave_stage_balanced_recall_risk": leave_stage.get("balanced_recall_risk"),
    }


def _delta(before: dict[str, Any], after: dict[str, Any], key: str) -> float | None:
    left = before.get(key)
    right = after.get(key)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return right - left
    return None


def build_payload(
    pre_probe: dict[str, Any] | None = None,
    labels: dict[str, Any] | None = None,
    post_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pre_probe = pre_probe or _load(PRE_PROBE)
    labels = labels or _load(LABELS)
    post_probe = post_probe or _load(POST_PROBE)
    before = _metrics(pre_probe)
    after = _metrics(post_probe)
    label_summary = labels.get("summary") or {}
    in_sample_improved = bool(
        (_delta(before, after, "best_positive_recall") or 0.0) > 0
        and after.get("best_negative_suppression") == 1.0
    )
    cross_stage_improved = bool(
        (_delta(before, after, "leave_stage_balanced_recall_risk") or 0.0) > 0.05
    )
    status = (
        "cross_stage_capacity_labels_improve_in_sample_but_generalization_blocked"
        if in_sample_improved and not cross_stage_improved
        else "cross_stage_capacity_labels_inconclusive"
    )
    return {
        "schema_version": "krk_candidate_generation_cross_stage_label_outcome_review.v3",
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PRE_PROBE), str(LABELS), str(POST_PROBE)],
        "label_run": {
            "label_count": label_summary.get("label_count"),
            "result_counts": label_summary.get("result_counts"),
            "stage7_label_count": label_summary.get("stage7_label_count"),
            "stage7_training_label_count": label_summary.get("stage7_training_label_count"),
            "result_counts_by_stage_family_cell": label_summary.get(
                "result_counts_by_stage_family_cell"
            ),
        },
        "before": before,
        "after": after,
        "deltas": {
            key: _delta(before, after, key)
            for key in (
                "capacity_row_count",
                "best_positive_recall",
                "best_negative_suppression",
                "best_balanced_recall_risk",
                "leave_stage_positive_recall",
                "leave_stage_negative_suppression",
                "leave_stage_balanced_recall_risk",
            )
        },
        "interpretation": {
            "in_sample_candidate_generation_signal_improved": in_sample_improved,
            "cross_stage_generalization_improved": cross_stage_improved,
            "selector_supported": False,
            "capacity_labels_are_not_ownership_labels": True,
            "more_blind_capacity_labels_recommended": False,
            "main_blocker": (
                "stage_family_scope_and_candidate_source_coverage"
                if in_sample_improved and not cross_stage_improved
                else "insufficient_cross_stage_capacity_evidence"
            ),
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "runtime_candidate_generator_refresh_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "review_stage_conditioned_candidate_generation_scope",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Candidate-Generation Cross-Stage Label Outcome Review v3",
        "",
        "This review checks whether the targeted cross-stage capacity labels changed the candidate-generation refresh decision.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_candidate_generator_refresh_allowed: `{payload['decision']['runtime_candidate_generator_refresh_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Label Run",
        "",
        f"- label_count: {payload['label_run']['label_count']}",
        f"- result_counts: `{payload['label_run']['result_counts']}`",
        f"- stage7_label_count: {payload['label_run']['stage7_label_count']}",
        f"- stage7_training_label_count: {payload['label_run']['stage7_training_label_count']}",
        "",
        "## Before / After",
        "",
        f"- before: `{payload['before']}`",
        f"- after: `{payload['after']}`",
        f"- deltas: `{payload['deltas']}`",
        "",
        "## Interpretation",
        "",
    ]
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The labels improve candidate-generation capacity evidence only. They are not selector labels, runtime inputs, score updates, guardrails, or promotion evidence.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
