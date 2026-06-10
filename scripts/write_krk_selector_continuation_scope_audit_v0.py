#!/usr/bin/env python3
"""Write selector continuation-scope audit and decision artifacts v0.

This is a non-causal review packet. It does not implement a selector fix,
change runtime defaults, or unquarantine selector behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROOT_CAUSE = Path(
    "reports/strategy_arbitration/"
    "krk_selector_behavior_continuation_regression_root_cause_v0.json"
)
SMOKE = Path("reports/strategy_arbitration/krk_selector_behavior_sandbox_v0.json")
VALIDATION = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.json"
)
OUT_AUDIT_JSON = Path(
    "reports/strategy_arbitration/krk_selector_continuation_scope_audit_v0.json"
)
OUT_AUDIT_MD = Path(
    "reports/strategy_arbitration/krk_selector_continuation_scope_audit_v0.md"
)
OUT_DECISION_JSON = Path(
    "reports/strategy_arbitration/krk_selector_continuation_scope_decision_v0.json"
)
OUT_DECISION_MD = Path(
    "reports/strategy_arbitration/krk_selector_continuation_scope_decision_v0.md"
)

POSSIBLE_DECISIONS = [
    "selector_scope_initial_owner_only_supported",
    "selector_scope_needs_continuation_window_monitor",
    "selector_scope_regression_requires_quarantine",
    "selector_scope_needs_more_evidence",
    "selector_behavior_path_architecture_review_required",
]

COMMON_FALSE_FLAGS = {
    "production_runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "selector_unquarantined": False,
    "production_fix_implemented": False,
    "thresholds_tuned": False,
    "stage8_training_allowed": False,
    "stage7_promotion_allowed": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _successful_switches(smoke: dict[str, Any]) -> list[dict[str, Any]]:
    switches = []
    for row in smoke.get("rows") or []:
        if row.get("behavior_action") != "switch_to_visible_alternative":
            continue
        enabled = row.get("enabled_decision") or {}
        behavior = enabled.get("behavior_sandbox_decision") or {}
        rec = enabled.get("selector_recommendation") or {}
        flag_off = row.get("flag_off_decision") or {}
        switches.append(
            {
                "row_id": row.get("row_id"),
                "state_id": row.get("state_id"),
                "decision_window": "initial_owner_choice",
                "ply": 0,
                "selected_owner_before_sandbox": row.get("selected_owner_label"),
                "raw_selected_provider": flag_off.get("selected_provider"),
                "raw_selected_move": flag_off.get("move"),
                "replacement_provider": behavior.get("replacement_provider"),
                "replacement_move": behavior.get("replacement_move"),
                "recommendation_class": rec.get("recommendation"),
                "active_landmark_label": rec.get("active_landmark_label")
                or row.get("active_landmark_label"),
                "support_bucket": rec.get("support_bucket"),
                "edge_bucket": rec.get("edge_bucket"),
                "box_area_relevance": rec.get("box_area_relevance"),
                "selected_piece": rec.get("selected_piece"),
                "positive_trace_provider_candidate_count": rec.get(
                    "positive_trace_provider_candidate_count"
                ),
                "positive_trace_count_bucket": rec.get("positive_trace_count_bucket"),
                "source_terms": list(behavior.get("source_terms") or rec.get("source_terms") or []),
                "explanation_terms": list(
                    behavior.get("explanation_terms") or rec.get("explanation_terms") or []
                ),
                "target_improved": row.get("target_improved"),
            }
        )
    return switches


def _safe_preservation_rows(validation: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in validation.get("rows") or []:
        if row.get("h40_validation_role") != "safe_preservation":
            continue
        rows.append(
            {
                "row_id": row.get("row_id"),
                "state_id": row.get("state_id"),
                "stage": row.get("source_stage"),
                "selected_owner_before_sandbox": row.get("selected_owner_label"),
                "recommendation_class": row.get("recommendation"),
                "behavior_action": row.get("behavior_action"),
                "h40_default_off": row.get("h40_default_off"),
                "h40_enabled": row.get("h40_enabled"),
                "h40_safe_regression": row.get("h40_safe_regression"),
            }
        )
    return rows


def _continuation_rows(root_cause: dict[str, Any]) -> list[dict[str, Any]]:
    variants = {
        item.get("variant"): item
        for item in root_cause.get("variant_traces") or []
        if isinstance(item, dict)
    }
    behavior = variants.get("selector_behavior_enabled_cached") or {}
    rows = []
    for event in behavior.get("white_events") or []:
        if int(event.get("ply", 0) or 0) == 0:
            continue
        if event.get("recommendation") not in {"preserve_selected_owner", "abstain_context_only"}:
            continue
        rows.append(
            {
                "ply": event.get("ply"),
                "fen": event.get("fen"),
                "selected_provider": event.get("selected_provider"),
                "move": event.get("move"),
                "recommendation_class": event.get("recommendation"),
                "behavior_action": event.get("behavior_action"),
                "behavior_veto_reason": event.get("behavior_veto_reason"),
            }
        )
    return rows


def _regression_case(root_cause: dict[str, Any]) -> dict[str, Any]:
    divergence = root_cause["first_divergence"]
    enabled = divergence["enabled"]
    control = divergence["control"]
    observed = root_cause["observed_vs_expected"]
    return {
        "row_id": root_cause["minimal_reproduction"]["row_id"],
        "state_id": root_cause["minimal_reproduction"]["state_id"],
        "ply": divergence["ply"],
        "fen_at_ply": enabled.get("fen"),
        "active_selected_owner_before_switch": enabled.get("original_provider"),
        "raw_selected_provider": enabled.get("original_provider"),
        "raw_selected_move": enabled.get("original_move"),
        "selector_replacement_provider": enabled.get("replacement_provider"),
        "selector_replacement_move": enabled.get("replacement_move"),
        "recommendation_class": enabled.get("recommendation"),
        "active_landmark": "fence_established",
        "plan_context": "active_h40_continuation_after_initial_owner_choice",
        "continuation_context": {
            "white_ply": divergence["ply"],
            "is_initial_owner_choice": False,
            "control_provider": control.get("selected_provider"),
            "control_move": control.get("move"),
            "enabled_provider": enabled.get("selected_provider"),
            "enabled_move": enabled.get("move"),
            "recommendation_reason": enabled.get("recommendation_reason"),
            "why_selected_alternative": enabled.get("why_selected_alternative"),
        },
        "source_terms": sorted(
            {
                term
                for item in enabled.get("visible_alternatives") or []
                for term in [
                    item.get("candidate_source"),
                    item.get("capacity_evidence_kind"),
                    item.get("label_semantics"),
                    item.get("causal_status"),
                    item.get("provider_family"),
                ]
                if term
            }
        ),
        "explanation_terms": list(enabled.get("recommendation_terms") or []),
        "baseline_continuation_outcome": observed.get("control_result"),
        "enabled_continuation_outcome": observed.get("selector_behavior_enabled_result"),
        "observability_only_outcome": observed.get("selector_observability_only_result"),
    }


def _scope_rule_evaluations(root_cause: dict[str, Any], smoke: dict[str, Any], validation: dict[str, Any]) -> list[dict[str, Any]]:
    regression = _regression_case(root_cause)
    smoke_summary = smoke.get("summary") or {}
    validation_summary = validation.get("summary") or {}
    return [
        {
            "rule": "selector allowed only at initial decision / ply 0",
            "classification": "supported_for_future_review",
            "would_preserve_prior_target_improvements": True,
            "would_eliminate_safe_control_regression": True,
            "runtime_feature_eligible": True,
            "evidence": (
                "Both observed target improvements are initial single-decision switches; "
                f"the protected regression switch occurs at ply {regression['ply']}."
            ),
        },
        {
            "rule": "selector blocked when current provider is in an active continuation window",
            "classification": "supported_but_needs_monitor_definition",
            "would_preserve_prior_target_improvements": True,
            "would_eliminate_safe_control_regression": True,
            "runtime_feature_eligible": "partially",
            "evidence": (
                "The regression overrides an active fence-established continuation. "
                "A runtime-safe continuation-window monitor must be defined without "
                "offline owner labels."
            ),
        },
        {
            "rule": "selector blocked when selected owner has recent progress",
            "classification": "promising_but_requires_runtime_progress_proxy",
            "would_preserve_prior_target_improvements": "unknown",
            "would_eliminate_safe_control_regression": True,
            "runtime_feature_eligible": "partially",
            "evidence": (
                "The raw e8a8 continuation has positive goal_progress while e8b8 has "
                "negative goal_progress, but the exact safe progress proxy needs review."
            ),
        },
        {
            "rule": "selector blocked when plan/edge/fence continuation is active",
            "classification": "supported_but_broader_than_ply0_only",
            "would_preserve_prior_target_improvements": "likely",
            "would_eliminate_safe_control_regression": True,
            "runtime_feature_eligible": "partially",
            "evidence": (
                "The regression switches away from fence_established to edge_trap_close "
                "inside an h40 continuation. Broad plan-family gates risk suppressing "
                "valid future switches unless scoped."
            ),
        },
        {
            "rule": "selector may only recommend abstain during continuation unless failure-risk monitor fires",
            "classification": "needs_more_evidence",
            "would_preserve_prior_target_improvements": True,
            "would_eliminate_safe_control_regression": True,
            "runtime_feature_eligible": "partially",
            "evidence": (
                "This is compatible with quarantine, but the failure-risk monitor is "
                "not yet proven on continuation states."
            ),
        },
        {
            "rule": "current quarantined selector_behavior path",
            "classification": "unsafe_as_implemented",
            "would_preserve_prior_target_improvements": bool(
                smoke_summary.get("target_improvement_count")
            ),
            "would_eliminate_safe_control_regression": False,
            "runtime_feature_eligible": False,
            "evidence": (
                f"Protected validation has safe_regression_count="
                f"{validation_summary.get('safe_regression_count')}."
            ),
        },
    ]


def build_audit_payload(
    *,
    root_cause: dict[str, Any] | None = None,
    smoke: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root_cause = root_cause or _load(ROOT_CAUSE)
    smoke = smoke or _load(SMOKE)
    validation = validation or _load(VALIDATION)
    regression = _regression_case(root_cause)
    successful = _successful_switches(smoke)
    safe_rows = _safe_preservation_rows(validation)
    continuation_preserve_abstain = _continuation_rows(root_cause)
    return {
        "schema_version": "krk_selector_continuation_scope_audit.v0",
        "causal_status": "non_causal_scope_review_no_runtime_change",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(ROOT_CAUSE), str(SMOKE), str(VALIDATION)],
        "summary": {
            "regression_row_id": regression["row_id"],
            "regression_ply": regression["ply"],
            "regression_is_initial_owner_choice": False,
            "successful_initial_switch_count": len(successful),
            "safe_preservation_row_count": len(safe_rows),
            "continuation_preserve_abstain_row_count": len(continuation_preserve_abstain),
            "selector_training_row_count": validation.get("summary", {}).get(
                "selector_training_row_count"
            ),
            "stage7_training_row_count": validation.get("summary", {}).get(
                "stage7_training_row_count"
            ),
            "capacity_label_used_as_ownership_label_count": validation.get("summary", {}).get(
                "capacity_label_used_as_ownership_label_count"
            ),
            "safe_regression_count": validation.get("summary", {}).get(
                "safe_regression_count"
            ),
            "target_improvement_count": smoke.get("summary", {}).get(
                "target_improvement_count"
            ),
        },
        "regression_row": regression,
        "comparison": {
            "ply0_successful_switch_cases": successful,
            "ply4_regression_case": regression,
            "safe_preservation_rows": safe_rows,
            "preserve_or_abstain_rows_inside_continuation_windows": continuation_preserve_abstain,
            "finding": (
                "The observed beneficial behavior is initial-owner switching; the "
                "observed harmful behavior is a later h40 continuation switch."
            ),
        },
        "non_causal_scope_rule_evaluations": _scope_rule_evaluations(
            root_cause, smoke, validation
        ),
        "evaluation": {
            "would_ply0_only_preserve_prior_target_improvements": True,
            "would_ply0_only_eliminate_safe_control_regression": True,
            "does_ply0_only_preserve_safe_owners": True,
            "does_ply0_only_avoid_switching_away_from_active_fence_edge_continuations": True,
            "is_ply0_only_runtime_feature_eligible": True,
            "runtime_feature_eligibility_notes": (
                "A future sandbox can use a runtime decision-window signal such as "
                "current_ply/white decision index where available. It must remain "
                "default-off and must not use offline ownership labels."
            ),
        },
        "decision_recommendation": "selector_scope_initial_owner_only_supported",
    }


def build_decision_payload(audit: dict[str, Any] | None = None) -> dict[str, Any]:
    audit = audit or build_audit_payload()
    return {
        "schema_version": "krk_selector_continuation_scope_decision.v0",
        "causal_status": "future_review_packet_only_no_runtime_change",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(OUT_AUDIT_JSON), str(ROOT_CAUSE), str(SMOKE), str(VALIDATION)],
        "possible_decisions": POSSIBLE_DECISIONS,
        "decision": {
            "status": "selector_scope_initial_owner_only_supported",
            "promote_selector": False,
            "make_default": False,
            "implement_fix_now": False,
            "write_future_narrowed_sandbox_review_only": True,
            "train_stage8": False,
            "promote_stage7": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "write a separate future default-off narrowed selector sandbox review "
                "that allows behavior only for initial-owner choice and blocks active "
                "continuation windows"
            ),
        },
        "evidence": {
            "regression_row_id": audit["summary"]["regression_row_id"],
            "regression_ply": audit["summary"]["regression_ply"],
            "successful_initial_switch_count": audit["summary"][
                "successful_initial_switch_count"
            ],
            "safe_regression_count": audit["summary"]["safe_regression_count"],
            "target_improvement_count": audit["summary"]["target_improvement_count"],
            "selector_training_row_count": audit["summary"]["selector_training_row_count"],
            "stage7_training_row_count": audit["summary"]["stage7_training_row_count"],
            "capacity_label_used_as_ownership_label_count": audit["summary"][
                "capacity_label_used_as_ownership_label_count"
            ],
            "selector_remains_quarantined": True,
        },
        "rationale": (
            "Initial-owner-only scoping matches the current positive evidence and "
            "blocks the known ply-4 continuation regression. It is not an implemented "
            "fix; it is only supported enough for a future default-off review packet."
        ),
    }


def _write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [f"# {title}", ""]
    if "summary" in payload:
        lines.extend(["## Summary", ""])
        for key, value in payload["summary"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(["", "## Regression Row", ""])
        for key, value in payload["regression_row"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(["", "## Scope Rule Evaluations", ""])
        for item in payload["non_causal_scope_rule_evaluations"]:
            lines.append(
                f"- {item['rule']}: `{item['classification']}`; evidence: {item['evidence']}"
            )
        lines.extend(["", "## Evaluation", ""])
        for key, value in payload["evaluation"].items():
            lines.append(f"- {key}: `{value}`")
        lines.append(f"- decision_recommendation: `{payload['decision_recommendation']}`")
    else:
        lines.extend(["## Decision", ""])
        for key, value in payload["decision"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(["", "## Evidence", ""])
        for key, value in payload["evidence"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(["", "## Rationale", "", payload["rationale"]])
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    audit = build_audit_payload()
    decision = build_decision_payload(audit)
    (ROOT / OUT_AUDIT_JSON).write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ROOT / OUT_DECISION_JSON).write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_md(OUT_AUDIT_MD, "KRK Selector Continuation Scope Audit v0", audit)
    _write_md(OUT_DECISION_MD, "KRK Selector Continuation Scope Decision v0", decision)
    print(OUT_AUDIT_JSON)
    print(OUT_AUDIT_MD)
    print(OUT_DECISION_JSON)
    print(OUT_DECISION_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
