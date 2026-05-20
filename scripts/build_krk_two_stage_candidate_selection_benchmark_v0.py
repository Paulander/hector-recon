#!/usr/bin/env python3
"""Build the non-causal KRK two-stage candidate/selection benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_two_stage_candidate_selection_benchmark_plan_v0.json")
CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
SELECTOR_PROBE = Path("reports/krk_state_local_contrast_selector_probe_v2.json")
OUT_JSON = Path("reports/krk_two_stage_candidate_selection_benchmark_v0.json")
OUT_MD = Path("reports/krk_two_stage_candidate_selection_benchmark_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def build_benchmark() -> dict[str, Any]:
    plan = _load(PLAN)
    capacity = _load(CAPACITY_FRAMES)
    selector_probe = _load(SELECTOR_PROBE)
    if plan.get("causal_status") != "non_causal_benchmark_plan":
        raise ValueError("benchmark plan must remain non-causal")
    if capacity.get("causal_status") != "non_causal_capacity_frame_dataset":
        raise ValueError("capacity frames must remain non-causal")
    if selector_probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("selector probe must remain non-causal")

    rows = list(capacity.get("rows") or [])
    positive = [row for row in rows if row.get("capacity_label") == "positive_capacity"]
    negative = [row for row in rows if row.get("capacity_label") == "negative_capacity"]
    current_positive_recalled = [row for row in positive if row.get("has_runtime_proposal_frame")]
    current_negative_included = [row for row in negative if row.get("has_runtime_proposal_frame")]
    expanded_positive_recalled = positive
    expanded_negative_included = negative
    best = selector_probe.get("best_training_result") or {}
    selector_summary = selector_probe.get("summary") or {}
    best_negative_suppression = best.get("negative_suppression")
    best_accuracy = best.get("accuracy")
    selector_ready = (
        (selector_probe.get("decision") or {}).get("status") != "state_local_contrast_signal_not_ready"
        and best_negative_suppression is not None
        and best_negative_suppression >= 0.7
    )

    status = "two_stage_benchmark_inconclusive"
    recommendation = "review_two_stage_benchmark"
    if positive and len(current_positive_recalled) == 0 and len(expanded_positive_recalled) == len(positive):
        status = "candidate_generation_recall_improves_selection_not_ready"
        recommendation = "improve_selector_label_balance_or_candidate_scoring_non_causal"
    if selector_ready:
        status = "two_stage_benchmark_selector_review_ready"
        recommendation = "review_for_default_off_sandbox_eligibility"

    payload = {
        "schema_version": "krk_two_stage_candidate_selection_benchmark.v0",
        "causal_status": "non_causal_benchmark",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN), str(CAPACITY_FRAMES), str(SELECTOR_PROBE)],
        "candidate_generation_track": {
            "current_runtime_proposal_frames": {
                "positive_capacity_recall_count": len(current_positive_recalled),
                "positive_capacity_total": len(positive),
                "positive_capacity_recall_rate": _rate(len(current_positive_recalled), len(positive)),
                "negative_capacity_inclusion_count": len(current_negative_included),
                "negative_capacity_total": len(negative),
                "negative_capacity_inclusion_rate": _rate(len(current_negative_included), len(negative)),
            },
            "validated_provider_candidate_set_expansion": {
                "positive_capacity_recall_count": len(expanded_positive_recalled),
                "positive_capacity_total": len(positive),
                "positive_capacity_recall_rate": _rate(len(expanded_positive_recalled), len(positive)),
                "negative_capacity_inclusion_count": len(expanded_negative_included),
                "negative_capacity_total": len(negative),
                "negative_capacity_inclusion_rate": _rate(len(expanded_negative_included), len(negative)),
            },
        },
        "strategy_selection_track": {
            "source_probe_status": (selector_probe.get("decision") or {}).get("status"),
            "training_row_count": selector_summary.get("training_row_count"),
            "training_state_count": selector_summary.get("training_state_count"),
            "training_label_counts": selector_summary.get("training_label_counts"),
            "stage7_eval_row_count": selector_summary.get("stage7_eval_row_count"),
            "stage7_training_leakage": selector_summary.get("stage7_training_leakage"),
            "best_objective": best.get("objective"),
            "best_accuracy": best_accuracy,
            "best_positive_precision": best.get("positive_precision"),
            "best_positive_recall": best.get("positive_recall"),
            "best_negative_suppression": best_negative_suppression,
            "selector_ready": selector_ready,
        },
        "interpretation": {
            "candidate_generation": "Validated-provider expansion fixes recall for known protected positive-capacity providers.",
            "selection": "Existing selector evidence is not ready because negative suppression remains poor/underpowered.",
            "combined": "Runtime work remains blocked until candidate generation and selection both pass non-causal benchmarks.",
        },
        "decision": {
            "status": status,
            "recommended_next_step": recommendation,
            "runtime_work_allowed": False,
            "candidate_generator_runtime_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_benchmark(payload)
    return payload


def validate_benchmark(payload: dict[str, Any]) -> None:
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
    if payload["strategy_selection_track"]["stage7_training_leakage"] is not False:
        raise ValueError("Stage 7 rows must not leak into training")
    if payload["decision"]["candidate_generator_runtime_allowed"] is not False:
        raise ValueError("runtime candidate generation remains blocked")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Two-Stage Candidate / Selection Benchmark v0",
        "",
        "This non-causal benchmark separates candidate-generation recall from selector suppression.",
        "",
        "## Candidate Generation",
        "",
    ]
    for name, metrics in payload["candidate_generation_track"].items():
        lines.append(f"- `{name}`: `{metrics}`")
    lines.extend(["", "## Strategy Selection", ""])
    for key, value in payload["strategy_selection_track"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_benchmark()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
