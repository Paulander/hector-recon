#!/usr/bin/env python3
"""Define the KRK normalized contrastive strategy-selector objective.

This is a design artifact only. It translates the objective review into a
concrete offline objective contract that can be probed before any further
runtime-test work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBJECTIVE_REVIEW = Path("reports/krk_arbitration_objective_review_v1.json")
OWNER_CONTRAST = Path("reports/krk_strategy_owner_contrast_probe_v0.json")
READINESS_V3 = Path("reports/krk_selector_readiness_v3_plan.json")
OUT_JSON = Path("reports/krk_normalized_strategy_selector_objective_v1.json")
OUT_MD = Path("reports/krk_normalized_strategy_selector_objective_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    review = _load_json(OBJECTIVE_REVIEW)
    contrast = _load_json(OWNER_CONTRAST)
    readiness = _load_json(READINESS_V3)

    if review.get("decision", {}).get("status") != "additive_support_objective_rejected_design_normalized_selector_objective":
        raise ValueError("objective review must reject additive support before this design")

    contrast_metrics = contrast.get("metrics") or {}
    readiness_checks = readiness.get("readiness_checks") or []
    plan = {
        "schema_version": "krk_normalized_strategy_selector_objective.v1",
        "causal_status": "non_causal_design_only",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OBJECTIVE_REVIEW), str(OWNER_CONTRAST), str(READINESS_V3)],
        "objective_id": "objective.krk.normalized_contrastive_strategy_selector.v1",
        "purpose": (
            "Learn strategy/provider ownership from normalized provider-local evidence and "
            "explicit label semantics, rather than raw global score or broad additive support."
        ),
        "input_frame": "StrategyProposalFrame",
        "required_input_fields": [
            "state_id",
            "active_landmark_label",
            "provider_id",
            "skill_id",
            "provider_version",
            "provider_family",
            "provider_maturity",
            "provider_local_rank",
            "normalized_score",
            "source_terms",
            "role_licenses",
            "plan_capsule_context",
            "move_shape_terms",
            "post_move_terms",
            "safety_terms",
            "known_outcome_label",
            "causal_status=non_causal",
        ],
        "label_channels": [
            {
                "label_channel": "selected_playout",
                "meaning": "result when current normal arbitration selected this provider/move",
                "use": "context, not sole target",
            },
            {
                "label_channel": "forced_provider",
                "meaning": "conversion result when a provider family is forced from the same state",
                "use": "contrastive candidate ownership signal",
            },
            {
                "label_channel": "same_move_provider_compatibility",
                "meaning": "whether another provider can support the same move without conflict",
                "use": "compatibility and guardrail-safety signal",
            },
            {
                "label_channel": "heldout_stage7_challenge",
                "meaning": "unresolved Stage7 residual family evidence",
                "use": "evaluation only, never training in v1",
            },
        ],
        "normalization_policy": {
            "raw_global_score": "audit_only_not_selector_target",
            "provider_local_rank": "required",
            "normalized_score": "required_if_available",
            "provider_family_maturity_prior": "allowed_as_feature_not_hidden_router",
            "support_scale": "not_used_in_training_target",
        },
        "candidate_objectives": [
            {
                "name": "family_maturity_ranked_logistic",
                "features": ["provider_family", "provider_maturity", "provider_local_rank"],
                "blocked_from_runtime_use": True,
            },
            {
                "name": "normalized_rank_plus_visible_terms",
                "features": [
                    "provider_local_rank",
                    "normalized_score",
                    "source_terms",
                    "move_shape_terms",
                    "post_move_terms",
                    "safety_terms",
                ],
                "blocked_from_runtime_use": True,
            },
            {
                "name": "contrastive_owner_pairwise",
                "features": [
                    "same_state_provider_pair",
                    "forced_provider_conversion_delta",
                    "provider_family",
                    "provider_maturity",
                    "provider_local_rank_delta",
                ],
                "blocked_from_runtime_use": True,
            },
        ],
        "evaluation_protocol": {
            "splits": [
                "protected_stage_family_holdout",
                "leave_provider_family_out_if_feasible",
                "stage7_challenge_holdout",
            ],
            "metrics": [
                "positive_owner_top1",
                "positive_owner_top3",
                "protected_negative_suppression",
                "stage7_challenge_no_training_leakage",
                "selected_stage0_dominance_reduction_offline",
                "guardrail_label_no_regression_proxy",
            ],
            "minimum_before_runtime_review": [
                "beats provider_family_maturity_prior on heldout protected rows",
                "does not train on Stage7 challenge rows",
                "can explain selected ownership with visible source terms",
                "keeps label channels separate in artifacts",
            ],
        },
        "evidence_context": {
            "contrast_training_positive_label_count": contrast_metrics.get("training_positive_label_count"),
            "contrast_training_negative_label_count": contrast_metrics.get("training_negative_label_count"),
            "contrast_heldout_row_count": contrast_metrics.get("heldout_row_count"),
            "readiness_checks": readiness_checks,
        },
        "forbidden_uses": [
            "runtime selector",
            "runtime provider support",
            "score bonus or provider penalty",
            "Stage7 repair",
            "Stage7 promotion",
            "Stage8 training",
            "runtime DTM/tablebase",
            "gameplay topology mutation",
            "hidden Python controller",
        ],
        "decision": {
            "status": "normalized_selector_objective_design_ready_for_offline_probe",
            "recommended_next_step": "run_offline_normalized_selector_objective_probe_v1",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if plan.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if plan.get("causal_status") != "non_causal_design_only":
        raise ValueError("objective plan must remain non-causal")
    if plan.get("decision", {}).get("runtime_test_allowed_next") is not False:
        raise ValueError("runtime tests must remain blocked by this design")


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# KRK Normalized Strategy Selector Objective v1",
        "",
        "This design defines a non-causal offline objective to replace broad additive support as the next arbitration experiment.",
        "",
        f"- Objective id: `{plan['objective_id']}`",
        f"- Causal status: `{plan['causal_status']}`",
        "",
        "## Purpose",
        "",
        plan["purpose"],
        "",
        "## Required Input Fields",
        "",
    ]
    for item in plan["required_input_fields"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Label Channels", ""])
    for channel in plan["label_channels"]:
        lines.append(f"### `{channel['label_channel']}`")
        lines.append("")
        lines.append(f"- Meaning: {channel['meaning']}")
        lines.append(f"- Use: {channel['use']}")
        lines.append("")
    lines.extend(["## Normalization Policy", ""])
    for key, value in plan["normalization_policy"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Candidate Objectives", ""])
    for objective in plan["candidate_objectives"]:
        lines.append(f"### `{objective['name']}`")
        lines.append("")
        lines.append(f"- Features: `{objective['features']}`")
        lines.append(f"- Blocked from runtime use: `{objective['blocked_from_runtime_use']}`")
        lines.append("")
    lines.extend(["## Evaluation Protocol", ""])
    lines.append("Splits:")
    for item in plan["evaluation_protocol"]["splits"]:
        lines.append(f"- `{item}`")
    lines.append("")
    lines.append("Metrics:")
    for item in plan["evaluation_protocol"]["metrics"]:
        lines.append(f"- `{item}`")
    lines.append("")
    lines.append("Minimum before runtime review:")
    for item in plan["evaluation_protocol"]["minimum_before_runtime_review"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Forbidden Uses", ""])
    for item in plan["forbidden_uses"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{plan['decision']['status']}`",
            f"- Recommended next step: `{plan['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{plan['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{plan['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{plan['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    plan = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(plan), encoding="utf-8")
    print(json.dumps(plan["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
