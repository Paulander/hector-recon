#!/usr/bin/env python3
"""Review context-enriched ownership-selection probe results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_DATASET = Path("reports/krk_ownership_selection_context_dataset_v0.json")
CONTEXT_PROBE = Path("reports/krk_ownership_selection_context_feature_probe_v0.json")
BASE_PROBE = Path("reports/krk_ownership_selection_feature_probe_v2.json")
OUT_JSON = Path("reports/krk_ownership_context_feature_review_v0.json")
OUT_MD = Path("reports/krk_ownership_context_feature_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _metric(result: dict[str, Any], key: str) -> float | None:
    value = result.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def build_review() -> dict[str, Any]:
    dataset = _load(CONTEXT_DATASET)
    probe = _load(CONTEXT_PROBE)
    base_probe = _load(BASE_PROBE)
    if dataset.get("causal_status") != "non_causal_context_feature_dataset":
        raise ValueError("context dataset must remain non-causal")
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("context probe must remain non-causal")
    if base_probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("base probe must remain non-causal")

    base_best = base_probe.get("best_result") or {}
    context_best = probe.get("best_result") or {}
    balanced = probe.get("best_balanced_result") or {}
    balanced_improves_recall = (_metric(balanced, "positive_recall") or 0.0) > (
        _metric(base_best, "positive_recall") or 0.0
    )
    balanced_loses_suppression = (_metric(balanced, "negative_suppression") or 0.0) < (
        _metric(base_best, "negative_suppression") or 0.0
    )
    threshold_pass = (
        (_metric(balanced, "negative_suppression") or 0.0) >= 0.6
        and (_metric(balanced, "positive_recall") or 0.0) >= 0.7
    )
    status = (
        "context_features_review_ready_but_not_runtime_ready"
        if balanced_improves_recall and not threshold_pass
        else "context_features_no_clear_gain"
    )
    payload = {
        "schema_version": "krk_ownership_context_feature_review.v0",
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(CONTEXT_DATASET), str(CONTEXT_PROBE), str(BASE_PROBE)],
        "summary": {
            "context_row_count": (dataset.get("summary") or {}).get("row_count"),
            "fen_join_count": (dataset.get("summary") or {}).get("fen_join_count"),
            "exact_move_context_count": (dataset.get("summary") or {}).get("exact_move_context_count"),
            "base_best_objective": base_best.get("objective"),
            "base_best_negative_suppression": base_best.get("negative_suppression"),
            "base_best_positive_recall": base_best.get("positive_recall"),
            "context_best_objective": context_best.get("objective"),
            "context_best_negative_suppression": context_best.get("negative_suppression"),
            "context_best_positive_recall": context_best.get("positive_recall"),
            "context_best_balanced_objective": balanced.get("objective"),
            "context_best_balanced_negative_suppression": balanced.get("negative_suppression"),
            "context_best_balanced_positive_recall": balanced.get("positive_recall"),
            "balanced_improves_recall": balanced_improves_recall,
            "balanced_loses_suppression": balanced_loses_suppression,
            "runtime_threshold_passed": threshold_pass,
        },
        "interpretation": [
            "FEN-derived context is useful for positive-owner preservation: the balanced context result raises positive recall to 0.88.",
            "The same context does not yet suppress enough unsafe selected owners: negative suppression remains 0.444 on the balanced result.",
            "The ownership evidence is still provider-family narrow: most rows are stage0_basin, so this should not be trained into a runtime selector.",
            "The next improvement should target source/provider diversity and normal-routing ownership labels, not another Stage 7 repair.",
        ],
        "decision": {
            "status": status,
            "recommended_next_step": "review_source_diversity_or_collect_non_stage7_normal_routing_ownership_labels_with_non_stage0_selected_providers",
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
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Ownership Context Feature Review v0",
        "",
        "Non-causal review of ownership-selection labels enriched with replay-free FEN and selected-move geometry context.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
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
