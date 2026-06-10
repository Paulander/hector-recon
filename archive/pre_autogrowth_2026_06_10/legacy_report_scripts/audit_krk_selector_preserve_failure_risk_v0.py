#!/usr/bin/env python3
"""Audit the remaining selector preserve-on-failure recommendation."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
EXPANDED = Path(
    "reports/strategy_arbitration/krk_selector_observability_expanded_recommendations_v0.json"
)
READINESS = Path(
    "reports/strategy_arbitration/krk_selector_observability_readiness_review_v0.json"
)
OUT_AUDIT_JSON = Path(
    "reports/strategy_arbitration/krk_selector_preserve_failure_risk_audit_v0.json"
)
OUT_AUDIT_MD = Path(
    "reports/strategy_arbitration/krk_selector_preserve_failure_risk_audit_v0.md"
)
OUT_DECISION_JSON = Path(
    "reports/strategy_arbitration/krk_selector_preserve_failure_risk_decision_v0.json"
)
OUT_DECISION_MD = Path(
    "reports/strategy_arbitration/krk_selector_preserve_failure_risk_decision_v0.md"
)

CLASSES = (
    "preserve_selected_owner",
    "prefer_visible_alternative",
    "abstain_context_only",
)
COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_provider_suppression": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _rec(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("enabled_decision", {}).get("selector_recommendation", {}) or {}


def _features(row: dict[str, Any]) -> dict[str, Any]:
    rec = _rec(row)
    return {
        "row_id": row.get("row_id"),
        "stage": row.get("source_stage"),
        "selected_provider": row.get("selected_provider_label"),
        "selected_move": rec.get("selected_move_before_recommendation")
        or row.get("enabled_decision", {}).get("move"),
        "target_label": row.get("offline_target_action"),
        "selected_owner_label": row.get("selected_owner_label"),
        "recommendation": row.get("recommendation"),
        "decision_reason": row.get("decision_reason"),
        "provider_family": str(row.get("selected_provider_label") or "").replace("krk.", ""),
        "selected_piece": rec.get("selected_piece"),
        "edge_bucket": rec.get("edge_bucket"),
        "support_bucket": rec.get("support_bucket"),
        "positive_trace_count_bucket": rec.get("positive_trace_count_bucket"),
        "positive_trace_provider_candidate_count": rec.get(
            "positive_trace_provider_candidate_count"
        ),
        "active_landmark": rec.get("active_landmark_label") or row.get("active_landmark_label"),
        "box_area_relevance": rec.get("box_area_relevance"),
        "visible_alternative_count": rec.get("visible_alternative_count"),
        "confidence": rec.get("confidence") or row.get("enabled_decision", {}).get("confidence"),
        "source_terms": list(rec.get("source_terms") or []),
        "explanation_terms": list(rec.get("explanation_terms") or []),
        "visible_alternatives": list(rec.get("visible_alternatives_considered") or []),
    }


def _runtime_pattern(row: dict[str, Any]) -> tuple[str, ...]:
    f = _features(row)
    return (
        str(f["stage"] or ""),
        str(f["active_landmark"] or ""),
        str(f["support_bucket"] or ""),
        str(f["selected_piece"] or ""),
        str(f["positive_trace_count_bucket"] or ""),
    )


def _target(row: dict[str, Any]) -> str:
    return str(row.get("offline_target_action") or "")


def _metrics(rows: list[dict[str, Any]], predictor: Callable[[dict[str, Any]], str]) -> dict[str, Any]:
    predicted_rows = []
    for row in rows:
        pred = predictor(row)
        predicted_rows.append({**_features(row), "target": _target(row), "refined": pred})
    counts = Counter(row["refined"] for row in predicted_rows)
    preserve_on_failure = sum(
        1
        for row in predicted_rows
        if row["refined"] == "preserve_selected_owner"
        and row["selected_owner_label"] == "selected_owner_failed"
    )
    switch_on_safe = sum(
        1
        for row in predicted_rows
        if row["refined"] == "prefer_visible_alternative"
        and row["selected_owner_label"] == "selected_owner_converted"
    )
    safe_rows = [
        row
        for row in predicted_rows
        if row["target"] == "preserve_selected_owner"
    ]
    switch_rows = [
        row
        for row in predicted_rows
        if row["target"] == "prefer_visible_alternative"
    ]
    abstain_rows = [
        row
        for row in predicted_rows
        if row["target"] == "abstain_context_only"
    ]
    return {
        "prediction_counts": {klass: int(counts.get(klass, 0)) for klass in CLASSES},
        "preserve_on_failure_count": preserve_on_failure,
        "switch_on_safe_owner_count": switch_on_safe,
        "safe_preservation_recall": (
            sum(1 for row in safe_rows if row["refined"] == "preserve_selected_owner")
            / len(safe_rows)
            if safe_rows
            else 0.0
        ),
        "switch_contrast_recall": (
            sum(1 for row in switch_rows if row["refined"] == "prefer_visible_alternative")
            / len(switch_rows)
            if switch_rows
            else 0.0
        ),
        "abstain_recall": (
            sum(1 for row in abstain_rows if row["refined"] == "abstain_context_only")
            / len(abstain_rows)
            if abstain_rows
            else 0.0
        ),
        "offline_accuracy": (
            sum(1 for row in predicted_rows if row["refined"] == row["target"])
            / len(predicted_rows)
            if predicted_rows
            else 0.0
        ),
        "predicted_rows": predicted_rows,
    }


def _base_prediction(row: dict[str, Any]) -> str:
    return str(row.get("recommendation") or "")


def _has_failure_risk_terms(row: dict[str, Any]) -> bool:
    f = _features(row)
    return (
        f["stage"] == "stage5"
        and f["active_landmark"] == "fence_established"
        and f["support_bucket"] == "close"
        and f["selected_piece"] == "king"
        and f["positive_trace_count_bucket"] == "high"
    )


def _refinement_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failing_pattern = None
    failing = [row for row in rows if row.get("preserve_on_selected_owner_failure")]
    if failing:
        failing_pattern = _runtime_pattern(failing[0])

    refinements: list[tuple[str, str, bool, Callable[[dict[str, Any]], str]]] = [
        (
            "baseline_combined_simple_rule_runtime_observation",
            "Existing recommendation record; no refinement.",
            True,
            _base_prediction,
        ),
        (
            "preserve_only_if_no_selected_owner_failure_risk_terms",
            "Abstain instead of preserve when runtime-visible failure-risk pattern terms are present.",
            True,
            lambda row: (
                "abstain_context_only"
                if _base_prediction(row) == "preserve_selected_owner"
                and _has_failure_risk_terms(row)
                else _base_prediction(row)
            ),
        ),
        (
            "preserve_only_if_positive_alternative_count_below_high",
            "Abstain instead of preserve when the positive trace count bucket is high.",
            True,
            lambda row: (
                "abstain_context_only"
                if _base_prediction(row) == "preserve_selected_owner"
                and _features(row)["positive_trace_count_bucket"] == "high"
                else _base_prediction(row)
            ),
        ),
        (
            "abstain_for_exact_preserve_failure_pattern",
            "Abstain instead of preserve for the exact runtime-visible failing pattern.",
            True,
            lambda row: (
                "abstain_context_only"
                if _base_prediction(row) == "preserve_selected_owner"
                and failing_pattern is not None
                and _runtime_pattern(row) == failing_pattern
                else _base_prediction(row)
            ),
        ),
        (
            "require_stronger_safe_preservation_confidence",
            "Abstain instead of preserve when confidence is below the minimum safe-preserve confidence observed in controls.",
            True,
            lambda row: _base_prediction(row),
        ),
    ]

    safe_confidences = [
        float((_features(row).get("confidence") or 0.0))
        for row in rows
        if row.get("recommendation") == "preserve_selected_owner"
        and row.get("selected_owner_label") == "selected_owner_converted"
    ]
    confidence_floor = min(safe_confidences) if safe_confidences else 0.0

    out = []
    for name, description, runtime_feature_eligible, predictor in refinements:
        if name == "require_stronger_safe_preservation_confidence":
            predictor = lambda row, floor=confidence_floor: (
                "abstain_context_only"
                if _base_prediction(row) == "preserve_selected_owner"
                and float((_features(row).get("confidence") or 0.0)) < floor
                else _base_prediction(row)
            )
        metrics = _metrics(rows, predictor)
        out.append({
            "refinement_id": name,
            "description": description,
            "runtime_feature_eligible": runtime_feature_eligible,
            "uses_offline_only_labels": False,
            "confidence_floor": confidence_floor if name == "require_stronger_safe_preservation_confidence" else None,
            "eliminates_preserve_on_failure": metrics["preserve_on_failure_count"] == 0,
            "keeps_switch_on_safe_owner_zero": metrics["switch_on_safe_owner_count"] == 0,
            "preserves_safe_preservation_recall": metrics["safe_preservation_recall"] == 1.0,
            "does_not_reduce_switch_contrast_recall_too_much": metrics[
                "switch_contrast_recall"
            ] >= 0.75,
            "metrics": {
                key: value
                for key, value in metrics.items()
                if key != "predicted_rows"
            },
        })
    return out


def _compare_terms(failing: dict[str, Any], safe_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fail = _features(failing)
    keys = [
        "provider_family",
        "selected_piece",
        "edge_bucket",
        "support_bucket",
        "positive_trace_count_bucket",
        "active_landmark",
        "box_area_relevance",
        "visible_alternative_count",
    ]
    comparisons = {}
    for key in keys:
        safe_values = sorted({str(_features(row).get(key)) for row in safe_rows})
        comparisons[key] = {
            "failing_value": fail.get(key),
            "safe_values": safe_values,
            "collides_with_safe": str(fail.get(key)) in safe_values,
        }
    return comparisons


def build_audit() -> dict[str, Any]:
    expanded = _load(EXPANDED)
    readiness = _load(READINESS)
    rows = [row for row in expanded.get("rows") or [] if isinstance(row, dict)]
    failing_rows = [row for row in rows if row.get("preserve_on_selected_owner_failure")]
    safe_preserve_rows = [
        row
        for row in rows
        if row.get("recommendation") == "preserve_selected_owner"
        and row.get("selected_owner_label") == "selected_owner_converted"
    ]
    refinements = _refinement_results(rows)
    viable = [
        row for row in refinements
        if row["refinement_id"] != "baseline_combined_simple_rule_runtime_observation"
        and row["eliminates_preserve_on_failure"]
        and row["keeps_switch_on_safe_owner_zero"]
        and row["preserves_safe_preservation_recall"]
        and row["does_not_reduce_switch_contrast_recall_too_much"]
        and row["runtime_feature_eligible"]
        and not row["uses_offline_only_labels"]
    ]
    decision_status = (
        "preserve_failure_risk_resolved_non_causal"
        if viable
        else "selector_observability_still_blocked"
    )
    return {
        "schema_version": "krk_selector_preserve_failure_risk_audit.v0",
        "causal_status": "non_causal_preserve_failure_risk_audit",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(EXPANDED), str(READINESS)],
        "failing_rows": [
            {
                **_features(row),
                "state_id": row.get("state_id"),
                "fen": row.get("fen"),
                "visible_alternatives": _features(row)["visible_alternatives"],
            }
            for row in failing_rows
        ],
        "safe_preserve_rows": [_features(row) for row in safe_preserve_rows],
        "term_comparison": (
            _compare_terms(failing_rows[0], safe_preserve_rows)
            if failing_rows
            else {}
        ),
        "refinement_results": refinements,
        "viable_refinements": viable,
        "summary": {
            "failing_row_count": len(failing_rows),
            "safe_preserve_row_count": len(safe_preserve_rows),
            "stage7_training_row_count": int(
                expanded.get("summary", {}).get("stage7_training_row_count", 0) or 0
            ),
            "selector_training_row_count": int(
                expanded.get("summary", {}).get("selector_training_row_count", 0) or 0
            ),
            "runtime_behavior_changed": False,
            "selected_move_delta_count": int(
                expanded.get("summary", {}).get("selected_move_delta_count", 0) or 0
            ),
            "selected_provider_delta_count": int(
                expanded.get("summary", {}).get("selected_provider_delta_count", 0) or 0
            ),
            "score_delta_count": int(expanded.get("summary", {}).get("score_delta_count", 0) or 0),
            "routing_delta_count": int(expanded.get("summary", {}).get("routing_delta_count", 0) or 0),
            "capacity_label_used_as_ownership_label_count": int(
                expanded.get("summary", {}).get(
                    "capacity_label_used_as_ownership_label_count",
                    0,
                )
                or 0
            ),
            "prior_readiness_status": readiness.get("decision", {}).get("status"),
            "viable_refinement_count": len(viable),
        },
        "decision": {
            "status": decision_status,
            "runtime_changes_allowed": False,
            "selector_runtime_ready": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "write_future_runtime_review_packet_recommendation_only"
                if viable
                else "collect_more_targeted_preserve_failure_rows_or_architecture_review"
            ),
        },
    }


def build_decision(audit: dict[str, Any]) -> dict[str, Any]:
    viable = audit.get("viable_refinements") or []
    best = viable[0] if viable else None
    return {
        "schema_version": "krk_selector_preserve_failure_risk_decision.v0",
        "causal_status": "non_causal_preserve_failure_risk_decision",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(OUT_AUDIT_JSON), str(EXPANDED), str(READINESS)],
        "summary": {
            **audit["summary"],
            "recommended_refinement_id": (
                best.get("refinement_id") if isinstance(best, dict) else None
            ),
            "future_runtime_review_packet_recommendation": (
                {
                    "scope": "review_only_default_off_selector_refinement",
                    "recommended_rule": best.get("refinement_id"),
                    "runtime_effect_if_later_approved": "recommendation_policy_only_review_not_implemented_here",
                    "must_remain_default_off": True,
                    "must_keep_trace_only_until_separately_approved": True,
                }
                if isinstance(best, dict)
                else None
            ),
        },
        "decision": {
            "status": audit["decision"]["status"],
            "runtime_changes_allowed": False,
            "selector_runtime_ready": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "behavior_changing_selector_implemented": False,
            "future_runtime_review_packet_recommended": bool(best),
        },
    }


def _write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [f"# {title}", "", "## Decision", ""]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    if payload.get("failing_rows"):
        lines.extend(["", "## Failing Row", ""])
        row = payload["failing_rows"][0]
        for key in (
            "row_id",
            "stage",
            "selected_provider",
            "selected_move",
            "target_label",
            "recommendation",
            "decision_reason",
            "positive_trace_provider_candidate_count",
            "positive_trace_count_bucket",
            "selected_piece",
            "support_bucket",
            "active_landmark",
        ):
            lines.append(f"- {key}: `{row.get(key)}`")
    if payload.get("viable_refinements"):
        lines.extend(["", "## Viable Refinements", ""])
        for item in payload["viable_refinements"]:
            lines.append(
                f"- `{item['refinement_id']}` metrics=`{item['metrics']}`"
            )
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    audit = build_audit()
    decision = build_decision(audit)
    (ROOT / OUT_AUDIT_JSON).write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_DECISION_JSON).write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_md(OUT_AUDIT_MD, "KRK Selector Preserve Failure Risk Audit v0", audit)
    _write_md(OUT_DECISION_MD, "KRK Selector Preserve Failure Risk Decision v0", decision)
    print(json.dumps(decision["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
