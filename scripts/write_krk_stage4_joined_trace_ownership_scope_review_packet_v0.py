#!/usr/bin/env python3
"""Write a Stage 4 joined trace/ownership observation scope review packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DIVERSITY = Path("reports/strategy_arbitration/krk_selector_objective_diversity_gap_review_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_stage4_joined_trace_ownership_scope_review_packet_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_stage4_joined_trace_ownership_scope_review_packet_v0.md")


def _load(path: Path = DIVERSITY) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(diversity: dict[str, Any] | None = None) -> dict[str, Any]:
    diversity = diversity or _load()
    candidates = [
        row
        for row in diversity.get("stage4_failure_candidates") or []
        if isinstance(row, dict)
    ]
    review_rows = candidates[:6]
    ready = (
        (diversity.get("decision") or {}).get("status")
        == "selector_objective_diversity_gap_requires_stage4_scope_review"
        and len(review_rows) > 0
    )
    return {
        "schema_version": "krk_stage4_joined_trace_ownership_scope_review_packet.v0",
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
        "source_artifacts": [str(DIVERSITY)],
        "implementation_authorized_by_this_packet": False,
        "approved_if_later_explicitly_authorized": {
            "scope": "stage4_observation_only_trace_collection_for_selector_objective_evidence",
            "protected_stages": ["stage4"],
            "excluded_stages": ["stage5", "stage6", "stage7", "stage8"],
            "max_rows": 6,
            "selected_review_row_count": len(review_rows),
            "default_off_required": True,
            "selected_move_provider_delta_allowed": False,
            "score_delta_allowed": False,
            "routing_allowed": False,
            "selector_training_allowed": False,
            "requires_new_stage4_observation_source": True,
        },
        "review_rows": review_rows,
        "why_stage4_is_needed": [
            "Stage 5/6 approved scope has no remaining selected-failure rows outside the seed",
            "Stage 4 contains the remaining selected-owner failure contrasts",
            "The current selector feature probe overfires because switch evidence is too narrow",
        ],
        "stage4_risks": [
            "Stage 4 candidate-generation cells were previously mixed",
            "Stage 4 observation source must not become a provider selector",
            "Any Stage 4 source must remain observation-only and default-off",
        ],
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
            "stage7_training_or_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
        "decision": {
            "status": (
                "stage4_joined_trace_ownership_scope_review_ready"
                if ready
                else "stage4_joined_trace_ownership_scope_review_blocked"
            ),
            "runtime_review_ready": ready,
            "implementation_authorized_by_this_packet": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed_without_explicit_approval": False,
            "recommended_next_step": (
                "explicit_approval_required_before_stage4_observation_source_design_or_run"
                if ready
                else "collect_more_stage5_6_evidence_if_available"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    approved = payload["approved_if_later_explicitly_authorized"]
    lines = [
        "# KRK Stage 4 Joined Trace/Ownership Scope Review Packet v0",
        "",
        "This packet reviews whether Stage 4 observation-only trace collection is justified for selector-objective evidence. It does not authorize implementation or execution by itself.",
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
    lines.extend(["", "## Why Stage 4 Is Needed", ""])
    lines.extend(f"- `{item}`" for item in payload["why_stage4_is_needed"])
    lines.extend(["", "## Stage 4 Risks", ""])
    lines.extend(f"- `{item}`" for item in payload["stage4_risks"])
    lines.extend(["", "## Review Rows", ""])
    for row in payload["review_rows"]:
        lines.append(
            "- "
            f"`{row['state_id']}` "
            f"label={row['active_landmark_label']} "
            f"selected={row['selected_provider']} "
            f"target={row['target_label']}"
        )
    lines.extend(["", "## Explicitly Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
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
