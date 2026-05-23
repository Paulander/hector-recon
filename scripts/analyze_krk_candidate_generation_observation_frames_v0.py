#!/usr/bin/env python3
"""Analyze emitted KRK candidate-generation observation frames non-causally."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("reports/strategy_arbitration/krk_candidate_generation_observation_sandbox_v0.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_observation_coverage_analysis_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_observation_coverage_analysis_v0.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _iter_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case in payload.get("cases") or []:
        observation = ((case.get("enabled_decision") or {}).get("observation") or {})
        for frame in observation.get("frames") or observation.get("sample_frames") or []:
            if isinstance(frame, dict):
                frames.append({**frame, "_case_id": case.get("case_id")})
    return frames


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    frames = _iter_frames(payload)
    by_case: dict[str, Counter[str]] = defaultdict(Counter)
    source_counts: Counter[str] = Counter()
    capacity_counts: Counter[str] = Counter()
    protected_counts: Counter[str] = Counter()
    invariant_failures: list[dict[str, Any]] = []
    for frame in frames:
        case_id = str(frame.get("_case_id") or "unknown")
        source = str(frame.get("candidate_source") or "unknown")
        source_counts[source] += 1
        by_case[case_id][source] += 1
        capacity_counts[str(frame.get("capacity_evidence_kind") or "unknown_capacity")] += 1
        protected_counts[str(frame.get("protected_status") or "unknown")] += 1
        if (
            frame.get("direct_request") is not False
            or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
            or frame.get("causal_status") != "observation_only"
        ):
            invariant_failures.append(frame)
    summary = dict(payload.get("summary") or {})
    generated_total = int(summary.get("generated_candidate_count", 0) or 0)
    sampled_total = len(frames)
    return {
        "schema_version": "krk_candidate_generation_observation_coverage_analysis.v0",
        "causal_status": "non_causal_observation_frame_analysis",
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
            "generated_candidate_count": generated_total,
            "sampled_frame_count": sampled_total,
            "candidate_count_by_source": dict(sorted(source_counts.items())),
            "candidate_count_by_case_and_source": {
                case: dict(sorted(counter.items()))
                for case, counter in sorted(by_case.items())
            },
            "capacity_evidence_counts": dict(sorted(capacity_counts.items())),
            "protected_status_counts": dict(sorted(protected_counts.items())),
            "invariant_failure_count": len(invariant_failures),
            "selected_move_or_provider_changed": bool(
                summary.get("selected_move_or_provider_changed")
            ),
            "playout_result_or_plies_changed": bool(
                summary.get("playout_result_or_plies_changed")
            ),
        },
        "interpretation": {
            "candidate_generation_visible": generated_total > 0,
            "protected_and_heldout_status_visible": bool(protected_counts),
            "positive_and_negative_capacity_visible": (
                capacity_counts.get("positive_capacity", 0) > 0
                and capacity_counts.get("negative_capacity", 0) > 0
            ),
            "candidate_move_hypotheses_visible": source_counts.get("candidate_move_frame", 0) > 0,
            "selector_still_blocked": True,
            "guardrails_still_blocked": True,
        },
        "invariant_failures": invariant_failures[:10],
        "decision": {
            "status": "observation_frames_usable_for_non_causal_coverage_analysis"
            if generated_total > 0 and not invariant_failures
            else "observation_frame_analysis_blocked",
            "recommended_next_step": "broaden_observation_sample_before_selector_review",
            "selector_allowed": False,
            "runtime_candidate_generator_changes_allowed": False,
            "guardrails_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    interpretation = payload["interpretation"]
    lines = [
        "# KRK Candidate-Generation Observation Coverage Analysis v0",
        "",
        "This analyzes emitted observation-only candidate frames. It does not authorize selection or further runtime changes.",
        "",
        "## Summary",
        "",
        f"- generated_candidate_count: {summary['generated_candidate_count']}",
        f"- sampled_frame_count: {summary['sampled_frame_count']}",
        f"- candidate_count_by_source: `{summary['candidate_count_by_source']}`",
        f"- capacity_evidence_counts: `{summary['capacity_evidence_counts']}`",
        f"- protected_status_counts: `{summary['protected_status_counts']}`",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        f"- selected_move_or_provider_changed: `{summary['selected_move_or_provider_changed']}`",
        f"- playout_result_or_plies_changed: `{summary['playout_result_or_plies_changed']}`",
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in interpretation.items())
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
            f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
            f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = analyze(_load(SOURCE))
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
