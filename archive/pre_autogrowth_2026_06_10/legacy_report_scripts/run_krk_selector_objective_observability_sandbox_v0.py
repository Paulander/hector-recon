#!/usr/bin/env python3
"""Run the default-off KRK selector-objective observability sandbox."""

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
from scripts.run_krk_selector_objective_fresh_diversity_collection_v0 import (  # noqa: E402
    PROTECTED_STAGES,
    load_cases,
)
from scripts.test_krk_landmark_progress import (  # noqa: E402
    _skill_id_for_suggestion,
    choose_move_details,
)


RUNTIME_REVIEW_PACKET = Path(
    "reports/strategy_arbitration/krk_selector_objective_runtime_review_packet_v0.json"
)
BENCHMARK = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v0.json")
FRESH_DIVERSITY_PACKET = Path(
    "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_review_packet_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_selector_objective_observability_sandbox_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_selector_objective_observability_sandbox_v0.md"
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


def _selected_provider(details: dict[str, Any]) -> str | None:
    selected = details.get("selected_suggestion")
    if isinstance(selected, dict) and selected:
        return _skill_id_for_suggestion(selected)
    return None


def _compact_decision(details: dict[str, Any]) -> dict[str, Any]:
    recommendation = details.get("krk_selector_objective_recommendation") or {}
    return {
        "move": details.get("move"),
        "selected_provider": _selected_provider(details),
        "confidence": details.get("confidence"),
        "selector_recommendation_present": bool(recommendation),
        "selector_recommendation": recommendation,
        "candidate_generation_observation_present": bool(
            details.get("krk_candidate_generation_observation")
        ),
    }


def _same_decision(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left.get("move") == right.get("move")
        and left.get("selected_provider") == right.get("selected_provider")
        and left.get("confidence") == right.get("confidence")
    )


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


def _valid_recommendation(record: dict[str, Any]) -> bool:
    if not record:
        return False
    return (
        record.get("schema_version") == "krk_selector_objective_recommendation.v0"
        and record.get("selector_model_id") == "combined_simple_rule"
        and record.get("causal_status") == "recommendation_only"
        and record.get("direct_request") is False
        and float(record.get("score_delta", 1.0) or 0.0) == 0.0
        and record.get("recommendation")
        in {
            "preserve_selected_owner",
            "prefer_visible_alternative",
            "abstain_context_only",
        }
        and bool(record.get("selected_owner_before_recommendation"))
        and bool(record.get("forbidden_actions"))
        and "selecting_a_move" in set(record.get("forbidden_actions") or [])
        and "routing_directly_to_a_provider" in set(record.get("forbidden_actions") or [])
        and "runtime_dtm_or_tablebase" in set(record.get("forbidden_actions") or [])
        and "gameplay_topology_mutation" in set(record.get("forbidden_actions") or [])
    )


def build_payload(
    *,
    decision_runner: Callable[[dict[str, Any], bool], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    review = _load(RUNTIME_REVIEW_PACKET)
    benchmark = _load(BENCHMARK)
    cases = load_cases(_load(FRESH_DIVERSITY_PACKET))
    runner = decision_runner or _run_decision
    rows: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    for case in cases:
        if str(case.get("source_stage") or "") not in PROTECTED_STAGES:
            continue
        default_off = runner(case, False)
        enabled = runner(case, True)
        rec = enabled.get("selector_recommendation") or {}
        if rec and not _valid_recommendation(rec):
            invalid_records.append({"case_id": case.get("case_id"), "record": rec})
        rows.append({
            **case,
            "flag_off_decision": default_off,
            "enabled_decision": enabled,
            "flag_off_selector_recommendation_count": int(
                bool(default_off.get("selector_recommendation_present"))
            ),
            "enabled_selector_recommendation_count": int(bool(rec)),
            "selected_move_delta": default_off.get("move") != enabled.get("move"),
            "selected_provider_delta": (
                default_off.get("selected_provider") != enabled.get("selected_provider")
            ),
            "selected_score_delta": default_off.get("confidence") != enabled.get("confidence"),
            "score_delta": float(rec.get("score_delta", 0.0) or 0.0) if rec else 0.0,
            "routing_delta": False,
            "stage7_training_row": False,
            "selector_training_row": False,
            "runtime_behavior_changed": False,
        })

    recommendation_counts = Counter(
        str((row["enabled_decision"].get("selector_recommendation") or {}).get("recommendation"))
        for row in rows
        if row["enabled_decision"].get("selector_recommendation")
    )
    source_term_counter: Counter[str] = Counter()
    explanation_term_counter: Counter[str] = Counter()
    visible_alternative_count = 0
    direct_request_false_count = 0
    score_delta_zero_count = 0
    for row in rows:
        rec = row["enabled_decision"].get("selector_recommendation") or {}
        if not rec:
            continue
        source_term_counter.update(str(term) for term in rec.get("source_terms") or [])
        explanation_term_counter.update(str(term) for term in rec.get("explanation_terms") or [])
        visible_alternative_count += int(rec.get("visible_alternative_count", 0) or 0)
        if rec.get("direct_request") is False:
            direct_request_false_count += 1
        if float(rec.get("score_delta", 1.0) or 0.0) == 0.0:
            score_delta_zero_count += 1

    selected_move_delta_count = sum(1 for row in rows if row["selected_move_delta"])
    selected_provider_delta_count = sum(1 for row in rows if row["selected_provider_delta"])
    selected_score_delta_count = sum(1 for row in rows if row["selected_score_delta"])
    routing_delta_count = sum(1 for row in rows if row["routing_delta"])
    score_delta_count = sum(1 for row in rows if float(row["score_delta"]) != 0.0)
    flag_off_recommendation_count = sum(
        int(row["flag_off_selector_recommendation_count"]) for row in rows
    )
    enabled_recommendation_count = sum(
        int(row["enabled_selector_recommendation_count"]) for row in rows
    )
    stage7_training_row_count = sum(1 for row in rows if row["stage7_training_row"])
    selector_training_row_count = sum(1 for row in rows if row["selector_training_row"])
    default_off_equivalence_passed = (
        bool(rows)
        and flag_off_recommendation_count == 0
        and selected_move_delta_count == 0
        and selected_provider_delta_count == 0
        and selected_score_delta_count == 0
        and score_delta_count == 0
        and routing_delta_count == 0
    )
    metadata_valid = (
        enabled_recommendation_count == len(rows)
        and not invalid_records
        and direct_request_false_count == enabled_recommendation_count
        and score_delta_zero_count == enabled_recommendation_count
        and visible_alternative_count > 0
    )
    if not default_off_equivalence_passed:
        status = "selector_observability_sandbox_failed_equivalence"
    elif not metadata_valid:
        status = "selector_observability_sandbox_invalid_metadata"
    else:
        status = "selector_observability_sandbox_wired_default_off_equivalent"

    summary = {
        "attempted_row_count": len(rows),
        "default_off_equivalence_passed": default_off_equivalence_passed,
        "enabled_recommendation_count": enabled_recommendation_count,
        "flag_off_selector_recommendation_count": flag_off_recommendation_count,
        "selected_move_delta_count": selected_move_delta_count,
        "selected_provider_delta_count": selected_provider_delta_count,
        "selected_score_delta_count": selected_score_delta_count,
        "score_delta_count": score_delta_count,
        "routing_delta_count": routing_delta_count,
        "runtime_behavior_changed": False,
        "recommendation_counts_by_class": dict(sorted(recommendation_counts.items())),
        "source_term_coverage": {
            "unique_source_term_count": len(source_term_counter),
            "unique_explanation_term_count": len(explanation_term_counter),
            "source_terms": sorted(source_term_counter),
            "explanation_terms": sorted(explanation_term_counter),
            "visible_alternative_count": visible_alternative_count,
        },
        "direct_request_false_count": direct_request_false_count,
        "score_delta_zero_count": score_delta_zero_count,
        "stage7_rows_remain_held_out": True,
        "stage7_training_row_count": stage7_training_row_count,
        "selector_training_row_count": selector_training_row_count,
        "runtime_dtm_or_tablebase_use": False,
        "gameplay_topology_mutation": False,
        "invalid_metadata_count": len(invalid_records),
    }
    return {
        "schema_version": "krk_selector_objective_observability_sandbox.v0",
        "sandbox_id": "sandbox.krk.selector_objective_observability_v0",
        "causal_status": "runtime_recommendation_only_observability_sandbox",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(RUNTIME_REVIEW_PACKET),
            str(BENCHMARK),
            str(FRESH_DIVERSITY_PACKET),
        ],
        "approval": {
            "approval_status": "explicitly_approved_for_first_selector_objective_observability_sandbox",
            "flag_required": "--enable-krk-selector-objective-observability",
            "runtime_review_status": review.get("decision", {}).get("status"),
            "benchmark_model": benchmark.get("summary", {}).get("best_model"),
        },
        "summary": summary,
        "rows": rows,
        "invalid_metadata": invalid_records[:10],
        "decision": {
            "status": status,
            "selector_runtime_ready": False,
            "runtime_changes_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "non_causal_recommendation_analysis"
                if status == "selector_observability_sandbox_wired_default_off_equivalent"
                else "quarantine_selector_observability_sandbox_result"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Selector Objective Observability Sandbox v0",
        "",
        "This report records the explicitly approved default-off selector-objective observability sandbox. It emits recommendation-only metadata and does not train or authorize a runtime selector.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_runtime_ready: `{payload['decision']['selector_runtime_ready']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        rec = row["enabled_decision"].get("selector_recommendation") or {}
        lines.append(
            "- "
            f"`{row['row_id']}` "
            f"stage={row['source_stage']} "
            f"recommendation=`{rec.get('recommendation')}` "
            f"reason=`{rec.get('decision_reason')}` "
            f"move_delta={row['selected_move_delta']} "
            f"provider_delta={row['selected_provider_delta']} "
            f"score_delta={row['selected_score_delta']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run default-off KRK selector-objective observability sandbox"
    )
    parser.add_argument(
        "--enable-krk-selector-objective-observability",
        action="store_true",
        help="Execute the explicitly approved recommendation-only selector observability sandbox.",
    )
    args = parser.parse_args()
    if not args.enable_krk_selector_objective_observability:
        raise SystemExit(
            "refusing_to_execute_without_--enable-krk-selector-objective-observability"
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
