#!/usr/bin/env python3
"""Review KRK selector-objective feature probe v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_review_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_review_v0.md")


def _load(path: Path = PROBE) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _best_by(results: dict[str, dict[str, Any]], key: str) -> dict[str, Any]:
    runtime = [result for result in results.values() if result.get("runtime_feature_eligible")]
    return max(runtime, key=lambda item: item.get(key) or 0.0, default={})


def build_payload(probe: dict[str, Any] | None = None) -> dict[str, Any]:
    probe = probe or _load()
    summary = probe.get("summary") or {}
    results = probe.get("results") or {}
    best_switch = _best_by(results, "switch_recall")
    best_preserve = _best_by(results, "preserve_recall")
    best_precision = _best_by(results, "switch_precision")
    no_runtime_ready = int(summary.get("runtime_threshold_passing_model_count", 0) or 0) == 0
    return {
        "schema_version": "krk_selector_objective_feature_probe_review.v0",
        "causal_status": "non_causal_feature_probe_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PROBE)],
        "summary": {
            "seed_row_count": summary.get("seed_row_count"),
            "target_channel_counts": summary.get("target_channel_counts"),
            "runtime_threshold_passing_model_count": summary.get(
                "runtime_threshold_passing_model_count"
            ),
            "best_switch_model": best_switch.get("model_id"),
            "best_switch_recall": best_switch.get("switch_recall"),
            "best_switch_preserve_recall": best_switch.get("preserve_recall"),
            "best_switch_precision": best_switch.get("switch_precision"),
            "best_preserve_model": best_preserve.get("model_id"),
            "best_preserve_recall": best_preserve.get("preserve_recall"),
            "best_preserve_switch_recall": best_preserve.get("switch_recall"),
            "best_precision_model": best_precision.get("model_id"),
            "best_precision": best_precision.get("switch_precision"),
            "best_precision_switch_recall": best_precision.get("switch_recall"),
            "offline_oracle_accuracy": summary.get("offline_oracle_accuracy"),
            "selector_training_row_count": summary.get("selector_training_row_count"),
            "stage7_training_row_count": summary.get("stage7_training_row_count"),
        },
        "blockers": [
            "simple_visible_features_do_not_pass_switch_and_preserve_thresholds",
            "best_switch_recall_models_overfire_and_destroy_preservation",
            "best_preservation_models_miss_too_many_switch_cases",
            "offline_outcome_oracle_is_not_runtime_feature_eligible",
            "seed_set_is_still_provider_family_narrow",
        ],
        "recommended_evidence": [
            "more_selected_failure_with_visible_positive_alternative_rows",
            "more_non_stage0_selected_owner_rows",
            "more_stage5_6_failure_rows_if_available",
            "separate_stage4_scope_review_if_stage4_rows_are_needed",
            "visible_progress_window_features_that_do_not_use_outcome_labels",
        ],
        "decision": {
            "status": (
                "selector_feature_probe_blocks_runtime_needs_diverse_evidence"
                if no_runtime_ready
                else "selector_feature_probe_review_ready"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "collect_more_diverse_joined_trace_ownership_evidence"
                if no_runtime_ready
                else "write_runtime_review_packet_only"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Feature Probe Review v0",
        "",
        "This review interprets the non-causal selector-objective feature probe. It does not authorize selector training or runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- `{item}`" for item in payload["blockers"])
    lines.extend(["", "## Recommended Evidence", ""])
    lines.extend(f"- `{item}`" for item in payload["recommended_evidence"])
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
