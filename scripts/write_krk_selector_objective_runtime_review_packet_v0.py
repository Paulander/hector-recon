#!/usr/bin/env python3
"""Write selector-objective runtime review packet v0.

This is a review packet only. It does not implement or authorize a runtime
selector, routing change, score change, provider-selection change, or default
behavior change.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v0.json")
DECISION = Path(
    "reports/strategy_arbitration/krk_selector_objective_benchmark_decision_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_selector_objective_runtime_review_packet_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_selector_objective_runtime_review_packet_v0.md"
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

FORBIDDEN_ACTIONS = [
    "runtime_selector_implementation_in_this_slice",
    "score_changes",
    "routing_changes",
    "provider_selection_changes",
    "provider_suppression",
    "broad_provider_penalties",
    "runtime_default_changes",
    "stage7_promotion",
    "stage8_training",
    "runtime_dtm_or_tablebase",
    "gameplay_time_topology_mutation",
    "state_hash_exceptions",
    "treating_capacity_labels_as_ownership_labels",
    "hidden_python_controller",
    "guardrails_before_target_smoke",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    *,
    benchmark: dict[str, Any] | None = None,
    decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    benchmark = benchmark or _load(BENCHMARK)
    decision = decision or _load(DECISION)
    benchmark_summary = benchmark.get("summary") or {}
    decision_summary = decision.get("summary") or {}
    best_model = str(decision_summary.get("best_model") or benchmark_summary.get("best_model"))
    constraints_satisfied = (
        (decision.get("decision") or {}).get("status")
        == "selector_objective_benchmark_promising_non_causal"
        and best_model == "combined_simple_rule"
        and decision_summary.get("selector_training_row_count") == 0
        and decision_summary.get("stage7_training_row_count") == 0
        and decision_summary.get("runtime_authorization_row_count") == 0
        and (decision.get("decision") or {}).get("selector_allowed") is False
        and (decision.get("decision") or {}).get("runtime_changes_allowed") is False
        and all(decision.get(key) is False for key in COMMON_FALSE_FLAGS)
    )
    status = (
        "selector_runtime_review_packet_ready"
        if constraints_satisfied
        else "selector_runtime_review_needs_more_evidence"
    )
    return {
        "schema_version": "krk_selector_objective_runtime_review_packet.v0",
        "causal_status": "non_causal_runtime_review_packet",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(BENCHMARK),
            str(DECISION),
            "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json",
            "reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json",
            "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_collection_v0.json",
            "reports/current_agent_brief.md",
        ],
        "proposed_sandbox": {
            "name": "default_off_selector_objective_sandbox",
            "implementation_status": "not_implemented",
            "authorization_status": "review_packet_only_not_approved_for_implementation",
            "default_off": True,
            "opt_in_only": True,
            "traceable": True,
            "reversible": True,
            "default_behavior_change": False,
        },
        "allowed_if_separately_approved_later": [
            "observe_current_selected_owner",
            "compute_combined_simple_rule_selector_objective",
            "emit_non_default_recommendation_preserve_selected_owner",
            "emit_non_default_recommendation_prefer_visible_alternative",
            "emit_non_default_recommendation_abstain_context_only",
            "trace_recommendation_inputs_and_outputs",
        ],
        "first_sandbox_scope_if_separately_approved_later": {
            "name": "trace_only_selector_objective_recommendation",
            "implementation_status": "not_implemented",
            "authorization_status": "not_authorized_by_this_packet",
            "may_compute": "combined_simple_rule_selector_objective",
            "may_emit_recommendations": [
                "preserve_selected_owner",
                "prefer_visible_alternative",
                "abstain_context_only",
            ],
            "may_record": [
                "recommendation",
                "explanation_terms",
                "source_terms",
                "selected_owner_observation",
            ],
            "direct_request": False,
            "score_delta": 0.0,
            "selected_move_delta_allowed": False,
            "selected_provider_delta_allowed": False,
            "routing_delta_allowed": False,
            "provider_suppression_allowed": False,
            "runtime_default_change_allowed": False,
            "runtime_effect": "recommendation_only_no_selection",
        },
        "not_authorized_by_this_packet": [
            "implement_runtime_selector",
            "change_runtime_behavior",
            "select_move_or_provider",
            "change_scores_or_routes",
            "suppress_or_penalize_providers",
            "bounded_selection_among_visible_alternatives",
        ],
        "possible_later_separate_sandbox": {
            "name": "bounded_visible_alternative_selection_sandbox",
            "status": "not_authorized_by_this_packet",
            "scope": (
                "A later separately approved sandbox could consider bounded selection among "
                "already-visible alternatives after trace-only evidence and guardrails pass."
            ),
        },
        "explicitly_forbidden": FORBIDDEN_ACTIONS,
        "supporting_evidence": {
            "benchmark_status": decision_summary.get("benchmark_status"),
            "seed_row_count": decision_summary.get("seed_row_count"),
            "target_action_counts": decision_summary.get("target_action_counts"),
            "best_model": best_model,
            "best_accuracy": decision_summary.get("best_accuracy"),
            "safe_preservation_recall": decision_summary.get("best_safe_preservation_recall"),
            "switch_contrast_recall": decision_summary.get("best_switch_contrast_recall"),
            "abstain_recall": decision_summary.get("best_abstain_recall"),
            "promising_runtime_feature_model_count": decision_summary.get(
                "promising_runtime_feature_model_count"
            ),
            "selector_training_row_count": decision_summary.get("selector_training_row_count"),
            "stage7_training_row_count": decision_summary.get("stage7_training_row_count"),
            "runtime_authorization_row_count": decision_summary.get(
                "runtime_authorization_row_count"
            ),
            "capacity_labels_are_not_ownership_labels": True,
        },
        "remaining_risks": [
            "small_seed",
            "possible_overfitting_to_hand_built_labels",
            "switch_contrast_recall_less_than_1_0",
            "stage7_held_out_not_training",
            "runtime_feature_eligibility_must_be_checked_carefully",
            "generated_candidate_quality_still_separate_from_selector_quality",
            "capacity_labels_are_not_ownership_labels",
        ],
        "future_sandbox_envelope_before_implementation": [
            "explicit_flag",
            "default_off_equivalence",
            "no_selected_move_delta_in_observation_mode",
            "no_selected_provider_delta_in_observation_mode",
            "trace_only_first",
            "report_recommendation_only",
            "no_score_changes",
            "no_routing_changes",
            "target_smoke_before_any_guardrails",
            "guardrails_before_promotion",
            "rollback_plan",
        ],
        "possible_statuses": [
            "selector_runtime_review_packet_ready",
            "selector_runtime_review_needs_more_evidence",
            "selector_runtime_review_blocked",
        ],
        "decision": {
            "status": status,
            "implementation_authorized_by_this_packet": False,
            "runtime_sandbox_authorized_by_this_packet": False,
            "runtime_review_packet_allowed_next": constraints_satisfied,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "score_changes_allowed": False,
            "routing_changes_allowed": False,
            "provider_selection_changes_allowed": False,
            "provider_suppression_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "explicit_approval_required_before_default_off_trace_only_sandbox"
                if constraints_satisfied
                else "collect_or_review_more_non_causal_selector_objective_evidence"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    ev = payload["supporting_evidence"]
    sandbox = payload["proposed_sandbox"]
    lines = [
        "# KRK Selector Objective Runtime Review Packet v0",
        "",
        "This packet reviews a possible future default-off selector-objective sandbox. It does not implement or authorize runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- implementation_authorized_by_this_packet: `{payload['decision']['implementation_authorized_by_this_packet']}`",
        f"- runtime_sandbox_authorized_by_this_packet: `{payload['decision']['runtime_sandbox_authorized_by_this_packet']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Proposed Sandbox",
        "",
        f"- name: `{sandbox['name']}`",
        f"- default_off: `{sandbox['default_off']}`",
        f"- opt_in_only: `{sandbox['opt_in_only']}`",
        f"- traceable: `{sandbox['traceable']}`",
        f"- reversible: `{sandbox['reversible']}`",
        f"- default_behavior_change: `{sandbox['default_behavior_change']}`",
        "",
        "## First Sandbox Scope If Separately Approved Later",
        "",
        f"- name: `{payload['first_sandbox_scope_if_separately_approved_later']['name']}`",
        f"- may_compute: `{payload['first_sandbox_scope_if_separately_approved_later']['may_compute']}`",
        f"- may_emit_recommendations: `{payload['first_sandbox_scope_if_separately_approved_later']['may_emit_recommendations']}`",
        f"- may_record: `{payload['first_sandbox_scope_if_separately_approved_later']['may_record']}`",
        f"- direct_request: `{payload['first_sandbox_scope_if_separately_approved_later']['direct_request']}`",
        f"- score_delta: `{payload['first_sandbox_scope_if_separately_approved_later']['score_delta']}`",
        f"- selected_move_delta_allowed: `{payload['first_sandbox_scope_if_separately_approved_later']['selected_move_delta_allowed']}`",
        f"- selected_provider_delta_allowed: `{payload['first_sandbox_scope_if_separately_approved_later']['selected_provider_delta_allowed']}`",
        f"- runtime_effect: `{payload['first_sandbox_scope_if_separately_approved_later']['runtime_effect']}`",
        "",
        "## Allowed Only If Separately Approved Later",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["allowed_if_separately_approved_later"])
    lines.extend(["", "## Not Authorized By This Packet", ""])
    lines.extend(f"- `{item}`" for item in payload["not_authorized_by_this_packet"])
    lines.extend(["", "## Explicitly Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
    lines.extend(
        [
            "",
            "## Supporting Evidence",
            "",
            f"- benchmark_status: `{ev['benchmark_status']}`",
            f"- seed_row_count: `{ev['seed_row_count']}`",
            f"- target_action_counts: `{ev['target_action_counts']}`",
            f"- best_model: `{ev['best_model']}`",
            f"- best_accuracy: `{ev['best_accuracy']}`",
            f"- safe_preservation_recall: `{ev['safe_preservation_recall']}`",
            f"- switch_contrast_recall: `{ev['switch_contrast_recall']}`",
            f"- abstain_recall: `{ev['abstain_recall']}`",
            f"- selector_training_row_count: `{ev['selector_training_row_count']}`",
            f"- stage7_training_row_count: `{ev['stage7_training_row_count']}`",
            f"- runtime_authorization_row_count: `{ev['runtime_authorization_row_count']}`",
            "",
            "## Remaining Risks",
            "",
        ]
    )
    lines.extend(f"- `{risk}`" for risk in payload["remaining_risks"])
    lines.extend(["", "## Future Sandbox Envelope Before Implementation", ""])
    lines.extend(f"- `{item}`" for item in payload["future_sandbox_envelope_before_implementation"])
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
