#!/usr/bin/env python3
"""Write a review packet for a scoped Stage 5/6 candidate-generation refresh sandbox."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = Path(
    "reports/strategy_arbitration/krk_stage_conditioned_candidate_generation_benchmark_v3.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_review_packet_v3.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_review_packet_v3.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(benchmark: dict[str, Any] | None = None) -> dict[str, Any]:
    benchmark = benchmark or _load(BENCHMARK)
    summary = benchmark.get("summary") or {}
    stage5_6_metrics = summary.get("stage5_6_positive_scope_metrics") or {}
    review_ready = bool(
        stage5_6_metrics.get("positive_recall", 0.0) >= 0.9
        and stage5_6_metrics.get("negative_suppression", 0.0) >= 0.9
        and summary.get("stage7_readiness_training_row_count") == 0
    )
    return {
        "schema_version": "krk_stage5_6_candidate_generation_refresh_review_packet.v3",
        "causal_status": "runtime_review_packet_non_causal",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(BENCHMARK)],
        "evidence_summary": {
            "benchmark_status": (benchmark.get("decision") or {}).get("status"),
            "stage5_6_metrics": stage5_6_metrics,
            "stage4_metrics": summary.get("stage4_positive_scope_metrics"),
            "positive_scope_cells": summary.get("positive_scope_cells"),
        },
        "approved_scope_if_later_authorized": {
            "source_stages": ["stage5", "stage6"],
            "excluded_stages": ["stage4", "stage7", "stage8"],
            "stage7_use": "held_out_challenge_only",
            "candidate_generation_cells": {
                "stage5": ["edge_trap", "fence_established", "stage0_basin"],
                "stage6": ["stage0_basin"],
            },
            "candidate_source": "validated_provider_capacity_scope",
            "allowed_runtime_effect": "emit_extra_candidate_generation_frames_only",
            "direct_request": False,
            "score_delta": 0.0,
            "causal_status_for_frames": "observation_or_candidate_generation_only",
        },
        "explicitly_forbidden": [
            "selecting_a_provider",
            "selecting_a_move",
            "suppressing_providers",
            "changing_scores",
            "direct_provider_routing",
            "stage4_scope_without_companion_review",
            "stage7_training_rows",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "hidden_python_controller",
        ],
        "implementation_requirements_if_approved_later": [
            "explicit opt-in flag",
            "default-off equivalence on protected Stage 5/6",
            "zero selected move/provider delta when observing only",
            "zero score delta",
            "bounded generated candidate count",
            "trace every generated candidate source term",
            "mark Stage 7 rows held-out if sampled diagnostically",
            "target smoke before any guardrails",
            "separate selector review before any candidate can affect routing",
        ],
        "risk_register": [
            "capacity labels are not ownership labels",
            "Stage 4 remains mixed and excluded",
            "Stage 7 remains held out",
            "candidate generation may expose negative-capacity candidates if scope leaks",
            "runtime selector is still blocked",
        ],
        "decision": {
            "status": (
                "stage5_6_candidate_generation_refresh_review_ready"
                if review_ready
                else "stage5_6_candidate_generation_refresh_review_blocked"
            ),
            "implementation_authorized_by_this_packet": False,
            "runtime_review_ready": review_ready,
            "selector_allowed": False,
            "runtime_candidate_generator_refresh_allowed_by_this_packet": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "explicit_approval_required_for_default_off_stage5_6_candidate_generation_refresh_sandbox"
                if review_ready
                else "continue_non_causal_stage_conditioned_review"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    decision = payload["decision"]
    evidence = payload["evidence_summary"]
    lines = [
        "# KRK Stage 5/6 Candidate-Generation Refresh Review Packet v3",
        "",
        "This packet reviews a narrow future default-off candidate-generation refresh sandbox for protected Stage 5/6 only. It does not authorize implementation by itself.",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- runtime_review_ready: `{decision['runtime_review_ready']}`",
        f"- implementation_authorized_by_this_packet: `{decision['implementation_authorized_by_this_packet']}`",
        f"- selector_allowed: `{decision['selector_allowed']}`",
        f"- runtime_candidate_generator_refresh_allowed_by_this_packet: `{decision['runtime_candidate_generator_refresh_allowed_by_this_packet']}`",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        "",
        "## Evidence",
        "",
        f"- benchmark_status: `{evidence['benchmark_status']}`",
        f"- stage5_6_metrics: `{evidence['stage5_6_metrics']}`",
        f"- stage4_metrics: `{evidence['stage4_metrics']}`",
        f"- positive_scope_cells: `{evidence['positive_scope_cells']}`",
        "",
        "## Approved Scope If Later Authorized",
        "",
    ]
    for key, value in payload["approved_scope_if_later_authorized"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Explicitly Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
    lines.extend(["", "## Implementation Requirements If Later Approved", ""])
    lines.extend(f"- `{item}`" for item in payload["implementation_requirements_if_approved_later"])
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
