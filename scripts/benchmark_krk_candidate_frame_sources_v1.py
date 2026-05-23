#!/usr/bin/env python3
"""Benchmark KRK StrategySequenceCandidateFrame source channels non-causally."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

FRAMES = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json")
QUALITY = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_quality_v1.json")
OUT_BENCHMARK_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_frame_source_benchmark_v1.json"
)
OUT_BENCHMARK_MD = Path("reports/strategy_arbitration/krk_candidate_frame_source_benchmark_v1.md")
OUT_DECISION_JSON = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_control_plane_decision_v1.json"
)
OUT_DECISION_MD = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_control_plane_decision_v1.md"
)


RUNTIME_FALSE_KEYS = (
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_candidate_generator_implemented",
    "runtime_terminals_added",
    "runtime_dtm_or_tablebase_lookup",
    "gameplay_topology_mutation",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    full = ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


def _channel(frame: dict[str, Any]) -> str:
    semantics = frame.get("label_semantics")
    if semantics == "capacity_evidence_not_ownership_label":
        return "protected_forced_capacity"
    if semantics == "visible_provider_proposal_context_not_capacity_or_ownership_label":
        return "visible_provider_proposal"
    if semantics == "sandbox_supported_move_hypothesis_not_selector_label":
        return "progress_window_supported_move"
    if semantics == "internal_monitor_context_not_runtime_route":
        return "internal_monitor_strategy_context"
    return "unknown"


def _result_is_mate(result: Any) -> bool:
    return str(result) == "mate"


def benchmark_frames(frames: list[dict[str, Any]]) -> dict[str, Any]:
    by_channel: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for frame in frames:
        by_channel[_channel(frame)].append(frame)

    channel_summaries: dict[str, dict[str, Any]] = {}
    for channel, rows in sorted(by_channel.items()):
        protected = [row for row in rows if not row.get("stage7_challenge_row")]
        stage7 = [row for row in rows if row.get("stage7_challenge_row")]
        capacity_labels = Counter(
            (row.get("capacity_evidence") or {}).get("capacity_label") or "none"
            for row in rows
        )
        outcomes = Counter(
            (row.get("ownership_evidence") or {}).get("frame_outcome")
            or (row.get("sequence_evidence") or {}).get("associated_outcome")
            or ((row.get("sequence_evidence") or {}).get("continuation_h40") or {}).get("result")
            or "unknown"
            for row in rows
        )
        positive_capacity = capacity_labels.get("positive_capacity", 0)
        negative_capacity = capacity_labels.get("negative_capacity", 0)
        capacity_total = positive_capacity + negative_capacity
        channel_summaries[channel] = {
            "frame_count": len(rows),
            "protected_count": len(protected),
            "stage7_challenge_count": len(stage7),
            "stage7_training_row_count": sum(
                1 for row in rows
                if row.get("stage7_challenge_row")
                and (
                    row.get("usable_for_selector_training")
                    or row.get("usable_for_candidate_generation_training")
                )
            ),
            "state_count": len({row.get("state_id") for row in rows}),
            "strategy_family_counts": dict(
                sorted(Counter(row.get("candidate_strategy_family") for row in rows).items())
            ),
            "capacity_label_counts": dict(sorted(capacity_labels.items())),
            "outcome_counts": dict(sorted(outcomes.items())),
            "positive_capacity_ratio": (
                positive_capacity / capacity_total if capacity_total else None
            ),
            "negative_capacity_ratio": (
                negative_capacity / capacity_total if capacity_total else None
            ),
            "selector_training_row_count": sum(
                1 for row in rows if row.get("usable_for_selector_training")
            ),
            "candidate_generation_training_row_count": sum(
                1 for row in rows if row.get("usable_for_candidate_generation_training")
            ),
        }
    return channel_summaries


def source_readiness(channel_summaries: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    readiness: dict[str, dict[str, Any]] = {}
    capacity = channel_summaries.get("protected_forced_capacity", {})
    readiness["protected_forced_capacity"] = {
        "candidate_generation_signal": "promising"
        if capacity.get("candidate_generation_training_row_count", 0) > 0
        else "absent",
        "selection_signal": "blocked_capacity_not_ownership_label",
        "risk": "negative_capacity_included"
        if (capacity.get("negative_capacity_ratio") or 0) > 0
        else "needs_negative_controls",
        "usable_next": "candidate_generation_benchmark_only",
    }

    proposals = channel_summaries.get("visible_provider_proposal", {})
    readiness["visible_provider_proposal"] = {
        "candidate_generation_signal": "existing_visible_candidates",
        "selection_signal": "context_only_needs_state_local_objective",
        "risk": "score_and_rank_not_sufficient_for_broad_selection",
        "usable_next": "source_channel_comparison_and_selector_holdout",
        "selector_training_row_count": proposals.get("selector_training_row_count", 0),
    }

    progress = channel_summaries.get("progress_window_supported_move", {})
    readiness["progress_window_supported_move"] = {
        "candidate_generation_signal": "failed_in_target_runtime_test",
        "selection_signal": "not_runtime_ready",
        "risk": "all_sampled_supported_stage7_sequence_candidates_failed_h40",
        "usable_next": "heldout_challenge_diagnostic_only",
        "sequence_candidate_mate_count": progress.get("outcome_counts", {}).get("mate", 0),
    }

    monitors = channel_summaries.get("internal_monitor_strategy_context", {})
    readiness["internal_monitor_strategy_context"] = {
        "candidate_generation_signal": "diagnostic_context",
        "selection_signal": "not_selector_label",
        "risk": "sparse_or_noisy_monitor_evidence",
        "usable_next": "features_for_non_causal_control_plane_benchmarks",
        "frame_count": monitors.get("frame_count", 0),
    }
    return readiness


def build_benchmark_payload() -> dict[str, Any]:
    frames_payload = _load(FRAMES)
    quality = _load(QUALITY)
    frames = list(frames_payload.get("frames") or [])
    channel_summaries = benchmark_frames(frames)
    readiness = source_readiness(channel_summaries)
    return {
        "schema_version": "krk_candidate_frame_source_benchmark.v1",
        "causal_status": "non_causal_candidate_source_benchmark",
        **_runtime_false_block(),
        "source_artifacts": [str(FRAMES), str(QUALITY)],
        "input_summary": frames_payload.get("summary", {}),
        "quality_checks": quality.get("quality_checks", {}),
        "channel_summaries": channel_summaries,
        "source_readiness": readiness,
        "decision": {
            "status": "candidate_generation_sources_promising_selector_blocked",
            "runtime_sandbox_allowed": False,
            "runtime_candidate_generator_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": "design_non_causal_candidate_generation_source_benchmark_v2_or_review_runtime_scope",
        },
    }


def build_decision_payload(benchmark: dict[str, Any]) -> dict[str, Any]:
    capacity = benchmark["channel_summaries"].get("protected_forced_capacity", {})
    progress = benchmark["channel_summaries"].get("progress_window_supported_move", {})
    stage7_training = sum(
        channel.get("stage7_training_row_count", 0)
        for channel in benchmark["channel_summaries"].values()
    )
    decision_status = "candidate_generation_control_plane_ready_for_architecture_review"
    recommended = "architecture_review_for_default_off_candidate_generation_sandbox_scope"
    blockers = [
        "selector policy remains blocked",
        "capacity labels are not ownership labels",
        "progress-window supported moves remain held-out target failures",
        "no runtime candidate generator has review authorization",
    ]
    if stage7_training != 0:
        decision_status = "blocked_stage7_leakage"
        recommended = "fix_stage7_exclusion_before_any_review"
    elif (capacity.get("candidate_generation_training_row_count") or 0) == 0:
        decision_status = "blocked_no_candidate_generation_signal"
        recommended = "collect_more_protected_candidate_generation_evidence"
    return {
        "schema_version": "krk_strategy_sequence_control_plane_decision.v1",
        "causal_status": "non_causal_architecture_decision_gate",
        **_runtime_false_block(),
        "source_artifacts": [str(OUT_BENCHMARK_JSON)],
        "decision": {
            "status": decision_status,
            "recommended_next_step": recommended,
            "runtime_sandbox_allowed_by_this_packet": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "evidence": {
            "protected_positive_capacity_candidates": capacity.get(
                "candidate_generation_training_row_count"
            ),
            "protected_negative_capacity_ratio": capacity.get("negative_capacity_ratio"),
            "progress_window_supported_move_h40_mate_count": (
                progress.get("outcome_counts", {}).get("mate", 0)
            ),
            "stage7_training_row_count": stage7_training,
            "runtime_flags_false": all(benchmark.get(key) is False for key in RUNTIME_FALSE_KEYS),
        },
        "blockers_before_runtime": blockers,
        "explicitly_still_forbidden": [
            "general_runtime_selector",
            "default_runtime_candidate_generator",
            "Stage7_promotion",
            "Stage8_training_from_unresolved_Stage7",
            "runtime_DTM_or_tablebase",
            "gameplay_topology_mutation",
            "hidden_Python_routing",
        ],
    }


def _write_benchmark_md(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Candidate Frame Source Benchmark v1",
        "",
        "This non-causal benchmark compares populated StrategySequenceCandidateFrame source channels before any runtime work.",
        "",
        "## Channel Summary",
        "",
    ]
    for channel, summary in payload["channel_summaries"].items():
        lines.extend(
            [
                f"### {channel}",
                "",
                f"- frame_count: {summary['frame_count']}",
                f"- protected_count: {summary['protected_count']}",
                f"- stage7_challenge_count: {summary['stage7_challenge_count']}",
                f"- candidate_generation_training_row_count: {summary['candidate_generation_training_row_count']}",
                f"- selector_training_row_count: {summary['selector_training_row_count']}",
                f"- capacity_label_counts: `{summary['capacity_label_counts']}`",
                f"- outcome_counts: `{summary['outcome_counts']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
            f"- runtime_sandbox_allowed: `{payload['decision']['runtime_sandbox_allowed']}`",
        ]
    )
    (ROOT / OUT_BENCHMARK_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_decision_md(payload: dict[str, Any]) -> None:
    evidence = payload["evidence"]
    lines = [
        "# KRK Strategy/Sequence Control Plane Decision v1",
        "",
        "This decision gate closes the candidate-frame source benchmark without authorizing runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        f"- runtime_sandbox_allowed_by_this_packet: `{payload['decision']['runtime_sandbox_allowed_by_this_packet']}`",
        "",
        "## Evidence",
        "",
        f"- protected_positive_capacity_candidates: {evidence['protected_positive_capacity_candidates']}",
        f"- protected_negative_capacity_ratio: {evidence['protected_negative_capacity_ratio']}",
        f"- progress_window_supported_move_h40_mate_count: {evidence['progress_window_supported_move_h40_mate_count']}",
        f"- stage7_training_row_count: {evidence['stage7_training_row_count']}",
        f"- runtime_flags_false: `{evidence['runtime_flags_false']}`",
        "",
        "## Blockers Before Runtime",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in payload["blockers_before_runtime"])
    lines.extend(
        [
            "",
            "## Still Forbidden",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in payload["explicitly_still_forbidden"])
    (ROOT / OUT_DECISION_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    benchmark = build_benchmark_payload()
    decision = build_decision_payload(benchmark)
    _write_json(OUT_BENCHMARK_JSON, benchmark)
    _write_benchmark_md(benchmark)
    _write_json(OUT_DECISION_JSON, decision)
    _write_decision_md(decision)
    print(
        json.dumps(
            {
                "benchmark_status": benchmark["decision"]["status"],
                "decision": decision["decision"],
                "evidence": decision["evidence"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
