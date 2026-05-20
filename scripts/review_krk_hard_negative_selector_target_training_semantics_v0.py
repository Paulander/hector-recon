#!/usr/bin/env python3
"""Review semantics for hard-negative selector target candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGETS = Path("reports/krk_hard_negative_selector_target_dataset_v0.json")
DIRECTED_REVIEW = Path("reports/krk_selector_directed_fix_review_v0.json")
OUT_JSON = Path("reports/krk_hard_negative_selector_target_training_semantics_review_v0.json")
OUT_MD = Path("reports/krk_hard_negative_selector_target_training_semantics_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    targets = _load(TARGETS)
    directed = _load(DIRECTED_REVIEW)
    if targets.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("hard-negative target dataset must remain non-causal")
    if directed.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("directed review must remain non-causal")
    summary = targets.get("summary") or {}
    hard_negatives = int((summary.get("target_kind_counts") or {}).get("hard_negative_capacity") or 0)
    positives = int((summary.get("target_kind_counts") or {}).get("positive_capacity_context") or 0)
    payload = {
        "schema_version": "krk_hard_negative_selector_target_training_semantics_review.v0",
        "causal_status": "non_causal_semantics_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(TARGETS), str(DIRECTED_REVIEW)],
        "summary": {
            "target_row_count": summary.get("row_count"),
            "hard_negative_capacity_count": hard_negatives,
            "positive_capacity_context_count": positives,
            "stage7_row_count": summary.get("stage7_row_count"),
            "current_training_row_count": summary.get("training_row_count"),
        },
        "approved_non_causal_uses": [
            "offline_hard_negative_selector_benchmark",
            "feature_ablation_for_negative_suppression",
            "candidate_generator_precision_review",
        ],
        "blocked_uses": [
            "runtime_selector_training",
            "runtime_provider_suppression",
            "runtime_provider_boost",
            "topology_mutation",
            "Stage7 promotion",
            "Stage8 training",
        ],
        "training_semantics": {
            "hard_negative_capacity": (
                "May be used as an offline benchmark negative for candidate scoring. It means forced first-move ownership failed h40, "
                "not that the provider is globally bad or should be suppressed at runtime."
            ),
            "positive_capacity_context": (
                "May be used as offline positive-capacity context. It is still not selected-playout success and should not be "
                "mixed with runtime proposal labels without channel separation."
            ),
        },
        "requirements_for_future_training": [
            "explicit objective separates capacity, runtime proposal, and selected-playout channels",
            "leave-state-out negative suppression improves above baseline",
            "hard-negative false positives are inspected",
            "Stage 7 remains held out",
            "guardrail suite passes before any causal sandbox",
        ],
        "decision": {
            "status": "hard_negative_targets_approved_for_offline_benchmark_only",
            "recommended_next_step": "run_hard_negative_selector_feature_ablation_v0",
            "offline_benchmark_allowed": True,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
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
        "# KRK Hard-Negative Selector Target Training Semantics Review v0",
        "",
        "This review authorizes offline benchmarking only. It does not authorize runtime selector training.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Approved Non-Causal Uses", ""])
    for item in payload["approved_non_causal_uses"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocked Uses", ""])
    for item in payload["blocked_uses"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Training Semantics", ""])
    for key, value in payload["training_semantics"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Requirements For Future Training", ""])
    for item in payload["requirements_for_future_training"]:
        lines.append(f"- `{item}`")
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
