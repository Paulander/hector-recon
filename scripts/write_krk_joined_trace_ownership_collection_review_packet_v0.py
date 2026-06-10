#!/usr/bin/env python3
"""Write a review packet for bounded joined trace/ownership observation collection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/strategy_arbitration/krk_joined_trace_ownership_collection_manifest_v0.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_joined_trace_ownership_collection_review_packet_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_joined_trace_ownership_collection_review_packet_v0.md"
)


def _load(path: Path = MANIFEST) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _select_review_rows(manifest_rows: list[dict[str, Any]], cap: int = 8) -> list[dict[str, Any]]:
    approved = [row for row in manifest_rows if row.get("approved_observation_scope")]
    high = [row for row in approved if row.get("priority") == "high_selected_failure"]
    other = [row for row in approved if row.get("priority") != "high_selected_failure"]
    return (high + other)[:cap]


def build_payload(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or _load()
    manifest_rows = [row for row in manifest.get("manifest_rows") or [] if isinstance(row, dict)]
    review_rows = _select_review_rows(manifest_rows)
    high_count = sum(1 for row in review_rows if row.get("priority") == "high_selected_failure")
    stage7_count = sum(1 for row in review_rows if row.get("source_stage") == "stage7")
    ready = (
        (manifest.get("decision") or {}).get("status")
        == "joined_trace_ownership_collection_manifest_ready_for_review"
        and len(review_rows) > 0
        and high_count > 0
        and stage7_count == 0
    )
    return {
        "schema_version": "krk_joined_trace_ownership_collection_review_packet.v0",
        "causal_status": "runtime_review_packet",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "implementation_authorized_by_this_packet": False,
        "approved_if_later_explicitly_authorized": {
            "scope": "bounded_observation_only_trace_collection",
            "protected_stages": ["stage5", "stage6"],
            "excluded_stages": ["stage4", "stage7", "stage8"],
            "max_rows": 8,
            "selected_review_row_count": len(review_rows),
            "high_priority_failure_row_count": high_count,
            "default_off_required": True,
            "selected_move_provider_delta_allowed": False,
            "score_delta_allowed": False,
            "routing_allowed": False,
            "selector_training_allowed": False,
        },
        "review_rows": review_rows,
        "acceptance_criteria_if_later_run": [
            "default_off_equivalence",
            "observation_frames_only",
            "selected_move_provider_delta_count_zero",
            "score_delta_count_zero",
            "stage7_training_row_count_zero",
            "runtime_dtm_or_tablebase_lookup_false",
            "gameplay_topology_mutation_false",
            "joined_trace_ownership_rows_increase",
        ],
        "explicitly_forbidden": [
            "selector_training",
            "provider_routing",
            "score_changes",
            "capacity_labels_as_ownership_labels",
            "stage4_runtime_scope",
            "stage7_training_or_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
        "decision": {
            "status": (
                "joined_trace_ownership_observation_collection_review_ready"
                if ready
                else "joined_trace_ownership_observation_collection_review_blocked"
            ),
            "runtime_review_ready": ready,
            "implementation_authorized_by_this_packet": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed_without_explicit_approval": False,
            "recommended_next_step": (
                "explicit_approval_required_before_observation_collection_run"
                if ready
                else "fix_collection_manifest_before_review"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    approved = payload["approved_if_later_explicitly_authorized"]
    lines = [
        "# KRK Joined Trace/Ownership Collection Review Packet v0",
        "",
        "This packet reviews a bounded observation-only trace collection run. It does not authorize implementation or execution by itself.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- runtime_review_ready: `{payload['decision']['runtime_review_ready']}`",
        f"- implementation_authorized_by_this_packet: `{payload['decision']['implementation_authorized_by_this_packet']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Approved Scope If Later Explicitly Authorized",
        "",
    ]
    for key, value in approved.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Acceptance Criteria If Later Run", ""])
    lines.extend(f"- `{item}`" for item in payload["acceptance_criteria_if_later_run"])
    lines.extend(["", "## Explicitly Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
    lines.extend(["", "## Review Rows", ""])
    for row in payload["review_rows"]:
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
