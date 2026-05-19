#!/usr/bin/env python3
"""Define KRK selector readiness v2 criteria."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCH_REVIEW = Path("reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.json")
OUT_JSON = Path("reports/krk_selector_readiness_v2_plan.json")
OUT_MD = Path("reports/krk_selector_readiness_v2_plan.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    review = _load_json(ARCH_REVIEW)
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("source review must remain non-causal")
    return {
        "schema_version": "krk_selector_readiness_v2_plan.v0",
        "causal_status": "non_causal_design_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(ARCH_REVIEW)],
        "purpose": (
            "Prevent future selector sandbox reviews from treating guardrail-positive, "
            "single-provider evidence as strategy-arbitration evidence."
        ),
        "readiness_requirements_v2": [
            {
                "requirement_id": "label_balance",
                "description": "Protected-control labels must include enough positive and negative examples per target semantics.",
                "minimum": {
                    "overall_positive_count": 6,
                    "overall_negative_count": 6,
                    "min_positive_negative_ratio": 0.5,
                },
            },
            {
                "requirement_id": "provider_diversity",
                "description": "Selected and candidate provider evidence must not be dominated by one provider family.",
                "minimum": {
                    "distinct_selected_provider_families": 3,
                    "max_selected_provider_family_dominance": 0.7,
                    "distinct_conversion_positive_provider_families": 2,
                },
            },
            {
                "requirement_id": "label_semantics_split",
                "description": "Evaluate selected playout, forced-provider conversion, and same-move compatibility separately.",
                "minimum": {
                    "selected_playout_rows": 12,
                    "forced_provider_rows": 12,
                    "same_move_compatibility_rows_if_available": 4,
                },
            },
            {
                "requirement_id": "stage_coverage",
                "description": "Protected controls must span Stage 4, Stage 5, and Stage 6 without using Stage 7 training rows.",
                "minimum": {
                    "stage4_rows": 4,
                    "stage5_rows": 4,
                    "stage6_rows": 4,
                    "stage7_training_rows": 0,
                },
            },
            {
                "requirement_id": "held_out_challenge_boundary",
                "description": "Stage 7 residuals remain held-out challenge cases unless explicitly reclassified by architecture review.",
                "minimum": {
                    "stage7_training_rows": 0,
                    "stage7_runtime_repair_allowed": False,
                },
            },
            {
                "requirement_id": "selector_outperforms_non_selector_baselines",
                "description": "A proposed selector must beat provider-prior/stage-prior/simple-score baselines on held-out protected controls.",
                "minimum": {
                    "held_out_positive_hit_rate_margin": 0.1,
                    "guardrail_regression_allowed": False,
                },
            },
        ],
        "blocked_by_current_evidence": [
            "class_imbalance",
            "selected_provider_family_dominance",
            "insufficient_non_stage0_conversion_positive_ownership_examples",
            "same_move_compatibility_not_executed_in_bounded_out_of_sample_run",
        ],
        "next_allowed_evidence_slice": {
            "name": "strategy_owner_contrast_dataset_v0",
            "causal_status": "non_causal_only",
            "goal": (
                "Find or collect small protected-control states where multiple providers are plausible "
                "and non-stage0 provider ownership has conversion evidence."
            ),
            "forbidden": [
                "runtime_arbiter",
                "selector_sandbox",
                "stage7_repair",
                "stage7_promotion",
                "stage8_training",
            ],
        },
        "decision": {
            "status": "selector_readiness_v2_defined_runtime_sandbox_blocked",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "build_non_causal_strategy_owner_contrast_dataset_v0",
        },
    }


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# KRK Selector Readiness v2 Plan",
        "",
        "This design-only plan tightens selector-readiness criteria after the out-of-sample "
        "controls showed strong guardrail conversion but weak selector evidence.",
        "",
        "## Purpose",
        "",
        plan["purpose"],
        "",
        "## Requirements",
        "",
    ]
    for item in plan["readiness_requirements_v2"]:
        lines.append(f"- `{item['requirement_id']}`: {item['description']} Minimum: `{item['minimum']}`")
    lines.extend(
        [
            "",
            "## Current Blockers",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in plan["blocked_by_current_evidence"])
    next_slice = plan["next_allowed_evidence_slice"]
    lines.extend(
        [
            "",
            "## Next Allowed Evidence Slice",
            "",
            f"- Name: `{next_slice['name']}`",
            f"- Status: `{next_slice['causal_status']}`",
            f"- Goal: {next_slice['goal']}",
            "",
            "## Decision",
            "",
            f"- Status: `{plan['decision']['status']}`",
            f"- Recommended next step: `{plan['decision']['recommended_next_step']}`",
            "- Runtime arbiter and selector sandbox remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    plan = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(plan), encoding="utf-8")
    print(json.dumps(plan["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
