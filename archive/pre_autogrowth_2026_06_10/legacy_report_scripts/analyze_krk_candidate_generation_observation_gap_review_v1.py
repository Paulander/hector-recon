#!/usr/bin/env python3
"""Review coverage gaps in broadened KRK candidate-generation observations."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_observation_broadened_sample_v1.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_observation_gap_review_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_observation_gap_review_v1.md"
)

EXPECTED_SOURCES = {
    "validated_provider_pack",
    "candidate_move_frame",
    "plan_capsule_sequence_candidate",
    "broader_strategy_candidate",
}


def _load(path: Path = SOURCE) -> dict[str, Any]:
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
                frames.append(
                    {
                        **frame,
                        "_case_id": case.get("case_id"),
                        "_source_stage": case.get("source_stage"),
                        "_held_out": case.get("held_out"),
                    }
                )
    return frames


def review(payload: dict[str, Any]) -> dict[str, Any]:
    frames = _iter_frames(payload)
    source_counts: Counter[str] = Counter()
    capacity_counts: Counter[str] = Counter()
    protected_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    unknown_by_source: Counter[str] = Counter()
    negative_by_source: Counter[str] = Counter()
    positive_by_source: Counter[str] = Counter()
    source_by_stage: dict[str, Counter[str]] = defaultdict(Counter)
    invariant_failures: list[dict[str, Any]] = []

    for frame in frames:
        source = str(frame.get("candidate_source") or "unknown")
        capacity = str(frame.get("capacity_evidence_kind") or "unknown_capacity")
        stage = str(frame.get("_source_stage") or "unknown")
        source_counts[source] += 1
        capacity_counts[capacity] += 1
        protected_counts[str(frame.get("protected_status") or "unknown")] += 1
        stage_counts[stage] += 1
        source_by_stage[stage][source] += 1
        if capacity == "unknown_capacity":
            unknown_by_source[source] += 1
        elif capacity == "negative_capacity":
            negative_by_source[source] += 1
        elif capacity == "positive_capacity":
            positive_by_source[source] += 1
        if (
            frame.get("direct_request") is not False
            or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
            or frame.get("causal_status") != "observation_only"
        ):
            invariant_failures.append(frame)

    total = len(frames)
    unknown_count = capacity_counts.get("unknown_capacity", 0)
    negative_count = capacity_counts.get("negative_capacity", 0)
    missing_sources = sorted(EXPECTED_SOURCES - set(source_counts))
    unknown_capacity_ratio = unknown_count / total if total else 1.0
    negative_capacity_ratio = negative_count / total if total else 0.0
    selector_blockers = []
    if unknown_capacity_ratio > 0.5:
        selector_blockers.append("candidate_capacity_mostly_unknown")
    if negative_count > 0:
        selector_blockers.append("generated_set_contains_negative_capacity_candidates")
    if "plan_capsule_sequence_candidate" in missing_sources:
        selector_blockers.append("plan_capsule_sequence_candidates_not_observed")
    if "broader_strategy_candidate" in missing_sources:
        selector_blockers.append("broader_strategy_candidates_not_observed")
    if invariant_failures:
        selector_blockers.append("observation_frame_invariant_failures")

    status = (
        "observation_gap_review_blocks_selector_recommends_capacity_annotation"
        if selector_blockers
        else "observation_gap_review_supports_selector_review"
    )
    return {
        "schema_version": "krk_candidate_generation_observation_gap_review.v1",
        "causal_status": "non_causal_observation_gap_review",
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
            "frame_count": total,
            "source_counts": dict(sorted(source_counts.items())),
            "capacity_evidence_counts": dict(sorted(capacity_counts.items())),
            "protected_status_counts": dict(sorted(protected_counts.items())),
            "stage_counts": dict(sorted(stage_counts.items())),
            "source_counts_by_stage": {
                stage: dict(sorted(counter.items()))
                for stage, counter in sorted(source_by_stage.items())
            },
            "unknown_capacity_ratio": unknown_capacity_ratio,
            "negative_capacity_ratio": negative_capacity_ratio,
            "missing_expected_sources": missing_sources,
            "unknown_capacity_by_source": dict(sorted(unknown_by_source.items())),
            "positive_capacity_by_source": dict(sorted(positive_by_source.items())),
            "negative_capacity_by_source": dict(sorted(negative_by_source.items())),
            "invariant_failure_count": len(invariant_failures),
            "stage7_readiness_training_row_count": 0,
        },
        "selector_blockers": selector_blockers,
        "interpretation": {
            "candidate_generation_visible": total > 0,
            "validated_provider_pack_visible": source_counts.get("validated_provider_pack", 0) > 0,
            "candidate_move_frames_visible": source_counts.get("candidate_move_frame", 0) > 0,
            "plan_capsule_sequence_candidates_visible": source_counts.get(
                "plan_capsule_sequence_candidate", 0
            )
            > 0,
            "broader_strategy_candidates_visible": source_counts.get(
                "broader_strategy_candidate", 0
            )
            > 0,
            "candidate_move_capacity_annotation_needed": unknown_by_source.get(
                "candidate_move_frame", 0
            )
            > 0,
            "provider_pack_contains_positive_capacity": positive_by_source.get(
                "validated_provider_pack", 0
            )
            > 0,
            "provider_pack_contains_negative_capacity": negative_by_source.get(
                "validated_provider_pack", 0
            )
            > 0,
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_candidate_generator_changes_allowed": False,
            "recommended_next_step": "non_causal_candidate_move_capacity_annotation_review",
            "stage7_training_rows_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    interpretation = payload["interpretation"]
    lines = [
        "# KRK Candidate-Generation Observation Gap Review v1",
        "",
        "This review uses broadened observation-only runtime frames. It remains non-causal and does not authorize selection.",
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
        f"- frame_count: {summary['frame_count']}",
        f"- source_counts: `{summary['source_counts']}`",
        f"- capacity_evidence_counts: `{summary['capacity_evidence_counts']}`",
        f"- protected_status_counts: `{summary['protected_status_counts']}`",
        f"- unknown_capacity_ratio: `{summary['unknown_capacity_ratio']:.3f}`",
        f"- negative_capacity_ratio: `{summary['negative_capacity_ratio']:.3f}`",
        f"- missing_expected_sources: `{summary['missing_expected_sources']}`",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        "",
        "## Selector Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in payload["selector_blockers"])
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {key}: `{value}`" for key, value in interpretation.items())
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The next step is capacity/quality annotation for visible candidate frames, not selector implementation or guardrails.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = review(_load())
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
