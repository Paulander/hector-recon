#!/usr/bin/env python3
"""Run approved Stage 5/6 selector-objective diversity observation collection.

This runner consumes the fresh diversity review packet and uses the existing
candidate-generation observability path to emit evidence frames. It does not
train a selector, alter routing or scores, change runtime defaults, promote
Stage 7, or train Stage 8.
"""

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
    _compact_decision,
    _new_graph_engine,
    _profile_kwargs,
    _same_decision,
)
from scripts.test_krk_landmark_progress import choose_move_details  # noqa: E402


PACKET = Path(
    "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_review_packet_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_collection_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_collection_v0.md"
)

PROTECTED_STAGES = {"stage5", "stage6"}
EXCLUDED_STAGES = {"stage4", "stage7", "stage8"}

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


def load_cases(packet: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    packet = packet or _load(PACKET)
    if packet.get("schema_version") != "krk_selector_objective_fresh_diversity_review_packet.v0":
        raise ValueError("unexpected_fresh_diversity_review_packet_schema")
    if packet.get("decision", {}).get("status") != (
        "fresh_stage5_stage6_diversity_collection_review_ready"
    ):
        raise ValueError("fresh_diversity_review_packet_not_ready")

    cases: list[dict[str, Any]] = []
    for row in packet.get("candidate_rows") or []:
        if not isinstance(row, dict):
            continue
        stage = str(row.get("source_stage") or "")
        if stage in EXCLUDED_STAGES or stage not in PROTECTED_STAGES:
            continue
        cases.append(
            {
                "case_id": f"fresh_selector_objective_diversity_{len(cases) + 1}",
                "row_id": row.get("row_id"),
                "state_id": row.get("state_id"),
                "frame_id": row.get("frame_id"),
                "source_type": row.get("source_type"),
                "fen": row.get("fen"),
                "source_stage": stage,
                "active_landmark_label": row.get("active_landmark_label"),
                "selected_provider_label": row.get("selected_provider"),
                "selected_owner_label": row.get("selected_owner_label"),
                "objective_channel": row.get("objective_channel"),
                "target_collection_goal": row.get("target_collection_goal"),
                "capacity_label_used_as_ownership_label": False,
                "stage7_training_row": False,
            }
        )
    return cases[:8]


def _run_decision(case: dict[str, Any], *, enabled: bool) -> dict[str, Any]:
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
        krk_candidate_generation_observability_enabled=enabled,
        krk_stage5_6_candidate_generation_refresh_enabled=enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def _frames(decision: dict[str, Any]) -> list[dict[str, Any]]:
    observation = decision.get("observation") or {}
    return [frame for frame in observation.get("frames") or [] if isinstance(frame, dict)]


def _refresh_frames(decision: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        frame
        for frame in _frames(decision)
        if frame.get("candidate_source") == "stage_conditioned_candidate_generation_refresh"
    ]


def _positive_frames(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        frame
        for frame in frames
        if str(frame.get("capacity_evidence_kind") or "").startswith("positive_capacity")
    ]


def _score_changed(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left.get("confidence") != right.get("confidence")


def _frame_valid(frame: dict[str, Any]) -> bool:
    return (
        frame.get("candidate_source") == "stage_conditioned_candidate_generation_refresh"
        and frame.get("policy") == "trace_stage_family_context"
        and frame.get("direct_request") is False
        and float(frame.get("score_delta", 1.0) or 0.0) == 0.0
        and frame.get("causal_status") == "candidate_generation_only"
        and frame.get("protected_status") == "protected_control"
        and str(frame.get("stage") or "") in PROTECTED_STAGES
    )


def _recovery_class(case: dict[str, Any], positive_count: int) -> str:
    if case.get("selected_owner_label") == "selected_owner_failed" and positive_count:
        return "selected_failure_with_visible_positive_capacity"
    if case.get("selected_owner_label") == "selected_owner_converted" and positive_count:
        return "safe_preservation_with_visible_positive_capacity"
    if case.get("selected_owner_label") == "selected_owner_failed":
        return "selected_failure_trace_context_only"
    return "safe_preservation_trace_context_only"


def build_payload(
    *,
    packet: dict[str, Any] | None = None,
    decision_runner: Callable[[dict[str, Any], bool], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    packet = packet or _load(PACKET)
    cases = load_cases(packet)
    runner = decision_runner or (lambda case, enabled: _run_decision(case, enabled=enabled))
    rows: list[dict[str, Any]] = []
    invalid_frames: list[dict[str, Any]] = []
    for case in cases:
        baseline = runner(case, False)
        enabled = runner(case, True)
        refresh = _refresh_frames(enabled)
        positive = _positive_frames(refresh)
        invalid_frames.extend(frame for frame in refresh if not _frame_valid(frame))
        rows.append(
            {
                **case,
                "baseline_decision": baseline,
                "enabled_decision": enabled,
                "baseline_refresh_frame_count": len(_refresh_frames(baseline)),
                "enabled_refresh_frame_count": len(refresh),
                "positive_capacity_frame_count": len(positive),
                "enabled_refresh_frames": refresh,
                "selected_move_delta": baseline.get("move") != enabled.get("move"),
                "selected_provider_delta": (
                    baseline.get("selected_provider") != enabled.get("selected_provider")
                ),
                "selected_score_delta": _score_changed(baseline, enabled),
                "selected_move_provider_score_equivalent": _same_decision(baseline, enabled),
                "routing_delta": False,
                "joined_trace_ownership_row": len(refresh) > 0,
                "recovery_class": _recovery_class(case, len(positive)),
                "capacity_label_used_as_ownership_label": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "stage7_training_row": False,
            }
        )

    joined = [row for row in rows if row["joined_trace_ownership_row"]]
    stage_counts = Counter(str(row.get("source_stage") or "unknown") for row in rows)
    owner_counts = Counter(str(row.get("selected_owner_label") or "unknown") for row in rows)
    channel_counts = Counter(str(row.get("objective_channel") or "unknown") for row in rows)
    provider_counts = Counter(str(row.get("selected_provider_label") or "unknown") for row in rows)
    recovery_counts = Counter(str(row.get("recovery_class") or "unknown") for row in joined)
    frame_stage_counts: Counter[str] = Counter()
    frame_family_counts: Counter[str] = Counter()
    direct_request_false_count = 0
    score_delta_zero_count = 0
    for row in rows:
        for frame in row.get("enabled_refresh_frames") or []:
            frame_stage_counts[str(frame.get("stage") or "unknown")] += 1
            frame_family_counts[str(frame.get("provider_family") or "unknown")] += 1
            if frame.get("direct_request") is False:
                direct_request_false_count += 1
            if float(frame.get("score_delta", 1.0) or 0.0) == 0.0:
                score_delta_zero_count += 1

    attempted = len(rows)
    selected_move_delta_count = sum(1 for row in rows if row["selected_move_delta"])
    selected_provider_delta_count = sum(1 for row in rows if row["selected_provider_delta"])
    selected_score_delta_count = sum(1 for row in rows if row["selected_score_delta"])
    routing_delta_count = sum(1 for row in rows if row["routing_delta"])
    baseline_refresh_frame_count = sum(int(row["baseline_refresh_frame_count"]) for row in rows)
    generated_frame_count = sum(int(row["enabled_refresh_frame_count"]) for row in rows)
    score_delta_count = generated_frame_count - score_delta_zero_count
    stage7_training_row_count = sum(1 for row in rows if row.get("stage7_training_row"))
    selector_training_row_count = sum(1 for row in rows if row.get("usable_for_selector_training"))
    runtime_authorization_row_count = sum(
        1 for row in rows if row.get("usable_for_runtime_authorization")
    )
    default_off_equivalence = (
        attempted > 0
        and baseline_refresh_frame_count == 0
        and selected_move_delta_count == 0
        and selected_provider_delta_count == 0
        and selected_score_delta_count == 0
        and routing_delta_count == 0
    )
    valid = (
        default_off_equivalence
        and not invalid_frames
        and score_delta_count == 0
        and stage7_training_row_count == 0
        and selector_training_row_count == 0
        and runtime_authorization_row_count == 0
        and len(joined) > 0
    )
    if not default_off_equivalence:
        status = "fresh_stage5_6_selector_objective_collection_failed_equivalence"
    elif invalid_frames or score_delta_count:
        status = "fresh_stage5_6_selector_objective_collection_invalid_semantics"
    elif len(joined) == attempted:
        status = "fresh_stage5_6_selector_objective_collection_complete"
    else:
        status = "fresh_stage5_6_selector_objective_collection_underpowered"

    return {
        "schema_version": "krk_selector_objective_fresh_diversity_collection.v0",
        "causal_status": "observation_only_collection",
        "sandbox_id": "bounded_fresh_stage5_6_selector_objective_diversity_collection_v0",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(PACKET)],
        "approval": {
            "approval_status": "explicitly_approved_for_single_bounded_observation_collection",
            "approved_scope": "fresh_stage5_6_selector_objective_diversity_review_packet_v0",
            "execute_reviewed_collection_flag_required": True,
        },
        "summary": {
            "attempted_row_count": attempted,
            "collected_row_count": len(rows),
            "joined_row_count": len(joined),
            "stage_counts": dict(sorted(stage_counts.items())),
            "selected_owner_counts": dict(sorted(owner_counts.items())),
            "objective_channel_counts": dict(sorted(channel_counts.items())),
            "selected_provider_counts": dict(sorted(provider_counts.items())),
            "generated_frame_count": generated_frame_count,
            "generated_frame_count_by_stage": dict(sorted(frame_stage_counts.items())),
            "generated_frame_count_by_provider_family": dict(sorted(frame_family_counts.items())),
            "selected_failure_with_visible_positive_capacity_count": recovery_counts[
                "selected_failure_with_visible_positive_capacity"
            ],
            "safe_preservation_with_visible_positive_capacity_count": recovery_counts[
                "safe_preservation_with_visible_positive_capacity"
            ],
            "selected_failure_trace_context_only_count": recovery_counts[
                "selected_failure_trace_context_only"
            ],
            "safe_preservation_trace_context_only_count": recovery_counts[
                "safe_preservation_trace_context_only"
            ],
            "selector_training_row_count": selector_training_row_count,
            "stage7_training_row_count": stage7_training_row_count,
            "runtime_authorization_row_count": runtime_authorization_row_count,
            "capacity_label_used_as_ownership_label_count": sum(
                1 for row in rows if row.get("capacity_label_used_as_ownership_label")
            ),
            "selected_move_delta_count": selected_move_delta_count,
            "selected_provider_delta_count": selected_provider_delta_count,
            "selected_score_delta_count": selected_score_delta_count,
            "score_delta_count": score_delta_count,
            "routing_delta_count": routing_delta_count,
            "baseline_refresh_frame_count": baseline_refresh_frame_count,
            "direct_request_false_count": direct_request_false_count,
            "score_delta_zero_count": score_delta_zero_count,
            "invalid_frame_count": len(invalid_frames),
            "default_off_equivalence_passed": default_off_equivalence,
            "runtime_behavior_changed": False,
        },
        "rows": rows,
        "invalid_frames": invalid_frames[:10],
        "decision": {
            "status": status,
            "collection_valid": valid,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "review_fresh_stage5_6_selector_objective_collection_result"
                if valid
                else "quarantine_fresh_stage5_6_selector_objective_collection_result"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selector Objective Fresh Diversity Collection v0",
        "",
        "This report records the explicitly approved bounded Stage 5/6 observation-only collection. It does not train or authorize a selector.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- collection_valid: `{payload['decision']['collection_valid']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            "- "
            f"`{row['row_id']}` "
            f"stage={row['source_stage']} "
            f"label={row['selected_owner_label']} "
            f"frames={row['enabled_refresh_frame_count']} "
            f"positive_capacity_frames={row['positive_capacity_frame_count']} "
            f"class=`{row['recovery_class']}`"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run approved fresh Stage 5/6 selector-objective diversity collection"
    )
    parser.add_argument(
        "--execute-reviewed-collection",
        action="store_true",
        help="Execute the explicitly approved observation-only collection.",
    )
    args = parser.parse_args()
    if not args.execute_reviewed_collection:
        raise SystemExit("refusing_to_execute_without_--execute-reviewed-collection")
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
