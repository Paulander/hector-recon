#!/usr/bin/env python3
"""Write a runtime-review packet for the v3 candidate-generation refresh benchmark.

The packet is review-only. It does not authorize runtime implementation or any
selector behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_benchmark_v3.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_runtime_review_packet_v3.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_runtime_review_packet_v3.md"
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


def _approved_cells(benchmark: dict[str, Any]) -> dict[str, list[str]]:
    rates = benchmark.get("rate_tables") or {}
    stage_family = rates.get("stage_family") or {}
    policy_name = (benchmark.get("summary") or {}).get("best_policy")
    if policy_name != "trace_stage_family_context":
        return {}
    trace_policy = (benchmark.get("policy_metrics") or {}).get("trace_stage_family_context") or {}
    if trace_policy.get("false_positive", 1) != 0:
        return {}
    cells: dict[str, list[str]] = {}
    for key, stats in stage_family.items():
        if stats.get("negative", 0) != 0:
            continue
        if stats.get("positive", 0) == 0:
            continue
        stage, _, family = key.partition("|")
        if stage not in {"stage4", "stage5", "stage6"}:
            continue
        # The trace-stage-family policy currently exposes only Stage 5/6 cells.
        if stage == "stage4":
            continue
        cells.setdefault(stage, []).append(family)
    return {stage: sorted(set(families)) for stage, families in sorted(cells.items())}


def build_payload(benchmark: dict[str, Any] | None = None) -> dict[str, Any]:
    benchmark = benchmark or _load(BENCHMARK)
    summary = benchmark.get("summary") or {}
    decision = benchmark.get("decision") or {}
    best_metrics = summary.get("best_policy_metrics") or {}
    best_lso = summary.get("best_policy_leave_stage_out_metrics") or {}
    thresholds = benchmark.get("thresholds") or {}
    review_ready = bool(
        decision.get("status")
        == "candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed"
        and summary.get("thresholds_met") is True
        and summary.get("selector_training_row_count") == 0
        and summary.get("stage7_training_row_count") == 0
    )
    approved_cells = _approved_cells(benchmark)
    return {
        "schema_version": "krk_candidate_generation_training_refresh_runtime_review_packet.v3",
        "causal_status": "non_causal_runtime_review_packet",
        **_runtime_false_block(),
        "source_artifacts": [str(BENCHMARK)],
        "evidence_summary": {
            "benchmark_status": decision.get("status"),
            "best_policy": summary.get("best_policy"),
            "best_policy_metrics": best_metrics,
            "best_policy_leave_stage_out_metrics": best_lso,
            "thresholds": thresholds,
            "thresholds_met": summary.get("thresholds_met"),
        },
        "approved_scope_if_later_authorized": {
            "sandbox_type": "default_off_candidate_generation_refresh",
            "allowed_effect": "emit_extra_candidate_generation_frames_only",
            "candidate_generation_policy": summary.get("best_policy"),
            "candidate_generation_cells": approved_cells,
            "protected_stages": ["stage5", "stage6"],
            "excluded_from_training_or_readiness": ["stage7", "stage8"],
            "stage4_status": "positive_capacity_exists_but_not_covered_by_current_trace_stage_family_policy",
            "stage7_use": "held_out_challenge_visibility_only",
            "direct_request": False,
            "score_delta": 0.0,
            "causal_status_for_frames": "candidate_generation_only",
        },
        "explicitly_forbidden": [
            "selector_training",
            "provider_selection",
            "move_selection",
            "score_changes",
            "provider_suppression",
            "direct_provider_routing",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "stage7_training_rows",
            "stage7_promotion",
            "stage8_training",
            "stage4_runtime_scope_without_separate_review",
            "guardrails_before_target_smoke",
        ],
        "implementation_requirements_if_explicitly_approved_later": [
            "explicit opt-in flag",
            "default-off equivalence before enabled smoke",
            "bounded candidate count per decision",
            "zero selected move/provider delta in observation-only mode",
            "zero score delta",
            "direct_request=false on every generated frame",
            "source terms and policy cell recorded on every frame",
            "Stage 7 frames marked held_out_challenge if diagnostic sampling is enabled",
            "target smoke before guardrails",
            "separate selector review before generated frames can affect routing or scoring",
        ],
        "risk_register": [
            "capacity labels are not ownership labels",
            "current best policy misses protected Stage 4 positive-capacity rows",
            "current best policy is a candidate-generation scope, not a sequence policy",
            "candidate generation can increase trace volume if unbounded",
            "selector remains blocked",
        ],
        "decision": {
            "status": (
                "candidate_generation_training_refresh_runtime_review_ready"
                if review_ready
                else "candidate_generation_training_refresh_runtime_review_blocked"
            ),
            "runtime_review_ready": review_ready,
            "implementation_authorized_by_this_packet": False,
            "runtime_candidate_generation_allowed_by_this_packet": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "explicit_approval_required_for_default_off_candidate_generation_refresh_sandbox"
                if review_ready
                else "continue_non_causal_candidate_generation_benchmark_review"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    decision = payload["decision"]
    evidence = payload["evidence_summary"]
    scope = payload["approved_scope_if_later_authorized"]
    lines = [
        "# KRK Candidate-Generation Training Refresh Runtime Review Packet v3",
        "",
        "This packet reviews a future default-off candidate-generation refresh sandbox. It does not authorize implementation, selection, scoring, routing, guardrails, promotion, or Stage 8 training.",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- runtime_review_ready: `{decision['runtime_review_ready']}`",
        f"- implementation_authorized_by_this_packet: `{decision['implementation_authorized_by_this_packet']}`",
        f"- runtime_candidate_generation_allowed_by_this_packet: `{decision['runtime_candidate_generation_allowed_by_this_packet']}`",
        f"- selector_allowed: `{decision['selector_allowed']}`",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        "",
        "## Evidence",
        "",
        f"- benchmark_status: `{evidence['benchmark_status']}`",
        f"- best_policy: `{evidence['best_policy']}`",
        f"- best_policy_metrics: `{evidence['best_policy_metrics']}`",
        f"- best_policy_leave_stage_out_metrics: `{evidence['best_policy_leave_stage_out_metrics']}`",
        f"- thresholds_met: `{evidence['thresholds_met']}`",
        "",
        "## Approved Scope If Later Authorized",
        "",
    ]
    for key, value in scope.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Explicitly Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
    lines.extend(["", "## Implementation Requirements If Explicitly Approved Later", ""])
    lines.extend(
        f"- `{item}`" for item in payload["implementation_requirements_if_explicitly_approved_later"]
    )
    lines.extend(["", "## Risk Register", ""])
    lines.extend(f"- `{item}`" for item in payload["risk_register"])
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
