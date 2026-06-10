#!/usr/bin/env python3
"""Probe selector-objective seed manifest v2 non-causally."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.md")


def _load(path: Path = MANIFEST) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _target_action(row: dict[str, Any]) -> str:
    channel = row.get("objective_channel")
    if channel == "candidate_switch_contrast_seed":
        return "prefer_visible_alternative"
    if channel == "safe_preservation_contrast_seed":
        return "preserve_selected_owner"
    if channel == "progress_window_failure_contrast_candidate":
        if row.get("selected_owner_label") == "selected_owner_failed":
            return "prefer_visible_alternative"
        return "preserve_selected_owner"
    return "abstain_context_only"


def _semantic_rule_prediction(row: dict[str, Any]) -> str:
    selected_failed = row.get("selected_owner_label") == "selected_owner_failed"
    selected_converted = row.get("selected_owner_label") == "selected_owner_converted"
    has_positive_alternative = int(row.get("positive_trace_provider_candidate_count") or 0) > 0
    if selected_failed and has_positive_alternative:
        return "prefer_visible_alternative"
    if selected_converted:
        return "preserve_selected_owner"
    return "abstain_context_only"


def build_payload(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or _load()
    seed_rows = [row for row in manifest.get("seed_rows") or [] if isinstance(row, dict)]
    predictions = []
    for row in seed_rows:
        target = _target_action(row)
        predicted = _semantic_rule_prediction(row)
        predictions.append(
            {
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "selected_provider": row.get("selected_provider"),
                "objective_channel": row.get("objective_channel"),
                "target_action": target,
                "predicted_action": predicted,
                "correct": predicted == target,
                "runtime_feature_eligible": False,
                "reason": "uses offline selected-owner outcome labels and observation-only capacity evidence",
            }
        )

    target_counts = Counter(prediction["target_action"] for prediction in predictions)
    stage_counts = Counter(str(prediction["source_stage"]) for prediction in predictions)
    correct_count = sum(1 for prediction in predictions if prediction["correct"])
    row_count = len(predictions)
    apparent_accuracy = correct_count / row_count if row_count else 0.0
    has_switch_and_preserve = (
        target_counts["prefer_visible_alternative"] > 0
        and target_counts["preserve_selected_owner"] > 0
    )
    underpowered = (
        row_count < 16
        or target_counts["prefer_visible_alternative"] < 4
        or target_counts["preserve_selected_owner"] < 4
    )
    return {
        "schema_version": "krk_selector_objective_seed_probe.v2",
        "causal_status": "non_causal_seed_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "summary": {
            "seed_row_count": row_count,
            "target_action_counts": dict(sorted(target_counts.items())),
            "source_stage_counts": dict(sorted(stage_counts.items())),
            "correct_count": correct_count,
            "apparent_semantic_rule_accuracy": apparent_accuracy,
            "has_switch_and_preserve_seeds": has_switch_and_preserve,
            "benchmark_underpowered": underpowered,
            "runtime_feature_eligible_prediction_count": sum(
                1 for prediction in predictions if prediction["runtime_feature_eligible"]
            ),
            "selector_training_row_count": (manifest.get("summary") or {}).get(
                "selector_training_row_count"
            ),
            "stage7_training_row_count": (manifest.get("summary") or {}).get(
                "stage7_training_row_count"
            ),
        },
        "predictions": predictions,
        "interpretation": {
            "semantics_confirmed": apparent_accuracy == 1.0 and has_switch_and_preserve,
            "stage4_switch_contrast_added": stage_counts["stage4"] > 0,
            "selector_training_supported": False,
            "runtime_selector_supported": False,
            "reason": (
                "The seed rows now include Stage 4 switch-context evidence and enough "
                "switch/preserve/abstain contrast for a non-causal objective benchmark, but "
                "the probe still uses offline labels and is not selector training."
            ),
        },
        "decision": {
            "status": (
                "selector_objective_seed_probe_v2_ready_for_non_causal_benchmark"
                if has_switch_and_preserve and not underpowered
                else "selector_objective_seed_probe_v2_underpowered_semantics_confirmed"
                if has_switch_and_preserve
                else "selector_objective_seed_probe_v2_missing_contrast_class"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "design_non_causal_selector_objective_benchmark"
                if not underpowered and has_switch_and_preserve
                else "collect_more_stage4_safe_preservation_or_runtime_visible_feature_evidence"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Seed Probe v2",
        "",
        "This non-causal probe checks whether the expanded seed manifest encodes switch-vs-preserve semantics after adding Stage 4 observation rows. It is not selector training.",
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
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
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
