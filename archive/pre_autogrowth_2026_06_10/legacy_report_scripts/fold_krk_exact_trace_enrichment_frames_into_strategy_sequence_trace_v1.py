#!/usr/bin/env python3
"""Fold exact trace enrichment sandbox frames into trace features."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_FRAMES = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json")
SANDBOX = Path("reports/strategy_arbitration/krk_exact_trace_enrichment_sandbox_v0.json")
COVERAGE = Path("reports/strategy_arbitration/krk_exact_trace_enrichment_coverage_analysis_v0.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_exact_trace_enrichment_trace_features_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_exact_trace_enrichment_trace_features_v1.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }


def _exact_frames(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        frame
        for frame in case.get("enabled_exact_frames") or []
        if isinstance(frame, dict) and frame.get("candidate_source") == "exact_trace_enrichment"
    ]


def trace_frames(sandbox: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case_idx, case in enumerate(sandbox.get("cases") or []):
        if not isinstance(case, dict):
            continue
        if case.get("source_stage") not in {"stage5", "stage6"}:
            continue
        state_id = str(case.get("state_id") or f"exact_trace_enrichment_state_{case_idx}")
        for frame_idx, frame in enumerate(_exact_frames(case)):
            frames.append(
                {
                    "schema_version": "krk_strategy_sequence_candidate_frame.v1",
                    "frame_id": (
                        f"ssf.runtime_observation.exact_trace_enrichment."
                        f"{state_id}.{frame_idx}"
                    ),
                    "state_id": state_id,
                    "fen": case.get("fen") or frame.get("state_fen"),
                    "source_stage": frame.get("stage") or case.get("source_stage"),
                    "active_landmark_label": case.get("active_landmark_label")
                    or frame.get("active_landmark_label"),
                    "frame_type": "exact_trace_enrichment_sandbox",
                    "candidate_id": (
                        f"candidate.exact_trace_enrichment.{frame.get('provider_id')}.{frame.get('move_id')}"
                    ),
                    "candidate_provider_id": frame.get("provider_id"),
                    "candidate_move_uci": frame.get("move_id"),
                    "candidate_plan_id": None,
                    "candidate_strategy_family": frame.get("provider_family"),
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
                        "policy": frame.get("policy"),
                        "policy_cell": frame.get("policy_cell"),
                        "provider_provenance": frame.get("provider_provenance"),
                        "protected_status": frame.get("protected_status"),
                        "candidate_generation_truncated": bool(
                            frame.get("candidate_generation_truncated")
                        ),
                        "candidate_count_before_truncation": frame.get(
                            "candidate_count_before_truncation"
                        ),
                        "exact_enrichment_reason": frame.get("exact_enrichment_reason"),
                        "source_artifact": str(SANDBOX),
                    },
                    "label_semantics": "runtime_observation_context_not_selector_label",
                    "stage7_challenge_row": False,
                    "usable_for_selector_training": False,
                    "usable_for_candidate_generation_training": False,
                    "causal_status": "non_causal_trace_feature",
                }
            )
    return frames


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
        "policy_cell_counts": dict(
            sorted(
                Counter(
                    (frame.get("sequence_evidence") or {}).get("policy_cell")
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
    sandbox_payload: dict[str, Any] | None = None,
    coverage_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_payload = base_payload or _load(BASE_FRAMES)
    sandbox_payload = sandbox_payload or _load(SANDBOX)
    coverage_payload = coverage_payload or _load(COVERAGE)
    frames = trace_frames(sandbox_payload)
    summary = _summarize(frames)
    trace_only_safe = (
        summary["trace_frame_count"] > 0
        and summary["stage7_trace_frame_count"] == 0
        and summary["selector_training_row_count"] == 0
        and summary["candidate_generation_training_row_count"] == 0
        and (coverage_payload.get("decision") or {}).get("selector_allowed") is False
        and (coverage_payload.get("decision") or {}).get("status")
        == "exact_trace_enrichment_coverage_ready_for_trace_dataset_refresh"
    )
    return {
        "schema_version": "krk_strategy_sequence_exact_trace_enrichment_trace_features.v1",
        "causal_status": "non_causal_trace_feature_augmentation",
        **_runtime_false_block(),
        "source_artifacts": [str(BASE_FRAMES), str(SANDBOX), str(COVERAGE)],
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
                "exact_trace_enrichment_trace_features_folded_non_causal"
                if trace_only_safe
                else "exact_trace_enrichment_trace_feature_fold_blocked"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "build_strategy_sequence_dataset_v5_non_causal"
                if trace_only_safe
                else "quarantine_exact_trace_enrichment_trace_features"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy-Sequence Exact Trace Enrichment Trace Features v1",
        "",
        "This artifact folds emitted exact trace enrichment sandbox frames into the strategy-sequence evidence track as trace-only features. It does not alter runtime behavior and does not authorize selector behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Trace Features",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "These frames are context evidence only. They are not capacity labels, ownership labels, selector rows, guardrail triggers, routing requests, or score changes.",
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
