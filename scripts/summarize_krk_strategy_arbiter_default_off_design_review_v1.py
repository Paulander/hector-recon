#!/usr/bin/env python3
"""Summarize the default-off KRK strategy arbiter design review after readiness v3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS_V3 = Path("reports/krk_selector_readiness_v3_plan.json")
CONTRAST_PROBE = Path("reports/krk_strategy_owner_contrast_probe_v0.json")
SELECTED_PROVIDER_REVIEW = Path("reports/krk_selected_provider_diversity_architecture_review_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_default_off_design_review_v1.json")
OUT_MD = Path("reports/krk_strategy_arbiter_default_off_design_review_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    readiness = _load_json(READINESS_V3)
    contrast = _load_json(CONTRAST_PROBE)
    selected_review = _load_json(SELECTED_PROVIDER_REVIEW)
    if readiness.get("causal_status") != "non_causal_design_plan":
        raise ValueError("selector readiness v3 must remain non-causal")
    if contrast.get("causal_status") != "non_causal_probe":
        raise ValueError("contrast probe must remain non-causal")
    if selected_review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("selected-provider review must remain non-causal")
    if (readiness.get("decision") or {}).get("runtime_arbiter_allowed") is not False:
        raise ValueError("runtime arbiter is still blocked")

    readiness_checks = readiness.get("readiness_checks_v3") or []
    passed_checks = [
        check["requirement_id"]
        for check in readiness_checks
        if check.get("status") == "passed"
    ]
    diagnostic_checks = [
        check["requirement_id"]
        for check in readiness_checks
        if check.get("status") == "diagnostic_only_not_sandbox_blocker"
    ]
    hard_blockers = list((readiness.get("decision") or {}).get("hard_blockers") or [])

    review = {
        "schema_version": "krk_strategy_arbiter_default_off_design_review.v1",
        "causal_status": "non_causal_design_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "selector_sandbox_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(READINESS_V3), str(CONTRAST_PROBE), str(SELECTED_PROVIDER_REVIEW)],
        "readiness_v3_summary": {
            "passed_checks": passed_checks,
            "diagnostic_only_checks": diagnostic_checks,
            "hard_blockers": hard_blockers,
            "reason": readiness.get("reason"),
        },
        "design_review_scope": {
            "allowed": [
                "define future default-off sandbox interface",
                "define trace metadata contract",
                "define default-off equivalence requirements",
                "define guardrail validation gates",
            ],
            "not_allowed": [
                "implement runtime arbiter",
                "enable selector sandbox",
                "change provider scores",
                "route providers",
                "promote Stage 7",
                "train Stage 8",
            ],
        },
        "future_sandbox_contract": {
            "sandbox_id": "sandbox.krk.strategy_arbiter_v1",
            "default_enabled": False,
            "activation_scope": [
                "KRK domain only",
                "explicit sandbox profile only",
                "handoff_composition_v1 or explicit successor profile",
                "Stage7 challenge rows held out from training/tuning",
            ],
            "allowed_inputs": [
                "StrategyProposalFrame records",
                "provider provenance and maturity metadata",
                "visible terminal-space context terms",
                "InternalTerminalSpec-derived non-causal monitor evidence only if promoted to visible runtime evidence in a future review",
                "plan-capsule observation metadata only as trace evidence",
            ],
            "forbidden_inputs": [
                "runtime DTM/tablebase lookup",
                "state hash exceptions",
                "hidden Python controller state",
                "unpromoted StructuralCandidate as causal input",
                "unpromoted InternalTerminalSpec as causal input",
                "unpromoted PlanCapsuleSpec as causal input",
            ],
            "future_outputs_if_approved": [
                "visible strategy-arbitration recommendation",
                "explicit provider eligibility/support evidence",
                "trace-only explanation before any score influence",
            ],
            "forbidden_outputs": [
                "direct move selection",
                "direct role-SCRIPT to provider request",
                "untraced provider score mutation",
                "gameplay topology mutation",
                "Stage7 promotion trigger",
                "Stage8 training trigger",
            ],
        },
        "required_default_off_tests_before_any_runtime_code": [
            "baseline vs flag-present-default-off selected first move equivalence",
            "selected provider equivalence",
            "local one-ply result equivalence",
            "conversion result equivalence on protected smoke",
            "shadow candidate equivalence where available",
            "no no-move/illegal/draw regression",
            "no observation metadata emitted when disabled",
        ],
        "minimum_enabled_sandbox_smoke_if_later_approved": [
            "trace metadata explains every recommendation",
            "direct_request=false unless explicitly promoted topology provides a visible edge",
            "score_delta is bounded and visible if scoring is ever enabled",
            "Stage7 remains held-out challenge evidence, not training data",
            "protected Stage4/5/6 smoke before any target validation",
        ],
        "promotion_gates_if_later_approved": [
            "target control-plane improvement",
            "protected Stage4/5/6/1 guardrails hold",
            "M1-M4 preservation holds",
            "selected-provider dominance does not regress",
            "no hidden controller",
            "no runtime DTM/tablebase",
            "no gameplay topology mutation",
        ],
        "open_risks": [
            {
                "risk": "selected_provider_stage0_dominance",
                "status": "diagnostic_only_pre_sandbox_promotion_risk",
                "detail": "Current selected-provider diversity remains poor; v3 treats this as the failure mode to test, not as a design-review blocker.",
            },
            {
                "risk": "stage7_overfit",
                "status": "must_hold_out",
                "detail": "Stage7 rows remain challenge cases and must not become training rows for a selector.",
            },
            {
                "risk": "forced_vs_selected_label_semantics",
                "status": "must_keep_separate",
                "detail": "Forced conversion labels can justify candidate ownership contrast, but they are not the same as selected-playout success labels.",
            },
        ],
        "decision": {
            "status": (
                "default_off_strategy_arbiter_design_ready_for_external_review"
                if not hard_blockers
                else "default_off_strategy_arbiter_design_blocked_by_readiness_gap"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "implementation_allowed": False,
            "recommended_next_step": (
                "external_architecture_review_before_runtime_sandbox"
                if not hard_blockers
                else "fill_selector_readiness_v3_evidence_gaps"
            ),
        },
        "blocked_next_steps": [
            "implement_runtime_arbiter",
            "enable_selector_sandbox",
            "add_stage7_repair",
            "promote_stage7",
            "train_stage8",
            "use_runtime_dtm_or_tablebase",
            "mutate_topology_during_gameplay",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    if review.get("causal_status") != "non_causal_design_review":
        raise ValueError("design review must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "selector_sandbox_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")
    decision = review.get("decision") or {}
    if decision.get("runtime_arbiter_allowed") is not False:
        raise ValueError("runtime arbiter must remain blocked")
    if decision.get("implementation_allowed") is not False:
        raise ValueError("implementation must remain blocked")


def render_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy Arbiter Default-Off Design Review v1",
        "",
        "This is a design-review artifact only. It does not implement a runtime arbiter or selector sandbox.",
        "",
        "## Readiness v3 Summary",
        "",
        f"- Passed checks: `{review['readiness_v3_summary']['passed_checks']}`",
        f"- Diagnostic-only checks: `{review['readiness_v3_summary']['diagnostic_only_checks']}`",
        f"- Hard blockers: `{review['readiness_v3_summary']['hard_blockers']}`",
        "",
        "## Future Sandbox Contract",
        "",
        f"- Sandbox id: `{review['future_sandbox_contract']['sandbox_id']}`",
        f"- Default enabled: `{review['future_sandbox_contract']['default_enabled']}`",
        "",
        "Allowed inputs:",
    ]
    for item in review["future_sandbox_contract"]["allowed_inputs"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "Forbidden inputs:"])
    for item in review["future_sandbox_contract"]["forbidden_inputs"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "Required default-off tests before runtime code:"])
    for item in review["required_default_off_tests_before_any_runtime_code"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Open Risks", ""])
    for risk in review["open_risks"]:
        lines.append(f"- `{risk['risk']}` status=`{risk['status']}`: {risk['detail']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{review['decision']['status']}`",
            f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
            "- Runtime arbiter implementation remains blocked.",
            "- Selector sandbox implementation remains blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
