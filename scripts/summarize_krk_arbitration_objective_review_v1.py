#!/usr/bin/env python3
"""Review KRK strategy-arbitration objectives after runtime-test slices.

The runtime-test evidence shows the default-off support sandbox is observable and
safe at small scale, but additive support is not a good objective to scale. This
script packages the non-causal objective evidence and recommends the next design
class before further runtime tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_REVIEW = Path("reports/krk_strategy_arbiter_runtime_test_review_v2.json")
SELECTOR_OBJECTIVE = Path("reports/krk_selector_objective_architecture_review_v1.json")
BALANCED_REVIEW = Path("reports/krk_selector_balanced_architecture_review_v1.json")
OWNER_CONTRAST = Path("reports/krk_strategy_owner_contrast_probe_v0.json")
READINESS_V3 = Path("reports/krk_selector_readiness_v3_plan.json")
OUT_JSON = Path("reports/krk_arbitration_objective_review_v1.json")
OUT_MD = Path("reports/krk_arbitration_objective_review_v1.md")


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


def _metric(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def build_review() -> dict[str, Any]:
    runtime = _load_json(RUNTIME_REVIEW)
    selector = _load_json(SELECTOR_OBJECTIVE)
    balanced = _load_json(BALANCED_REVIEW)
    contrast = _load_json(OWNER_CONTRAST)
    readiness = _load_json(READINESS_V3)

    if runtime.get("decision", {}).get("status") != "runtime_sandbox_safe_but_additive_support_not_ready_to_scale":
        raise ValueError("runtime review must block additive support scale-up")
    for payload, source in (
        (runtime, RUNTIME_REVIEW),
        (selector, SELECTOR_OBJECTIVE),
        (balanced, BALANCED_REVIEW),
        (contrast, OWNER_CONTRAST),
        (readiness, READINESS_V3),
    ):
        if payload.get("runtime_defaults_changed") is True:
            raise ValueError(f"{source}: runtime defaults must not be changed")

    contrast_metrics = contrast.get("metrics") or {}
    training_rates = contrast_metrics.get("training_provider_family_rates") or {}
    heldout_rates = contrast_metrics.get("heldout_provider_family_rates") or {}
    positive_families = sorted(
        family for family, stats in training_rates.items() if (stats or {}).get("positive", 0) > 0
    )

    review = {
        "schema_version": "krk_arbitration_objective_review.v1",
        "causal_status": "non_causal_objective_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(RUNTIME_REVIEW),
            str(SELECTOR_OBJECTIVE),
            str(BALANCED_REVIEW),
            str(OWNER_CONTRAST),
            str(READINESS_V3),
        ],
        "evidence_statuses": {
            "runtime_test_review": _decision_status(runtime),
            "selector_objective_review": _decision_status(selector),
            "balanced_selector_review": _decision_status(balanced),
            "strategy_owner_contrast": _decision_status(contrast),
            "selector_readiness_v3": _decision_status(readiness),
        },
        "objective_assessment": {
            "broad_additive_support": {
                "status": "reject_as_next_runtime_objective",
                "reason": (
                    "Low support is observable but not effective for Stage7; high support can "
                    "perturb protected one-ply ownership before safe Stage7 evidence exists."
                ),
            },
            "raw_provider_id_prior": {
                "status": "non_causal_evidence_only",
                "reason": (
                    "Provider-prior signal can encode maturity/provenance and dataset bias; it "
                    "does not prove guardrail-safe runtime ownership."
                ),
            },
            "provider_provenance_maturity": {
                "status": "promising_non_causal_feature_family",
                "reason": "Provenance/maturity reproduced the provider-prior signal in prior probes.",
            },
            "selected_playout_labels": {
                "status": "insufficient_alone",
                "reason": "Current raw selected-provider observations are stage0-dominant.",
            },
            "forced_and_contrast_labels": {
                "status": "useful_for_training_contrast_not_direct_runtime_policy",
                "reason": "Conversion-positive provider diversity exists in protected contrast labels.",
            },
            "stage7_heldout_rows": {
                "status": "challenge_only",
                "reason": "Stage7 remains unresolved and must not become training evidence for a selector.",
            },
        },
        "key_metrics": {
            "balanced_best_accuracy": _metric(balanced, "evidence", "best_baseline_accuracy")
            or _metric(balanced, "metrics", "best_baseline_accuracy"),
            "contrast_training_positive_label_count": contrast_metrics.get("training_positive_label_count"),
            "contrast_training_negative_label_count": contrast_metrics.get("training_negative_label_count"),
            "contrast_positive_provider_families": positive_families,
            "contrast_heldout_provider_family_rates": heldout_rates,
            "readiness_v3_hard_blockers": _metric(readiness, "decision", "hard_blockers"),
        },
        "next_objective_contract": {
            "name": "normalized_contrastive_strategy_selector_objective",
            "causal_status": "non_causal_design_only",
            "must_use": [
                "StrategyProposalFrame-compatible proposal rows",
                "provider family/provenance/maturity metadata",
                "provider-local rank or normalized within-provider score",
                "separate selected-playout, forced-provider, and same-move compatibility labels",
                "protected Stage4/5/6 controls",
                "Stage7 residuals as held-out challenge cases only",
            ],
            "must_not_use": [
                "raw global additive score scale as sole arbitration mechanism",
                "runtime DTM/tablebase",
                "state-hash exceptions",
                "hidden provider routing",
                "unpromoted InternalTerminalSpec/StructuralCandidate/PlanCapsuleSpec as causal inputs",
            ],
        },
        "decision": {
            "status": "additive_support_objective_rejected_design_normalized_selector_objective",
            "recommended_next_step": "design_non_causal_normalized_strategy_selector_objective_v1",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "blocked_next_steps": [
            "higher_additive_support_playout",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "causal_internal_terminal",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")
    decision = review.get("decision") or {}
    if decision.get("runtime_test_allowed_next") is not False:
        raise ValueError("more runtime tests must remain blocked by this review")


def render_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# KRK Arbitration Objective Review v1",
        "",
        "This non-causal review decides what arbitration objective should replace broad additive support before any further runtime tests.",
        "",
        "## Evidence Statuses",
        "",
    ]
    for key, value in review["evidence_statuses"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Objective Assessment", ""])
    for name, item in review["objective_assessment"].items():
        lines.append(f"### `{name}`")
        lines.append("")
        lines.append(f"- Status: `{item['status']}`")
        lines.append(f"- Reason: {item['reason']}")
        lines.append("")
    lines.extend(["## Key Metrics", ""])
    for key, value in review["key_metrics"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Next Objective Contract", ""])
    lines.append(f"- Name: `{review['next_objective_contract']['name']}`")
    lines.append(f"- Causal status: `{review['next_objective_contract']['causal_status']}`")
    lines.append("")
    lines.append("Must use:")
    for item in review["next_objective_contract"]["must_use"]:
        lines.append(f"- `{item}`")
    lines.append("")
    lines.append("Must not use:")
    for item in review["next_objective_contract"]["must_not_use"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{review['decision']['status']}`",
            f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{review['decision']['runtime_test_allowed_next']}`",
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
