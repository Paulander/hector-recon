#!/usr/bin/env python3
"""Write KRK strategy-sequence dataset design v2 with trace-feature channel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TRACE_REVIEW = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_trace_feature_integration_review_v1.json"
)
OUT_JSON = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v2.json")
OUT_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v2.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(trace_review: dict[str, Any] | None = None) -> dict[str, Any]:
    trace_review = trace_review or _load(TRACE_REVIEW)
    return {
        "schema_version": "krk_strategy_sequence_dataset_design.v2",
        "causal_status": "non_causal_design",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(TRACE_REVIEW)],
        "design_goal": (
            "Make KRK strategy-sequence evidence channels explicit so future "
            "candidate generation, monitor, and selector work cannot conflate "
            "capacity labels, ownership labels, and trace-only context."
        ),
        "evidence_channels": [
            {
                "channel": "validated_provider_capacity",
                "label_semantics": "forced_provider_capacity_label",
                "allowed_use": "candidate_generation_recall_benchmark",
                "forbidden_use": "selector_training_label",
            },
            {
                "channel": "visible_provider_proposal",
                "label_semantics": "normal_routing_proposal_context",
                "allowed_use": "proposal_context_and_score_scale_analysis",
                "forbidden_use": "capacity_or_ownership_label_without_outcome",
            },
            {
                "channel": "candidate_move_frame",
                "label_semantics": "legal_move_hypothesis",
                "allowed_use": "candidate_coverage_and_feature_quality",
                "forbidden_use": "runtime_move_suggestion_without_selector_review",
            },
            {
                "channel": "plan_capsule_sequence_candidate",
                "label_semantics": "heldout_or_plan_context",
                "allowed_use": "sequence_policy_evidence",
                "forbidden_use": "stage7_training_row_or_promotion_evidence",
            },
            {
                "channel": "internal_monitor_candidate",
                "label_semantics": "internal_control_context",
                "allowed_use": "self_monitoring_and_growth_pressure_analysis",
                "forbidden_use": "direct_provider_route",
            },
            {
                "channel": "runtime_observation_trace_feature",
                "label_semantics": "trace_context_not_selector_label",
                "allowed_use": "future_strategy_sequence_dataset_context",
                "forbidden_use": "selector_training_or_guardrail_trigger",
            },
        ],
        "partition_rules": {
            "protected_readiness_stages": ["stage4", "stage5", "stage6"],
            "heldout_challenge_stages": ["stage7"],
            "stage7_training_rows_allowed": False,
            "stage8_training_allowed": False,
        },
        "minimum_next_dataset_refresh_requirements": [
            "keep channel-specific label_semantics",
            "carry trace_feature_channel separately from candidate-generation labels",
            "preserve stage7 held-out status",
            "report selector_training_row_count by channel",
            "report candidate_generation_training_row_count by channel",
            "report trace-only context row count by channel",
            "block selector review unless ownership labels are explicit",
        ],
        "trace_feature_status": {
            "integration_review_status": (trace_review.get("decision") or {}).get("status"),
            "trace_frame_count": (trace_review.get("summary") or {}).get("trace_frame_count"),
            "selector_blockers": list(trace_review.get("selector_blockers") or []),
        },
        "decision": {
            "status": "strategy_sequence_dataset_design_v2_ready",
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "recommended_next_step": "implement_strategy_sequence_dataset_refresh_v2_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy-Sequence Dataset Design v2",
        "",
        payload["design_goal"],
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- implementation_allowed_by_this_artifact: `{payload['decision']['implementation_allowed_by_this_artifact']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Evidence Channels",
        "",
    ]
    for channel in payload["evidence_channels"]:
        lines.extend(
            [
                f"### {channel['channel']}",
                "",
                f"- label_semantics: `{channel['label_semantics']}`",
                f"- allowed_use: `{channel['allowed_use']}`",
                f"- forbidden_use: `{channel['forbidden_use']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Partition Rules",
            "",
            f"- protected_readiness_stages: `{payload['partition_rules']['protected_readiness_stages']}`",
            f"- heldout_challenge_stages: `{payload['partition_rules']['heldout_challenge_stages']}`",
            f"- stage7_training_rows_allowed: `{payload['partition_rules']['stage7_training_rows_allowed']}`",
            f"- stage8_training_allowed: `{payload['partition_rules']['stage8_training_allowed']}`",
            "",
            "## Minimum Next Refresh Requirements",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in payload["minimum_next_dataset_refresh_requirements"])
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
