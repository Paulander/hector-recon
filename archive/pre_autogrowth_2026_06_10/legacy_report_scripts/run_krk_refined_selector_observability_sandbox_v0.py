#!/usr/bin/env python3
"""Run the default-off refined KRK selector-objective observability sandbox."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_candidate_generation_observation_sandbox_v0 import (  # noqa: E402
    _new_graph_engine,
    _profile_kwargs,
)
from scripts.run_krk_selector_observability_expansion_v0 import (  # noqa: E402
    RECOMMENDATION_CLASSES,
    build_manifest,
)
from scripts.test_krk_landmark_progress import (  # noqa: E402
    _skill_id_for_suggestion,
    choose_move_details,
)


RUNTIME_REVIEW_PACKET = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_observability_runtime_review_packet_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_refined_selector_observability_sandbox_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_refined_selector_observability_sandbox_v0.md"
)

SANDBOX_ID = "sandbox.krk.refined_selector_objective_observability_v0"
REFINEMENT_ID = "preserve_only_if_no_selected_owner_failure_risk_terms"

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

FORBIDDEN_ACTIONS = {
    "selecting_a_provider",
    "selecting_a_move",
    "changing_scores",
    "suppressing_providers",
    "routing_directly_to_a_provider",
    "runtime_dtm_or_tablebase",
    "gameplay_topology_mutation",
    "stage7_promotion",
    "stage8_training",
}

DECISION_STATUSES = [
    "refined_selector_observability_sandbox_wired_default_off_equivalent",
    "refined_selector_observability_sandbox_failed_equivalence",
    "refined_selector_observability_sandbox_invalid_metadata",
    "refined_selector_observability_ready_for_recommendation_analysis",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _selected_provider(details: dict[str, Any]) -> str | None:
    selected = details.get("selected_suggestion")
    if isinstance(selected, dict) and selected:
        return _skill_id_for_suggestion(selected)
    return None


def _compact_decision(details: dict[str, Any]) -> dict[str, Any]:
    rec = details.get("krk_selector_objective_recommendation") or {}
    return {
        "move": details.get("move"),
        "selected_provider": _selected_provider(details),
        "confidence": details.get("confidence"),
        "selector_recommendation_present": bool(rec),
        "selector_recommendation": rec,
        "candidate_generation_observation_present": bool(
            details.get("krk_candidate_generation_observation")
        ),
    }


def _run_decision(case: dict[str, Any], enabled: bool) -> dict[str, Any]:
    graph, engine = _new_graph_engine()
    board = chess.Board(str(case["fen"]))
    details = choose_move_details(
        graph,
        engine,
        board,
        max_ticks=200,
        suggestion_limit=10,
        active_landmark_label=str(case["active_landmark_label"]),
        early_stop_stable_suggestions=2,
        krk_refined_selector_objective_observability_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def _offline_target(row: dict[str, Any], rec: dict[str, Any]) -> str:
    if int(rec.get("positive_trace_provider_candidate_count", 0) or 0) <= 0:
        return "abstain_context_only"
    if row.get("selected_owner_label") == "selected_owner_failed":
        return "prefer_visible_alternative"
    if row.get("selected_owner_label") == "selected_owner_converted":
        return "preserve_selected_owner"
    return "abstain_context_only"


def _valid_refined_recommendation(rec: dict[str, Any]) -> bool:
    if not rec:
        return False
    forbidden = set(rec.get("forbidden_actions") or [])
    refinement = rec.get("preserve_failure_risk_refinement") or {}
    abstain_guard = rec.get("abstain_guard") or {}
    return (
        rec.get("schema_version") == "krk_selector_objective_recommendation.v0"
        and rec.get("sandbox_id") == SANDBOX_ID
        and rec.get("selector_model_id") == "combined_simple_rule"
        and rec.get("selector_refinement_id") == REFINEMENT_ID
        and rec.get("causal_status") == "recommendation_only"
        and rec.get("direct_request") is False
        and float(rec.get("score_delta", 1.0) or 0.0) == 0.0
        and rec.get("recommendation") in set(RECOMMENDATION_CLASSES)
        and bool(rec.get("source_terms") is not None)
        and bool(rec.get("explanation_terms"))
        and bool(rec.get("selected_owner_before_recommendation"))
        and isinstance(rec.get("visible_alternatives_considered"), list)
        and refinement.get("enabled") is True
        and refinement.get("uses_offline_only_labels") is False
        and refinement.get("status")
        in {"triggered_abstain_context_only", "risk_terms_detected_not_preserve", "not_triggered"}
        and abstain_guard.get("enabled") is True
        and abstain_guard.get("preserves_existing_abstain_behavior") is True
        and FORBIDDEN_ACTIONS.issubset(forbidden)
    )


def build_payload(
    *,
    decision_runner: Callable[[dict[str, Any], bool], dict[str, Any]] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review = _load(RUNTIME_REVIEW_PACKET)
    manifest = manifest or build_manifest()
    runner = decision_runner or _run_decision

    rows = []
    invalid_metadata = []
    for case in manifest.get("cases") or []:
        default_off = runner(case, False)
        enabled = runner(case, True)
        rec = enabled.get("selector_recommendation") or {}
        if rec and not _valid_refined_recommendation(rec):
            invalid_metadata.append({"case_id": case.get("case_id"), "record": rec})
        target = _offline_target(case, rec)
        rows.append({
            **case,
            "flag_off_decision": default_off,
            "enabled_decision": enabled,
            "flag_off_selector_recommendation_count": int(
                bool(default_off.get("selector_recommendation_present"))
            ),
            "enabled_selector_recommendation_count": int(bool(rec)),
            "recommendation": rec.get("recommendation"),
            "decision_reason": rec.get("decision_reason"),
            "offline_target_action": target,
            "recommendation_aligns_with_offline_label": rec.get("recommendation") == target,
            "preserve_on_selected_owner_failure": (
                rec.get("recommendation") == "preserve_selected_owner"
                and case.get("selected_owner_label") == "selected_owner_failed"
            ),
            "switch_on_safe_owner": (
                rec.get("recommendation") == "prefer_visible_alternative"
                and case.get("selected_owner_label") == "selected_owner_converted"
            ),
            "abstain_target": target == "abstain_context_only",
            "abstain_target_recalled": (
                target == "abstain_context_only"
                and rec.get("recommendation") == "abstain_context_only"
            ),
            "preserve_failure_risk_refinement_status": (
                (rec.get("preserve_failure_risk_refinement") or {}).get("status")
            ),
            "abstain_guard_status": (rec.get("abstain_guard") or {}).get("status"),
            "source_terms": list(rec.get("source_terms") or []),
            "explanation_terms": list(rec.get("explanation_terms") or []),
            "visible_alternative_count": int(rec.get("visible_alternative_count", 0) or 0),
            "direct_request": rec.get("direct_request"),
            "causal_status": rec.get("causal_status"),
            "score_delta": float(rec.get("score_delta", 0.0) or 0.0),
            "selected_move_delta": default_off.get("move") != enabled.get("move"),
            "selected_provider_delta": (
                default_off.get("selected_provider") != enabled.get("selected_provider")
            ),
            "selected_score_delta": default_off.get("confidence") != enabled.get("confidence"),
            "routing_delta": False,
            "runtime_behavior_changed": False,
            "stage7_training_row": False,
            "selector_training_row": False,
        })

    rec_counts = Counter(str(row.get("recommendation") or "") for row in rows)
    source_terms = sorted({term for row in rows for term in row.get("source_terms") or []})
    explanation_terms = sorted(
        {term for row in rows for term in row.get("explanation_terms") or []}
    )
    attempted_count = len(rows)
    enabled_count = sum(int(row["enabled_selector_recommendation_count"]) for row in rows)
    flag_off_count = sum(int(row["flag_off_selector_recommendation_count"]) for row in rows)
    selected_move_delta_count = sum(1 for row in rows if row["selected_move_delta"])
    selected_provider_delta_count = sum(1 for row in rows if row["selected_provider_delta"])
    selected_score_delta_count = sum(1 for row in rows if row["selected_score_delta"])
    score_delta_count = sum(1 for row in rows if row["score_delta"] != 0.0)
    routing_delta_count = sum(1 for row in rows if row["routing_delta"])
    preserve_on_failure_count = sum(1 for row in rows if row["preserve_on_selected_owner_failure"])
    switch_on_safe_owner_count = sum(1 for row in rows if row["switch_on_safe_owner"])
    abstain_target_count = sum(1 for row in rows if row["abstain_target"])
    abstain_target_recalled_count = sum(1 for row in rows if row["abstain_target_recalled"])
    abstain_recall = (
        abstain_target_recalled_count / abstain_target_count
        if abstain_target_count
        else None
    )
    refinement_trigger_count = sum(
        1
        for row in rows
        if row["preserve_failure_risk_refinement_status"]
        == "triggered_abstain_context_only"
    )
    default_off_equivalence_passed = (
        attempted_count > 0
        and flag_off_count == 0
        and selected_move_delta_count == 0
        and selected_provider_delta_count == 0
        and selected_score_delta_count == 0
        and score_delta_count == 0
        and routing_delta_count == 0
    )
    metadata_valid = (
        enabled_count == attempted_count
        and not invalid_metadata
        and preserve_on_failure_count == 0
        and abstain_recall == 1.0
    )
    if not default_off_equivalence_passed:
        status = "refined_selector_observability_sandbox_failed_equivalence"
    elif not metadata_valid:
        status = "refined_selector_observability_sandbox_invalid_metadata"
    elif enabled_count >= attempted_count and set(rec_counts).issuperset(RECOMMENDATION_CLASSES):
        status = "refined_selector_observability_ready_for_recommendation_analysis"
    else:
        status = "refined_selector_observability_sandbox_wired_default_off_equivalent"

    summary = {
        "attempted_row_count": attempted_count,
        "default_off_equivalence_passed": default_off_equivalence_passed,
        "enabled_recommendation_count": enabled_count,
        "default_off_selector_recommendation_count": flag_off_count,
        "recommendation_counts_by_class": {
            klass: int(rec_counts.get(klass, 0)) for klass in RECOMMENDATION_CLASSES
        },
        "preserve_on_failure_count": preserve_on_failure_count,
        "preserve_failure_risk_refinement_trigger_count": refinement_trigger_count,
        "switch_on_safe_owner_count": switch_on_safe_owner_count,
        "abstain_count": int(rec_counts.get("abstain_context_only", 0)),
        "abstain_target_count": abstain_target_count,
        "abstain_target_recalled_count": abstain_target_recalled_count,
        "abstain_recall": abstain_recall,
        "selected_move_delta_count": selected_move_delta_count,
        "selected_provider_delta_count": selected_provider_delta_count,
        "selected_score_delta_count": selected_score_delta_count,
        "score_delta_count": score_delta_count,
        "routing_delta_count": routing_delta_count,
        "runtime_behavior_changed": False,
        "stage7_training_row_count": sum(1 for row in rows if row["stage7_training_row"]),
        "selector_training_row_count": sum(1 for row in rows if row["selector_training_row"]),
        "runtime_dtm_or_tablebase_use": False,
        "gameplay_topology_mutation": False,
        "hidden_python_controller": False,
        "capacity_label_used_as_ownership_label_count": sum(
            1 for row in rows if row.get("capacity_label_used_as_ownership_label")
        ),
        "invalid_metadata_count": len(invalid_metadata),
        "direct_request_false_count": sum(
            1 for row in rows if row["direct_request"] is False
        ),
        "score_delta_zero_count": sum(1 for row in rows if row["score_delta"] == 0.0),
        "source_term_coverage": {
            "unique_source_term_count": len(source_terms),
            "unique_explanation_term_count": len(explanation_terms),
            "source_terms": source_terms,
            "explanation_terms": explanation_terms,
        },
    }
    return {
        "schema_version": "krk_refined_selector_observability_sandbox.v0",
        "sandbox_id": SANDBOX_ID,
        "causal_status": "runtime_recommendation_only_observability_sandbox",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(RUNTIME_REVIEW_PACKET),
            "reports/strategy_arbitration/krk_selector_observability_expansion_manifest_v0.json",
            "reports/strategy_arbitration/krk_selector_preserve_failure_risk_audit_v0.json",
        ],
        "approval": {
            "approval_status": "explicitly_approved_for_first_refined_selector_objective_observability_sandbox",
            "flag_required": "--enable-krk-refined-selector-observability",
            "runtime_review_status": review.get("decision", {}).get("status"),
            "behavior_changing_selector_allowed": False,
        },
        "summary": summary,
        "rows": rows,
        "invalid_metadata": invalid_metadata[:10],
        "possible_statuses": DECISION_STATUSES,
        "decision": {
            "status": status,
            "runtime_changes_allowed": False,
            "behavior_changing_selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "non_causal_refined_recommendation_analysis"
                if status
                == "refined_selector_observability_ready_for_recommendation_analysis"
                else "quarantine_refined_selector_observability_sandbox_result"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Refined Selector Observability Sandbox v0",
        "",
        "This report records the explicitly approved default-off refined selector-objective observability sandbox. It emits recommendation-only metadata and does not alter move, provider, score, or routing behavior.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            "- "
            f"`{row.get('row_id') or row.get('case_id')}` "
            f"stage={row.get('source_stage')} "
            f"recommendation=`{row.get('recommendation')}` "
            f"target=`{row.get('offline_target_action')}` "
            f"refinement=`{row.get('preserve_failure_risk_refinement_status')}` "
            f"abstain_guard=`{row.get('abstain_guard_status')}` "
            f"move_delta={row.get('selected_move_delta')} "
            f"provider_delta={row.get('selected_provider_delta')} "
            f"score_delta={row.get('selected_score_delta')}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run default-off refined KRK selector-objective observability sandbox"
    )
    parser.add_argument(
        "--enable-krk-refined-selector-observability",
        action="store_true",
        help="Execute the explicitly approved refined recommendation-only sandbox.",
    )
    args = parser.parse_args()
    if not args.enable_krk_refined_selector_observability:
        raise SystemExit(
            "refusing_to_execute_without_--enable-krk-refined-selector-observability"
        )
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
