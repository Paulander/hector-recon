#!/usr/bin/env python3
"""Write selector behavior regression audit and decision artifacts v0.

This audit is post-hoc and non-causal. It does not implement or authorize a
selector behavior fix.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SMOKE_REPORT = Path("reports/strategy_arbitration/krk_selector_behavior_sandbox_v0.json")
VALIDATION_REPORT = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.json"
)
AUDIT_JSON = Path(
    "reports/strategy_arbitration/krk_selector_behavior_regression_audit_v0.json"
)
AUDIT_MD = Path(
    "reports/strategy_arbitration/krk_selector_behavior_regression_audit_v0.md"
)
DECISION_JSON = Path(
    "reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.json"
)
DECISION_MD = Path(
    "reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.md"
)

POSSIBLE_DECISIONS = [
    "selector_behavior_quarantined_due_to_safe_regression",
    "selector_behavior_can_be_narrowed_with_veto_review",
    "selector_behavior_needs_more_observability_data",
    "selector_behavior_regression_due_to_bug",
    "selector_behavior_path_architecture_review_required",
]

CAUSE_CLASSES = [
    "recommendation_wrong",
    "alternative_selection_wrong",
    "safe_preservation_veto_missing",
    "visible_alternative_overtrusted",
    "label_semantics_mismatch",
    "horizon/noise issue",
    "implementation bug",
]

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_score_changes": False,
    "runtime_provider_suppression": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "runtime_selector_implemented": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
    "fix_implemented": False,
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _visible_alternatives(decision: dict[str, Any]) -> list[dict[str, Any]]:
    rec = decision.get("selector_recommendation") or {}
    alternatives = rec.get("visible_alternatives_considered") or []
    return [item for item in alternatives if isinstance(item, dict)]


def _compact_visible_alternatives(decision: dict[str, Any]) -> list[dict[str, Any]]:
    compact = []
    for item in _visible_alternatives(decision):
        compact.append(
            {
                "provider_id": item.get("provider_id"),
                "provider_family": item.get("provider_family"),
                "move_id": item.get("move_id"),
                "candidate_source": item.get("candidate_source"),
                "capacity_evidence_kind": item.get("capacity_evidence_kind"),
                "label_semantics": item.get("label_semantics"),
                "causal_status": item.get("causal_status"),
                "stage": item.get("stage"),
                "direct_request": item.get("direct_request"),
                "score_delta": item.get("score_delta"),
            }
        )
    return compact


def _recommendation(decision: dict[str, Any]) -> dict[str, Any]:
    rec = decision.get("selector_recommendation") or {}
    return rec if isinstance(rec, dict) else {}


def _behavior(decision: dict[str, Any]) -> dict[str, Any]:
    behavior = decision.get("behavior_sandbox_decision") or {}
    return behavior if isinstance(behavior, dict) else {}


def _row_terms(row: dict[str, Any]) -> dict[str, Any]:
    rec = _recommendation(row.get("enabled_decision") or {})
    behavior = _behavior(row.get("enabled_decision") or {})
    return {
        "active_landmark_label": rec.get("active_landmark_label")
        or row.get("active_landmark_label"),
        "support_bucket": rec.get("support_bucket"),
        "edge_bucket": rec.get("edge_bucket"),
        "box_area_relevance": rec.get("box_area_relevance"),
        "selected_piece": rec.get("selected_piece"),
        "positive_trace_count_bucket": rec.get("positive_trace_count_bucket"),
        "positive_trace_provider_candidate_count": rec.get(
            "positive_trace_provider_candidate_count"
        ),
        "candidate_source_values": sorted(
            {
                str(item.get("candidate_source"))
                for item in _visible_alternatives(row.get("enabled_decision") or {})
                if item.get("candidate_source")
            }
        ),
        "selected_owner_family": row.get("selected_owner_label"),
        "selected_provider_family": (
            str(row.get("selected_provider_label")).split(".")[-1]
            if row.get("selected_provider_label")
            else None
        ),
        "source_terms": list(behavior.get("source_terms") or rec.get("source_terms") or []),
        "explanation_terms": list(
            behavior.get("explanation_terms") or rec.get("explanation_terms") or []
        ),
    }


def _baseline_enabled_outcome(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "baseline_outcome": row.get("h40_default_off"),
        "enabled_outcome": row.get("h40_enabled"),
        "direct_safe_regression": row.get("direct_safe_regression"),
        "h40_safe_regression": row.get("h40_safe_regression"),
        "h40_regressed": row.get("h40_regressed"),
        "h40_improved": row.get("h40_improved"),
    }


def _regressed_row(row: dict[str, Any]) -> dict[str, Any]:
    enabled = row.get("enabled_decision") or {}
    flag_off = row.get("flag_off_decision") or {}
    rec = _recommendation(enabled)
    behavior = _behavior(enabled)
    return {
        "row_id": row.get("row_id"),
        "case_id": row.get("case_id"),
        "state_id": row.get("state_id"),
        "frame_id": row.get("frame_id"),
        "fen": row.get("fen"),
        "stage": row.get("source_stage"),
        "h40_validation_role": row.get("h40_validation_role"),
        "selected_owner_before_sandbox": row.get("selected_owner_label"),
        "selected_provider_before_sandbox": flag_off.get("selected_provider")
        or row.get("selected_provider_label"),
        "selected_move_before_sandbox": flag_off.get("move"),
        "sandbox_action": behavior.get("action") or row.get("behavior_action"),
        "sandbox_replacement_owner": behavior.get("replacement_provider")
        or row.get("replacement_provider"),
        "sandbox_replacement_move": behavior.get("replacement_move"),
        "sandbox_veto_reason": behavior.get("veto_reason")
        or row.get("behavior_veto_reason"),
        "recommendation_class": rec.get("recommendation") or row.get("recommendation"),
        "visible_alternatives": _compact_visible_alternatives(enabled),
        "source_terms": list(behavior.get("source_terms") or rec.get("source_terms") or []),
        "explanation_terms": list(
            behavior.get("explanation_terms") or rec.get("explanation_terms") or []
        ),
        **_baseline_enabled_outcome(row),
        "first_row_switch_observed": row.get("behavior_action")
        == "switch_to_visible_alternative",
        "interpretation": (
            "The protected safe-control state did not switch on the first selector "
            "decision; it preserved the selected owner. The regression appears only "
            "in the enabled h40 continuation, so the saved data is insufficient to "
            "name a specific replacement move/provider as the direct cause."
        ),
        "terms": _row_terms(row),
    }


def _successful_switch(row: dict[str, Any]) -> dict[str, Any]:
    enabled = row.get("enabled_decision") or {}
    flag_off = row.get("flag_off_decision") or {}
    behavior = _behavior(enabled)
    rec = _recommendation(enabled)
    return {
        "row_id": row.get("row_id"),
        "case_id": row.get("case_id"),
        "state_id": row.get("state_id"),
        "stage": row.get("source_stage"),
        "selected_owner_before_sandbox": row.get("selected_owner_label"),
        "selected_provider_before_sandbox": flag_off.get("selected_provider"),
        "selected_move_before_sandbox": flag_off.get("move"),
        "sandbox_replacement_owner": behavior.get("replacement_provider"),
        "sandbox_replacement_move": behavior.get("replacement_move"),
        "recommendation_class": rec.get("recommendation"),
        "target_improved": row.get("target_improved"),
        "visible_alternatives": _compact_visible_alternatives(enabled),
        "terms": _row_terms(row),
    }


def _summarize_values(rows: list[dict[str, Any]], field_path: tuple[str, ...]) -> list[Any]:
    values = set()
    for row in rows:
        current: Any = row
        for field in field_path:
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(field)
        if current is not None:
            if isinstance(current, list):
                values.update(item for item in current if item is not None)
            else:
                values.add(current)
    return sorted(values)


def _build_comparison(
    regressions: list[dict[str, Any]], successes: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "successful_switch_count": len(successes),
        "regressed_safe_control_count": len(regressions),
        "successful_switches": successes,
        "observed_separators": {
            "owner_label": {
                "successful_switch_values": _summarize_values(
                    successes, ("selected_owner_before_sandbox",)
                ),
                "regressed_values": _summarize_values(
                    regressions, ("selected_owner_before_sandbox",)
                ),
                "assessment": (
                    "Successful switches came from selected_owner_failed rows; the "
                    "regression row was selected_owner_converted."
                ),
            },
            "first_row_action": {
                "successful_switch_values": _summarize_values(
                    successes, ("recommendation_class",)
                ),
                "regressed_values": _summarize_values(
                    regressions, ("recommendation_class",)
                ),
                "assessment": (
                    "Successful rows had prefer_visible_alternative and a first-row "
                    "switch; the regression row preserved selected owner on the first "
                    "decision and regressed later in h40."
                ),
            },
            "stage_and_landmark": {
                "successful_stages": _summarize_values(successes, ("stage",)),
                "regressed_stages": _summarize_values(regressions, ("stage",)),
                "successful_landmarks": _summarize_values(
                    successes, ("terms", "active_landmark_label")
                ),
                "regressed_landmarks": _summarize_values(
                    regressions, ("terms", "active_landmark_label")
                ),
            },
            "support_edge_box_king_terms": {
                "successful_support_buckets": _summarize_values(
                    successes, ("terms", "support_bucket")
                ),
                "regressed_support_buckets": _summarize_values(
                    regressions, ("terms", "support_bucket")
                ),
                "successful_edge_buckets": _summarize_values(
                    successes, ("terms", "edge_bucket")
                ),
                "regressed_edge_buckets": _summarize_values(
                    regressions, ("terms", "edge_bucket")
                ),
                "successful_box_area_relevance": _summarize_values(
                    successes, ("terms", "box_area_relevance")
                ),
                "regressed_box_area_relevance": _summarize_values(
                    regressions, ("terms", "box_area_relevance")
                ),
                "successful_selected_pieces": _summarize_values(
                    successes, ("terms", "selected_piece")
                ),
                "regressed_selected_pieces": _summarize_values(
                    regressions, ("terms", "selected_piece")
                ),
            },
            "positive_trace_and_source": {
                "successful_positive_count_buckets": _summarize_values(
                    successes, ("terms", "positive_trace_count_bucket")
                ),
                "regressed_positive_count_buckets": _summarize_values(
                    regressions, ("terms", "positive_trace_count_bucket")
                ),
                "successful_candidate_sources": _summarize_values(
                    successes, ("terms", "candidate_source_values")
                ),
                "regressed_candidate_sources": _summarize_values(
                    regressions, ("terms", "candidate_source_values")
                ),
            },
        },
        "separation_assessment": (
            "The available first-row metadata separates successful target switches "
            "from the safe-control row, but the actual regression is a later h40 "
            "continuation effect. That prevents a clean causal narrowing rule from "
            "this artifact alone."
        ),
    }


def _fix_evaluation() -> list[dict[str, Any]]:
    return [
        {
            "fix": "add safe-preservation veto",
            "assessment": "promising_but_not_sufficient_from_current_data",
            "reason": (
                "The regressed row is an offline safe-preservation control, but using "
                "that label directly at runtime would violate label semantics. A "
                "runtime-visible proxy needs a separate review."
            ),
        },
        {
            "fix": "require stronger failure-risk evidence before switch",
            "assessment": "needs_more_continuation_observability",
            "reason": (
                "The first-row decision did not switch, so stronger first-row evidence "
                "would not explain the h40 continuation regression without tracing "
                "later enabled decisions."
            ),
        },
        {
            "fix": "require target row class / switch-contrast scope",
            "assessment": "not_runtime_eligible_as_stated",
            "reason": (
                "Target row class is an audit label, not a runtime-visible ownership "
                "label. It can scope future tests but should not become behavior logic."
            ),
        },
        {
            "fix": "abstain instead of switching on ambiguous patterns",
            "assessment": "promising_only_after_terms_are_identified",
            "reason": (
                "Ambiguity terms must be runtime-visible and must capture the later "
                "continuation switch, not just the protected row's first decision."
            ),
        },
        {
            "fix": "restrict to exact recommendation/evidence class that improved earlier",
            "assessment": "overfit_risk",
            "reason": (
                "The two successful switches are a tiny sample and do not cover h40 "
                "continuation behavior on protected safe controls."
            ),
        },
        {
            "fix": "quarantine behavior selector if separation is not clean",
            "assessment": "recommended_now",
            "reason": (
                "Protected validation produced one safe-control regression and no "
                "h40 improvements. Quarantine prevents promoting an unsafe causal path."
            ),
        },
    ]


def build_audit_payload(
    *,
    validation_report: dict[str, Any] | None = None,
    smoke_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation_report = validation_report or _load(VALIDATION_REPORT)
    smoke_report = smoke_report or _load(SMOKE_REPORT)
    validation_summary = validation_report.get("summary") or {}
    smoke_summary = smoke_report.get("summary") or {}
    regression_rows = [
        _regressed_row(row)
        for row in validation_report.get("rows") or []
        if row.get("safe_regression") or row.get("h40_safe_regression")
    ]
    successful_switches = [
        _successful_switch(row)
        for row in smoke_report.get("rows") or []
        if row.get("behavior_action") == "switch_to_visible_alternative"
        and row.get("target_improved") is True
    ]

    return {
        "schema_version": "krk_selector_behavior_regression_audit.v0",
        "causal_status": "non_causal_post_validation_regression_audit",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(SMOKE_REPORT), str(VALIDATION_REPORT)],
        "summary": {
            "validation_decision_status": validation_report.get("decision", {}).get(
                "status"
            ),
            "smoke_decision_status": smoke_report.get("decision", {}).get("status"),
            "regressed_safe_control_count": len(regression_rows),
            "successful_switch_count": len(successful_switches),
            "sample_scope": validation_summary.get("sample_scope"),
            "sample_count": validation_summary.get("sample_count"),
            "enabled_switch_count": validation_summary.get("enabled_switch_count"),
            "target_improvement_count": validation_summary.get(
                "target_improvement_count"
            ),
            "safe_regression_count": validation_summary.get("safe_regression_count"),
            "h40_regression_count": validation_summary.get("h40_regression_count"),
            "h40_improvement_count": validation_summary.get("h40_improvement_count"),
            "preserve_noop_count": validation_summary.get("preserve_noop_count"),
            "abstain_noop_count": validation_summary.get("abstain_noop_count"),
            "stage7_training_row_count": validation_summary.get(
                "stage7_training_row_count"
            ),
            "selector_training_row_count": validation_summary.get(
                "selector_training_row_count"
            ),
            "capacity_label_used_as_ownership_label_count": validation_summary.get(
                "capacity_label_used_as_ownership_label_count"
            ),
            "smoke_target_improvement_count": smoke_summary.get(
                "target_improvement_count"
            ),
            "smoke_safe_regression_count": smoke_summary.get("safe_regression_count"),
        },
        "regressed_safe_control_rows": regression_rows,
        "regression_cause_classification": {
            "allowed_classes": CAUSE_CLASSES,
            "primary_causes": [
                "safe_preservation_veto_missing",
                "visible_alternative_overtrusted",
                "horizon/noise issue",
            ],
            "rejected_or_unproven_causes": {
                "recommendation_wrong": (
                    "Unproven for the protected first row because the recommendation "
                    "was preserve_selected_owner."
                ),
                "alternative_selection_wrong": (
                    "Unproven from saved row data because no first-row replacement was "
                    "selected on the regressed row."
                ),
                "label_semantics_mismatch": (
                    "A risk for any future veto design, but the validation artifact "
                    "kept capacity labels separate from ownership labels."
                ),
                "implementation bug": (
                    "No invalid switch, score delta, routing delta, DTM/tablebase "
                    "lookup, or topology mutation was observed."
                ),
            },
            "explanation": (
                "The regression is a protected h40 safe-control regression without a "
                "first-position switch. The cause is therefore classified as a missing "
                "safe-preservation/continuation veto plus overtrust in visible "
                "alternatives under limited-horizon validation, not as a demonstrated "
                "implementation bug."
            ),
        },
        "successful_switch_comparison": _build_comparison(
            regression_rows, successful_switches
        ),
        "non_causal_fix_evaluation": _fix_evaluation(),
        "decision_recommendation": "selector_behavior_quarantined_due_to_safe_regression",
        "possible_decisions": POSSIBLE_DECISIONS,
    }


def build_decision_payload(audit: dict[str, Any] | None = None) -> dict[str, Any]:
    audit = audit or build_audit_payload()
    summary = audit.get("summary") or {}
    status = "selector_behavior_quarantined_due_to_safe_regression"
    return {
        "schema_version": "krk_selector_behavior_regression_decision.v0",
        "causal_status": "non_causal_regression_decision_no_runtime_fix",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(AUDIT_JSON),
            str(SMOKE_REPORT),
            str(VALIDATION_REPORT),
        ],
        "possible_decisions": POSSIBLE_DECISIONS,
        "decision": {
            "status": status,
            "promote": False,
            "make_default": False,
            "implement_fix_now": False,
            "write_narrowing_review_packet_now": False,
            "run_full_broad_guardrails": False,
            "train_anything": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "quarantine_behavior_selector_and_collect_continuation_observability_"
                "before_any_narrowing_or_veto_review"
            ),
        },
        "evidence": {
            "regressed_safe_control_count": summary.get("regressed_safe_control_count"),
            "successful_switch_count": summary.get("successful_switch_count"),
            "protected_safe_regression_row_ids": [
                row.get("row_id")
                for row in audit.get("regressed_safe_control_rows") or []
            ],
            "enabled_switch_count_on_protected_sample": summary.get(
                "enabled_switch_count"
            ),
            "target_improvement_count_on_protected_sample": summary.get(
                "target_improvement_count"
            ),
            "h40_regression_count": summary.get("h40_regression_count"),
            "h40_improvement_count": summary.get("h40_improvement_count"),
            "stage7_training_row_count": summary.get("stage7_training_row_count"),
            "selector_training_row_count": summary.get("selector_training_row_count"),
            "capacity_label_used_as_ownership_label_count": summary.get(
                "capacity_label_used_as_ownership_label_count"
            ),
            "runtime_behavior_changed": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
        },
        "rationale": (
            "Protected validation found one safe-control h40 regression and no h40 "
            "improvements. Because the regression row did not switch on the first "
            "decision, the current artifacts do not provide a clean causal separator "
            "for a narrow fix. The behavior selector should remain quarantined rather "
            "than narrowed or promoted."
        ),
    }


def _format_dict_items(items: dict[str, Any]) -> list[str]:
    return [f"- {key}: `{value}`" for key, value in items.items()]


def write_audit_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    causes = payload["regression_cause_classification"]
    comparison = payload["successful_switch_comparison"]
    lines = [
        "# KRK Selector Behavior Regression Audit v0",
        "",
        "This is a non-causal audit of the protected validation regression. It does not implement a fix or authorize runtime behavior changes.",
        "",
        "## Summary",
        "",
    ]
    lines.extend(_format_dict_items(summary))
    lines.extend(["", "## Regressed Safe-Control Row", ""])
    for row in payload["regressed_safe_control_rows"]:
        lines.append(f"- row_id: `{row['row_id']}`")
        lines.append(f"- state_id: `{row['state_id']}`")
        lines.append(f"- stage: `{row['stage']}`")
        lines.append(
            f"- selected_before: `{row['selected_owner_before_sandbox']} / {row['selected_provider_before_sandbox']} / {row['selected_move_before_sandbox']}`"
        )
        lines.append(
            f"- replacement: `{row['sandbox_replacement_owner']} / {row['sandbox_replacement_move']}`"
        )
        lines.append(f"- recommendation_class: `{row['recommendation_class']}`")
        lines.append(f"- baseline_outcome: `{row['baseline_outcome']}`")
        lines.append(f"- enabled_outcome: `{row['enabled_outcome']}`")
        lines.append(f"- interpretation: {row['interpretation']}")
    lines.extend(["", "## Cause Classification", ""])
    lines.append(f"- primary_causes: `{causes['primary_causes']}`")
    lines.append(f"- explanation: {causes['explanation']}")
    lines.extend(["", "## Successful Switch Comparison", ""])
    lines.append(f"- successful_switch_count: `{comparison['successful_switch_count']}`")
    lines.append(f"- regressed_safe_control_count: `{comparison['regressed_safe_control_count']}`")
    lines.append(f"- separation_assessment: {comparison['separation_assessment']}")
    for row in comparison["successful_switches"]:
        lines.append(
            f"- successful_switch: `{row['row_id']}` `{row['stage']}` `{row['selected_owner_before_sandbox']}` `{row['selected_move_before_sandbox']} -> {row['sandbox_replacement_move']}`"
        )
    lines.extend(["", "## Non-Causal Fix Evaluation", ""])
    for item in payload["non_causal_fix_evaluation"]:
        lines.append(f"- {item['fix']}: `{item['assessment']}` - {item['reason']}")
    lines.extend(["", "## Recommendation", ""])
    lines.append(f"- decision_recommendation: `{payload['decision_recommendation']}`")
    (ROOT / AUDIT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Behavior Regression Decision v0",
        "",
        "This decision records the result of the regression audit. It does not implement a fix or authorize runtime behavior changes.",
        "",
        "## Decision",
        "",
    ]
    lines.extend(_format_dict_items(payload["decision"]))
    lines.extend(["", "## Evidence", ""])
    lines.extend(_format_dict_items(payload["evidence"]))
    lines.extend(["", "## Rationale", "", payload["rationale"], ""])
    (ROOT / DECISION_MD).write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    audit = build_audit_payload()
    decision = build_decision_payload(audit)
    (ROOT / AUDIT_JSON).write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ROOT / DECISION_JSON).write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_audit_markdown(audit)
    write_decision_markdown(decision)
    print(AUDIT_JSON)
    print(AUDIT_MD)
    print(DECISION_JSON)
    print(DECISION_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
