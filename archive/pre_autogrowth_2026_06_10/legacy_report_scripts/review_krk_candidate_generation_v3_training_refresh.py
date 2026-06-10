#!/usr/bin/env python3
"""Review whether dataset v3 supports a non-causal candidate-generation training refresh."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = Path("reports/strategy_arbitration/krk_candidate_generation_v3_runtime_boundary_review.json")
BENCHMARK = Path("reports/strategy_arbitration/krk_candidate_generation_v3_context_benchmark.json")
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v3.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_v3_training_refresh_review.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_v3_training_refresh_review.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    boundary: dict[str, Any] | None = None,
    benchmark: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    boundary = boundary or _load(BOUNDARY)
    benchmark = benchmark or _load(BENCHMARK)
    dataset = dataset or _load(DATASET)
    bsum = benchmark.get("summary") or {}
    dsum = dataset.get("summary") or {}
    exact_recall = float(bsum.get("exact_positive_capacity_recall_from_trace", 0.0) or 0.0)
    stage_family_recall = float(
        bsum.get("stage_family_positive_capacity_recall_from_trace", 0.0) or 0.0
    )
    negative_exposure = float(
        bsum.get("stage_family_negative_capacity_exposure_from_trace", 0.0) or 0.0
    )
    design_ready = (
        (boundary.get("decision") or {}).get("selector_allowed") is False
        and int(dsum.get("candidate_generation_training_row_count", 0) or 0) >= 20
        and int(dsum.get("selector_training_row_count", 0) or 0) == 0
        and int(dsum.get("stage7_readiness_training_row_count", 0) or 0) == 0
        and stage_family_recall >= 0.7
        and negative_exposure == 0.0
    )
    return {
        "schema_version": "krk_candidate_generation_v3_training_refresh_review.v1",
        "causal_status": "non_causal_training_refresh_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(BOUNDARY), str(BENCHMARK), str(DATASET)],
        "summary": {
            "candidate_generation_training_row_count": dsum.get(
                "candidate_generation_training_row_count"
            ),
            "selector_training_row_count": dsum.get("selector_training_row_count"),
            "stage7_readiness_training_row_count": dsum.get(
                "stage7_readiness_training_row_count"
            ),
            "runtime_trace_feature_row_count": dsum.get("runtime_trace_feature_row_count"),
            "exact_positive_capacity_recall_from_trace": exact_recall,
            "stage_family_positive_capacity_recall_from_trace": stage_family_recall,
            "stage_family_negative_capacity_exposure_from_trace": negative_exposure,
        },
        "allowed_next_design_scope": {
            "offline_candidate_generation_training_refresh_design": design_ready,
            "runtime_candidate_generator_change": False,
            "selector_training": False,
            "score_or_routing_change": False,
            "stage7_training_or_promotion": False,
        },
        "design_requirements": [
            "train/evaluate candidate-generation recall only, not ownership selection",
            "use protected Stage 4/5/6 rows only for readiness",
            "keep Stage 7 as held-out challenge evidence",
            "separate exact state/provider/move coverage from stage/family context",
            "report negative-capacity exposure by stage/family",
            "emit review packet before any runtime change",
        ],
        "blockers_before_runtime": [
            "no explicit ownership selector labels",
            "exact positive-capacity trace recall is partial",
            "capacity labels are not runtime ownership labels",
            "runtime observation context cannot select or score",
        ],
        "decision": {
            "status": (
                "candidate_generation_v3_training_refresh_design_ready_non_causal"
                if design_ready
                else "candidate_generation_v3_training_refresh_review_blocked"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "design_offline_candidate_generation_training_refresh_v3"
                if design_ready
                else "collect_more_candidate_generation_context"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    scope = payload["allowed_next_design_scope"]
    lines = [
        "# KRK Candidate-Generation v3 Training Refresh Review",
        "",
        "This review decides whether dataset v3 supports designing an offline candidate-generation training refresh. It does not implement training or runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Allowed Next Design Scope", ""])
    for key, value in scope.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Design Requirements", ""])
    lines.extend(f"- `{item}`" for item in payload["design_requirements"])
    lines.extend(["", "## Blockers Before Runtime", ""])
    lines.extend(f"- `{item}`" for item in payload["blockers_before_runtime"])
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
