#!/usr/bin/env python3
"""Summarize ownership-label source/provider diversity before more collection."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v3.json")
CONTEXT_PROBE = Path("reports/krk_ownership_selection_context_feature_probe_v1.json")
SOURCE_ARTIFACTS = [
    Path("reports/krk_selector_feature_dataset_v0.json"),
    Path("reports/krk_strategy_arbiter_labeled_observation_controls_v0.json"),
    Path("reports/krk_strategy_arbiter_observation_selector_probe_v0.json"),
    Path("reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.json"),
    Path("reports/krk_selected_provider_diversity_observation_scan_v0.json"),
]
OUT_JSON = Path("reports/krk_ownership_source_diversity_review_v0.json")
OUT_MD = Path("reports/krk_ownership_source_diversity_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload.get("rows") or payload.get("labels") or payload.get("observations") or payload.get("records") or []


def _selected_provider(row: dict[str, Any]) -> str | None:
    return (
        row.get("selected_provider")
        or row.get("selected_provider_before_observation")
        or row.get("selected_provider_id")
    )


def _artifact_summary(path: Path) -> dict[str, Any]:
    payload = _load(path)
    rows = _rows(payload)
    provider_counts = Counter(str(provider) for row in rows if (provider := _selected_provider(row)))
    stage_counts = Counter(str(row.get("source_stage")) for row in rows if row.get("source_stage"))
    selected_playout_rows = [
        row
        for row in rows
        if row.get("target_kind") == "selected_playout_success"
        or row.get("selected_playout_success") is not None
        or row.get("selected_provider_id") is not None
    ]
    return {
        "path": str(path),
        "causal_status": payload.get("causal_status"),
        "row_count": len(rows),
        "selected_provider_counts": dict(provider_counts),
        "source_stage_counts": dict(stage_counts),
        "selected_playout_or_observation_row_count": len(selected_playout_rows),
        "non_stage0_selected_count": sum(
            count for provider, count in provider_counts.items() if provider != "krk.stage0_basin"
        ),
    }


def build_review() -> dict[str, Any]:
    ownership = _load(OWNERSHIP)
    probe = _load(CONTEXT_PROBE)
    if ownership.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership labels must remain non-causal")
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("context probe must remain non-causal")
    rows = [row for row in ownership.get("rows") or [] if row.get("source_stage") != "stage7"]
    by_source_provider: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_source_provider[str(row.get("label_source"))][str(row.get("provider_id"))] += 1
    artifact_summaries = [_artifact_summary(path) for path in SOURCE_ARTIFACTS if (ROOT / path).exists()]
    non_stage0_artifacts = [
        item
        for item in artifact_summaries
        if item["non_stage0_selected_count"] > 0
    ]
    provider_counts = Counter(str(row.get("provider_id")) for row in rows)
    label_counts = Counter(str(row.get("target_label")) for row in rows)
    balanced = probe.get("best_balanced_result") or {}
    status = "source_diversity_gap_blocks_runtime"
    payload = {
        "schema_version": "krk_ownership_source_diversity_review.v0",
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
        "source_artifacts": [str(OWNERSHIP), str(CONTEXT_PROBE), *map(str, SOURCE_ARTIFACTS)],
        "summary": {
            "ownership_row_count": len(rows),
            "ownership_label_counts": dict(label_counts),
            "ownership_provider_counts": dict(provider_counts),
            "non_stage0_ownership_row_count": sum(
                count for provider, count in provider_counts.items() if provider != "krk.stage0_basin"
            ),
            "source_provider_counts": {source: dict(counter) for source, counter in by_source_provider.items()},
            "artifact_count_reviewed": len(artifact_summaries),
            "artifact_count_with_non_stage0_selected": len(non_stage0_artifacts),
            "best_balanced_objective": balanced.get("objective"),
            "best_balanced_negative_suppression": balanced.get("negative_suppression"),
            "best_balanced_positive_recall": balanced.get("positive_recall"),
        },
        "artifact_summaries": artifact_summaries,
        "interpretation": [
            "Ownership evidence is still dominated by stage0_basin selected owners.",
            "Existing replay-free artifacts prove non-stage0 selected owners exist, but only a small subset has been converted into direct ownership labels.",
            "More random selected-provider diversity sampling is likely inefficient because two bounded slices overlapped heavily.",
            "The next useful evidence should target non-stage0 selected-owner contexts or explain why current handoff_composition_v1 routes protected jobs to stage0_basin so often.",
        ],
        "decision": {
            "status": status,
            "recommended_next_step": "design_targeted_non_stage0_ownership_label_manifest_or_review_routing_profile_dominance",
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
        "# KRK Ownership Source Diversity Review v0",
        "",
        "Non-causal review of ownership-label source/provider diversity after context enrichment.",
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
