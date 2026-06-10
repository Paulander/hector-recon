#!/usr/bin/env python3
"""Review split selector objective readiness before training/runtime."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_split_selector_objective_dataset_v0.json")
FEATURE_REVIEW = Path("reports/krk_stronger_selector_feature_review_v0.json")
OUT_JSON = Path("reports/krk_split_selector_objective_readiness_v0.json")
OUT_MD = Path("reports/krk_split_selector_objective_readiness_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _channel_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("objective_channel"))].append(row)
    out = {}
    for channel, channel_rows in grouped.items():
        out[channel] = {
            "row_count": len(channel_rows),
            "offline_probe_row_count": sum(1 for row in channel_rows if row.get("usable_for_offline_probe")),
            "selector_training_row_count": sum(1 for row in channel_rows if row.get("usable_for_selector_training")),
            "target_label_counts": dict(Counter(str(row.get("target_label")) for row in channel_rows)),
            "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in channel_rows if row.get("source_stage"))),
            "state_count": len({row.get("state_id") for row in channel_rows if row.get("state_id")}),
        }
    return out


def build_review() -> dict[str, Any]:
    dataset = _load(DATASET)
    feature_review = _load(FEATURE_REVIEW)
    if dataset.get("causal_status") != "non_causal_split_objective_dataset":
        raise ValueError("split objective dataset must remain non-causal")
    if feature_review.get("causal_status") != "non_causal_feature_review":
        raise ValueError("feature review must remain non-causal")
    rows = list(dataset.get("rows") or [])
    channels = _channel_summary(rows)
    best = feature_review.get("best_result") or {}
    readiness = {
        "capacity_recall": {
            "status": "offline_evidence_available",
            "ready_for": "candidate_recall_benchmark_only",
            "blocked_for": "runtime ownership selection",
            "reason": "positive capacity rows identify providers worth including, not selecting.",
        },
        "capacity_risk": {
            "status": "offline_feature_signal_promising",
            "ready_for": "capacity-risk feature review",
            "blocked_for": "runtime suppression or selector training",
            "reason": (
                f"best feature `{best.get('objective')}` reaches negative suppression "
                f"`{best.get('negative_suppression')}` but labels are forced-path risk, not ownership."
            ),
        },
        "safe_preservation": {
            "status": "offline_evidence_available",
            "ready_for": "preservation constraint design",
            "blocked_for": "positive runtime ownership selection",
            "reason": "safe rows define what future suppressors must not break.",
        },
        "ownership_selection": {
            "status": "missing_label_channel",
            "ready_for": "nothing beyond requirements definition",
            "blocked_for": "selector training and runtime behavior",
            "reason": "forced-provider labels do not identify normal-routing owner choice.",
        },
    }
    payload = {
        "schema_version": "krk_split_selector_objective_readiness.v0",
        "causal_status": "non_causal_readiness_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(FEATURE_REVIEW)],
        "summary": {
            "objective_channel_count": len(channels),
            "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "ownership_selection_available": (dataset.get("summary") or {}).get("ownership_selection_available"),
            "capacity_risk_best_objective": best.get("objective"),
            "capacity_risk_best_negative_suppression": best.get("negative_suppression"),
            "capacity_risk_best_positive_recall": best.get("positive_recall"),
        },
        "channel_summary": channels,
        "readiness": readiness,
        "minimum_before_selector_training": [
            "ownership_selection labels from normal-routing or paired-selection evidence",
            "safe-preservation gate that protects validated converting providers",
            "capacity-risk feature reviewed as auxiliary risk, not direct target",
            "default-off sandbox review after offline objectives are separated",
        ],
        "decision": {
            "status": "split_objectives_fixed_semantics_runtime_still_blocked",
            "recommended_next_step": "collect_or_recover_ownership_selection_labels_before_selector_training",
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
    if payload["summary"]["selector_training_row_count"] != 0:
        raise ValueError("selector training remains blocked")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Split Selector Objective Readiness v0",
        "",
        "Readiness review after splitting forced-provider capacity evidence into separate objective channels.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Channel Readiness", ""])
    for key, value in payload["readiness"].items():
        lines.append(
            f"- `{key}` status=`{value['status']}` ready_for=`{value['ready_for']}` "
            f"blocked_for=`{value['blocked_for']}`. {value['reason']}"
        )
    lines.extend(["", "## Minimum Before Selector Training", ""])
    for item in payload["minimum_before_selector_training"]:
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
