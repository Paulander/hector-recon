#!/usr/bin/env python3
"""Review strategy-sequence trace-feature integration status."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_FRAMES = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json")
TRACE_FEATURES = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_repair_monitor_trace_features_v1.json"
)
QUALITY_REVIEW = Path(
    "reports/strategy_arbitration/krk_repair_monitor_observation_source_quality_review_v1.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_trace_feature_integration_review_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_trace_feature_integration_review_v1.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    *,
    base_payload: dict[str, Any] | None = None,
    trace_payload: dict[str, Any] | None = None,
    quality_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_payload = base_payload or _load(BASE_FRAMES)
    trace_payload = trace_payload or _load(TRACE_FEATURES)
    quality_payload = quality_payload or _load(QUALITY_REVIEW)
    base_summary = base_payload.get("summary") or {}
    trace_summary = trace_payload.get("summary") or {}
    quality_summary = quality_payload.get("summary") or {}
    integration_safe = (
        (trace_payload.get("decision") or {}).get("selector_allowed") is False
        and int(trace_summary.get("selector_training_row_count") or 0) == 0
        and int(trace_summary.get("candidate_generation_training_row_count") or 0) == 0
        and int(trace_summary.get("stage7_trace_frame_count") or 0) == 0
        and all(
            trace_payload.get(key) is False
            for key in (
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
        )
    )
    selector_blockers = []
    if int(trace_summary.get("selector_training_row_count") or 0) == 0:
        selector_blockers.append("trace_features_are_not_selector_labels")
    if int(trace_summary.get("trace_frame_count") or 0) < 12:
        selector_blockers.append("trace_feature_sample_too_small")
    if int(quality_summary.get("risk_term_set_count") or 0) <= 1:
        selector_blockers.append("repair_monitor_risk_terms_not_diverse")
    if (quality_payload.get("interpretation") or {}).get("quality_signal_mature") is False:
        selector_blockers.append("quality_signal_not_mature")
    return {
        "schema_version": "krk_strategy_sequence_trace_feature_integration_review.v1",
        "causal_status": "non_causal_trace_feature_integration_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(BASE_FRAMES),
            str(TRACE_FEATURES),
            str(QUALITY_REVIEW),
        ],
        "summary": {
            "base_frame_count": base_summary.get("frame_count"),
            "base_stage7_challenge_row_count": base_summary.get(
                "stage7_challenge_row_count"
            ),
            "base_readiness_training_stage7_row_count": base_summary.get(
                "readiness_training_stage7_row_count"
            ),
            "trace_frame_count": trace_summary.get("trace_frame_count"),
            "trace_stage_counts": trace_summary.get("stage_counts"),
            "trace_stage7_frame_count": trace_summary.get("stage7_trace_frame_count"),
            "trace_selector_training_row_count": trace_summary.get(
                "selector_training_row_count"
            ),
            "trace_candidate_generation_training_row_count": trace_summary.get(
                "candidate_generation_training_row_count"
            ),
            "trace_integration_safe": integration_safe,
        },
        "selector_blockers": selector_blockers,
        "validated_progress": [
            "default_off_repair_monitor_observation_source_wired",
            "broadened_protected_sample_default_off_equivalent",
            "repair_monitor_frames_folded_as_trace_only_context",
        ],
        "still_forbidden": [
            "selector_training_from_trace_features",
            "score_changes",
            "provider_routing",
            "guardrail_campaign_for_this_source",
            "stage7_promotion",
            "stage8_training",
        ],
        "decision": {
            "status": (
                "strategy_sequence_trace_features_integrated_selector_still_blocked"
                if integration_safe
                else "strategy_sequence_trace_feature_integration_blocked"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "refresh_strategy_sequence_dataset_design_with_trace_feature_channel"
                if integration_safe
                else "fix_trace_feature_invariants"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy-Sequence Trace Feature Integration Review v1",
        "",
        "This closes the repair-monitor observation-source loop by reviewing whether the trace-only integration changes selector readiness. It does not authorize runtime selection.",
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
        f"- base_frame_count: {summary['base_frame_count']}",
        f"- base_stage7_challenge_row_count: {summary['base_stage7_challenge_row_count']}",
        f"- base_readiness_training_stage7_row_count: {summary['base_readiness_training_stage7_row_count']}",
        f"- trace_frame_count: {summary['trace_frame_count']}",
        f"- trace_stage_counts: `{summary['trace_stage_counts']}`",
        f"- trace_stage7_frame_count: {summary['trace_stage7_frame_count']}",
        f"- trace_selector_training_row_count: {summary['trace_selector_training_row_count']}",
        f"- trace_candidate_generation_training_row_count: {summary['trace_candidate_generation_training_row_count']}",
        f"- trace_integration_safe: `{summary['trace_integration_safe']}`",
        "",
        "## Selector Blockers",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["selector_blockers"])
    lines.extend(
        [
            "",
            "## Validated Progress",
            "",
            *[f"- `{item}`" for item in payload["validated_progress"]],
            "",
            "## Still Forbidden",
            "",
            *[f"- `{item}`" for item in payload["still_forbidden"]],
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
