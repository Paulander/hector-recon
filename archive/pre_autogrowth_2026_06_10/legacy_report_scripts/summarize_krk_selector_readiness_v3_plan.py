#!/usr/bin/env python3
"""Define KRK selector readiness v3 criteria."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCH_REVIEW = Path("reports/krk_selected_provider_diversity_architecture_review_v0.json")
CONTRAST_DATASET = Path("reports/krk_strategy_owner_contrast_dataset_v0.json")
CONTRAST_PROBE = Path("reports/krk_strategy_owner_contrast_probe_v0.json")
OUT_JSON = Path("reports/krk_selector_readiness_v3_plan.json")
OUT_MD = Path("reports/krk_selector_readiness_v3_plan.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    review = _load_json(ARCH_REVIEW)
    dataset = _load_json(CONTRAST_DATASET)
    probe = _load_json(CONTRAST_PROBE)
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("architecture review must remain non-causal")
    if dataset.get("causal_status") != "non_causal_dataset":
        raise ValueError("contrast dataset must remain non-causal")
    if probe.get("causal_status") != "non_causal_probe":
        raise ValueError("contrast probe must remain non-causal")
    summary = dataset.get("summary") or {}
    readiness = dataset.get("readiness_v2_assessment") or {}
    metrics = probe.get("metrics") or {}
    proposal_family_rates = metrics.get("training_provider_family_rates") or {}
    positive_families = sorted(
        family for family, stats in proposal_family_rates.items() if (stats or {}).get("positive", 0) > 0
    )
    readiness_checks = [
        {
            "requirement_id": "proposal_family_diversity",
            "status": "passed" if len(proposal_family_rates) >= 3 else "blocked",
            "minimum": {"distinct_strategy_proposal_families": 3},
            "observed": {"distinct_strategy_proposal_families": len(proposal_family_rates)},
        },
        {
            "requirement_id": "conversion_positive_provider_diversity",
            "status": "passed" if len(positive_families) >= 3 else "blocked",
            "minimum": {"distinct_conversion_positive_provider_families": 3},
            "observed": {
                "distinct_conversion_positive_provider_families": len(positive_families),
                "families": positive_families,
            },
        },
        {
            "requirement_id": "label_balance",
            "status": (
                "passed"
                if summary.get("training_positive_provider_label_count", 0) >= 6
                and summary.get("training_negative_provider_label_count", 0) >= 6
                else "blocked"
            ),
            "minimum": {"positive": 6, "negative": 6},
            "observed": {
                "positive": summary.get("training_positive_provider_label_count"),
                "negative": summary.get("training_negative_provider_label_count"),
            },
        },
        {
            "requirement_id": "protected_stage_coverage",
            "status": (
                "passed"
                if all((summary.get("row_count_by_stage") or {}).get(stage, 0) > 0 for stage in ("stage4", "stage5", "stage6"))
                else "blocked"
            ),
            "minimum": {"stages": ["stage4", "stage5", "stage6"]},
            "observed": {"row_count_by_stage": summary.get("row_count_by_stage")},
        },
        {
            "requirement_id": "stage7_heldout_boundary",
            "status": "passed" if summary.get("stage7_training_rows") == 0 else "blocked",
            "minimum": {"stage7_training_rows": 0},
            "observed": {"stage7_training_rows": summary.get("stage7_training_rows")},
        },
        {
            "requirement_id": "current_selected_provider_diversity",
            "status": "diagnostic_only_not_sandbox_blocker",
            "minimum": {"promotion_requires_no_stage0_dominance_regression": True},
            "observed": {"v2_blockers": readiness.get("blockers")},
        },
    ]
    hard_blockers = [
        check["requirement_id"]
        for check in readiness_checks
        if check["status"] == "blocked"
    ]
    plan = {
        "schema_version": "krk_selector_readiness_v3_plan.v0",
        "causal_status": "non_causal_design_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(ARCH_REVIEW), str(CONTRAST_DATASET), str(CONTRAST_PROBE)],
        "reason": (
            "Selected-provider diversity from the current raw arbiter is stage0-dominant; "
            "requiring it as a pre-sandbox hard gate blocks the mechanism meant to correct that dominance."
        ),
        "readiness_checks_v3": readiness_checks,
        "sandbox_design_requirements": [
            "default_off",
            "default_off_equivalence_before_enabled_tests",
            "visible_source_terms_and_provider_metadata",
            "no_runtime_dtm_or_tablebase",
            "no_gameplay_topology_mutation",
            "stage7_held_out_challenge_only",
            "guardrail_validation_before_promotion",
        ],
        "promotion_still_requires": [
            "target_improvement",
            "protected_stage4_5_6_guardrails_hold",
            "selected_provider_dominance_not_regressed",
            "M1_M4_preserved",
            "no_hidden_controller",
        ],
        "decision": {
            "status": (
                "selector_readiness_v3_sandbox_design_review_allowed"
                if not hard_blockers
                else "selector_readiness_v3_evidence_incomplete"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "hard_blockers": hard_blockers,
            "recommended_next_step": (
                "design_default_off_strategy_arbiter_sandbox_for_review"
                if not hard_blockers
                else "fill_selector_readiness_v3_evidence_gaps"
            ),
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox_without_design_review",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("causal_status") != "non_causal_design_plan":
        raise ValueError("plan must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if plan.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if (plan.get("decision") or {}).get("runtime_arbiter_allowed") is not False:
        raise ValueError("runtime arbiter must remain blocked")


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# KRK Selector Readiness v3 Plan",
        "",
        "This design-only plan reframes selector-readiness criteria after selected-provider "
        "sampling showed the current raw arbiter is stage0-dominant. It does not implement a sandbox.",
        "",
        "## Reason",
        "",
        plan["reason"],
        "",
        "## Readiness Checks",
        "",
    ]
    for check in plan["readiness_checks_v3"]:
        lines.append(
            f"- `{check['requirement_id']}` status=`{check['status']}` "
            f"observed=`{check['observed']}`"
        )
    lines.extend(
        [
            "",
            "## Sandbox Design Requirements",
            "",
        ]
    )
    for requirement in plan["sandbox_design_requirements"]:
        lines.append(f"- `{requirement}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{plan['decision']['status']}`",
            f"- Hard blockers: `{plan['decision']['hard_blockers']}`",
            f"- Recommended next step: `{plan['decision']['recommended_next_step']}`",
            "- Runtime arbiter and selector sandbox remain blocked until explicit design review.",
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
