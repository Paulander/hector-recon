#!/usr/bin/env python3
"""Review the KRK normalized selector objective probe before runtime tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBJECTIVE_PLAN = Path("reports/krk_normalized_strategy_selector_objective_v1.json")
PROBE = Path("reports/krk_normalized_strategy_selector_objective_probe_v1.json")
OUT_JSON = Path("reports/krk_normalized_selector_probe_review_v1.json")
OUT_MD = Path("reports/krk_normalized_selector_probe_review_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    plan = _load_json(OBJECTIVE_PLAN)
    probe = _load_json(PROBE)

    if plan.get("decision", {}).get("status") != "normalized_selector_objective_design_ready_for_offline_probe":
        raise ValueError("objective plan must be finalized")
    if probe.get("decision", {}).get("status") != "normalized_objective_probe_underpowered_fields_available":
        raise ValueError("probe must complete with fields available but underpowered")

    best = probe.get("best_results") or {}
    provenance_best = best.get("provenance") or {}
    baseline = (
        probe.get("results", {})
        .get("provenance_leave_one_out", {})
        .get("family_maturity", {})
        .get("accuracy")
    )
    normalized = provenance_best.get("accuracy")
    improvement = (
        normalized - baseline
        if isinstance(normalized, (int, float)) and isinstance(baseline, (int, float))
        else None
    )

    review = {
        "schema_version": "krk_normalized_selector_probe_review.v1",
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OBJECTIVE_PLAN), str(PROBE)],
        "probe_summary": {
            "status": probe.get("decision", {}).get("status"),
            "benchmark_underpowered": probe.get("benchmark_underpowered"),
            "normalized_fields_available": probe.get("normalized_fields_available"),
            "stage7_training_leakage": probe.get("interpretation", {}).get("stage7_training_leakage"),
            "best_provenance_objective": provenance_best.get("objective"),
            "best_provenance_accuracy": normalized,
            "family_maturity_baseline_accuracy": baseline,
            "normalized_over_baseline_delta": improvement,
        },
        "interpretation": {
            "positive_signal": (
                "family_rank_score_bucket improved over the family/maturity provenance baseline "
                "on existing provenance rows"
            ),
            "readiness_blocker": (
                "dataset is still small, balanced rows lack rank/score fields, and Stage7 is held out"
            ),
            "runtime_conclusion": "not_runtime_ready",
        },
        "minimum_next_evidence": [
            "export ranked StrategyProposalFrame rows for balanced/protected controls",
            "keep selected/forced/same-move label channels separate",
            "include provider_local_rank and normalized_score in every new labeled row",
            "keep Stage7 residual rows held out as challenge/evaluation only",
            "rerun normalized objective probe before any runtime test",
        ],
        "decision": {
            "status": "normalized_selector_signal_promising_more_ranked_frames_required",
            "recommended_next_step": "build_ranked_strategy_proposal_frame_dataset_v1",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "blocked_next_steps": [
            "runtime_selector",
            "higher_additive_support_playout",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if review.get("decision", {}).get("runtime_test_allowed_next") is not False:
        raise ValueError("runtime tests remain blocked")


def render_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# KRK Normalized Selector Probe Review v1",
        "",
        "This review gates the normalized selector objective before any further runtime test.",
        "",
        "## Probe Summary",
        "",
    ]
    for key, value in review["probe_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for key, value in review["interpretation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Minimum Next Evidence", ""])
    for item in review["minimum_next_evidence"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{review['decision']['status']}`",
            f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{review['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{review['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{review['decision']['stage8_training_allowed']}`",
            "",
            "## Blocked Next Steps",
            "",
        ]
    )
    for item in review["blocked_next_steps"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
