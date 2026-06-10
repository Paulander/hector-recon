#!/usr/bin/env python3
"""Summarize selector readiness after diverse state-local contrast labels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_state_local_contrast_labels_v2.json")
PROBE = Path("reports/krk_state_local_contrast_selector_probe_v2.json")
OUT_JSON = Path("reports/krk_state_local_contrast_readiness_review_v2.json")
OUT_MD = Path("reports/krk_state_local_contrast_readiness_review_v2.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    dataset = _load_json(DATASET)
    probe = _load_json(PROBE)
    if dataset.get("causal_status") != "non_causal_state_local_contrast_dataset":
        raise ValueError("contrast dataset must remain non-causal")
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("selector probe must remain non-causal")
    summary = dataset.get("summary") or {}
    best = probe.get("best_training_result") or {}
    stage7_results = probe.get("stage7_heldout_results") or {}
    best_stage7_suppression = max(
        ((metrics or {}).get("negative_suppression") or 0.0 for metrics in stage7_results.values()),
        default=0.0,
    )
    review = {
        "schema_version": "krk_state_local_contrast_readiness_review.v2",
        "causal_status": "non_causal_readiness_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(PROBE)],
        "evidence_summary": {
            "row_count": summary.get("row_count"),
            "usable_training_row_count": summary.get("usable_training_row_count"),
            "training_state_count": summary.get("training_state_count"),
            "stage7_challenge_row_count": summary.get("stage7_challenge_row_count"),
            "training_contrast_label_counts": summary.get("training_contrast_label_counts"),
            "stage7_contrast_label_counts": summary.get("stage7_contrast_label_counts"),
            "best_training_objective": best.get("objective"),
            "best_training_accuracy": best.get("accuracy"),
            "best_training_negative_suppression": best.get("negative_suppression"),
            "best_stage7_negative_suppression": best_stage7_suppression,
            "benchmark_underpowered": probe.get("benchmark_underpowered"),
        },
        "readiness_failures": [
            "training_rows_under_40",
            "training_negative_labels_sparse",
            "leave_state_out_negative_suppression_zero",
            "stage7_heldout_negative_suppression_zero",
            "stage4_wrong_tempo_labels_deferred_due_to_runtime_cost",
        ],
        "interpretation": [
            "The diverse labels confirm Stage 7 residual providers remain max_plies under forced ownership, but those rows are correctly held out and cannot train a selector.",
            "Protected training labels remain too positive-heavy after dedupe, so simple selectors still predict positives and fail to suppress negative controls.",
            "A runtime selector would currently inherit the same failure mode as broad additive support: insufficient negative ownership evidence.",
        ],
        "decision": {
            "status": "runtime_selector_blocked_negative_suppression_zero",
            "recommended_next_step": "architecture_review_before_more_runtime_tests",
            "runtime_test_allowed_next": False,
            "allowed_next_classes": [
                "review whether more protected negative controls are worth collecting",
                "design cheaper targeted stage4 wrong-tempo label runner",
                "return to broader curriculum integration review",
            ],
            "blocked_next_steps": [
                "runtime_selector",
                "stage7_repair",
                "stage7_promotion",
                "stage8_training",
                "runtime_dtm_or_tablebase",
                "gameplay_topology_mutation",
                "m3_m4_arbitration_update",
            ],
        },
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if review.get("causal_status") != "non_causal_readiness_review":
        raise ValueError("review must remain non-causal")


def render_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Contrast Readiness Review v2",
        "",
        "This review closes the bounded diverse contrast-label slice. It is non-causal and does not authorize a runtime selector.",
        "",
        "## Evidence Summary",
        "",
    ]
    for key, value in review["evidence_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Readiness Failures", ""])
    for item in review["readiness_failures"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Interpretation", ""])
    for item in review["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{review['decision']['status']}`",
            f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{review['decision']['runtime_test_allowed_next']}`",
            f"- Blocked next steps: `{review['decision']['blocked_next_steps']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
