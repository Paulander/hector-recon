#!/usr/bin/env python3
"""Summarize selector evidence into a directed non-causal fix review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TWO_STAGE = Path("reports/krk_two_stage_candidate_selection_benchmark_v0.json")
NEGATIVE = Path("reports/krk_selector_negative_suppression_evidence_v0.json")
GEOMETRY = Path("reports/krk_geometry_augmented_selector_feature_probe_v0.json")
CANDIDATE_SET = Path("reports/krk_validated_provider_candidate_set_audit_v0.json")
CAPACITY_SEMANTICS = Path("reports/krk_protected_provider_capacity_frame_training_semantics_review_v0.json")
OUT_JSON = Path("reports/krk_selector_directed_fix_review_v0.json")
OUT_MD = Path("reports/krk_selector_directed_fix_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    two_stage = _load(TWO_STAGE)
    negative = _load(NEGATIVE)
    geometry = _load(GEOMETRY)
    candidate_set = _load(CANDIDATE_SET)
    capacity_semantics = _load(CAPACITY_SEMANTICS)
    expected = {
        str(TWO_STAGE): "non_causal_benchmark",
        str(NEGATIVE): "non_causal_evidence_audit",
        str(GEOMETRY): "non_causal_feature_probe",
        str(CANDIDATE_SET): "non_causal_candidate_set_audit",
        str(CAPACITY_SEMANTICS): "non_causal_semantics_review",
    }
    for path, causal_status in expected.items():
        payload = {
            str(TWO_STAGE): two_stage,
            str(NEGATIVE): negative,
            str(GEOMETRY): geometry,
            str(CANDIDATE_SET): candidate_set,
            str(CAPACITY_SEMANTICS): capacity_semantics,
        }[path]
        if payload.get("causal_status") != causal_status:
            raise ValueError(f"{path}: expected {causal_status}")

    two_gen = two_stage.get("candidate_generation_track") or {}
    current = two_gen.get("current_runtime_proposal_frames") or {}
    expanded = two_gen.get("validated_provider_candidate_set_expansion") or {}
    neg_balance = negative.get("label_balance") or {}
    geom_best = geometry.get("best_result") or {}
    payload = {
        "schema_version": "krk_selector_directed_fix_review.v0",
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
        "source_artifacts": [
            str(TWO_STAGE),
            str(NEGATIVE),
            str(GEOMETRY),
            str(CANDIDATE_SET),
            str(CAPACITY_SEMANTICS),
        ],
        "evidence_summary": {
            "candidate_generation_gap": {
                "current_positive_capacity_recall": current.get("positive_capacity_recall_rate"),
                "expanded_positive_capacity_recall": expanded.get("positive_capacity_recall_rate"),
                "expanded_negative_capacity_inclusion": expanded.get("negative_capacity_inclusion_rate"),
                "interpretation": "Validated-provider candidate expansion fixes recall but includes hard negatives.",
            },
            "selector_negative_gap": {
                "training_positive_count": neg_balance.get("training_positive_count"),
                "training_negative_count": neg_balance.get("training_negative_count"),
                "training_negative_state_count": neg_balance.get("training_negative_state_count"),
                "best_negative_suppression": (negative.get("leave_state_out_best_objective_replay") or {}).get(
                    "negative_suppression"
                ),
                "interpretation": "Current selector evidence cannot suppress negatives; negatives are sparse and concentrated.",
            },
            "geometry_gap": {
                "best_geometry_objective": geom_best.get("objective"),
                "best_geometry_negative_suppression": geom_best.get("negative_suppression"),
                "geometry_underpowered": (geometry.get("summary") or {}).get("underpowered"),
                "interpretation": "Simple geometry terms alone do not fix suppression on current data.",
            },
        },
        "rejected_fixes": [
            {
                "fix": "runtime_selector_now",
                "reason": "selection negative suppression is 0.0 in current probes",
            },
            {
                "fix": "runtime_candidate_generator_now",
                "reason": "candidate expansion includes negative-capacity providers and needs selection semantics",
            },
            {
                "fix": "train_selector_on_forced_capacity_as_positive",
                "reason": "forced-provider capacity is not a direct runtime ownership label",
            },
            {
                "fix": "add_simple_geometry_terms_only",
                "reason": "geometry feature probe still has 0.0 negative suppression",
            },
            {
                "fix": "return_to_stage7_patch",
                "reason": "Stage 7 is held-out boundary evidence, not the current training target",
            },
        ],
        "directed_fix_requirements": [
            "keep candidate generation and selection as separate channels",
            "create a hard-negative selector target dataset from protected capacity negatives",
            "keep forced-capacity labels distinct from selected-playout labels",
            "add move/post-move geometry only as non-causal scoring features",
            "evaluate leave-state-out suppression before any sandbox",
            "keep Stage 7 held out",
        ],
        "recommended_fix_class": {
            "name": "non_causal_hard_negative_selector_target_design",
            "description": (
                "Build a reviewed selector benchmark that uses protected capacity negatives as hard-negative evaluation/training candidates "
                "only after preserving label semantics, and adds geometry/post-move features to test suppression."
            ),
            "not_runtime": True,
        },
        "decision": {
            "status": "directed_fix_review_complete_runtime_blocked",
            "recommended_next_step": "design_hard_negative_selector_target_dataset_v0",
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
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selector Directed Fix Review v0",
        "",
        "This review consolidates the non-causal evidence for a directed selector-side fix.",
        "",
        "## Evidence Summary",
        "",
    ]
    for key, value in payload["evidence_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rejected Fixes", ""])
    for item in payload["rejected_fixes"]:
        lines.append(f"- `{item['fix']}`: {item['reason']}")
    lines.extend(["", "## Directed Fix Requirements", ""])
    for item in payload["directed_fix_requirements"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Recommended Fix Class",
            "",
            f"- Name: `{payload['recommended_fix_class']['name']}`",
            f"- Description: {payload['recommended_fix_class']['description']}",
            "",
            "## Decision",
            "",
        ]
    )
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
