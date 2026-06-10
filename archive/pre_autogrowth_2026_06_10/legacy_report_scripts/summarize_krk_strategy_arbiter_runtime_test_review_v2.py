#!/usr/bin/env python3
"""Summarize KRK strategy-arbiter runtime-test evidence.

This review is intentionally non-causal. It packages the default-off sandbox
smoke, protected controls, Stage 7 holdout/challenge checks, and support-scale
sensitivity into a single decision artifact.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SMOKE = Path("reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.json")
PROTECTED_V2 = Path("reports/krk_strategy_arbiter_protected_control_matrix_v2.json")
HOLDOUT = Path("reports/krk_strategy_arbiter_stage7_holdout_lock_v1.json")
STAGE7_CHALLENGE = Path("reports/krk_strategy_arbiter_stage7_challenge_probe_v1.json")
SENSITIVITY = Path("reports/krk_strategy_arbiter_support_sensitivity_v1.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_runtime_test_review_v2.json")
OUT_MD = Path("reports/krk_strategy_arbiter_runtime_test_review_v2.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _decision_status(payload: dict[str, Any]) -> str | None:
    decision = payload.get("decision")
    if isinstance(decision, dict):
        status = decision.get("status")
        return status if isinstance(status, str) else None
    return None


def _require_runtime_invariants(payload: dict[str, Any], source: Path) -> None:
    for key in (
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{source}: {key} must be false")


def build_review() -> dict[str, Any]:
    smoke = _load_json(SMOKE)
    protected = _load_json(PROTECTED_V2)
    holdout = _load_json(HOLDOUT)
    challenge = _load_json(STAGE7_CHALLENGE)
    sensitivity = _load_json(SENSITIVITY)

    for source, payload in (
        (SMOKE, smoke),
        (PROTECTED_V2, protected),
        (HOLDOUT, holdout),
        (STAGE7_CHALLENGE, challenge),
        (SENSITIVITY, sensitivity),
    ):
        _require_runtime_invariants(payload, source)

    smoke_decision = smoke.get("decision") or {}
    protected_summary = protected.get("summary") or {}
    holdout_equivalence = holdout.get("equivalence") or {}
    challenge_summary = challenge.get("summary") or {}
    sensitivity_summary = sensitivity.get("summary") or {}

    default_off_passed = bool(smoke_decision.get("default_off_equivalence_passed")) and bool(
        protected_summary.get("default_off_equivalence_passed")
    )
    stage7_holdout_locked = bool(holdout_equivalence.get("enabled_blocked_matches_baseline")) and bool(
        holdout_equivalence.get("support_blocked")
    )
    protected_small_scale_safe = bool(
        protected_summary.get("enabled_has_no_conversion_regression")
    ) and bool(protected_summary.get("enabled_has_no_no_move_or_draw_spike"))
    stage7_small_support_effective = (
        (challenge_summary.get("conversion_delta") or 0) > 0
        or (challenge_summary.get("selected_supported_count") or 0) > 0
    )
    high_support_risk = (
        sensitivity_summary.get("support_scale_risk")
        == "high_support_changes_protected_ownership_before_safe_stage7_evidence"
    )

    decision_status = (
        "runtime_sandbox_safe_but_additive_support_not_ready_to_scale"
        if default_off_passed
        and stage7_holdout_locked
        and protected_small_scale_safe
        and not stage7_small_support_effective
        and high_support_risk
        else "runtime_test_evidence_mixed_review_required"
    )

    review = {
        "schema_version": "krk_strategy_arbiter_runtime_test_review.v2",
        "causal_status": "runtime_test_review_non_promoting",
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(SMOKE),
            str(PROTECTED_V2),
            str(HOLDOUT),
            str(STAGE7_CHALLENGE),
            str(SENSITIVITY),
        ],
        "evidence_statuses": {
            "smoke": _decision_status(smoke),
            "protected_control_matrix_v2": _decision_status(protected),
            "stage7_holdout_lock": _decision_status(holdout),
            "stage7_challenge_probe": _decision_status(challenge),
            "support_sensitivity": _decision_status(sensitivity),
        },
        "findings": {
            "default_off_equivalence_passed": default_off_passed,
            "stage7_holdout_locked_by_default": stage7_holdout_locked,
            "small_support_trace_visible": bool(protected_summary.get("enabled_support_total")),
            "small_support_protected_no_regression": protected_small_scale_safe,
            "small_support_stage7_effective": stage7_small_support_effective,
            "stage7_challenge_conversion_delta": challenge_summary.get("conversion_delta"),
            "stage7_challenge_selected_supported_count": challenge_summary.get(
                "selected_supported_count"
            ),
            "low_support_cap": sensitivity_summary.get("low_support_cap"),
            "stage7_changes_under_low_support_cap": sensitivity_summary.get(
                "stage7_changes_under_low_support_cap"
            ),
            "protected_labels_with_high_support_change": sensitivity_summary.get(
                "protected_labels_with_provider_change"
            ),
            "high_support_scale_risk": high_support_risk,
        },
        "interpretation": {
            "validated": [
                "default-off runtime-test contract",
                "trace-visible bounded support metadata",
                "Stage7 challenge holdout lock",
                "small protected-control no-regression behavior",
            ],
            "not_validated": [
                "Stage7 effectiveness",
                "promotion",
                "higher additive support scale",
                "runtime strategy arbiter as a solved ownership mechanism",
            ],
            "blocked_path": "raise_additive_support_bonus",
            "reason": (
                "Low support is trace-visible but not effective for Stage7 ownership; "
                "high support can perturb protected one-ply ownership before there is "
                "safe Stage7 conversion evidence."
            ),
        },
        "decision": {
            "status": decision_status,
            "recommended_next_step": "non_causal_arbitration_objective_review_before_more_runtime_tests",
            "runtime_promotion_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "blocked_next_steps": [
            "increase_broad_additive_support",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    for key in (
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")
    decision = review.get("decision") or {}
    if decision.get("runtime_promotion_allowed") is not False:
        raise ValueError("runtime promotion must remain blocked")


def render_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy Arbiter Runtime-Test Review v2",
        "",
        "This review summarizes the approved default-off runtime-test slices. It does not promote or enable runtime behavior by default.",
        "",
        "## Evidence Statuses",
        "",
    ]
    for key, value in review["evidence_statuses"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Findings", ""])
    for key, value in review["findings"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    lines.append("Validated:")
    for item in review["interpretation"]["validated"]:
        lines.append(f"- `{item}`")
    lines.append("")
    lines.append("Not validated:")
    for item in review["interpretation"]["not_validated"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            f"Blocked path: `{review['interpretation']['blocked_path']}`",
            "",
            f"Reason: {review['interpretation']['reason']}",
            "",
            "## Decision",
            "",
            f"- Status: `{review['decision']['status']}`",
            f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
            f"- Runtime promotion allowed: `{review['decision']['runtime_promotion_allowed']}`",
            f"- Stage 7 promotion allowed: `{review['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{review['decision']['stage8_training_allowed']}`",
            "",
            "## Blocked Next Steps",
            "",
        ]
    )
    for item in review["blocked_next_steps"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
