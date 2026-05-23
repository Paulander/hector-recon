#!/usr/bin/env python3
"""Build KRK strategy-sequence dataset v2 with explicit evidence channels."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_FRAMES = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json")
TRACE_FEATURES = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_repair_monitor_trace_features_v1.json"
)
DESIGN = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v2.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v2.json")
OUT_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v2.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _channel_for_frame(frame: dict[str, Any]) -> str:
    semantics = str(frame.get("label_semantics") or "")
    frame_type = str(frame.get("frame_type") or "")
    if semantics == "capacity_evidence_not_ownership_label":
        return "validated_provider_capacity"
    if semantics == "visible_provider_proposal_context_not_capacity_or_ownership_label":
        return "visible_provider_proposal"
    if semantics == "sandbox_supported_move_hypothesis_not_selector_label":
        return "candidate_move_frame"
    if semantics == "internal_monitor_context_not_runtime_route":
        return "internal_monitor_candidate"
    if semantics == "runtime_observation_context_not_selector_label":
        return "runtime_observation_trace_feature"
    if frame_type == "candidate_move_hypothesis":
        return "candidate_move_frame"
    if frame_type == "broader_krk_strategy_candidate":
        return "internal_monitor_candidate"
    return "unknown"


def _row_from_frame(frame: dict[str, Any], *, source_artifact: str) -> dict[str, Any]:
    channel = _channel_for_frame(frame)
    stage7 = bool(frame.get("stage7_challenge_row"))
    capacity = frame.get("capacity_evidence") or {}
    v2_candidate_generation = (
        channel == "validated_provider_capacity"
        and capacity.get("capacity_label") == "positive_capacity"
        and not stage7
    )
    return {
        "schema_version": "krk_strategy_sequence_dataset_row.v2",
        "row_id": frame.get("frame_id"),
        "state_id": frame.get("state_id"),
        "fen": frame.get("fen"),
        "source_stage": frame.get("source_stage"),
        "active_landmark_label": frame.get("active_landmark_label"),
        "evidence_channel": channel,
        "frame_type": frame.get("frame_type"),
        "candidate_strategy_family": frame.get("candidate_strategy_family"),
        "candidate_provider_id": frame.get("candidate_provider_id"),
        "candidate_move_uci": frame.get("candidate_move_uci"),
        "label_semantics": frame.get("label_semantics"),
        "stage7_challenge_row": stage7,
        "legacy_usable_for_selector_training": bool(
            frame.get("usable_for_selector_training")
        ),
        "usable_for_selector_training_v2": False,
        "usable_for_candidate_generation_training_v2": v2_candidate_generation,
        "capacity_label": capacity.get("capacity_label"),
        "source_terms": list(frame.get("source_terms") or []),
        "move_shape_terms": list(frame.get("move_shape_terms") or []),
        "post_move_terms": list(frame.get("post_move_terms") or []),
        "safety_terms": list(frame.get("safety_terms") or []),
        "internal_monitor_terms": list(frame.get("internal_monitor_terms") or []),
        "sequence_evidence_keys": sorted((frame.get("sequence_evidence") or {}).keys()),
        "source_artifact": source_artifact,
        "causal_status": "non_causal_dataset_row",
    }


def build_payload(
    *,
    base_payload: dict[str, Any] | None = None,
    trace_payload: dict[str, Any] | None = None,
    design_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_payload = base_payload or _load(BASE_FRAMES)
    trace_payload = trace_payload or _load(TRACE_FEATURES)
    design_payload = design_payload or _load(DESIGN)
    rows = [
        _row_from_frame(frame, source_artifact=str(BASE_FRAMES))
        for frame in base_payload.get("frames") or []
        if isinstance(frame, dict)
    ]
    rows.extend(
        _row_from_frame(frame, source_artifact=str(TRACE_FEATURES))
        for frame in trace_payload.get("trace_only_frames") or []
        if isinstance(frame, dict)
    )
    channel_counts = Counter(row["evidence_channel"] for row in rows)
    channel_stage7 = Counter(
        row["evidence_channel"] for row in rows if row["stage7_challenge_row"]
    )
    channel_selector_rows = Counter(
        row["evidence_channel"] for row in rows if row["usable_for_selector_training_v2"]
    )
    channel_generator_rows = Counter(
        row["evidence_channel"]
        for row in rows
        if row["usable_for_candidate_generation_training_v2"]
    )
    stage_counts = Counter(str(row.get("source_stage") or "unknown") for row in rows)
    summary = {
        "row_count": len(rows),
        "row_count_by_channel": dict(sorted(channel_counts.items())),
        "stage7_row_count_by_channel": dict(sorted(channel_stage7.items())),
        "selector_training_row_count_by_channel": dict(sorted(channel_selector_rows.items())),
        "candidate_generation_training_row_count_by_channel": dict(
            sorted(channel_generator_rows.items())
        ),
        "source_stage_counts": dict(sorted(stage_counts.items())),
        "stage7_challenge_row_count": sum(1 for row in rows if row["stage7_challenge_row"]),
        "stage7_readiness_training_row_count": sum(
            1
            for row in rows
            if row["stage7_challenge_row"]
            and (
                row["usable_for_selector_training_v2"]
                or row["usable_for_candidate_generation_training_v2"]
            )
        ),
        "selector_training_row_count": sum(
            1 for row in rows if row["usable_for_selector_training_v2"]
        ),
        "candidate_generation_training_row_count": sum(
            1 for row in rows if row["usable_for_candidate_generation_training_v2"]
        ),
        "runtime_trace_feature_row_count": channel_counts.get(
            "runtime_observation_trace_feature",
            0,
        ),
    }
    return {
        "schema_version": "krk_strategy_sequence_dataset.v2",
        "causal_status": "non_causal_dataset_refresh",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(BASE_FRAMES), str(TRACE_FEATURES), str(DESIGN)],
        "design_version": design_payload.get("schema_version"),
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "strategy_sequence_dataset_v2_refreshed_non_causal_selector_blocked",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "probe_strategy_sequence_dataset_v2_quality_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy-Sequence Dataset v2",
        "",
        "This non-causal dataset refresh applies explicit evidence-channel semantics and adds the repair-monitor runtime-observation trace-feature channel.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- row_count: {summary['row_count']}",
        f"- row_count_by_channel: `{summary['row_count_by_channel']}`",
        f"- source_stage_counts: `{summary['source_stage_counts']}`",
        f"- stage7_challenge_row_count: {summary['stage7_challenge_row_count']}",
        f"- stage7_readiness_training_row_count: {summary['stage7_readiness_training_row_count']}",
        f"- selector_training_row_count: {summary['selector_training_row_count']}",
        f"- candidate_generation_training_row_count: {summary['candidate_generation_training_row_count']}",
        f"- runtime_trace_feature_row_count: {summary['runtime_trace_feature_row_count']}",
        "",
        "## Boundary",
        "",
        "V2 makes all selector-training rows false until explicit ownership labels are recovered. Positive forced-capacity rows remain candidate-generation evidence only.",
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
