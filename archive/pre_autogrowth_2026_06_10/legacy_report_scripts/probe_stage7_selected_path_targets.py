#!/usr/bin/env python3
"""Probe split Stage 7 selected-path targets non-causally."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/structural_candidates/stage7_selected_path_target_dataset_v1.json")
OUT_JSON = Path("reports/structural_candidates/stage7_selected_path_target_probe_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_selected_path_target_probe_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _bool_feature(row: dict[str, Any], name: str) -> bool:
    return bool((row.get("features") or {}).get(name))


def _feature_separation(rows: list[dict[str, Any]], positive_roles: set[str], feature: str) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        positive = row.get("row_role") in positive_roles
        predicted = _bool_feature(row, feature)
        if predicted and positive:
            tp += 1
        elif predicted and not positive:
            fp += 1
        elif not predicted and positive:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {
        "feature": feature,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
    }


def _group_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["target_id"]].append(row)
    return dict(grouped)


def build_probe() -> dict[str, Any]:
    dataset = _load(DATASET)
    rows = dataset.get("rows") or []
    grouped = _group_rows(rows)
    ownership_rows = grouped.get("stage7.selected_path.strategy_ownership_gap.v0", [])
    sequence_rows = grouped.get("stage7.selected_path.sequence_continuation_gap.v0", [])
    ownership_positive = {"stage7_selected_owner_failed_positive"}
    sequence_gap = {"stage7_sequence_gap_unresolved"}

    ownership_feature_results = [
        _feature_separation(ownership_rows, ownership_positive, feature)
        for feature in (
            "local_provider_competition_failed",
            "selected_owner_failed_h40",
            "alternative_provider_known_conversion_h40",
        )
    ]
    sequence_feature_results = [
        _feature_separation(sequence_rows, sequence_gap, feature)
        for feature in (
            "post_plan_stagnation",
            "forced_providers_h40_no_mate",
            "legal_first_h40_no_mate",
        )
    ]
    sequence_source_counts = Counter(
        (row.get("features") or {}).get("control_quality", "gap_or_unqualified")
        for row in sequence_rows
    )
    ownership_state_count = len({row.get("state_id") for row in ownership_rows})
    sequence_state_count = len({row.get("state_id") for row in sequence_rows})
    source_biased = sequence_source_counts.get("sandbox_sourced_replay_free_success_control", 0) > 0
    decision = (
        "split_targets_separable_but_source_biased_no_runtime"
        if source_biased
        else "split_targets_probe_ready_for_review"
    )
    return {
        "schema_version": "stage7_selected_path_target_probe.v0",
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET)],
        "summary": {
            "row_count": len(rows),
            "ownership_row_count": len(ownership_rows),
            "sequence_row_count": len(sequence_rows),
            "ownership_state_count": ownership_state_count,
            "sequence_state_count": sequence_state_count,
            "sequence_source_counts": dict(sequence_source_counts),
            "source_bias_detected": source_biased,
        },
        "ownership_target_probe": {
            "positive_role": "stage7_selected_owner_failed_positive",
            "control_role": "protected_safe_owner_control",
            "feature_results": ownership_feature_results,
            "interpretation": "Ownership positives separate from protected safe controls, but there are only two Stage 7 positives.",
        },
        "sequence_target_probe": {
            "gap_role": "stage7_sequence_gap_unresolved",
            "success_control_role": "stage7_sequence_success_control_recovered",
            "feature_results": sequence_feature_results,
            "interpretation": "Sequence gap rows separate from recovered success controls, but recovered controls are prior-sandbox-sourced and may encode artifact/source bias.",
        },
        "decision": {
            "status": decision,
            "recommended_next_step": "architecture_review_or_collect_clean_sequence_controls_before_runtime",
            "why": "The split target framing is useful, but existing evidence is too small and source-biased to justify runtime behavior.",
            "blocked_runtime_work": [
                "runtime arbiter",
                "abstention selector tuning",
                "plan capsule runtime repair",
                "Stage 7 promotion",
                "Stage 8 training",
            ],
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Selected Path Target Probe v0",
        "",
        f"Decision: `{payload['decision']['status']}`",
        "",
        "This is a non-causal offline probe. It does not authorize runtime behavior.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Ownership Target", ""])
    for result in payload["ownership_target_probe"]["feature_results"]:
        lines.append(
            f"- `{result['feature']}`: precision=`{result['precision']}`, recall=`{result['recall']}`, "
            f"tp=`{result['tp']}`, fp=`{result['fp']}`, fn=`{result['fn']}`"
        )
    lines.extend(["", payload["ownership_target_probe"]["interpretation"], "", "## Sequence Target", ""])
    for result in payload["sequence_target_probe"]["feature_results"]:
        lines.append(
            f"- `{result['feature']}`: precision=`{result['precision']}`, recall=`{result['recall']}`, "
            f"tp=`{result['tp']}`, fp=`{result['fp']}`, fn=`{result['fn']}`"
        )
    lines.extend([
        "",
        payload["sequence_target_probe"]["interpretation"],
        "",
        "## Decision",
        "",
        f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
        f"- Why: {payload['decision']['why']}",
        "",
        "Blocked runtime work:",
        "",
    ])
    for item in payload["decision"]["blocked_runtime_work"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
