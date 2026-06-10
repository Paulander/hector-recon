#!/usr/bin/env python3
"""Write narrow behavior-changing selector sandbox review packet v0.

This packet reviews a possible future behavior-changing sandbox. It does not
implement or authorize behavior-changing selector behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFINED_SANDBOX = Path(
    "reports/strategy_arbitration/krk_refined_selector_observability_sandbox_v0.json"
)
REFINED_RUNTIME_REVIEW = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_observability_runtime_review_packet_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_review_packet_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_review_packet_v0.md"
)

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_provider_suppression": False,
    "hidden_python_controller": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}

POSSIBLE_STATUSES = [
    "selector_behavior_sandbox_review_ready",
    "selector_behavior_sandbox_needs_more_observation",
    "selector_behavior_sandbox_blocked",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    *,
    refined_sandbox: dict[str, Any] | None = None,
    runtime_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    refined_sandbox = refined_sandbox or _load(REFINED_SANDBOX)
    runtime_review = runtime_review or _load(REFINED_RUNTIME_REVIEW)
    summary = refined_sandbox.get("summary") or {}
    counts = summary.get("recommendation_counts_by_class") or {}
    switch_count = int(counts.get("prefer_visible_alternative", 0) or 0)
    source_terms = list((summary.get("source_term_coverage") or {}).get("source_terms") or [])

    no_deltas = all(
        int(summary.get(key, 0) or 0) == 0
        for key in (
            "selected_move_delta_count",
            "selected_provider_delta_count",
            "score_delta_count",
            "routing_delta_count",
            "stage7_training_row_count",
            "selector_training_row_count",
            "capacity_label_used_as_ownership_label_count",
            "invalid_metadata_count",
        )
    )
    constraints_satisfied = (
        refined_sandbox.get("decision", {}).get("status")
        == "refined_selector_observability_ready_for_recommendation_analysis"
        and runtime_review.get("decision", {}).get("status")
        == "refined_selector_observability_runtime_review_ready"
        and summary.get("default_off_equivalence_passed") is True
        and summary.get("runtime_behavior_changed") is False
        and summary.get("preserve_on_failure_count") == 0
        and summary.get("abstain_recall") == 1.0
        and summary.get("switch_on_safe_owner_count") == 0
        and switch_count > 0
        and bool(source_terms)
        and refined_sandbox.get("runtime_dtm_or_tablebase_lookup") is False
        and refined_sandbox.get("gameplay_topology_mutation") is False
        and refined_sandbox.get("hidden_python_controller") is False
        and no_deltas
    )
    status = (
        "selector_behavior_sandbox_review_ready"
        if constraints_satisfied
        else "selector_behavior_sandbox_needs_more_observation"
    )

    return {
        "schema_version": "krk_selector_behavior_sandbox_review_packet.v0",
        "causal_status": "non_causal_behavior_sandbox_review_packet",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(REFINED_SANDBOX), str(REFINED_RUNTIME_REVIEW)],
        "proposed_sandbox": {
            "name": "default_off_narrow_selector_behavior_sandbox",
            "implementation_status": "not_implemented",
            "authorization_status": "review_packet_only_not_approved_for_implementation",
            "default_off_required": True,
            "opt_in_only": True,
            "opt_in_flag": "--enable-krk-selector-behavior-sandbox",
            "active_only_when_recommendation": "prefer_visible_alternative",
            "preserve_selected_owner_effect": "no_op",
            "abstain_context_only_effect": "no_op",
            "may_choose_only_already_visible_alternative": True,
            "new_candidate_generation_allowed": False,
            "direct_provider_request_allowed": False,
            "hidden_routing_allowed": False,
            "stage7_training_or_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "allowed_effect": {
            "bounded_switch_from_selected_owner_to_visible_alternative": True,
            "only_when_recommendation": "prefer_visible_alternative",
            "record_original_selected_owner": True,
            "record_original_selected_move": True,
            "record_replacement_owner": True,
            "record_replacement_move": True,
            "record_source_terms": True,
            "record_explanation_terms": True,
            "direct_request": False,
            "score_delta": 0.0,
            "runtime_dtm_or_tablebase_allowed": False,
            "gameplay_topology_mutation_allowed": False,
        },
        "required_vetoes": [
            "no_switch_if_recommendation_is_preserve_selected_owner",
            "no_switch_if_recommendation_is_abstain_context_only",
            "no_switch_if_no_visible_alternative_exists",
            "no_switch_if_safe_preservation_veto_fires",
            "no_switch_if_alternative_lacks_runtime_visible_provenance",
            "no_switch_if_stage7_row_or_training_context",
            "no_switch_if_source_terms_missing",
        ],
        "required_validation_before_later_implementation": [
            "explicit_approval",
            "default_off_equivalence",
            "trace_only_comparison_first",
            "tiny_targeted_switch_smoke",
            "selected_move_provider_deltas_allowed_only_when_enabled_and_reviewed_switch_case",
            "score_delta_remains_zero_unless_separately_reviewed",
            "target_improvement_before_guardrails",
            "guardrails_before_promotion",
            "rollback_tag",
        ],
        "explicitly_forbidden": [
            "implementation_by_this_packet",
            "runtime_default_change",
            "routing_changes",
            "score_changes_without_separate_review",
            "provider_suppression",
            "new_candidate_generation",
            "direct_provider_request",
            "hidden_routing",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "treating_capacity_labels_as_ownership_labels",
        ],
        "supporting_evidence": {
            "refined_observability_status": refined_sandbox.get("decision", {}).get(
                "status"
            ),
            "enabled_recommendation_count": summary.get("enabled_recommendation_count"),
            "recommendation_counts_by_class": counts,
            "switch_recommendation_count": switch_count,
            "source_terms": source_terms,
            "preserve_on_failure_count": summary.get("preserve_on_failure_count"),
            "abstain_recall": summary.get("abstain_recall"),
            "switch_on_safe_owner_count": summary.get("switch_on_safe_owner_count"),
            "selector_training_row_count": summary.get("selector_training_row_count"),
            "stage7_training_row_count": summary.get("stage7_training_row_count"),
            "selected_move_delta_count": summary.get("selected_move_delta_count"),
            "selected_provider_delta_count": summary.get("selected_provider_delta_count"),
            "score_delta_count": summary.get("score_delta_count"),
            "routing_delta_count": summary.get("routing_delta_count"),
            "runtime_behavior_changed": summary.get("runtime_behavior_changed"),
            "runtime_dtm_or_tablebase_use": summary.get("runtime_dtm_or_tablebase_use"),
            "gameplay_topology_mutation": summary.get("gameplay_topology_mutation"),
            "capacity_label_used_as_ownership_label_count": summary.get(
                "capacity_label_used_as_ownership_label_count"
            ),
        },
        "remaining_risks": [
            "tiny_evidence_set",
            "switch_recall_less_than_perfect",
            "visible_alternatives_may_still_be_poor_candidates",
            "candidate_generation_quality_remains_separate",
            "selector_not_yet_tested_causally",
        ],
        "possible_statuses": POSSIBLE_STATUSES,
        "decision": {
            "status": status,
            "implementation_authorized_by_this_packet": False,
            "behavior_changing_implementation_present": False,
            "behavior_changing_selector_allowed_by_this_packet": False,
            "runtime_changes_allowed_by_this_packet": False,
            "default_off_required": True,
            "selector_runtime_ready": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "runtime_dtm_or_tablebase_allowed": False,
            "gameplay_topology_mutation_allowed": False,
            "recommended_next_step": (
                "seek_explicit_approval_before_any_default_off_behavior_sandbox_implementation"
                if constraints_satisfied
                else "collect_more_refined_observability_or_switch_evidence"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    decision = payload["decision"]
    sandbox = payload["proposed_sandbox"]
    effect = payload["allowed_effect"]
    evidence = payload["supporting_evidence"]
    lines = [
        "# KRK Selector Behavior Sandbox Review Packet v0",
        "",
        "This packet reviews a possible future default-off, narrow behavior-changing selector sandbox. It does not implement or authorize selector behavior.",
        "",
        "## Decision",
        "",
    ]
    for key, value in decision.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Proposed Sandbox", ""])
    for key, value in sandbox.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Allowed Effect If Separately Approved Later", ""])
    for key, value in effect.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Required Vetoes", ""])
    lines.extend(f"- `{item}`" for item in payload["required_vetoes"])
    lines.extend(["", "## Required Validation Before Later Implementation", ""])
    lines.extend(
        f"- `{item}`" for item in payload["required_validation_before_later_implementation"]
    )
    lines.extend(["", "## Explicitly Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
    lines.extend(["", "## Evidence", ""])
    for key, value in evidence.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Remaining Risks", ""])
    lines.extend(f"- `{item}`" for item in payload["remaining_risks"])
    lines.extend(["", "## Possible Statuses", ""])
    lines.extend(f"- `{item}`" for item in payload["possible_statuses"])
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
