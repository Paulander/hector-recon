#!/usr/bin/env python3
"""Write review packet for protected strategy-monitor observation source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPANSION = Path(
    "reports/strategy_arbitration/krk_protected_strategy_monitor_frame_expansion_v1.json"
)
QUALITY = Path("reports/strategy_arbitration/krk_protected_strategy_monitor_frame_quality_v1.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_protected_strategy_monitor_observation_source_review_packet_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_protected_strategy_monitor_observation_source_review_packet_v1.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    expansion: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expansion = expansion or _load(EXPANSION)
    quality = quality or _load(QUALITY)
    family_stats = quality.get("family_stats") or {}
    repair_stats = family_stats.get("terminal.krk.repair_needed_monitor") or {}
    review_ready = (
        int(repair_stats.get("frame_count") or 0) >= 5
        and float(repair_stats.get("failure_precision") or 0.0) >= 0.7
        and (expansion.get("summary") or {}).get("stage7_challenge_row_count") == 0
    )
    return {
        "schema_version": "krk_protected_strategy_monitor_observation_source_review_packet.v1",
        "causal_status": "non_causal_runtime_review_packet",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_candidate_generator_changes_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(EXPANSION), str(QUALITY)],
        "approved_scope_for_future_review": {
            "candidate_source": "broader_strategy_candidate",
            "strategy_family": "terminal.krk.repair_needed_monitor",
            "mode": "observation_only",
            "default_off_required": True,
            "direct_request": False,
            "score_delta": 0.0,
            "causal_status": "observation_only",
            "protected_stages": ["stage4", "stage5", "stage6"],
            "stage7_usage": "held_out_evaluation_only",
        },
        "evidence": {
            "expanded_frame_count": (expansion.get("summary") or {}).get("frame_count"),
            "expanded_frame_count_by_stage": (expansion.get("summary") or {}).get(
                "frame_count_by_stage"
            ),
            "repair_needed_frame_count": repair_stats.get("frame_count"),
            "repair_needed_failure_precision": repair_stats.get("failure_precision"),
            "repair_needed_success_precision": repair_stats.get("success_precision"),
            "stage7_challenge_row_count": (expansion.get("summary") or {}).get(
                "stage7_challenge_row_count"
            ),
        },
        "required_future_acceptance": [
            "separate explicit approval before implementation",
            "default-off flag",
            "default-off equivalence on protected Stage 4/5/6 and Stage 7 held-out smoke",
            "emit observation frames only",
            "no selected move/provider delta",
            "no score changes",
            "no direct routing or provider request",
            "bounded candidate count",
            "trace visible source terms and monitor id",
            "Stage 7 remains held-out and not training/readiness",
        ],
        "explicitly_forbidden": [
            "selector",
            "provider_boost",
            "provider_suppression",
            "score_change",
            "direct_provider_route",
            "guardrail_campaign_from_observation_only_source",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
        "decision": {
            "status": "protected_repair_monitor_observation_source_review_ready"
            if review_ready
            else "protected_strategy_monitor_observation_source_review_blocked",
            "implementation_allowed_by_this_packet": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed_without_explicit_approval": False,
            "recommended_next_step": "request_explicit_approval_for_default_off_repair_monitor_observation_source"
            if review_ready
            else "refine_protected_strategy_monitor_evidence",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    evidence = payload["evidence"]
    scope = payload["approved_scope_for_future_review"]
    lines = [
        "# KRK Protected Strategy Monitor Observation Source Review Packet v1",
        "",
        "This packet is a review artifact only. It does not implement runtime source expansion.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- implementation_allowed_by_this_packet: `{payload['decision']['implementation_allowed_by_this_packet']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Future Scope If Explicitly Approved Later",
        "",
    ]
    for key, value in scope.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Evidence", ""])
    for key, value in evidence.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Required Future Acceptance", ""])
    lines.extend(f"- {item}" for item in payload["required_future_acceptance"])
    lines.extend(["", "## Explicitly Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
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
