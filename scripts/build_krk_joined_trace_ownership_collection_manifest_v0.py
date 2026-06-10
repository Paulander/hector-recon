#!/usr/bin/env python3
"""Build a non-causal manifest for collecting more joined trace/ownership evidence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v5.json")
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json")
SEED_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_joined_trace_ownership_collection_manifest_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_joined_trace_ownership_collection_manifest_v0.md")


APPROVED_REFRESH_CELLS = {
    "stage5": {"stage0_basin", "edge_trap", "fence_established"},
    "stage6": {"stage0_basin"},
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_trace_state_ids(dataset: dict[str, Any]) -> set[str]:
    return {
        str(row.get("state_id") or "")
        for row in dataset.get("rows") or []
        if isinstance(row, dict)
        and row.get("evidence_channel") == "runtime_observation_trace_feature"
        and row.get("candidate_provider_id")
        and not row.get("stage7_challenge_row")
    }


def _is_approved_cell(stage: str, family: str) -> bool:
    return family in APPROVED_REFRESH_CELLS.get(stage, set())


def _priority(row: dict[str, Any], approved_cell: bool) -> str:
    if not approved_cell:
        return "excluded_requires_separate_review"
    if row.get("target_label") == "selected_owner_failed":
        return "high_selected_failure"
    if row.get("provider_family") != "stage0_basin":
        return "medium_non_stage0_preservation"
    return "medium_safe_preservation_control"


def build_payload(
    *,
    ownership: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
    seed_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ownership = ownership or _load(OWNERSHIP)
    dataset = dataset or _load(DATASET)
    seed_probe = seed_probe or _load(SEED_PROBE)
    trace_state_ids = _provider_trace_state_ids(dataset)
    rows = [
        row
        for row in ownership.get("rows") or []
        if isinstance(row, dict) and row.get("source_stage") != "stage7"
    ]
    missing_rows = [
        row for row in rows if str(row.get("state_id") or "") not in trace_state_ids
    ]
    manifest_rows = []
    for row in missing_rows:
        stage = str(row.get("source_stage") or "")
        family = str(row.get("provider_family") or "")
        approved_cell = _is_approved_cell(stage, family)
        priority = _priority(row, approved_cell)
        manifest_rows.append(
            {
                "schema_version": "krk_joined_trace_ownership_collection_manifest_row.v0",
                "causal_status": "non_causal_collection_candidate",
                "state_id": row.get("state_id"),
                "source_stage": stage,
                "selected_provider": row.get("provider_id"),
                "selected_provider_family": family,
                "selected_owner_label": row.get("target_label"),
                "approved_observation_scope": approved_cell,
                "priority": priority,
                "stage7_training_row": False,
                "runtime_collection_allowed_by_manifest": False,
                "requires_review_before_runtime_collection": True,
            }
        )
    approved_rows = [row for row in manifest_rows if row["approved_observation_scope"]]
    excluded_rows = [row for row in manifest_rows if not row["approved_observation_scope"]]
    priority_counts = Counter(row["priority"] for row in manifest_rows)
    stage_counts = Counter(row["source_stage"] for row in manifest_rows)
    label_counts = Counter(row["selected_owner_label"] for row in manifest_rows)
    approved_label_counts = Counter(row["selected_owner_label"] for row in approved_rows)
    ready = (
        len(approved_rows) > 0
        and approved_label_counts["selected_owner_failed"] > 0
        and approved_label_counts["selected_owner_converted"] > 0
        and (seed_probe.get("decision") or {}).get("selector_allowed") is False
    )
    return {
        "schema_version": "krk_joined_trace_ownership_collection_manifest.v0",
        "causal_status": "non_causal_collection_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OWNERSHIP), str(DATASET), str(SEED_PROBE)],
        "approved_refresh_cells": {
            stage: sorted(families) for stage, families in APPROVED_REFRESH_CELLS.items()
        },
        "summary": {
            "ownership_row_count": len(rows),
            "existing_provider_trace_state_count": len(trace_state_ids),
            "missing_provider_trace_ownership_row_count": len(missing_rows),
            "approved_observation_scope_candidate_count": len(approved_rows),
            "excluded_requires_separate_review_count": len(excluded_rows),
            "priority_counts": dict(sorted(priority_counts.items())),
            "missing_source_stage_counts": dict(sorted(stage_counts.items())),
            "missing_label_counts": dict(sorted(label_counts.items())),
            "approved_scope_label_counts": dict(sorted(approved_label_counts.items())),
            "stage7_training_row_count": sum(1 for row in manifest_rows if row["stage7_training_row"]),
            "runtime_collection_allowed_row_count": sum(
                1 for row in manifest_rows if row["runtime_collection_allowed_by_manifest"]
            ),
        },
        "manifest_rows": manifest_rows,
        "decision": {
            "status": (
                "joined_trace_ownership_collection_manifest_ready_for_review"
                if ready
                else "joined_trace_ownership_collection_manifest_underpowered"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "runtime_collection_allowed_by_manifest": False,
            "recommended_next_step": (
                "review_bounded_observation_only_trace_collection_scope"
                if ready
                else "identify_additional_protected_ownership_labels"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Joined Trace/Ownership Collection Manifest v0",
        "",
        "This manifest identifies protected ownership-labeled states that lack provider trace context. It does not authorize a runtime run by itself.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- runtime_collection_allowed_by_manifest: `{payload['decision']['runtime_collection_allowed_by_manifest']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Approved Refresh Cells", ""])
    for stage, families in payload["approved_refresh_cells"].items():
        lines.append(f"- `{stage}`: `{families}`")
    lines.extend(["", "## Highest Priority Rows", ""])
    for row in payload["manifest_rows"]:
        if row["priority"].startswith("high"):
            lines.append(
                "- "
                f"`{row['state_id']}` "
                f"stage={row['source_stage']} "
                f"selected={row['selected_provider']} "
                f"label={row['selected_owner_label']} "
                f"priority=`{row['priority']}`"
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
