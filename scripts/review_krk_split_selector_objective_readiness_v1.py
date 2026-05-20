#!/usr/bin/env python3
"""Review split selector readiness after recovering ownership labels."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPLIT = Path("reports/krk_split_selector_objective_dataset_v1.json")
OWNERSHIP_PROBE = Path("reports/krk_ownership_selection_feature_probe_v0.json")
CAPACITY_FEATURE_REVIEW = Path("reports/krk_stronger_selector_feature_review_v0.json")
OUT_JSON = Path("reports/krk_split_selector_objective_readiness_v1.json")
OUT_MD = Path("reports/krk_split_selector_objective_readiness_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _channel_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("objective_channel"))].append(row)
    return {
        channel: {
            "row_count": len(channel_rows),
            "target_label_counts": dict(Counter(str(row.get("target_label")) for row in channel_rows)),
            "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in channel_rows if row.get("source_stage"))),
            "state_count": len({row.get("state_id") for row in channel_rows if row.get("state_id")}),
            "selector_training_row_count": sum(1 for row in channel_rows if row.get("usable_for_selector_training")),
        }
        for channel, channel_rows in sorted(grouped.items())
    }


def build_review() -> dict[str, Any]:
    split = _load(SPLIT)
    ownership_probe = _load(OWNERSHIP_PROBE)
    capacity_review = _load(CAPACITY_FEATURE_REVIEW)
    if split.get("causal_status") != "non_causal_split_objective_dataset":
        raise ValueError("split dataset must remain non-causal")
    if ownership_probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("ownership probe must remain non-causal")
    if capacity_review.get("causal_status") != "non_causal_feature_review":
        raise ValueError("capacity review must remain non-causal")
    rows = list(split.get("rows") or [])
    ownership_best = ownership_probe.get("best_result") or {}
    capacity_best = capacity_review.get("best_result") or {}
    ownership_summary = ownership_probe.get("summary") or {}
    sufficient_for_review = (
        (ownership_best.get("negative_suppression") or 0) >= 0.5
        and (ownership_best.get("positive_recall") or 0) >= 0.7
        and not ownership_summary.get("underpowered")
    )
    status = "ownership_labels_recovered_but_underpowered"
    recommendation = "collect_more_normal_routing_ownership_labels_or_review_underpowered_probe"
    if sufficient_for_review:
        status = "split_objectives_ready_for_architecture_review"
        recommendation = "architecture_review_before_any_default_off_selector_training_or_runtime"
    payload = {
        "schema_version": "krk_split_selector_objective_readiness.v1",
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
        "source_artifacts": [str(SPLIT), str(OWNERSHIP_PROBE), str(CAPACITY_FEATURE_REVIEW)],
        "summary": {
            "objective_channel_count": len(_channel_summary(rows)),
            "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "ownership_selection_available": (split.get("summary") or {}).get("ownership_selection_available"),
            "ownership_selection_row_count": (split.get("summary") or {}).get("ownership_selection_row_count"),
            "ownership_probe_negative_suppression": ownership_best.get("negative_suppression"),
            "ownership_probe_positive_recall": ownership_best.get("positive_recall"),
            "ownership_probe_underpowered": ownership_summary.get("underpowered"),
            "capacity_risk_best_negative_suppression": capacity_best.get("negative_suppression"),
            "capacity_risk_best_positive_recall": capacity_best.get("positive_recall"),
        },
        "channel_summary": _channel_summary(rows),
        "readiness": {
            "capacity_recall": "available_for_candidate_recall_benchmark",
            "capacity_risk": "promising_auxiliary_risk_signal",
            "safe_preservation": "available_as_preservation_constraint",
            "ownership_selection": (
                "recovered_but_underpowered"
                if ownership_summary.get("underpowered")
                else "recovered_for_architecture_review"
            ),
        },
        "minimum_before_selector_training": [
            "architecture review of recovered ownership-selection semantics",
            "safe-preservation gate combined with ownership and capacity-risk objectives",
            "default-off sandbox review if offline evidence is accepted",
            "no Stage 7 training rows and no runtime DTM/tablebase",
        ],
        "decision": {
            "status": status,
            "recommended_next_step": recommendation,
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
        "# KRK Split Selector Objective Readiness v1",
        "",
        "Readiness review after recovering normal-routing ownership-selection labels.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Readiness", ""])
    for key, value in payload["readiness"].items():
        lines.append(f"- `{key}`: `{value}`")
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
