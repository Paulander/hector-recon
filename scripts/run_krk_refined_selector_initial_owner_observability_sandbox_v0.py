#!/usr/bin/env python3
"""Run initial-owner-only refined selector observability sandbox v0.

This sandbox is trace-only/recommendation-only. It does not change move,
provider, score, routing, topology, or training behavior.
"""

from __future__ import annotations

import argparse
import json
import random
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
    play_to_mate,
)


OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_observability_sandbox_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_observability_sandbox_v0.md"
)
SCOPE_DECISION = Path(
    "reports/strategy_arbitration/krk_selector_continuation_scope_decision_v0.json"
)
VALIDATION = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.json"
)

SANDBOX_ID = "sandbox.krk.refined_selector_initial_owner_observability_v0"
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
    "refined_selector_initial_owner_observability_wired_default_off_equivalent",
    "refined_selector_initial_owner_observability_failed_equivalence",
    "refined_selector_initial_owner_observability_invalid_scope",
    "refined_selector_initial_owner_observability_ready_for_recommendation_analysis",
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
        krk_refined_selector_initial_owner_observability_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def _regression_case() -> dict[str, Any]:
    validation = _load(VALIDATION)
    for row in validation.get("rows") or []:
        if row.get("row_id") == "joined_trace_ownership_4":
            return row
    raise ValueError("joined_trace_ownership_4 not found")


def _run_continuation_trace(enabled: bool) -> dict[str, Any]:
    case = _regression_case()
    graph, engine = _new_graph_engine()
    board = chess.Board(str(case["fen"]))
    result = play_to_mate(
        graph,
        engine,
        board,
        random.Random(40),
        str(case["active_landmark_label"]),
        stage_filter=None,
        max_plies=12,
        black_policy="adversarial",
        trace=True,
        trace_max_plies=12,
        max_ticks=200,
        suggestion_limit=10,
        early_stop_stable_suggestions=2,
        krk_refined_selector_initial_owner_observability_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    white_events = []
    for event in result.get("trace") or []:
        if event.get("turn") != "white":
            continue
        engine_details = event.get("engine") if isinstance(event.get("engine"), dict) else {}
        rec = engine_details.get("krk_selector_objective_recommendation") or {}
        white_events.append(
            {
                "ply": event.get("ply"),
                "move": event.get("move"),
                "selected_provider": _selected_provider(engine_details),
                "selector_recommendation_present": bool(rec),
                "recommendation": rec.get("recommendation"),
                "selector_scope": rec.get("selector_scope"),
                "decision_window": rec.get("decision_window"),
                "continuation_recommendation": rec.get("continuation_recommendation"),
            }
        )
    return {
        "row_id": case.get("row_id"),
        "result": result.get("result"),
        "plies": result.get("plies"),
        "white_events": white_events,
        "initial_recommendation_count": sum(
            1 for event in white_events if event["selector_recommendation_present"] and event["ply"] == 0
        ),
        "continuation_recommendation_count": sum(
            1 for event in white_events if event["selector_recommendation_present"] and int(event["ply"] or 0) > 0
        ),
    }


def _valid_recommendation(rec: dict[str, Any]) -> bool:
    forbidden = set(rec.get("forbidden_actions") or [])
    refinement = rec.get("preserve_failure_risk_refinement") or {}
    abstain_guard = rec.get("abstain_guard") or {}
    return (
        rec.get("schema_version") == "krk_selector_objective_recommendation.v0"
        and rec.get("sandbox_id") == SANDBOX_ID
        and rec.get("selector_refinement_id") == REFINEMENT_ID
        and rec.get("causal_status") == "recommendation_only"
        and rec.get("selector_scope") == "initial_owner_only"
        and rec.get("decision_window") == "initial_owner_choice"
        and rec.get("continuation_recommendation") is False
        and rec.get("plan_capsule_continuation_influence") is False
        and rec.get("progress_window_reconsideration_influence") is False
        and rec.get("move_provider_selection_effect") is False
        and rec.get("direct_request") is False
        and float(rec.get("score_delta", 1.0) or 0.0) == 0.0
        and rec.get("recommendation") in set(RECOMMENDATION_CLASSES)
        and bool(rec.get("selected_owner_before_recommendation"))
        and isinstance(rec.get("visible_alternatives_considered"), list)
        and bool(rec.get("explanation_terms"))
        and refinement.get("enabled") is True
        and refinement.get("uses_offline_only_labels") is False
        and abstain_guard.get("enabled") is True
        and abstain_guard.get("preserves_existing_abstain_behavior") is True
        and FORBIDDEN_ACTIONS.issubset(forbidden)
    )


def _offline_target(row: dict[str, Any], rec: dict[str, Any]) -> str:
    if int(rec.get("positive_trace_provider_candidate_count", 0) or 0) <= 0:
        return "abstain_context_only"
    if row.get("selected_owner_label") == "selected_owner_failed":
        return "prefer_visible_alternative"
    if row.get("selected_owner_label") == "selected_owner_converted":
        return "preserve_selected_owner"
    return "abstain_context_only"


def build_payload(
    *,
    decision_runner: Callable[[dict[str, Any], bool], dict[str, Any]] | None = None,
    continuation_runner: Callable[[bool], dict[str, Any]] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scope_decision = _load(SCOPE_DECISION)
    manifest = manifest or build_manifest()
    runner = decision_runner or _run_decision
    run_continuation = continuation_runner or _run_continuation_trace
    rows = []
    invalid_metadata = []

    for case in manifest.get("cases") or []:
        default_off = runner(case, False)
        enabled = runner(case, True)
        rec = enabled.get("selector_recommendation") or {}
        if rec and not _valid_recommendation(rec):
            invalid_metadata.append({"case_id": case.get("case_id"), "record": rec})
        target = _offline_target(case, rec)
        rows.append(
            {
                **case,
                "flag_off_decision": default_off,
                "enabled_decision": enabled,
                "flag_off_selector_recommendation_count": int(
                    bool(default_off.get("selector_recommendation_present"))
                ),
                "enabled_selector_recommendation_count": int(bool(rec)),
                "recommendation": rec.get("recommendation"),
                "offline_target_action": target,
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
                "selector_scope": rec.get("selector_scope"),
                "decision_window": rec.get("decision_window"),
                "continuation_recommendation": rec.get("continuation_recommendation"),
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
                "capacity_label_used_as_ownership_label": False,
            }
        )

    continuation_enabled = run_continuation(True)
    continuation_default_off = run_continuation(False)
    rec_counts = Counter(row.get("recommendation") for row in rows)
    attempted_count = len(rows)
    enabled_count = sum(row["enabled_selector_recommendation_count"] for row in rows)
    flag_off_count = sum(row["flag_off_selector_recommendation_count"] for row in rows)
    abstain_target_count = sum(1 for row in rows if row["abstain_target"])
    abstain_target_recalled_count = sum(1 for row in rows if row["abstain_target_recalled"])
    abstain_recall = (
        abstain_target_recalled_count / abstain_target_count
        if abstain_target_count
        else None
    )
    selected_move_delta_count = sum(1 for row in rows if row["selected_move_delta"])
    selected_provider_delta_count = sum(1 for row in rows if row["selected_provider_delta"])
    score_delta_count = sum(1 for row in rows if row["score_delta"] != 0.0)
    routing_delta_count = sum(1 for row in rows if row["routing_delta"])
    continuation_recommendation_count = int(
        continuation_enabled.get("continuation_recommendation_count", 0) or 0
    )
    invalid_scope = (
        continuation_recommendation_count != 0
        or any(row["selector_scope"] != "initial_owner_only" for row in rows)
        or any(row["decision_window"] != "initial_owner_choice" for row in rows)
    )
    default_off_equivalence_passed = (
        attempted_count > 0
        and flag_off_count == 0
        and selected_move_delta_count == 0
        and selected_provider_delta_count == 0
        and score_delta_count == 0
        and routing_delta_count == 0
        and not continuation_default_off.get("initial_recommendation_count")
        and not continuation_default_off.get("continuation_recommendation_count")
    )
    if not default_off_equivalence_passed:
        status = "refined_selector_initial_owner_observability_failed_equivalence"
    elif invalid_scope or invalid_metadata:
        status = "refined_selector_initial_owner_observability_invalid_scope"
    elif enabled_count >= attempted_count and set(rec_counts).issuperset(RECOMMENDATION_CLASSES):
        status = "refined_selector_initial_owner_observability_ready_for_recommendation_analysis"
    else:
        status = "refined_selector_initial_owner_observability_wired_default_off_equivalent"

    summary = {
        "attempted_row_count": attempted_count,
        "default_off_equivalence_passed": default_off_equivalence_passed,
        "enabled_recommendation_count": enabled_count,
        "default_off_selector_recommendation_count": flag_off_count,
        "recommendation_counts_by_class": {
            klass: int(rec_counts.get(klass, 0)) for klass in RECOMMENDATION_CLASSES
        },
        "preserve_on_failure_count": sum(
            1 for row in rows if row["preserve_on_selected_owner_failure"]
        ),
        "switch_on_safe_owner_count": sum(1 for row in rows if row["switch_on_safe_owner"]),
        "abstain_count": int(rec_counts.get("abstain_context_only", 0)),
        "abstain_target_count": abstain_target_count,
        "abstain_target_recalled_count": abstain_target_recalled_count,
        "abstain_recall": abstain_recall,
        "continuation_recommendation_count": continuation_recommendation_count,
        "selected_move_delta_count": selected_move_delta_count,
        "selected_provider_delta_count": selected_provider_delta_count,
        "selected_score_delta_count": sum(1 for row in rows if row["selected_score_delta"]),
        "score_delta_count": score_delta_count,
        "routing_delta_count": routing_delta_count,
        "runtime_behavior_changed": False,
        "stage7_training_row_count": sum(1 for row in rows if row["stage7_training_row"]),
        "selector_training_row_count": sum(1 for row in rows if row["selector_training_row"]),
        "runtime_dtm_or_tablebase_use": False,
        "gameplay_topology_mutation": False,
        "hidden_python_controller": False,
        "capacity_label_used_as_ownership_label_count": sum(
            1 for row in rows if row["capacity_label_used_as_ownership_label"]
        ),
        "invalid_metadata_count": len(invalid_metadata),
        "initial_owner_only_scope_count": sum(
            1 for row in rows if row["selector_scope"] == "initial_owner_only"
        ),
        "direct_request_false_count": sum(1 for row in rows if row["direct_request"] is False),
        "score_delta_zero_count": sum(1 for row in rows if row["score_delta"] == 0.0),
        "preserve_failure_risk_refinement_present_count": sum(
            1 for row in rows if row["preserve_failure_risk_refinement_status"]
        ),
        "abstain_guard_present_count": sum(1 for row in rows if row["abstain_guard_status"]),
    }
    return {
        "schema_version": "krk_refined_selector_initial_owner_observability_sandbox.v0",
        "sandbox_id": SANDBOX_ID,
        "causal_status": "recommendation_only_initial_owner_observability_sandbox",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(SCOPE_DECISION),
            "reports/strategy_arbitration/krk_selector_continuation_scope_audit_v0.json",
            "reports/strategy_arbitration/krk_selector_observability_expansion_manifest_v0.json",
        ],
        "approval": {
            "approval_status": "explicitly_approved_trace_only_initial_owner_refined_selector_observability",
            "flag_required": "--enable-krk-refined-selector-observability",
            "scope_decision_status": scope_decision.get("decision", {}).get("status"),
            "behavior_changing_selector_allowed": False,
        },
        "scope": {
            "selector_scope": "initial_owner_only",
            "continuation_recommendations_allowed": False,
            "plan_capsule_continuation_influence_allowed": False,
            "progress_window_reconsideration_influence_allowed": False,
            "move_provider_selection_effect_allowed": False,
        },
        "summary": summary,
        "continuation_scope_probe": {
            "default_off": continuation_default_off,
            "enabled": continuation_enabled,
        },
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
                "non_causal_initial_owner_recommendation_analysis"
                if status
                == "refined_selector_initial_owner_observability_ready_for_recommendation_analysis"
                else "quarantine_initial_owner_observability_sandbox_result"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Refined Selector Initial Owner Observability Sandbox v0",
        "",
        "This report records a default-off, recommendation-only refined selector observability sandbox scoped to the initial owner decision. It does not alter move, provider, score, routing, training, topology, or runtime defaults.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Scope", ""])
    for key, value in payload["scope"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            "- "
            f"`{row.get('row_id') or row.get('case_id')}` "
            f"recommendation=`{row.get('recommendation')}` "
            f"scope=`{row.get('selector_scope')}` "
            f"move_delta={row.get('selected_move_delta')} "
            f"provider_delta={row.get('selected_provider_delta')} "
            f"routing_delta={row.get('routing_delta')}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run default-off initial-owner-only refined selector observability sandbox"
    )
    parser.add_argument(
        "--enable-krk-refined-selector-observability",
        action="store_true",
        help="Execute the explicitly approved trace-only initial-owner refined selector observability sandbox.",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
