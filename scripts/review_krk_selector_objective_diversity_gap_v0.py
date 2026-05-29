#!/usr/bin/env python3
"""Review selector-objective diversity gaps after feature probe v0."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v5.json")
COLLECTION = Path("reports/strategy_arbitration/krk_joined_trace_ownership_collection_v0.json")
SEED = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.json")
SEED_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v1.json")
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
    collection: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
    seed_probe: dict[str, Any] | None = None,
    feature_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ownership = ownership or _load(OWNERSHIP)
    collection = collection or _load(COLLECTION)
    seed = seed or _load(SEED)
    seed_probe = seed_probe or _load(SEED_PROBE)
    feature_review = feature_review or _load(FEATURE_REVIEW)
    seed_rows = [row for row in seed.get("seed_rows") or [] if isinstance(row, dict)]
    seed_states = {str(row.get("state_id") or "") for row in seed_rows}
    joined_rows = [row for row in collection.get("rows") or [] if isinstance(row, dict)]
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
    seed_by_label = Counter(str(row.get("selected_owner_label") or "unknown") for row in seed_rows)
    seed_by_family = Counter(
        str(row.get("selected_provider_family") or "unknown") for row in seed_rows
    )
    seed_by_stage = Counter(str(row.get("source_stage") or "unknown") for row in seed_rows)
    selected_failure_seed_rows = [
        row for row in seed_rows if row.get("selected_owner_label") == "selected_owner_failed"
    ]
    safe_preservation_seed_rows = [
        row for row in seed_rows if row.get("selected_owner_label") == "selected_owner_converted"
    ]
    selected_failure_families = Counter(
        str(row.get("selected_provider_family") or "unknown")
        for row in selected_failure_seed_rows
    )
    selected_failure_types = Counter(
        str(row.get("active_landmark_label") or "unknown")
        for row in selected_failure_seed_rows
    )
    safe_preservation_families = Counter(
        str(row.get("selected_provider_family") or "unknown")
        for row in safe_preservation_seed_rows
    )
    non_stage0_seed_rows = [
        row
        for row in seed_rows
        if row.get("selected_provider_family") not in {None, "", "stage0_basin"}
    ]
    replay_free_stage5_6_extra = [
        row for row in stage5_6_remaining if str(row.get("state_id") or "") not in seed_states
    ]
    replay_free_stage5_6_extra_by_label = Counter(
        str(row.get("target_label") or "unknown") for row in replay_free_stage5_6_extra
    )
    replay_free_stage5_6_extra_by_family = Counter(
        str(row.get("provider_family") or "unknown")
        for row in replay_free_stage5_6_extra
    )
    replay_free_recovery_enough = (
        replay_free_stage5_6_extra_by_label["selected_owner_failed"] >= 2
        and sum(
            count
            for family, count in replay_free_stage5_6_extra_by_family.items()
            if family != "stage0_basin"
        )
        >= 2
        and len(joined_rows) >= len(seed_rows) + 2
    )
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
        "runtime_provider_suppression": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(OWNERSHIP),
            str(COLLECTION),
            str(SEED),
            str(SEED_PROBE),
            str(FEATURE_REVIEW),
        ],
        "summary": {
            "collection_status": (collection.get("decision") or {}).get("status"),
            "seed_probe_status": (seed_probe.get("decision") or {}).get("status"),
            "seed_row_count": len(seed_rows),
            "seed_by_stage": dict(sorted(seed_by_stage.items())),
            "seed_by_label": dict(sorted(seed_by_label.items())),
            "seed_by_provider_family": dict(sorted(seed_by_family.items())),
            "remaining_ownership_row_count": len(remaining),
            "remaining_by_stage": dict(sorted(remaining_by_stage.items())),
            "remaining_by_label": dict(sorted(remaining_by_label.items())),
            "remaining_by_provider_family": dict(sorted(remaining_by_family.items())),
            "remaining_selected_failure_count": len(selected_failures),
            "remaining_non_stage0_count": len(non_stage0),
            "remaining_stage4_selected_failure_count": len(stage4_failures),
            "remaining_stage5_6_selected_failure_count": len(stage5_6_failures),
            "remaining_stage5_6_non_stage0_count": len(stage5_6_non_stage0),
            "replay_free_stage5_6_extra_row_count": len(replay_free_stage5_6_extra),
            "replay_free_stage5_6_extra_by_label": dict(
                sorted(replay_free_stage5_6_extra_by_label.items())
            ),
            "replay_free_stage5_6_extra_by_provider_family": dict(
                sorted(replay_free_stage5_6_extra_by_family.items())
            ),
            "joined_trace_row_count": len(joined_rows),
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "feature_probe_status": (feature_review.get("decision") or {}).get("status"),
        },
        "questions": {
            "primary_blockers": [
                "provider_diversity",
                "failure_type_diversity",
                "feature_quality_under_current_seed",
            ],
            "row_count_is_primary_blocker": False,
            "provider_diversity_is_blocker": True,
            "stage_diversity_is_blocker": False,
            "failure_type_diversity_is_blocker": True,
            "feature_quality_is_blocker": True,
            "overrepresented_provider_families": [
                family
                for family, count in seed_by_family.items()
                if family == "stage0_basin" and count >= max(1, len(seed_rows) // 2)
            ],
            "selected_owner_failed_rows_diverse_enough": False,
            "selected_owner_failed_provider_family_counts": dict(
                sorted(selected_failure_families.items())
            ),
            "selected_owner_failed_failure_type_counts": dict(
                sorted(selected_failure_types.items())
            ),
            "safe_preservation_rows_diverse_enough": False,
            "safe_preservation_provider_family_counts": dict(
                sorted(safe_preservation_families.items())
            ),
            "non_stage0_selected_owners_represented": len(non_stage0_seed_rows) > 0,
            "non_stage0_selected_owner_seed_count": len(non_stage0_seed_rows),
            "can_recover_more_rows_replay_free_from_existing_artifacts": (
                replay_free_recovery_enough
            ),
            "why_replay_free_recovery_is_not_enough": (
                "Remaining Stage 5/6 replay-free ownership rows add safe-preservation "
                "context but not enough selected-owner failure or non-stage0 joined "
                "trace/ownership evidence. Rows without joined trace observation remain "
                "review candidates, not selector seeds."
            ),
            "bounded_observation_only_collection_needed": {
                "scope": "Stage 5/6 joined trace/ownership observation for selector-objective diversity",
                "max_rows": 8,
                "excluded_stages": ["stage4", "stage7", "stage8"],
                "requires_explicit_approval": True,
                "must_remain_observation_only": True,
            },
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
            "capacity_labels_are_not_ownership_labels": True,
            "replay_free_recovery_enough": replay_free_recovery_enough,
            "runtime_selector_supported": False,
        },
        "decision": {
            "status": "selector_objective_diverse_collection_review_ready",
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "write_selector_objective_diverse_collection_review_packet_v0",
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
    lines.extend(["", "## Required Questions", ""])
    for key, value in payload["questions"].items():
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
