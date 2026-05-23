#!/usr/bin/env python3
"""Review selector-objective diversity gaps after feature probe v0."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v5.json")
SEED = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.json")
FEATURE_REVIEW = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_review_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_diversity_gap_review_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_diversity_gap_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    ownership: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
    feature_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ownership = ownership or _load(OWNERSHIP)
    seed = seed or _load(SEED)
    feature_review = feature_review or _load(FEATURE_REVIEW)
    seed_states = {str(row.get("state_id") or "") for row in seed.get("seed_rows") or []}
    remaining = [
        row
        for row in ownership.get("rows") or []
        if isinstance(row, dict)
        and row.get("source_stage") != "stage7"
        and str(row.get("state_id") or "") not in seed_states
    ]
    remaining_by_stage = Counter(str(row.get("source_stage") or "unknown") for row in remaining)
    remaining_by_label = Counter(str(row.get("target_label") or "unknown") for row in remaining)
    remaining_by_family = Counter(str(row.get("provider_family") or "unknown") for row in remaining)
    selected_failures = [
        row for row in remaining if row.get("target_label") == "selected_owner_failed"
    ]
    non_stage0 = [
        row for row in remaining if row.get("provider_family") != "stage0_basin"
    ]
    stage4_failures = [
        row
        for row in selected_failures
        if row.get("source_stage") == "stage4"
    ]
    stage5_6_remaining = [
        row for row in remaining if row.get("source_stage") in {"stage5", "stage6"}
    ]
    stage5_6_failures = [
        row
        for row in stage5_6_remaining
        if row.get("target_label") == "selected_owner_failed"
    ]
    stage5_6_non_stage0 = [
        row
        for row in stage5_6_remaining
        if row.get("provider_family") != "stage0_basin"
    ]
    needs_stage4 = len(stage5_6_failures) == 0 and len(stage4_failures) > 0
    needs_new_non_stage0_source = len(stage5_6_non_stage0) <= 1
    return {
        "schema_version": "krk_selector_objective_diversity_gap_review.v0",
        "causal_status": "non_causal_diversity_gap_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OWNERSHIP), str(SEED), str(FEATURE_REVIEW)],
        "summary": {
            "seed_row_count": len(seed.get("seed_rows") or []),
            "remaining_ownership_row_count": len(remaining),
            "remaining_by_stage": dict(sorted(remaining_by_stage.items())),
            "remaining_by_label": dict(sorted(remaining_by_label.items())),
            "remaining_by_provider_family": dict(sorted(remaining_by_family.items())),
            "remaining_selected_failure_count": len(selected_failures),
            "remaining_non_stage0_count": len(non_stage0),
            "remaining_stage4_selected_failure_count": len(stage4_failures),
            "remaining_stage5_6_selected_failure_count": len(stage5_6_failures),
            "remaining_stage5_6_non_stage0_count": len(stage5_6_non_stage0),
            "feature_probe_status": (feature_review.get("decision") or {}).get("status"),
        },
        "stage4_failure_candidates": [
            {
                "state_id": row.get("state_id"),
                "frame_id": row.get("frame_id"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "selected_provider": row.get("provider_id"),
                "provider_family": row.get("provider_family"),
                "target_label": row.get("target_label"),
            }
            for row in stage4_failures
        ],
        "stage5_6_non_stage0_candidates": [
            {
                "state_id": row.get("state_id"),
                "frame_id": row.get("frame_id"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "selected_provider": row.get("provider_id"),
                "provider_family": row.get("provider_family"),
                "target_label": row.get("target_label"),
            }
            for row in stage5_6_non_stage0
        ],
        "interpretation": {
            "stage5_6_approved_scope_nearly_exhausted_for_switch_evidence": (
                len(stage5_6_failures) == 0
            ),
            "stage4_scope_needed_for_more_switch_contrast": needs_stage4,
            "new_non_stage0_label_source_needed": needs_new_non_stage0_source,
            "runtime_selector_supported": False,
        },
        "decision": {
            "status": (
                "selector_objective_diversity_gap_requires_stage4_scope_review"
                if needs_stage4
                else "selector_objective_diversity_gap_needs_new_label_source"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "write_stage4_observation_scope_review_packet"
                if needs_stage4
                else "collect_more_non_stage0_ownership_labels_non_causal"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Diversity Gap Review v0",
        "",
        "This review explains why the selector-objective feature probe remains blocked. It is non-causal and does not authorize runtime behavior.",
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
    lines.extend(["", "## Stage 4 Failure Candidates", ""])
    for row in payload["stage4_failure_candidates"]:
        lines.append(
            "- "
            f"`{row['state_id']}` "
            f"label={row['active_landmark_label']} "
            f"selected={row['selected_provider']} "
            f"target={row['target_label']}"
        )
    lines.extend(["", "## Stage 5/6 Non-Stage0 Candidates", ""])
    for row in payload["stage5_6_non_stage0_candidates"]:
        lines.append(
            "- "
            f"`{row['state_id']}` "
            f"stage={row['source_stage']} "
            f"selected={row['selected_provider']} "
            f"target={row['target_label']}"
        )
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
