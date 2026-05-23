#!/usr/bin/env python3
"""Analyze Stage 5/6 candidate-generation refresh observation coverage."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_smoke_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_coverage_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_coverage_v0.md"
)


def _load(path: Path = SOURCE) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _refresh_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case in payload.get("cases") or []:
        observation = (
            (case.get("enabled_decision") or {}).get("observation")
            if isinstance(case.get("enabled_decision"), dict)
            else {}
        )
        all_frames = []
        if isinstance(observation, dict):
            all_frames = list(observation.get("frames") or [])
        if not all_frames:
            all_frames = list(case.get("enabled_refresh_sample_frames") or [])
        for frame in all_frames:
            if isinstance(frame, dict):
                if frame.get("candidate_source") != "stage_conditioned_candidate_generation_refresh":
                    continue
                frames.append({
                    **frame,
                    "_source_stage": case.get("source_stage"),
                    "_case_id": case.get("case_id"),
                })
    return frames


def build_payload(source: dict[str, Any] | None = None) -> dict[str, Any]:
    source = source or _load()
    frames = _refresh_frames(source)
    by_stage = Counter(str(frame.get("_source_stage") or "unknown") for frame in frames)
    by_provider = Counter(str(frame.get("provider_id") or "unknown") for frame in frames)
    by_capacity = Counter(str(frame.get("capacity_evidence_kind") or "unknown") for frame in frames)
    by_provenance = Counter(str(frame.get("provider_provenance") or "unknown") for frame in frames)
    invariant_failures = []
    for frame in frames:
        if (
            frame.get("candidate_source") != "stage_conditioned_candidate_generation_refresh"
            or frame.get("direct_request") is not False
            or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
            or frame.get("causal_status") != "observation_only"
            or frame.get("protected_status") != "protected_control"
        ):
            invariant_failures.append(frame)
    source_summary = source.get("summary") or {}
    smoke_passed = (
        (source.get("decision") or {}).get("status")
        == "stage5_6_candidate_generation_refresh_wired_default_off_equivalent"
    )
    stage7_case_count = int(source_summary.get("stage7_case_count", 0) or 0)
    selected_delta_count = int(
        source_summary.get("selected_move_provider_delta_count", 0) or 0
    )
    status = (
        "stage5_6_refresh_coverage_ready_for_broadened_analysis"
        if smoke_passed
        and frames
        and not invariant_failures
        and stage7_case_count == 0
        and selected_delta_count == 0
        else "stage5_6_refresh_coverage_blocked"
    )
    return {
        "schema_version": "krk_stage5_6_candidate_generation_refresh_coverage.v0",
        "causal_status": "non_causal_runtime_observation_analysis",
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
            "refresh_frame_count": len(frames),
            "frame_count_by_stage": dict(sorted(by_stage.items())),
            "provider_counts": dict(sorted(by_provider.items())),
            "capacity_evidence_counts": dict(sorted(by_capacity.items())),
            "provider_provenance_counts": dict(sorted(by_provenance.items())),
            "invariant_failure_count": len(invariant_failures),
            "stage7_case_count": stage7_case_count,
            "selected_move_provider_delta_count": selected_delta_count,
            "baseline_refresh_frame_count": int(
                source_summary.get("baseline_refresh_frame_count", 0) or 0
            ),
        },
        "invariant_failures": invariant_failures[:10],
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "broaden_stage5_6_candidate_generation_refresh_sample_non_causal"
                if status == "stage5_6_refresh_coverage_ready_for_broadened_analysis"
                else "quarantine_stage5_6_candidate_generation_refresh_source"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Stage 5/6 Candidate-Generation Refresh Coverage v0",
        "",
        "This analyzes emitted Stage 5/6 refresh observation frames. It does not authorize selection, scoring, guardrails, or promotion.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- refresh_frame_count: {summary['refresh_frame_count']}",
        f"- frame_count_by_stage: `{summary['frame_count_by_stage']}`",
        f"- provider_counts: `{summary['provider_counts']}`",
        f"- capacity_evidence_counts: `{summary['capacity_evidence_counts']}`",
        f"- provider_provenance_counts: `{summary['provider_provenance_counts']}`",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        f"- stage7_case_count: {summary['stage7_case_count']}",
        f"- selected_move_provider_delta_count: {summary['selected_move_provider_delta_count']}",
        f"- baseline_refresh_frame_count: {summary['baseline_refresh_frame_count']}",
    ]
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
