#!/usr/bin/env python3
"""Fold Stage 5/6 refresh observation frames into strategy-sequence trace features."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_FRAMES = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json")
REFRESH_SOURCE = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_broadened_v0.json"
)
QUALITY_REVIEW = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_quality_review_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_stage5_6_refresh_trace_features_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_stage5_6_refresh_trace_features_v0.md"
)

RUNTIME_FALSE_KEYS = (
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_score_changes",
    "runtime_direct_routing",
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


def _runtime_false_block() -> dict[str, bool]:
    return {key: False for key in RUNTIME_FALSE_KEYS}


def _case_frames(case: dict[str, Any]) -> list[dict[str, Any]]:
    observation = (
        (case.get("enabled_decision") or {}).get("observation")
        if isinstance(case.get("enabled_decision"), dict)
        else {}
    )
    frames = list((observation or {}).get("frames") or [])
    if not frames:
        frames = list(case.get("enabled_refresh_sample_frames") or [])
    return [
        frame
        for frame in frames
        if isinstance(frame, dict)
        and frame.get("candidate_source") == "stage_conditioned_candidate_generation_refresh"
    ]


def stage5_6_refresh_trace_frames(source: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case_idx, case in enumerate(source.get("cases") or []):
        if case.get("source_stage") not in {"stage5", "stage6"}:
            continue
        for frame_idx, frame in enumerate(_case_frames(case)):
            state_id = str(case.get("state_id") or f"stage5_6_refresh_state_{case_idx}")
            frames.append(
                {
                    "schema_version": "krk_strategy_sequence_candidate_frame.v1",
                    "frame_id": f"ssf.runtime_observation.stage5_6_refresh.{state_id}.{frame_idx}",
                    "state_id": state_id,
                    "fen": case.get("fen") or frame.get("state_fen"),
                    "source_stage": case.get("source_stage"),
                    "active_landmark_label": case.get("active_landmark_label")
                    or frame.get("active_landmark_label"),
                    "frame_type": "stage_conditioned_candidate_generation_refresh",
                    "candidate_id": (
                        f"candidate.stage5_6_refresh.{frame.get('provider_id')}.{frame.get('move_id')}"
                    ),
                    "candidate_provider_id": frame.get("provider_id"),
                    "candidate_move_uci": frame.get("move_id"),
                    "candidate_plan_id": None,
                    "candidate_strategy_family": _provider_family(str(frame.get("provider_id") or "")),
                    "source_terms": list(frame.get("source_terms") or []),
                    "move_shape_terms": [],
                    "post_move_terms": [],
                    "safety_terms": [],
                    "internal_monitor_terms": [],
                    "capacity_evidence": {
                        "capacity_label": frame.get("capacity_evidence_kind"),
                        "capacity_evidence_source": frame.get("capacity_evidence_source"),
                        "label_semantics": frame.get("label_semantics")
                        or "runtime_observation_context_not_capacity_label",
                    },
                    "ownership_evidence": {
                        "selected_provider_before_observation": frame.get(
                            "selected_provider_before_observation"
                        ),
                        "selected_move_before_observation": frame.get(
                            "selected_move_before_observation"
                        ),
                        "selected_move_provider_score_equivalent": case.get(
                            "selected_move_provider_score_equivalent"
                        ),
                        "label_semantics": "runtime_observation_context_not_ownership_label",
                    },
                    "sequence_evidence": {
                        "candidate_source": frame.get("candidate_source"),
                        "provider_provenance": frame.get("provider_provenance"),
                        "protected_status": frame.get("protected_status"),
                        "source_artifact": str(REFRESH_SOURCE),
                    },
                    "label_semantics": "runtime_observation_context_not_selector_label",
                    "stage7_challenge_row": False,
                    "usable_for_selector_training": False,
                    "usable_for_candidate_generation_training": False,
                    "causal_status": "non_causal_trace_feature",
                }
            )
    return frames


def _provider_family(provider_id: str) -> str:
    if "stage0_basin" in provider_id:
        return "stage0_basin"
    if "edge_trap" in provider_id:
        return "edge_trap"
    if "fence_established" in provider_id:
        return "fence_established"
    if "drive_to_edge" in provider_id:
        return "drive_to_edge"
    return "other"


def _summarize(frames: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "trace_frame_count": len(frames),
        "stage_counts": dict(sorted(Counter(frame.get("source_stage") for frame in frames).items())),
        "strategy_family_counts": dict(
            sorted(Counter(frame.get("candidate_strategy_family") for frame in frames).items())
        ),
        "capacity_label_counts": dict(
            sorted(
                Counter(
                    (frame.get("capacity_evidence") or {}).get("capacity_label")
                    for frame in frames
                ).items()
            )
        ),
        "stage7_trace_frame_count": sum(1 for frame in frames if frame.get("stage7_challenge_row")),
        "selector_training_row_count": sum(
            1 for frame in frames if frame.get("usable_for_selector_training")
        ),
        "candidate_generation_training_row_count": sum(
            1 for frame in frames if frame.get("usable_for_candidate_generation_training")
        ),
    }


def build_payload(
    *,
    base_payload: dict[str, Any] | None = None,
    refresh_payload: dict[str, Any] | None = None,
    quality_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_payload = base_payload or _load(BASE_FRAMES)
    refresh_payload = refresh_payload or _load(REFRESH_SOURCE)
    quality_payload = quality_payload or _load(QUALITY_REVIEW)
    frames = stage5_6_refresh_trace_frames(refresh_payload)
    summary = _summarize(frames)
    trace_only_safe = (
        summary["trace_frame_count"] > 0
        and summary["stage7_trace_frame_count"] == 0
        and summary["selector_training_row_count"] == 0
        and summary["candidate_generation_training_row_count"] == 0
        and (quality_payload.get("decision") or {}).get("selector_allowed") is False
    )
    return {
        "schema_version": "krk_strategy_sequence_stage5_6_refresh_trace_features.v0",
        "causal_status": "non_causal_trace_feature_augmentation",
        **_runtime_false_block(),
        "source_artifacts": [
            str(BASE_FRAMES),
            str(REFRESH_SOURCE),
            str(QUALITY_REVIEW),
        ],
        "base_dataset_summary": base_payload.get("summary") or {},
        "summary": summary,
        "trace_only_frames": frames,
        "interpretation": {
            "folded_into_strategy_sequence_context": trace_only_safe,
            "safe_use": "trace_only_feature_for_future_strategy_sequence_dataset",
            "capacity_labels_are_not_selector_labels": True,
            "ownership_labels_are_not_selector_labels": True,
            "selector_or_guardrail_authorized": False,
        },
        "decision": {
            "status": (
                "stage5_6_refresh_trace_features_folded_non_causal"
                if trace_only_safe
                else "stage5_6_refresh_trace_feature_fold_blocked"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "strategy_sequence_dataset_v3_design_or_integration_review"
                if trace_only_safe
                else "quarantine_stage5_6_refresh_trace_features"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    base = payload["base_dataset_summary"]
    lines = [
        "# KRK Strategy-Sequence Stage 5/6 Refresh Trace Features v0",
        "",
        "This artifact folds Stage 5/6 refresh observation frames into the strategy-sequence evidence track as trace-only features. It does not alter the base dataset and does not authorize selector behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Added Trace Features",
        "",
        f"- trace_frame_count: {summary['trace_frame_count']}",
        f"- stage_counts: `{summary['stage_counts']}`",
        f"- strategy_family_counts: `{summary['strategy_family_counts']}`",
        f"- capacity_label_counts: `{summary['capacity_label_counts']}`",
        f"- stage7_trace_frame_count: {summary['stage7_trace_frame_count']}",
        f"- selector_training_row_count: {summary['selector_training_row_count']}",
        f"- candidate_generation_training_row_count: {summary['candidate_generation_training_row_count']}",
        "",
        "## Base Dataset Context",
        "",
        f"- base_frame_count: {base.get('frame_count')}",
        f"- base_stage7_challenge_row_count: {base.get('stage7_challenge_row_count')}",
        f"- base_readiness_training_stage7_row_count: {base.get('readiness_training_stage7_row_count')}",
        "",
        "## Boundary",
        "",
        "These frames are context evidence only. They are not capacity labels, ownership labels, selector rows, guardrail triggers, routing requests, or score changes.",
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
