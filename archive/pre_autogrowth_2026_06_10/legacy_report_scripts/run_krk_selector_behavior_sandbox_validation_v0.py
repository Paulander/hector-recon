#!/usr/bin/env python3
"""Validate the narrow selector behavior sandbox on protected Stage 5/6 rows."""

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
from scripts.run_krk_selector_behavior_sandbox_v0 import _compact_decision  # noqa: E402
from scripts.test_krk_landmark_progress import choose_move_details, play_to_mate  # noqa: E402


SOURCE_COLLECTION = Path(
    "reports/strategy_arbitration/krk_joined_trace_ownership_collection_v0.json"
)
SMOKE_REPORT = Path("reports/strategy_arbitration/krk_selector_behavior_sandbox_v0.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.md"
)

POSSIBLE_STATUSES = [
    "selector_behavior_sandbox_validation_promising",
    "selector_behavior_sandbox_overfit_to_tiny_target",
    "selector_behavior_sandbox_regresses_safe_controls",
    "selector_behavior_sandbox_failed_default_off_equivalence",
    "selector_behavior_sandbox_needs_more_evidence",
    "selector_behavior_sandbox_ready_for_guardrail_review_packet",
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
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_manifest(collection: dict[str, Any] | None = None) -> dict[str, Any]:
    collection = collection or _load(SOURCE_COLLECTION)
    cases = []
    for row in collection.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("source_stage") not in {"stage5", "stage6"}:
            continue
        cases.append({
            "case_id": row.get("case_id"),
            "row_id": row.get("case_id"),
            "fen": row.get("fen"),
            "source_stage": row.get("source_stage"),
            "active_landmark_label": row.get("active_landmark_label"),
            "selected_owner_label": row.get("selected_owner_label"),
            "selected_provider_label": row.get("selected_provider_label"),
            "recovery_class": row.get("recovery_class"),
            "priority": row.get("priority"),
            "state_id": row.get("state_id"),
            "frame_id": row.get("frame_id"),
            "positive_refresh_frame_count": int(
                row.get("positive_refresh_frame_count", 0) or 0
            ),
            "stage7_training_row": False,
            "selector_training_row": False,
            "capacity_label_used_as_ownership_label": False,
            "h40_validation_role": (
                "switch_contrast"
                if row.get("selected_owner_label") == "selected_owner_failed"
                else "safe_preservation"
            ),
        })
    return {
        "schema_version": "krk_selector_behavior_sandbox_validation_manifest.v0",
        "source_artifacts": [str(SOURCE_COLLECTION), str(SMOKE_REPORT)],
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "stage_counts": dict(sorted(Counter(c["source_stage"] for c in cases).items())),
            "role_counts": dict(
                sorted(Counter(c["h40_validation_role"] for c in cases).items())
            ),
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
        },
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
        krk_selector_behavior_sandbox_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def _run_h40(case: dict[str, Any], enabled: bool) -> dict[str, Any]:
    graph, engine = _new_graph_engine()
    board = chess.Board(str(case["fen"]))
    result = play_to_mate(
        graph,
        engine,
        board,
        random.Random(40),
        str(case["active_landmark_label"]),
        stage_filter=None,
        max_plies=40,
        black_policy="adversarial",
        max_ticks=200,
        suggestion_limit=10,
        early_stop_stable_suggestions=2,
        krk_selector_behavior_sandbox_enabled=enabled,
        enable_diagnostic_caches=True,
    )
    return {
        "result": result.get("result"),
        "plies": result.get("plies"),
        "engine_decision_count": result.get("engine_decision_count"),
        "engine_ticks_total": result.get("engine_ticks_total"),
        "engine_ticks_max": result.get("engine_ticks_max"),
    }


def _h40_improved(default_off: dict[str, Any], enabled: dict[str, Any]) -> bool:
    if default_off.get("result") != "mate" and enabled.get("result") == "mate":
        return True
    if default_off.get("result") == "mate" and enabled.get("result") == "mate":
        return int(enabled.get("plies", 999) or 999) < int(default_off.get("plies", 999) or 999)
    return False


def _h40_regressed(default_off: dict[str, Any], enabled: dict[str, Any]) -> bool:
    if default_off.get("result") == "mate" and enabled.get("result") != "mate":
        return True
    if default_off.get("result") == "mate" and enabled.get("result") == "mate":
        return int(enabled.get("plies", 999) or 999) > int(default_off.get("plies", 999) or 999)
    return False


def build_payload(
    *,
    decision_runner: Callable[[dict[str, Any], bool], dict[str, Any]] | None = None,
    h40_runner: Callable[[dict[str, Any], bool], dict[str, Any]] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    smoke = _load(SMOKE_REPORT)
    manifest = manifest or build_manifest()
    decide = decision_runner or _run_decision
    run_h40 = h40_runner or _run_h40

    rows = []
    for case in manifest.get("cases") or []:
        default_off = decide(case, False)
        enabled = decide(case, True)
        h40_default = run_h40(case, False)
        h40_enabled = run_h40(case, True)
        rec = enabled.get("selector_recommendation") or {}
        behavior = enabled.get("behavior_sandbox_decision") or {}
        action = behavior.get("action") or "not_evaluated"
        switched = action == "switch_to_visible_alternative"
        selected_move_delta = default_off.get("move") != enabled.get("move")
        selected_provider_delta = (
            default_off.get("selected_provider") != enabled.get("selected_provider")
        )
        selected_score_delta = default_off.get("confidence") != enabled.get("confidence")
        target_improved = (
            switched
            and case.get("selected_owner_label") == "selected_owner_failed"
            and rec.get("recommendation") == "prefer_visible_alternative"
        )
        h40_improved = _h40_improved(h40_default, h40_enabled)
        h40_regressed = _h40_regressed(h40_default, h40_enabled)
        direct_safe_regression = switched and case.get("selected_owner_label") == (
            "selected_owner_converted"
        )
        h40_safe_regression = (
            case.get("h40_validation_role") == "safe_preservation" and h40_regressed
        )
        safe_regression = direct_safe_regression or h40_safe_regression
        visible_pairs = {
            (item.get("provider_id"), item.get("move_id"))
            for item in rec.get("visible_alternatives_considered") or []
            if isinstance(item, dict)
        }
        replacement_pair = (
            behavior.get("replacement_provider"),
            behavior.get("replacement_move"),
        )
        rows.append({
            **case,
            "flag_off_decision": default_off,
            "enabled_decision": enabled,
            "flag_off_behavior_metadata_count": int(
                bool(default_off.get("behavior_sandbox_decision_present"))
            ),
            "enabled_behavior_metadata_count": int(bool(behavior)),
            "recommendation": rec.get("recommendation"),
            "behavior_action": action,
            "behavior_veto_reason": behavior.get("veto_reason"),
            "selected_move_delta": selected_move_delta,
            "selected_provider_delta": selected_provider_delta,
            "selected_score_delta": selected_score_delta,
            "score_delta": float(behavior.get("score_delta", 0.0) or 0.0),
            "routing_delta": False,
            "target_improved": target_improved,
            "safe_regression": safe_regression,
            "direct_safe_regression": direct_safe_regression,
            "h40_safe_regression": h40_safe_regression,
            "switch_used_visible_alternative": (
                switched and replacement_pair in visible_pairs
            ),
            "runtime_dtm_or_tablebase": bool(
                behavior.get("runtime_dtm_or_tablebase", False)
            ),
            "gameplay_topology_mutation": bool(
                behavior.get("gameplay_topology_mutation", False)
            ),
            "source_terms": list(behavior.get("source_terms") or []),
            "replacement_provider": behavior.get("replacement_provider"),
            "original_selected_provider": behavior.get("original_selected_provider"),
            "h40_default_off": h40_default,
            "h40_enabled": h40_enabled,
            "h40_improved": h40_improved,
            "h40_regressed": h40_regressed,
            "shadow_candidate_delta": None,
        })

    action_counts = Counter(row["behavior_action"] for row in rows)
    stage_counts = Counter(row["source_stage"] for row in rows)
    provider_counts = Counter(
        row.get("replacement_provider") or row.get("original_selected_provider") or "none"
        for row in rows
    )
    switch_source_terms = sorted({term for row in rows if row["behavior_action"] == "switch_to_visible_alternative" for term in row.get("source_terms") or []})
    selected_move_delta_count = sum(1 for row in rows if row["selected_move_delta"])
    selected_provider_delta_count = sum(1 for row in rows if row["selected_provider_delta"])
    score_delta_count = sum(1 for row in rows if row["score_delta"] != 0.0)
    routing_delta_count = sum(1 for row in rows if row["routing_delta"])
    enabled_switch_count = int(action_counts.get("switch_to_visible_alternative", 0))
    preserve_noop_count = sum(
        1 for row in rows if row["recommendation"] == "preserve_selected_owner" and row["behavior_action"] == "no_op"
    )
    abstain_noop_count = sum(
        1 for row in rows if row["recommendation"] == "abstain_context_only" and row["behavior_action"] == "no_op"
    )
    target_improvement_count = sum(1 for row in rows if row["target_improved"])
    safe_regression_count = sum(1 for row in rows if row["safe_regression"])
    invalid_switch_count = sum(
        1
        for row in rows
        if row["behavior_action"] == "switch_to_visible_alternative"
        and (
            row["recommendation"] != "prefer_visible_alternative"
            or not row["switch_used_visible_alternative"]
        )
    )
    default_off_equivalence_passed = (
        bool(rows)
        and sum(row["flag_off_behavior_metadata_count"] for row in rows) == 0
        and score_delta_count == 0
        and routing_delta_count == 0
        and not any(row["runtime_dtm_or_tablebase"] for row in rows)
        and not any(row["gameplay_topology_mutation"] for row in rows)
    )
    h40_improvement_count = sum(1 for row in rows if row["h40_improved"])
    h40_regression_count = sum(1 for row in rows if row["h40_regressed"])
    if not default_off_equivalence_passed:
        status = "selector_behavior_sandbox_failed_default_off_equivalence"
    elif safe_regression_count or h40_regression_count:
        status = "selector_behavior_sandbox_regresses_safe_controls"
    elif invalid_switch_count:
        status = "selector_behavior_sandbox_needs_more_evidence"
    elif enabled_switch_count <= 0:
        status = "selector_behavior_sandbox_overfit_to_tiny_target"
    elif target_improvement_count > 0 and h40_improvement_count > 0 and len(rows) >= 20:
        status = "selector_behavior_sandbox_ready_for_guardrail_review_packet"
    elif target_improvement_count > 0:
        status = "selector_behavior_sandbox_validation_promising"
    else:
        status = "selector_behavior_sandbox_needs_more_evidence"

    summary = {
        "sample_count": len(rows),
        "sample_scope": "stage5_6_protected_joined_trace_h40",
        "default_off_equivalence_passed": default_off_equivalence_passed,
        "enabled_switch_count": enabled_switch_count,
        "target_improvement_count": target_improvement_count,
        "safe_regression_count": safe_regression_count,
        "preserve_noop_count": preserve_noop_count,
        "abstain_noop_count": abstain_noop_count,
        "selected_move_delta_count": selected_move_delta_count,
        "selected_provider_delta_count": selected_provider_delta_count,
        "score_delta_count": score_delta_count,
        "routing_delta_count": routing_delta_count,
        "h40_improvement_count": h40_improvement_count,
        "h40_regression_count": h40_regression_count,
        "mate_max_plies_before_vs_after": [
            {
                "row_id": row["row_id"],
                "before": row["h40_default_off"],
                "after": row["h40_enabled"],
            }
            for row in rows
        ],
        "shadow_candidate_delta_available": False,
        "per_stage_breakdown": dict(sorted(stage_counts.items())),
        "per_provider_breakdown": dict(sorted(provider_counts.items())),
        "switch_source_term_coverage": switch_source_terms,
        "invalid_switch_count": invalid_switch_count,
        "stage7_training_row_count": 0,
        "selector_training_row_count": 0,
        "runtime_dtm_or_tablebase": False,
        "topology_mutation": False,
        "capacity_label_used_as_ownership_label_count": 0,
    }
    return {
        "schema_version": "krk_selector_behavior_sandbox_validation.v0",
        "causal_status": "protected_behavior_sandbox_validation_no_promotion",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(SOURCE_COLLECTION), str(SMOKE_REPORT)],
        "summary": summary,
        "rows": rows,
        "possible_statuses": POSSIBLE_STATUSES,
        "decision": {
            "status": status,
            "promote": False,
            "make_default": False,
            "run_full_broad_guardrails": (
                status == "selector_behavior_sandbox_ready_for_guardrail_review_packet"
            ),
            "write_guardrail_review_packet_only_if_ready": (
                status == "selector_behavior_sandbox_ready_for_guardrail_review_packet"
            ),
            "train_anything": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "prior_smoke_status": smoke.get("decision", {}).get("status"),
    }


def write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selector Behavior Sandbox Validation v0",
        "",
        "This report validates the existing default-off narrow selector behavior sandbox on protected Stage 5/6 rows with h40 playout comparison. It does not promote, make default, train, or broaden selector logic.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        if key == "mate_max_plies_before_vs_after":
            continue
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            "- "
            f"`{row['row_id']}` stage={row['source_stage']} role={row['h40_validation_role']} "
            f"recommendation=`{row['recommendation']}` action=`{row['behavior_action']}` "
            f"target_improved={row['target_improved']} safe_regression={row['safe_regression']} "
            f"h40={row['h40_default_off']['result']}->{row['h40_enabled']['result']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate selector behavior sandbox on protected Stage 5/6 sample"
    )
    parser.add_argument(
        "--execute-protected-validation",
        action="store_true",
        help="Execute the protected h40 validation for the existing default-off sandbox.",
    )
    args = parser.parse_args()
    if not args.execute_protected_validation:
        raise SystemExit("refusing_to_execute_without_--execute-protected-validation")
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
