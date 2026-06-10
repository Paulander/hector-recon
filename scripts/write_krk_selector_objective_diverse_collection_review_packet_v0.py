#!/usr/bin/env python3
"""Write a future bounded selector-objective diversity collection review packet."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DIVERSITY_REVIEW = Path(
    "reports/strategy_arbitration/krk_selector_objective_diversity_review_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_selector_objective_diverse_collection_review_packet_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_selector_objective_diverse_collection_review_packet_v0.md"
)

PROTECTED_STAGES = ["stage5", "stage6"]
EXCLUDED_STAGES = ["stage4", "stage7", "stage8"]


def _load(path: Path = DIVERSITY_REVIEW) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _review_rows(diversity_review: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(diversity_review.get("future_collection_candidates") or [], start=1):
        if not isinstance(row, dict):
            continue
        stage = str(row.get("source_stage") or "")
        label = str(row.get("selected_owner_label") or "")
        if stage not in PROTECTED_STAGES or stage in EXCLUDED_STAGES:
            continue
        if label not in {"selected_owner_failed", "selected_owner_converted"}:
            continue
        rows.append(
            {
                "schema_version": "krk_selector_objective_diverse_collection_review_row.v0",
                "causal_status": "non_causal_collection_candidate",
                "row_id": f"selector_objective_diverse_collection.{index:02d}",
                "state_id": row.get("state_id"),
                "frame_id": row.get("frame_id"),
                "fen": row.get("fen"),
                "source_stage": stage,
                "active_landmark_label": row.get("active_landmark_label"),
                "selected_provider": row.get("selected_provider"),
                "selected_provider_family": row.get("selected_provider_family"),
                "selected_owner_label": label,
                "objective_channel": row.get("objective_channel"),
                "recovery_class": row.get("recovery_class"),
                "priority_reason": row.get("priority_reason"),
                "approved_observation_scope": True,
                "requires_explicit_collection_approval": True,
                "runtime_collection_allowed_by_packet": False,
                "stage7_training_row": False,
                "usable_for_selector_training": False,
            }
        )
    return rows[:8]


def build_payload(diversity_review: dict[str, Any] | None = None) -> dict[str, Any]:
    diversity_review = diversity_review or _load()
    rows = _review_rows(diversity_review)
    stage_counts = Counter(row["source_stage"] for row in rows)
    label_counts = Counter(row["selected_owner_label"] for row in rows)
    family_counts = Counter(row["selected_provider_family"] for row in rows)
    valid_scope = (
        (diversity_review.get("decision") or {}).get("status")
        == "selector_objective_diverse_collection_review_ready"
        and len(rows) > 0
        and len(rows) <= 8
        and all(row["source_stage"] in PROTECTED_STAGES for row in rows)
        and all(row["source_stage"] not in EXCLUDED_STAGES for row in rows)
        and all(row["stage7_training_row"] is False for row in rows)
        and all(row["usable_for_selector_training"] is False for row in rows)
    )
    return {
        "schema_version": "krk_selector_objective_diverse_collection_review_packet.v0",
        "causal_status": "runtime_review_packet",
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
        "source_artifacts": [str(DIVERSITY_REVIEW)],
        "approved_if_later_explicitly_authorized": {
            "scope": "bounded_stage5_6_observation_only_selector_objective_diversity_collection",
            "max_rows": 8,
            "selected_review_row_count": len(rows),
            "protected_stages": PROTECTED_STAGES,
            "excluded_stages": EXCLUDED_STAGES,
            "default_off_required": True,
            "selected_move_provider_delta_allowed": False,
            "score_delta_allowed": False,
            "routing_allowed": False,
            "selector_training_allowed": False,
            "runtime_dtm_or_tablebase_allowed": False,
            "gameplay_topology_mutation_allowed": False,
        },
        "explicitly_forbidden": [
            "selector_training",
            "selector_implementation",
            "provider_routing",
            "score_changes",
            "provider_suppression",
            "capacity_labels_as_ownership_labels",
            "stage4_runtime_scope",
            "stage7_training_or_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
        "summary": {
            "review_row_count": len(rows),
            "stage_counts": dict(sorted(stage_counts.items())),
            "owner_label_counts": dict(sorted(label_counts.items())),
            "provider_family_counts": dict(sorted(family_counts.items())),
            "switch_contrast_candidate_count": label_counts["selected_owner_failed"],
            "safe_preservation_candidate_count": label_counts[
                "selected_owner_converted"
            ],
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "runtime_collection_allowed_row_count": 0,
            "stage4_row_count": stage_counts["stage4"],
            "stage7_row_count": stage_counts["stage7"],
            "stage8_row_count": stage_counts["stage8"],
        },
        "review_rows": rows,
        "decision": {
            "status": (
                "selector_objective_diverse_collection_review_ready"
                if valid_scope
                else "selector_objective_path_blocked_architecture_review_needed"
            ),
            "runtime_review_ready": valid_scope,
            "implementation_authorized_by_this_packet": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed_without_explicit_approval": False,
            "recommended_next_step": "explicit_approval_required_before_diverse_observation_collection",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Objective Diverse Collection Review Packet v0",
        "",
        "This packet defines a future bounded Stage 5/6 observation-only collection. It is not approval to execute the collection.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- runtime_review_ready: `{payload['decision']['runtime_review_ready']}`",
        f"- implementation_authorized_by_this_packet: `{payload['decision']['implementation_authorized_by_this_packet']}`",
        f"- selector_training_allowed: `{payload['decision']['selector_training_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Review Rows", ""])
    for row in payload["review_rows"]:
        lines.append(
            "- "
            f"`{row['row_id']}` "
            f"state={row['state_id']} "
            f"stage={row['source_stage']} "
            f"provider={row['selected_provider']} "
            f"label={row['selected_owner_label']} "
            f"reason={row['priority_reason']}"
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
