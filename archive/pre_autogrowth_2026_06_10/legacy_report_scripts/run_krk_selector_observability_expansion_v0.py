#!/usr/bin/env python3
"""Expand selector-objective observability over protected Stage 4/5/6 rows."""

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
from scripts.test_krk_landmark_progress import (  # noqa: E402
    _skill_id_for_suggestion,
    choose_move_details,
)


STAGE4_COLLECTION = Path(
    "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_collection_v0.json"
)
FRESH_COLLECTION = Path(
    "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_collection_v0.json"
)
PRIOR_ANALYSIS = Path(
    "reports/strategy_arbitration/krk_selector_objective_recommendation_analysis_v0.json"
)
NEXT_GATE = Path("reports/strategy_arbitration/krk_selector_objective_next_gate_v0.json")
SEED_MANIFEST = Path(
    "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json"
)
OUT_MANIFEST_JSON = Path(
    "reports/strategy_arbitration/krk_selector_observability_expansion_manifest_v0.json"
)
OUT_MANIFEST_MD = Path(
    "reports/strategy_arbitration/krk_selector_observability_expansion_manifest_v0.md"
)
OUT_EXPANDED_JSON = Path(
    "reports/strategy_arbitration/krk_selector_observability_expanded_recommendations_v0.json"
)
OUT_EXPANDED_MD = Path(
    "reports/strategy_arbitration/krk_selector_observability_expanded_recommendations_v0.md"
)
OUT_REVIEW_JSON = Path(
    "reports/strategy_arbitration/krk_selector_observability_readiness_review_v0.json"
)
OUT_REVIEW_MD = Path(
    "reports/strategy_arbitration/krk_selector_observability_readiness_review_v0.md"
)

RECOMMENDATION_CLASSES = (
    "preserve_selected_owner",
    "prefer_visible_alternative",
    "abstain_context_only",
)
PROTECTED_STAGES = {"stage4", "stage5", "stage6"}
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


def _selected_provider(details: dict[str, Any]) -> str | None:
    selected = details.get("selected_suggestion")
    if isinstance(selected, dict) and selected:
        return _skill_id_for_suggestion(selected)
    return None


def _compact_decision(details: dict[str, Any]) -> dict[str, Any]:
    return {
        "move": details.get("move"),
        "selected_provider": _selected_provider(details),
        "confidence": details.get("confidence"),
        "selector_recommendation": details.get("krk_selector_objective_recommendation")
        or {},
        "selector_recommendation_present": bool(
            details.get("krk_selector_objective_recommendation")
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
        krk_selector_objective_observability_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def _stage4_cases(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    for row in payload.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("source_stage") != "stage4":
            continue
        if not row.get("fen"):
            continue
        cases.append({
            "case_id": row.get("case_id"),
            "row_id": row.get("case_id"),
            "state_id": row.get("state_id"),
            "frame_id": row.get("frame_id"),
            "fen": row.get("fen"),
            "source_stage": "stage4",
            "active_landmark_label": row.get("active_landmark_label"),
            "selected_owner_label": row.get("selected_owner_label"),
            "selected_provider_label": row.get("selected_provider_label"),
            "objective_channel": (
                "candidate_switch_contrast_seed"
                if int(row.get("positive_capacity_frame_count", 0) or 0) > 0
                else "failure_context_without_candidate_seed"
            ),
            "source_type": "stage4_joined_trace_ownership_collection",
            "target_collection_goal": (
                "switch_contrast_observation"
                if int(row.get("positive_capacity_frame_count", 0) or 0) > 0
                else "abstain_context_observation"
            ),
            "positive_capacity_frame_count": int(
                row.get("positive_capacity_frame_count", 0) or 0
            ),
            "stage7_training_row": False,
            "selector_training_row": False,
            "capacity_label_used_as_ownership_label": False,
        })
    return cases


def _fresh_cases(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    for row in payload.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("source_stage") or "") not in {"stage5", "stage6"}:
            continue
        if not row.get("fen"):
            continue
        cases.append({
            "case_id": row.get("case_id"),
            "row_id": row.get("row_id"),
            "state_id": row.get("state_id"),
            "frame_id": row.get("frame_id"),
            "fen": row.get("fen"),
            "source_stage": row.get("source_stage"),
            "active_landmark_label": row.get("active_landmark_label"),
            "selected_owner_label": row.get("selected_owner_label"),
            "selected_provider_label": row.get("selected_provider_label"),
            "objective_channel": row.get("objective_channel"),
            "source_type": row.get("source_type"),
            "target_collection_goal": row.get("target_collection_goal"),
            "positive_capacity_frame_count": int(
                row.get("positive_capacity_frame_count", 0) or 0
            ),
            "stage7_training_row": False,
            "selector_training_row": False,
            "capacity_label_used_as_ownership_label": False,
        })
    return cases


def build_manifest(
    *,
    stage4_collection: dict[str, Any] | None = None,
    fresh_collection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage4_collection = stage4_collection or _load(STAGE4_COLLECTION)
    fresh_collection = fresh_collection or _load(FRESH_COLLECTION)
    cases = _stage4_cases(stage4_collection) + _fresh_cases(fresh_collection)
    stage_counts = Counter(str(case.get("source_stage") or "") for case in cases)
    owner_counts = Counter(str(case.get("selected_owner_label") or "") for case in cases)
    channel_counts = Counter(str(case.get("objective_channel") or "") for case in cases)
    non_stage0_owner_count = sum(
        1
        for case in cases
        if case.get("selected_provider_label")
        and case.get("selected_provider_label") != "krk.stage0_basin"
    )
    manifest_ready = (
        bool(cases)
        and set(stage_counts).issubset(PROTECTED_STAGES)
        and channel_counts["failure_context_without_candidate_seed"] > 0
        and channel_counts["candidate_switch_contrast_seed"] > 0
        and (
            channel_counts["safe_preservation_contrast_seed"]
            + channel_counts["progress_window_failure_contrast_candidate"]
        )
        > 0
    )
    return {
        "schema_version": "krk_selector_observability_expansion_manifest.v0",
        "causal_status": "non_causal_observation_manifest",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(PRIOR_ANALYSIS), str(NEXT_GATE), str(STAGE4_COLLECTION), str(FRESH_COLLECTION)],
        "summary": {
            "case_count": len(cases),
            "stage_counts": dict(sorted(stage_counts.items())),
            "selected_owner_counts": dict(sorted(owner_counts.items())),
            "objective_channel_counts": dict(sorted(channel_counts.items())),
            "non_stage0_owner_count": non_stage0_owner_count,
            "stage7_training_row_count": sum(
                1 for case in cases if case.get("stage7_training_row")
            ),
            "selector_training_row_count": sum(
                1 for case in cases if case.get("selector_training_row")
            ),
            "capacity_label_used_as_ownership_label_count": sum(
                1 for case in cases if case.get("capacity_label_used_as_ownership_label")
            ),
            "replay_free_recovery_used_first": True,
            "bounded_observation_run_needed": True,
        },
        "cases": cases,
        "decision": {
            "status": (
                "selector_observability_expansion_manifest_ready"
                if manifest_ready
                else "selector_observability_expansion_manifest_underpowered"
            ),
            "runtime_changes_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "execute_without_separate_runtime_behavior_approval": True,
            "behavior_changing_selector_allowed": False,
        },
    }


def _offline_target(row: dict[str, Any], rec: dict[str, Any]) -> str:
    if int(rec.get("positive_trace_provider_candidate_count", 0) or 0) <= 0:
        return "abstain_context_only"
    if row.get("selected_owner_label") == "selected_owner_failed":
        return "prefer_visible_alternative"
    if row.get("selected_owner_label") == "selected_owner_converted":
        return "preserve_selected_owner"
    return "abstain_context_only"


def build_expanded(
    manifest: dict[str, Any],
    *,
    decision_runner: Callable[[dict[str, Any], bool], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    runner = decision_runner or _run_decision
    rows = []
    for case in manifest.get("cases") or []:
        default_off = runner(case, False)
        enabled = runner(case, True)
        rec = enabled.get("selector_recommendation") or {}
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
            "offline_target_action": _offline_target(case, rec),
            "recommendation_aligns_with_offline_label": (
                rec.get("recommendation") == _offline_target(case, rec)
            ),
            "preserve_on_selected_owner_failure": (
                rec.get("recommendation") == "preserve_selected_owner"
                and case.get("selected_owner_label") == "selected_owner_failed"
            ),
            "switch_on_safe_owner": (
                rec.get("recommendation") == "prefer_visible_alternative"
                and case.get("selected_owner_label") == "selected_owner_converted"
            ),
            "abstain_weak_evidence": (
                rec.get("recommendation") == "abstain_context_only"
                and int(rec.get("positive_trace_provider_candidate_count", 0) or 0) <= 0
            ),
            "visible_alternative_count": int(rec.get("visible_alternative_count", 0) or 0),
            "source_terms": list(rec.get("source_terms") or []),
            "explanation_terms": list(rec.get("explanation_terms") or []),
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
        })
    rec_counts = Counter(str(row.get("recommendation") or "") for row in rows)
    source_terms = sorted({term for row in rows for term in row.get("source_terms") or []})
    explanation_terms = sorted(
        {term for row in rows for term in row.get("explanation_terms") or []}
    )
    selected_move_delta_count = sum(1 for row in rows if row["selected_move_delta"])
    selected_provider_delta_count = sum(1 for row in rows if row["selected_provider_delta"])
    selected_score_delta_count = sum(1 for row in rows if row["selected_score_delta"])
    score_delta_count = sum(1 for row in rows if row["score_delta"] != 0.0)
    routing_delta_count = sum(1 for row in rows if row["routing_delta"])
    summary = {
        "attempted_row_count": len(rows),
        "recommendation_count_by_class": {
            klass: int(rec_counts.get(klass, 0)) for klass in RECOMMENDATION_CLASSES
        },
        "preserve_on_failure_count": sum(
            1 for row in rows if row["preserve_on_selected_owner_failure"]
        ),
        "switch_on_safe_owner_count": sum(1 for row in rows if row["switch_on_safe_owner"]),
        "abstain_recommendation_count": int(rec_counts.get("abstain_context_only", 0)),
        "abstain_weak_evidence_count": sum(
            1 for row in rows if row["abstain_weak_evidence"]
        ),
        "offline_label_alignment_count": sum(
            1 for row in rows if row["recommendation_aligns_with_offline_label"]
        ),
        "offline_label_mismatch_count": sum(
            1 for row in rows if not row["recommendation_aligns_with_offline_label"]
        ),
        "rows_with_visible_alternatives": sum(
            1 for row in rows if row["visible_alternative_count"] > 0
        ),
        "source_term_coverage": {
            "unique_source_term_count": len(source_terms),
            "unique_explanation_term_count": len(explanation_terms),
            "source_terms": source_terms,
            "explanation_terms": explanation_terms,
        },
        "stage7_training_row_count": sum(1 for row in rows if row["stage7_training_row"]),
        "selector_training_row_count": sum(1 for row in rows if row["selector_training_row"]),
        "capacity_label_used_as_ownership_label_count": sum(
            1 for row in rows if row["capacity_label_used_as_ownership_label"]
        ),
        "selected_move_delta_count": selected_move_delta_count,
        "selected_provider_delta_count": selected_provider_delta_count,
        "selected_score_delta_count": selected_score_delta_count,
        "score_delta_count": score_delta_count,
        "routing_delta_count": routing_delta_count,
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_use": False,
        "gameplay_topology_mutation": False,
        "default_off_selector_recommendation_count": sum(
            int(row["flag_off_selector_recommendation_count"]) for row in rows
        ),
        "trace_only_recommendation_count": sum(
            1
            for row in rows
            if row["causal_status"] == "recommendation_only"
            and row["direct_request"] is False
            and row["score_delta"] == 0.0
        ),
    }
    return {
        "schema_version": "krk_selector_observability_expanded_recommendations.v0",
        "causal_status": "non_causal_expanded_recommendation_observation",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(OUT_MANIFEST_JSON), str(STAGE4_COLLECTION), str(FRESH_COLLECTION)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "selector_observability_expanded_recommendations_complete",
            "runtime_changes_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "behavior_changing_selector_allowed": False,
        },
    }


def build_review(expanded: dict[str, Any]) -> dict[str, Any]:
    summary = expanded["summary"]
    no_runtime_deltas = all(
        int(summary.get(key, 0) or 0) == 0
        for key in (
            "selected_move_delta_count",
            "selected_provider_delta_count",
            "selected_score_delta_count",
            "score_delta_count",
            "routing_delta_count",
            "stage7_training_row_count",
            "selector_training_row_count",
            "capacity_label_used_as_ownership_label_count",
            "default_off_selector_recommendation_count",
        )
    )
    abstain_count = int(summary["recommendation_count_by_class"]["abstain_context_only"])
    preserve_failure_count = int(summary["preserve_on_failure_count"])
    switch_safe_count = int(summary["switch_on_safe_owner_count"])
    if not no_runtime_deltas:
        status = "selector_path_architecture_review_required"
    elif preserve_failure_count > 0:
        status = "selector_observability_blocked_by_preserve_failure_risk"
    elif abstain_count <= 0:
        status = "selector_observability_blocked_by_no_abstain_cases"
    elif switch_safe_count > 0:
        status = "selector_observability_data_improved_not_runtime_ready"
    else:
        status = "selector_observability_ready_for_runtime_review_packet"
    return {
        "schema_version": "krk_selector_observability_readiness_review.v0",
        "causal_status": "non_causal_readiness_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(OUT_EXPANDED_JSON), str(OUT_MANIFEST_JSON), str(SEED_MANIFEST)],
        "summary": {
            **summary,
            "class_balance": summary["recommendation_count_by_class"],
            "no_runtime_deltas": no_runtime_deltas,
            "stage7_remains_held_out": summary["stage7_training_row_count"] == 0,
            "evidence_improved_over_prior": abstain_count > 0,
            "ready_for_runtime_review_packet": (
                status == "selector_observability_ready_for_runtime_review_packet"
            ),
        },
        "missing_or_blocking_evidence": [
            *(
                ["preserve_selected_owner still appears on selected-owner failure rows"]
                if preserve_failure_count
                else []
            ),
            *(
                ["abstain_context_only runtime observations are still missing"]
                if abstain_count <= 0
                else []
            ),
            *(
                ["prefer_visible_alternative appears on safe-owner rows"]
                if switch_safe_count
                else []
            ),
        ],
        "decision": {
            "status": status,
            "runtime_changes_allowed": False,
            "selector_runtime_ready": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "future_behavior_changing_selector_review_packet_allowed": (
                status == "selector_observability_ready_for_runtime_review_packet"
            ),
            "recommended_next_step": (
                "write_runtime_review_packet_only"
                if status == "selector_observability_ready_for_runtime_review_packet"
                else "review_preserve_failure_risk_before_any_behavior_changing_selector"
            ),
        },
    }


def _write_md(path: Path, title: str, payload: dict[str, Any], rows_key: str) -> None:
    lines = [f"# {title}", "", "## Decision", ""]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    if rows_key in payload:
        lines.extend(["", "## Rows", ""])
        for row in payload[rows_key]:
            lines.append(
                "- "
                f"`{row.get('row_id') or row.get('case_id')}` "
                f"stage={row.get('source_stage')} "
                f"owner={row.get('selected_owner_label')} "
                f"recommendation=`{row.get('recommendation', '')}` "
                f"target=`{row.get('offline_target_action', '')}`"
            )
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_artifacts(manifest: dict[str, Any], expanded: dict[str, Any], review: dict[str, Any]) -> None:
    for path, payload in (
        (OUT_MANIFEST_JSON, manifest),
        (OUT_EXPANDED_JSON, expanded),
        (OUT_REVIEW_JSON, review),
    ):
        (ROOT / path).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _write_md(
        OUT_MANIFEST_MD,
        "KRK Selector Observability Expansion Manifest v0",
        manifest,
        "cases",
    )
    _write_md(
        OUT_EXPANDED_MD,
        "KRK Selector Observability Expanded Recommendations v0",
        expanded,
        "rows",
    )
    _write_md(
        OUT_REVIEW_MD,
        "KRK Selector Observability Readiness Review v0",
        review,
        "rows",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run bounded selector-objective observability expansion"
    )
    parser.add_argument(
        "--execute-observation-only",
        action="store_true",
        help="Execute the bounded trace-only observation expansion.",
    )
    args = parser.parse_args()
    if not args.execute_observation_only:
        raise SystemExit("refusing_to_execute_without_--execute-observation-only")
    manifest = build_manifest()
    expanded = build_expanded(manifest)
    review = build_review(expanded)
    write_artifacts(manifest, expanded, review)
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
