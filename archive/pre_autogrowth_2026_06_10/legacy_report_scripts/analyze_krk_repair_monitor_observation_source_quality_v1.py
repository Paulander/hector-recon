#!/usr/bin/env python3
"""Review repair-monitor observation-source quality after broadened sampling."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    "reports/strategy_arbitration/"
    "krk_repair_monitor_observation_source_broadened_v1.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_repair_monitor_observation_source_quality_review_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_repair_monitor_observation_source_quality_review_v1.md"
)


def _load(path: Path = SOURCE) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _repair_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case in payload.get("cases") or []:
        for frame in case.get("enabled_repair_monitor_sample_frames") or []:
            if isinstance(frame, dict):
                frames.append(
                    {
                        **frame,
                        "_source_stage": case.get("source_stage"),
                        "_selected_provider": case.get("selected_provider"),
                        "_case_id": case.get("case_id"),
                    }
                )
    return frames


def build_payload(source: dict[str, Any] | None = None) -> dict[str, Any]:
    source = source or _load()
    frames = _repair_frames(source)
    stage_counts = Counter(str(frame.get("_source_stage") or "unknown") for frame in frames)
    provider_counts = Counter(
        str(frame.get("_selected_provider") or "unknown") for frame in frames
    )
    risk_term_sets = Counter(
        tuple(sorted(str(term) for term in frame.get("risk_terms") or []))
        for frame in frames
    )
    licensed_provider_sets = Counter(
        tuple(sorted(str(term) for term in frame.get("licensed_provider_families") or []))
        for frame in frames
    )
    invariant_failures = [
        frame
        for frame in frames
        if (
            frame.get("direct_request") is not False
            or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
            or frame.get("causal_status") != "observation_only"
            or frame.get("protected_status") != "protected_control"
        )
    ]
    summary = source.get("summary") or {}
    risk_term_diversity = len(risk_term_sets)
    stage_diversity = len(stage_counts)
    provider_diversity = len(provider_counts)
    source_stable = (
        bool(frames)
        and int(summary.get("selected_move_provider_delta_count") or 0) == 0
        and int(summary.get("baseline_repair_monitor_frame_count") or 0) == 0
        and int(summary.get("invariant_failure_count") or 0) == 0
        and int(summary.get("stage7_case_count") or 0) == 0
        and not invariant_failures
    )
    selector_blockers = []
    if risk_term_diversity <= 1:
        selector_blockers.append("repair_monitor_terms_not_diverse_enough")
    if len(frames) < 12:
        selector_blockers.append("protected_sample_too_small_for_quality_threshold")
    if not any("fence_or_cut_not_preserved" in terms for terms in risk_term_sets):
        selector_blockers.append("missing_cut_or_fence_break_examples")
    if not any("cut_unstable" in terms or "fence_unstable" in terms for terms in risk_term_sets):
        selector_blockers.append("missing_explicit_instability_examples")
    status = (
        "repair_monitor_observation_source_quality_trace_only_retained"
        if source_stable
        else "repair_monitor_observation_source_quality_blocked"
    )
    return {
        "schema_version": "krk_repair_monitor_observation_source_quality_review.v1",
        "causal_status": "non_causal_observation_source_quality_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(SOURCE),
        "summary": {
            "repair_monitor_frame_count": len(frames),
            "stage_counts": dict(sorted(stage_counts.items())),
            "selected_provider_counts": dict(sorted(provider_counts.items())),
            "risk_term_set_count": risk_term_diversity,
            "risk_term_sets": {
                "|".join(key): value for key, value in sorted(risk_term_sets.items())
            },
            "licensed_provider_sets": {
                "|".join(key): value
                for key, value in sorted(licensed_provider_sets.items())
            },
            "source_stable": source_stable,
            "invariant_failure_count": len(invariant_failures),
            "stage7_case_count": summary.get("stage7_case_count"),
            "selected_move_provider_delta_count": summary.get(
                "selected_move_provider_delta_count"
            ),
        },
        "selector_blockers": selector_blockers,
        "interpretation": {
            "observation_source_useful": source_stable,
            "quality_signal_mature": False,
            "reason": (
                "The source is stable as trace-only candidate context, but the current "
                "sample is small and risk terms are not diverse enough to support "
                "selector or guardrail review."
            ),
            "safe_use": "trace_only_strategy_sequence_dataset_feature",
            "forbidden_use": [
                "selector_input_without_separate_review",
                "score_delta",
                "provider_route",
                "guardrail_campaign",
                "stage7_training_or_promotion",
                "stage8_training",
            ],
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "fold_repair_monitor_frames_into_strategy_sequence_dataset_trace_only"
                if source_stable
                else "quarantine_repair_monitor_observation_source"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Repair-Monitor Observation Source Quality Review v1",
        "",
        "This review classifies the repair-monitor broader-strategy source after the broadened protected sample. It is non-causal and does not authorize selector behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- repair_monitor_frame_count: {summary['repair_monitor_frame_count']}",
        f"- stage_counts: `{summary['stage_counts']}`",
        f"- selected_provider_counts: `{summary['selected_provider_counts']}`",
        f"- risk_term_set_count: {summary['risk_term_set_count']}",
        f"- risk_term_sets: `{summary['risk_term_sets']}`",
        f"- source_stable: `{summary['source_stable']}`",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        f"- stage7_case_count: {summary['stage7_case_count']}",
        f"- selected_move_provider_delta_count: {summary['selected_move_provider_delta_count']}",
        "",
        "## Blockers",
        "",
    ]
    if payload["selector_blockers"]:
        lines.extend(f"- `{item}`" for item in payload["selector_blockers"])
    else:
        lines.append("- none for trace-only use")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"]["reason"],
            "",
            "Safe use: trace-only feature in future strategy-sequence datasets.",
            "",
            "Forbidden: selector input, score changes, routing, guardrails, Stage 7 promotion, or Stage 8 training without a separate review.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
