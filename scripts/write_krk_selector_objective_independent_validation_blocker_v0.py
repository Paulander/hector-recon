#!/usr/bin/env python3
"""Summarize blocker after selector-objective independent validation v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = Path("reports/strategy_arbitration/krk_selector_objective_independent_validation_v0.json")
LABELS = Path("reports/strategy_arbitration/krk_selector_objective_independent_validation_labels_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_independent_validation_blocker_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_independent_validation_blocker_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def build_payload(validation: dict[str, Any] | None = None, labels: dict[str, Any] | None = None) -> dict[str, Any]:
    validation = validation or _load(VALIDATION)
    labels = labels or _load(LABELS)
    summary = validation.get("summary") or {}
    target_counts = summary.get("target_counts") or {}
    switch_count = int(target_counts.get("switch") or 0)
    preserve_count = int(target_counts.get("preserve") or 0)
    blocked = switch_count < 2
    return {
        "schema_version": "krk_selector_objective_independent_validation_blocker.v0",
        "causal_status": "non_causal_blocker_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(VALIDATION), str(LABELS)],
        "evidence_summary": {
            "validation_status": (validation.get("decision") or {}).get("status"),
            "label_count": (labels.get("summary") or {}).get("label_count"),
            "target_counts": target_counts,
            "prediction_counts": summary.get("prediction_counts"),
            "accuracy": summary.get("accuracy"),
            "switch_recall": summary.get("switch_recall"),
            "preserve_recall": summary.get("preserve_recall"),
            "stage7_training_row_count": summary.get("stage7_training_row_count"),
            "selector_training_row_count": summary.get("selector_training_row_count"),
        },
        "blocker": {
            "runtime_selector_blocked": True,
            "blocker_class": (
                "independent_switch_contrast_absent" if blocked else "independent_validation_failed"
            ),
            "why": (
                "The independent bounded protected slice validated safe preservation only; "
                "it produced no selected-owner failure/switch rows, so switch recall cannot "
                "be independently validated."
                if blocked
                else "Independent validation did not meet thresholds."
            ),
        },
        "recommended_next_evidence": [
            "targeted protected selected-owner failure discovery from Stage 4 caveat cases",
            "normal-routing failure rows with visible competing proposal evidence",
            "paired switch-vs-preserve rows that exclude current benchmark seed states",
        ],
        "explicitly_forbidden": [
            "runtime_selector",
            "selector_training",
            "score_changes",
            "provider_suppression",
            "direct_provider_routing",
            "capacity_labels_as_ownership_labels",
            "stage7_training_or_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
        "decision": {
            "status": (
                "selector_objective_runtime_blocked_pending_independent_switch_contrasts"
                if blocked
                else "selector_objective_runtime_blocked_after_failed_validation"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "targeted_stage4_failure_discovery_or_keep_selector_blocked",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Independent Validation Blocker v0",
        "",
        "This review closes the current selector-objective validation slice. It does not authorize runtime selector work.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Evidence Summary", ""])
    for key, value in payload["evidence_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Blocker", ""])
    for key, value in payload["blocker"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Recommended Next Evidence", ""])
    for item in payload["recommended_next_evidence"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Explicitly Forbidden", ""])
    for item in payload["explicitly_forbidden"]:
        lines.append(f"- `{item}`")
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
