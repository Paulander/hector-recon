#!/usr/bin/env python3
"""Build selector-objective seed manifest v1 with joined collection rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEED_V0 = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v0.json")
COLLECTION = Path("reports/strategy_arbitration/krk_joined_trace_ownership_collection_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _objective_channel(recovery_class: str) -> str:
    if recovery_class == "selected_failure_with_visible_positive_alternative":
        return "candidate_switch_contrast_seed"
    if recovery_class == "safe_preservation_with_visible_positive_alternative":
        return "safe_preservation_contrast_seed"
    if recovery_class == "selected_failure_with_trace_context_only":
        return "failure_context_without_candidate_seed"
    return "context_only_preservation_seed"


def _row_from_collection(row: dict[str, Any]) -> dict[str, Any]:
    recovery_class = str(row.get("recovery_class") or "unknown")
    return {
        "schema_version": "krk_selector_objective_seed_manifest_row.v1",
        "causal_status": "non_causal_selector_objective_seed",
        "state_id": row.get("state_id"),
        "source_stage": row.get("source_stage"),
        "selected_provider": row.get("selected_provider_label"),
        "selected_provider_family": str(row.get("selected_provider_label") or "").replace(
            "krk.", ""
        ),
        "selected_owner_label": row.get("selected_owner_label"),
        "trace_provider_candidate_count": row.get("enabled_refresh_frame_count"),
        "positive_trace_provider_candidate_count": row.get("positive_refresh_frame_count"),
        "trace_sources": ["stage5_6_candidate_generation_refresh_collection"],
        "recovery_class": recovery_class,
        "objective_channel": _objective_channel(recovery_class),
        "source_collection": "joined_trace_ownership_collection_v0",
        "usable_for_selector_training": False,
        "usable_for_runtime": False,
        "stage7_training_row": False,
    }


def build_payload(
    *,
    seed_v0: dict[str, Any] | None = None,
    collection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed_v0 = seed_v0 or _load(SEED_V0)
    collection = collection or _load(COLLECTION)
    rows_by_state: dict[str, dict[str, Any]] = {}
    for row in seed_v0.get("seed_rows") or []:
        if not isinstance(row, dict):
            continue
        updated = dict(row)
        updated["schema_version"] = "krk_selector_objective_seed_manifest_row.v1"
        updated["usable_for_selector_training"] = False
        updated["usable_for_runtime"] = False
        updated["stage7_training_row"] = False
        rows_by_state[str(updated.get("state_id") or "")] = updated
    added_count = 0
    for row in collection.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if not row.get("joined_trace_ownership_row"):
            continue
        updated = _row_from_collection(row)
        state_id = str(updated.get("state_id") or "")
        if state_id not in rows_by_state:
            added_count += 1
        rows_by_state[state_id] = updated
    seed_rows = [rows_by_state[key] for key in sorted(rows_by_state)]
    channel_counts = Counter(str(row.get("objective_channel")) for row in seed_rows)
    recovery_counts = Counter(str(row.get("recovery_class")) for row in seed_rows)
    stage_counts = Counter(str(row.get("source_stage")) for row in seed_rows)
    ready_for_probe = (
        channel_counts["candidate_switch_contrast_seed"] >= 4
        and channel_counts["safe_preservation_contrast_seed"] >= 4
        and (collection.get("decision") or {}).get("collection_valid") is True
    )
    return {
        "schema_version": "krk_selector_objective_seed_manifest.v1",
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
        "source_artifacts": [str(SEED_V0), str(COLLECTION)],
        "summary": {
            "input_seed_v0_row_count": len(seed_v0.get("seed_rows") or []),
            "collection_joined_row_count": (collection.get("summary") or {}).get(
                "joined_row_count"
            ),
            "added_collection_seed_row_count": added_count,
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
        },
        "seed_rows": seed_rows,
        "decision": {
            "status": (
                "selector_objective_seed_manifest_v1_ready_non_causal"
                if ready_for_probe
                else "selector_objective_seed_manifest_v1_underpowered"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "probe_selector_objective_seed_manifest_v1"
                if ready_for_probe
                else "collect_more_joined_trace_ownership_evidence_non_causal"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Seed Manifest v1",
        "",
        "This manifest adds bounded joined trace/ownership collection rows to the non-causal selector-objective seed set. It is not selector training data.",
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
