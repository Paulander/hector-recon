#!/usr/bin/env python3
"""Summarize two-stage candidate-generation and strategy-selection review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_SET_AUDIT = Path("reports/krk_validated_provider_candidate_set_audit_v0.json")
CAPACITY_SEMANTICS = Path("reports/krk_protected_provider_capacity_frame_training_semantics_review_v0.json")
OUT_JSON = Path("reports/krk_two_stage_candidate_selection_review_v0.json")
OUT_MD = Path("reports/krk_two_stage_candidate_selection_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    audit = _load(CANDIDATE_SET_AUDIT)
    semantics = _load(CAPACITY_SEMANTICS)
    if audit.get("causal_status") != "non_causal_candidate_set_audit":
        raise ValueError("candidate-set audit must remain non-causal")
    if semantics.get("causal_status") != "non_causal_semantics_review":
        raise ValueError("capacity semantics review must remain non-causal")
    summary = audit.get("summary") or {}
    positive = int(summary.get("added_positive_capacity_count") or 0)
    negative = int(summary.get("added_negative_capacity_count") or 0)
    payload = {
        "schema_version": "krk_two_stage_candidate_selection_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(CANDIDATE_SET_AUDIT), str(CAPACITY_SEMANTICS)],
        "current_evidence": {
            "candidate_generation_recall_gap_confirmed": True,
            "positive_capacity_recovered_by_validated_provider_set": positive,
            "negative_capacity_also_included": negative,
            "direct_selector_training_allowed": False,
            "runtime_work_allowed": False,
        },
        "two_stage_architecture": {
            "stage_1_candidate_generation": {
                "purpose": "Represent plausible validated providers/strategies so the selector can evaluate them.",
                "evidence_target": "high recall for protected positive-capacity providers",
                "must_not": [
                    "select moves",
                    "boost providers",
                    "suppress providers",
                    "mutate topology",
                    "use runtime DTM/tablebase",
                ],
            },
            "stage_2_strategy_selection": {
                "purpose": "Choose among represented providers using separated label semantics.",
                "evidence_target": "suppress negative-capacity and selected-failure candidates while preserving positive-capacity/selected-success candidates",
                "must_not": [
                    "train on forced-provider capacity as direct runtime-positive labels",
                    "mix Stage 7 held-out residuals into protected training",
                    "ignore guardrail preservation",
                ],
            },
        },
        "minimum_next_benchmark_requirements": [
            "candidate-generator recall for protected positive-capacity providers",
            "selector suppression of protected negative-capacity providers",
            "separate selected-playout, forced-capacity, and runtime-proposal label channels",
            "leave-state-out evaluation over protected Stage 4/5/6 rows",
            "Stage 7 held-out challenge evaluation only",
            "no runtime behavior changes",
        ],
        "blocked_paths": [
            "runtime_selector",
            "runtime_candidate_generator",
            "direct Stage 7 repair",
            "Stage 7 promotion",
            "Stage 8 training",
            "runtime DTM/tablebase",
            "gameplay topology mutation",
        ],
        "decision": {
            "status": "two_stage_non_causal_benchmark_design_needed",
            "recommended_next_step": "plan_two_stage_candidate_selection_benchmark_v0",
            "runtime_work_allowed": False,
            "candidate_generator_runtime_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_review(payload)
    return payload


def validate_review(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["decision"]["candidate_generator_runtime_allowed"] is not False:
        raise ValueError("candidate generator runtime remains blocked")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Two-Stage Candidate / Selection Review v0",
        "",
        "This architecture review separates candidate generation from strategy selection. It is non-causal and does not implement runtime behavior.",
        "",
        "## Current Evidence",
        "",
    ]
    for key, value in payload["current_evidence"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Two-Stage Architecture", ""])
    for stage, spec in payload["two_stage_architecture"].items():
        lines.append(f"- `{stage}` purpose: {spec['purpose']}")
        lines.append(f"- `{stage}` evidence target: {spec['evidence_target']}")
        lines.append(f"- `{stage}` must not: `{spec['must_not']}`")
    lines.extend(["", "## Minimum Next Benchmark Requirements", ""])
    for item in payload["minimum_next_benchmark_requirements"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocked Paths", ""])
    for item in payload["blocked_paths"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
