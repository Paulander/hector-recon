#!/usr/bin/env python3
"""Build selector-objective seed manifest v2 with replay-free observation rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEED_V1 = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.json")
STAGE4_COLLECTION = Path(
    "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_collection_v0.json"
)
FRESH_DIVERSITY_COLLECTION = Path(
    "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_collection_v0.json"
)
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _objective_channel(row: dict[str, Any]) -> str:
    recovery_class = str(row.get("recovery_class") or "")
    if recovery_class == "stage4_selected_failure_with_visible_positive_capacity":
        return "candidate_switch_contrast_seed"
    if recovery_class == "stage4_selected_failure_trace_context_only":
        return "failure_context_without_candidate_seed"
    return "context_only_preservation_seed"


def _row_from_stage4(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "krk_selector_objective_seed_manifest_row.v2",
        "causal_status": "non_causal_selector_objective_seed",
        "state_id": row.get("state_id"),
        "source_stage": row.get("source_stage"),
        "selected_provider": row.get("selected_provider_label"),
        "selected_provider_family": str(row.get("selected_provider_label") or "").replace(
            "krk.", ""
        ),
        "selected_owner_label": row.get("selected_owner_label"),
        "trace_provider_candidate_count": row.get("enabled_observation_frame_count"),
        "positive_trace_provider_candidate_count": row.get("positive_capacity_frame_count"),
        "trace_sources": ["stage4_candidate_generation_observation_collection"],
        "recovery_class": row.get("recovery_class"),
        "objective_channel": _objective_channel(row),
        "source_collection": "stage4_joined_trace_ownership_collection_v0",
        "usable_for_selector_training": False,
        "usable_for_runtime": False,
        "stage7_training_row": False,
    }


def _fresh_recovery_class(row: dict[str, Any]) -> str:
    recovery_class = str(row.get("recovery_class") or "")
    if recovery_class:
        return recovery_class
    if row.get("selected_owner_label") == "selected_owner_failed":
        return "selected_failure_with_visible_positive_capacity"
    return "safe_preservation_with_visible_positive_capacity"


def _row_from_fresh_collection(row: dict[str, Any]) -> dict[str, Any]:
    provider = str(row.get("selected_provider_label") or "")
    return {
        "schema_version": "krk_selector_objective_seed_manifest_row.v2",
        "causal_status": "non_causal_selector_objective_seed",
        "state_id": row.get("state_id"),
        "source_stage": row.get("source_stage"),
        "selected_provider": provider,
        "selected_provider_family": provider.replace("krk.", ""),
        "selected_owner_label": row.get("selected_owner_label"),
        "trace_provider_candidate_count": row.get("enabled_refresh_frame_count"),
        "positive_trace_provider_candidate_count": row.get("positive_capacity_frame_count"),
        "trace_sources": ["fresh_stage5_6_selector_objective_diversity_collection"],
        "recovery_class": _fresh_recovery_class(row),
        "objective_channel": row.get("objective_channel"),
        "source_collection": "fresh_stage5_6_selector_objective_diversity_collection_v0",
        "source_type": row.get("source_type"),
        "capacity_label_used_as_ownership_label": False,
        "usable_for_selector_training": False,
        "usable_for_runtime": False,
        "stage7_training_row": False,
    }


def _prefer_fresh_row(existing: dict[str, Any] | None, fresh: dict[str, Any]) -> bool:
    if existing is None:
        return True
    existing_positive = int(existing.get("positive_trace_provider_candidate_count") or 0)
    fresh_positive = int(fresh.get("positive_trace_provider_candidate_count") or 0)
    if fresh_positive > existing_positive:
        return True
    existing_trace = int(existing.get("trace_provider_candidate_count") or 0)
    fresh_trace = int(fresh.get("trace_provider_candidate_count") or 0)
    return fresh_positive == existing_positive and fresh_trace > existing_trace


def build_payload(
    *,
    seed_v1: dict[str, Any] | None = None,
    stage4_collection: dict[str, Any] | None = None,
    fresh_collection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed_v1 = seed_v1 or _load(SEED_V1)
    stage4_collection = stage4_collection or _load(STAGE4_COLLECTION)
    fresh_collection = fresh_collection or _load(FRESH_DIVERSITY_COLLECTION)
    rows_by_state: dict[str, dict[str, Any]] = {}
    for row in seed_v1.get("seed_rows") or []:
        if not isinstance(row, dict):
            continue
        updated = dict(row)
        updated["schema_version"] = "krk_selector_objective_seed_manifest_row.v2"
        updated["usable_for_selector_training"] = False
        updated["usable_for_runtime"] = False
        updated["stage7_training_row"] = False
        rows_by_state[str(updated.get("state_id") or "")] = updated

    added_count = 0
    for row in stage4_collection.get("rows") or []:
        if not isinstance(row, dict) or not row.get("joined_trace_ownership_row"):
            continue
        updated = _row_from_stage4(row)
        state_id = str(updated.get("state_id") or "")
        if state_id not in rows_by_state:
            added_count += 1
        rows_by_state[state_id] = updated

    fresh_added_count = 0
    fresh_replaced_count = 0
    fresh_duplicate_count = 0
    for row in fresh_collection.get("rows") or []:
        if not isinstance(row, dict) or not row.get("joined_trace_ownership_row"):
            continue
        if row.get("source_stage") not in {"stage5", "stage6"}:
            continue
        updated = _row_from_fresh_collection(row)
        state_id = str(updated.get("state_id") or "")
        existing = rows_by_state.get(state_id)
        if _prefer_fresh_row(existing, updated):
            if existing is None:
                fresh_added_count += 1
            else:
                fresh_replaced_count += 1
            rows_by_state[state_id] = updated
        else:
            fresh_duplicate_count += 1

    seed_rows = [rows_by_state[key] for key in sorted(rows_by_state)]
    channel_counts = Counter(str(row.get("objective_channel")) for row in seed_rows)
    recovery_counts = Counter(str(row.get("recovery_class")) for row in seed_rows)
    stage_counts = Counter(str(row.get("source_stage")) for row in seed_rows)
    ready_for_probe = (
        len(seed_rows) >= 12
        and channel_counts["candidate_switch_contrast_seed"] >= 4
        and channel_counts["safe_preservation_contrast_seed"] >= 4
        and (stage4_collection.get("decision") or {}).get("collection_valid") is True
    )
    return {
        "schema_version": "krk_selector_objective_seed_manifest.v2",
        "causal_status": "non_causal_selector_objective_seed_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(SEED_V1),
            str(STAGE4_COLLECTION),
            str(FRESH_DIVERSITY_COLLECTION),
        ],
        "summary": {
            "input_seed_v1_row_count": len(seed_v1.get("seed_rows") or []),
            "stage4_joined_row_count": (stage4_collection.get("summary") or {}).get(
                "joined_row_count"
            ),
            "added_stage4_seed_row_count": added_count,
            "fresh_collection_joined_row_count": (fresh_collection.get("summary") or {}).get(
                "joined_row_count"
            ),
            "fresh_collection_added_seed_row_count": fresh_added_count,
            "fresh_collection_replaced_seed_row_count": fresh_replaced_count,
            "fresh_collection_duplicate_lower_value_row_count": fresh_duplicate_count,
            "seed_row_count": len(seed_rows),
            "objective_channel_counts": dict(sorted(channel_counts.items())),
            "recovery_class_counts": dict(sorted(recovery_counts.items())),
            "source_stage_counts": dict(sorted(stage_counts.items())),
            "candidate_switch_contrast_seed_count": channel_counts[
                "candidate_switch_contrast_seed"
            ],
            "safe_preservation_contrast_seed_count": channel_counts[
                "safe_preservation_contrast_seed"
            ],
            "selector_training_row_count": sum(
                1 for row in seed_rows if row.get("usable_for_selector_training")
            ),
            "stage7_training_row_count": sum(
                1 for row in seed_rows if row.get("stage7_training_row")
            ),
            "runtime_authorization_row_count": sum(
                1 for row in seed_rows if row.get("usable_for_runtime")
            ),
            "capacity_label_used_as_ownership_label_count": sum(
                1 for row in seed_rows if row.get("capacity_label_used_as_ownership_label")
            ),
        },
        "seed_rows": seed_rows,
        "decision": {
            "status": (
                "selector_objective_seed_manifest_v2_ready_non_causal"
                if ready_for_probe
                else "selector_objective_seed_manifest_v2_underpowered"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "probe_selector_objective_seed_manifest_v2"
                if ready_for_probe
                else "collect_more_or_better_joined_trace_ownership_evidence_non_causal"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Seed Manifest v2",
        "",
        "This manifest adds replay-free observation-only trace rows to the non-causal selector-objective seed set. It remains evidence only.",
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
    lines.extend(["", "## Seed Rows", ""])
    for row in payload["seed_rows"]:
        lines.append(
            "- "
            f"`{row['state_id']}` "
            f"stage={row.get('source_stage')} "
            f"channel=`{row['objective_channel']}` "
            f"selected={row['selected_provider']} "
            f"label={row['selected_owner_label']} "
            f"positive_trace_candidates={row['positive_trace_provider_candidate_count']}"
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
