#!/usr/bin/env python3
"""Write refined selector-observability runtime review packet v0.

This packet is review-only. It does not implement or authorize behavior-changing
selection, routing, score changes, provider selection, or runtime defaults.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPANDED_RECOMMENDATIONS = Path(
    "reports/strategy_arbitration/krk_selector_observability_expanded_recommendations_v0.json"
)
READINESS_REVIEW = Path(
    "reports/strategy_arbitration/krk_selector_observability_readiness_review_v0.json"
)
PRESERVE_AUDIT = Path(
    "reports/strategy_arbitration/krk_selector_preserve_failure_risk_audit_v0.json"
)
PRESERVE_DECISION = Path(
    "reports/strategy_arbitration/krk_selector_preserve_failure_risk_decision_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_observability_runtime_review_packet_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_observability_runtime_review_packet_v0.md"
)

RECOMMENDED_REFINEMENT_ID = "preserve_only_if_no_selected_owner_failure_risk_terms"

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

FORBIDDEN_ACTIONS = [
    "behavior_changing_selection",
    "routing_changes",
    "score_changes",
    "provider_selection_changes",
    "provider_suppression",
    "runtime_default_changes",
    "stage7_promotion",
    "stage8_training",
    "runtime_dtm_or_tablebase",
    "gameplay_topology_mutation",
    "treating_capacity_labels_as_ownership_labels",
]

POSSIBLE_STATUSES = [
    "refined_selector_observability_runtime_review_ready",
    "refined_selector_observability_needs_more_evidence",
    "refined_selector_observability_blocked",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _refinement_by_id(audit: dict[str, Any], refinement_id: str) -> dict[str, Any]:
    for result in audit.get("refinement_results") or []:
        if result.get("refinement_id") == refinement_id:
            if not isinstance(result, dict):
                break
            return result
    return {}


def _source_terms(summary: dict[str, Any], key: str) -> list[str]:
    coverage = summary.get("source_term_coverage") or {}
    values = coverage.get(key) or []
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def build_payload(
    *,
    expanded: dict[str, Any] | None = None,
    readiness: dict[str, Any] | None = None,
    preserve_audit: dict[str, Any] | None = None,
    preserve_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expanded = expanded or _load(EXPANDED_RECOMMENDATIONS)
    readiness = readiness or _load(READINESS_REVIEW)
    preserve_audit = preserve_audit or _load(PRESERVE_AUDIT)
    preserve_decision = preserve_decision or _load(PRESERVE_DECISION)

    expanded_summary = expanded.get("summary") or {}
    readiness_summary = readiness.get("summary") or {}
    decision_summary = preserve_decision.get("summary") or {}
    audit_decision = preserve_audit.get("decision") or {}
    preserve_decision_block = preserve_decision.get("decision") or {}
    refinement = _refinement_by_id(preserve_audit, RECOMMENDED_REFINEMENT_ID)
    refinement_metrics = refinement.get("metrics") or {}

    false_flags_ok = all(
        preserve_decision.get(key) is False for key in COMMON_FALSE_FLAGS
    ) and all(expanded.get(key) is False for key in COMMON_FALSE_FLAGS if key in expanded)
    no_runtime_deltas = all(
        decision_summary.get(key) == 0
        for key in [
            "selected_move_delta_count",
            "selected_provider_delta_count",
            "score_delta_count",
            "routing_delta_count",
        ]
    )
    constraints_satisfied = (
        audit_decision.get("status") == "preserve_failure_risk_resolved_non_causal"
        and preserve_decision_block.get("status")
        == "preserve_failure_risk_resolved_non_causal"
        and preserve_decision_block.get("future_runtime_review_packet_recommended") is True
        and decision_summary.get("recommended_refinement_id")
        == RECOMMENDED_REFINEMENT_ID
        and refinement.get("eliminates_preserve_on_failure") is True
        and refinement.get("preserves_safe_preservation_recall") is True
        and refinement.get("keeps_switch_on_safe_owner_zero") is True
        and refinement.get("runtime_feature_eligible") is True
        and refinement.get("uses_offline_only_labels") is False
        and refinement_metrics.get("preserve_on_failure_count") == 0
        and refinement_metrics.get("abstain_recall") == 1.0
        and refinement_metrics.get("switch_on_safe_owner_count") == 0
        and decision_summary.get("selector_training_row_count") == 0
        and decision_summary.get("stage7_training_row_count") == 0
        and decision_summary.get("capacity_label_used_as_ownership_label_count") == 0
        and no_runtime_deltas
        and false_flags_ok
    )
    status = (
        "refined_selector_observability_runtime_review_ready"
        if constraints_satisfied
        else "refined_selector_observability_needs_more_evidence"
    )

    return {
        "schema_version": "krk_refined_selector_observability_runtime_review_packet.v0",
        "causal_status": "non_causal_refined_runtime_review_packet",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(EXPANDED_RECOMMENDATIONS),
            str(READINESS_REVIEW),
            str(PRESERVE_AUDIT),
            str(PRESERVE_DECISION),
            "reports/strategy_arbitration/krk_selector_objective_observability_sandbox_v0.json",
        ],
        "proposed_sandbox": {
            "name": "default_off_refined_selector_objective_observability_sandbox",
            "implementation_status": "not_implemented",
            "authorization_status": "review_packet_only_not_approved_for_implementation",
            "default_off": True,
            "opt_in_only": True,
            "opt_in_flag": "--enable-krk-refined-selector-objective-observability",
            "trace_only": True,
            "recommendation_only": True,
            "default_behavior_change": False,
            "base_model": "combined_simple_rule",
            "refinement_id": RECOMMENDED_REFINEMENT_ID,
            "preserve_failure_risk_refinement": (
                "abstain_context_only_when_runtime_visible_failure_risk_terms_are_present"
            ),
            "may_emit_recommendations": [
                "preserve_selected_owner",
                "prefer_visible_alternative",
                "abstain_context_only",
            ],
        },
        "allowed_effect": {
            "emit_recommendation_metadata": True,
            "record_source_terms": True,
            "record_explanation_terms": True,
            "record_selected_owner_before_recommendation": True,
            "record_visible_alternatives": True,
            "direct_request": False,
            "score_delta": 0.0,
            "causal_status": "recommendation_only",
            "selected_move_delta_allowed": False,
            "selected_provider_delta_allowed": False,
            "routing_delta_allowed": False,
            "provider_suppression_allowed": False,
            "runtime_default_change_allowed": False,
        },
        "explicitly_forbidden": FORBIDDEN_ACTIONS,
        "supporting_evidence": {
            "recommendation_class_balance": expanded_summary.get(
                "recommendation_count_by_class"
            ),
            "expanded_attempted_row_count": expanded_summary.get("attempted_row_count"),
            "trace_only_recommendation_count": expanded_summary.get(
                "trace_only_recommendation_count"
            ),
            "preserve_failure_risk_status": audit_decision.get("status"),
            "prior_readiness_status": readiness.get("decision", {}).get("status"),
            "recommended_refinement_id": decision_summary.get("recommended_refinement_id"),
            "refined_prediction_counts": refinement_metrics.get("prediction_counts"),
            "refined_preserve_on_failure_count": refinement_metrics.get(
                "preserve_on_failure_count"
            ),
            "refined_safe_preservation_recall": refinement_metrics.get(
                "safe_preservation_recall"
            ),
            "refined_switch_contrast_recall": refinement_metrics.get(
                "switch_contrast_recall"
            ),
            "refined_abstain_recall": refinement_metrics.get("abstain_recall"),
            "refined_switch_on_safe_owner_count": refinement_metrics.get(
                "switch_on_safe_owner_count"
            ),
            "selector_training_row_count": decision_summary.get(
                "selector_training_row_count"
            ),
            "stage7_training_row_count": decision_summary.get("stage7_training_row_count"),
            "selected_move_delta_count": decision_summary.get("selected_move_delta_count"),
            "selected_provider_delta_count": decision_summary.get(
                "selected_provider_delta_count"
            ),
            "score_delta_count": decision_summary.get("score_delta_count"),
            "routing_delta_count": decision_summary.get("routing_delta_count"),
            "capacity_label_used_as_ownership_label_count": decision_summary.get(
                "capacity_label_used_as_ownership_label_count"
            ),
            "source_terms": _source_terms(expanded_summary, "source_terms"),
            "explanation_terms": _source_terms(expanded_summary, "explanation_terms"),
        },
        "remaining_risks": [
            "small_dataset",
            "recommendation_only_not_selector_training",
            "not_tested_as_behavior_changing_policy",
            "stage7_held_out",
            "switch_contrast_recall_less_than_1_0",
            "candidate_quality_remains_separate_from_selector_quality",
        ],
        "requirements_before_later_implementation": [
            "explicit_approval",
            "default_off_equivalence",
            "no_selected_move_or_provider_delta",
            "score_delta_count_equals_zero",
            "recommendation_only_metadata",
            "focused_tests",
            "full_suite_if_reasonable",
        ],
        "possible_statuses": POSSIBLE_STATUSES,
        "decision": {
            "status": status,
            "implementation_authorized_by_this_packet": False,
            "behavior_changing_selector_allowed": False,
            "runtime_sandbox_authorized_by_this_packet": False,
            "runtime_changes_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "score_changes_allowed": False,
            "routing_changes_allowed": False,
            "provider_selection_changes_allowed": False,
            "provider_suppression_allowed": False,
            "runtime_default_changes_allowed": False,
            "recommended_next_step": (
                "explicit_approval_required_before_default_off_trace_only_refined_observability_sandbox"
                if constraints_satisfied
                else "collect_or_review_more_refined_selector_observability_evidence"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    decision = payload["decision"]
    sandbox = payload["proposed_sandbox"]
    allowed = payload["allowed_effect"]
    evidence = payload["supporting_evidence"]
    lines = [
        "# KRK Refined Selector Observability Runtime Review Packet v0",
        "",
        "This packet reviews a possible future default-off refined selector-objective observability sandbox. It does not implement or authorize behavior-changing selection.",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- implementation_authorized_by_this_packet: `{decision['implementation_authorized_by_this_packet']}`",
        f"- behavior_changing_selector_allowed: `{decision['behavior_changing_selector_allowed']}`",
        f"- runtime_sandbox_authorized_by_this_packet: `{decision['runtime_sandbox_authorized_by_this_packet']}`",
        f"- runtime_changes_allowed: `{decision['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        "",
        "## Proposed Sandbox",
        "",
        f"- name: `{sandbox['name']}`",
        f"- implementation_status: `{sandbox['implementation_status']}`",
        f"- default_off: `{sandbox['default_off']}`",
        f"- opt_in_only: `{sandbox['opt_in_only']}`",
        f"- opt_in_flag: `{sandbox['opt_in_flag']}`",
        f"- trace_only: `{sandbox['trace_only']}`",
        f"- recommendation_only: `{sandbox['recommendation_only']}`",
        f"- base_model: `{sandbox['base_model']}`",
        f"- refinement_id: `{sandbox['refinement_id']}`",
        f"- preserve_failure_risk_refinement: `{sandbox['preserve_failure_risk_refinement']}`",
        f"- may_emit_recommendations: `{sandbox['may_emit_recommendations']}`",
        "",
        "## Allowed Effect If Separately Approved Later",
        "",
        f"- emit_recommendation_metadata: `{allowed['emit_recommendation_metadata']}`",
        f"- record_source_terms: `{allowed['record_source_terms']}`",
        f"- record_explanation_terms: `{allowed['record_explanation_terms']}`",
        f"- record_selected_owner_before_recommendation: `{allowed['record_selected_owner_before_recommendation']}`",
        f"- record_visible_alternatives: `{allowed['record_visible_alternatives']}`",
        f"- direct_request: `{allowed['direct_request']}`",
        f"- score_delta: `{allowed['score_delta']}`",
        f"- causal_status: `{allowed['causal_status']}`",
        f"- selected_move_delta_allowed: `{allowed['selected_move_delta_allowed']}`",
        f"- selected_provider_delta_allowed: `{allowed['selected_provider_delta_allowed']}`",
        "",
        "## Explicitly Forbidden",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
    lines.extend(
        [
            "",
            "## Supporting Evidence",
            "",
            f"- recommendation_class_balance: `{evidence['recommendation_class_balance']}`",
            f"- preserve_failure_risk_status: `{evidence['preserve_failure_risk_status']}`",
            f"- recommended_refinement_id: `{evidence['recommended_refinement_id']}`",
            f"- refined_prediction_counts: `{evidence['refined_prediction_counts']}`",
            f"- refined_preserve_on_failure_count: `{evidence['refined_preserve_on_failure_count']}`",
            f"- refined_safe_preservation_recall: `{evidence['refined_safe_preservation_recall']}`",
            f"- refined_switch_contrast_recall: `{evidence['refined_switch_contrast_recall']}`",
            f"- refined_abstain_recall: `{evidence['refined_abstain_recall']}`",
            f"- refined_switch_on_safe_owner_count: `{evidence['refined_switch_on_safe_owner_count']}`",
            f"- selector_training_row_count: `{evidence['selector_training_row_count']}`",
            f"- stage7_training_row_count: `{evidence['stage7_training_row_count']}`",
            f"- selected_move_delta_count: `{evidence['selected_move_delta_count']}`",
            f"- selected_provider_delta_count: `{evidence['selected_provider_delta_count']}`",
            f"- score_delta_count: `{evidence['score_delta_count']}`",
            f"- routing_delta_count: `{evidence['routing_delta_count']}`",
            f"- capacity_label_used_as_ownership_label_count: `{evidence['capacity_label_used_as_ownership_label_count']}`",
            "",
            "## Remaining Risks",
            "",
        ]
    )
    lines.extend(f"- `{risk}`" for risk in payload["remaining_risks"])
    lines.extend(["", "## Requirements Before Later Implementation", ""])
    lines.extend(f"- `{item}`" for item in payload["requirements_before_later_implementation"])
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
