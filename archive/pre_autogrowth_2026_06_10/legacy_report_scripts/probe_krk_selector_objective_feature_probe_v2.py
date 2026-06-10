#!/usr/bin/env python3
"""Write selector-objective feature probe v2 from the non-causal benchmark."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import benchmark_krk_selector_objective_v2 as benchmark  # noqa: E402

OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_v2.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_v2.md")


def build_payload(benchmark_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    benchmark_payload = benchmark_payload or benchmark.build_payload()
    summary = benchmark_payload.get("summary") or {}
    interpretation = benchmark_payload.get("interpretation") or {}
    results = benchmark_payload.get("results") or {}
    runtime_models = {
        model_id: result
        for model_id, result in results.items()
        if isinstance(result, dict) and result.get("runtime_feature_eligible") is True
    }
    passing_models = {
        model_id: result
        for model_id, result in runtime_models.items()
        if (result.get("switch_recall") or 0.0) >= 0.70
        and (result.get("switch_precision") or 0.0) >= 0.70
        and (result.get("preserve_recall") or 0.0) >= 0.80
        and (result.get("abstain_recall") or 0.0) >= 0.60
    }
    return {
        "schema_version": "krk_selector_objective_feature_probe.v2",
        "causal_status": "non_causal_feature_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_provider_suppression": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json",
            "reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json",
            "reports/strategy_arbitration/krk_selector_objective_benchmark_v2.json",
        ],
        "summary": {
            "seed_row_count": summary.get("seed_row_count"),
            "target_action_counts": summary.get("target_action_counts"),
            "runtime_feature_model_count": len(runtime_models),
            "runtime_threshold_passing_model_count": len(passing_models),
            "best_runtime_model": summary.get("best_runtime_model"),
            "best_runtime_accuracy": summary.get("best_runtime_accuracy"),
            "best_runtime_switch_precision": summary.get("best_runtime_switch_precision"),
            "best_runtime_switch_recall": summary.get("best_runtime_switch_recall"),
            "best_runtime_preserve_recall": summary.get("best_runtime_preserve_recall"),
            "best_runtime_abstain_recall": summary.get("best_runtime_abstain_recall"),
            "selector_training_row_count": summary.get("selector_training_row_count"),
            "stage7_training_row_count": summary.get("stage7_training_row_count"),
            "runtime_authorization_row_count": 0,
        },
        "runtime_feature_models": runtime_models,
        "passing_runtime_feature_models": passing_models,
        "interpretation": {
            "feature_probe_ready_for_review": bool(passing_models),
            "selector_training_supported": False,
            "runtime_selector_supported": False,
            "independent_validation_required_before_runtime": bool(passing_models),
            "offline_semantics_confirmed": interpretation.get("offline_semantics_confirmed"),
            "capacity_labels_are_not_ownership_labels": True,
            "reason": (
                "Feature probe v2 summarizes runtime-visible non-causal models only. "
                "It does not train or authorize a selector and does not use ownership "
                "labels as runtime features."
            ),
        },
        "decision": {
            "status": (
                "selector_objective_feature_probe_v2_review_ready"
                if passing_models
                else "selector_objective_feature_probe_v2_underpowered"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "review_selector_objective_feature_probe_v2_before_any_runtime_design"
                if passing_models
                else "collect_or_recover_more_diverse_non_causal_selector_objective_evidence"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Feature Probe v2",
        "",
        "This is a non-causal feature probe over the v2 seed manifest. It does not train or authorize a selector.",
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
    lines.extend(["", "## Passing Runtime-Visible Probe Models", ""])
    for model_id, result in sorted(payload["passing_runtime_feature_models"].items()):
        lines.append(
            "- "
            f"`{model_id}` "
            f"accuracy={result.get('accuracy')} "
            f"switch_precision={result.get('switch_precision')} "
            f"switch_recall={result.get('switch_recall')} "
            f"preserve_recall={result.get('preserve_recall')} "
            f"abstain_recall={result.get('abstain_recall')}"
        )
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
