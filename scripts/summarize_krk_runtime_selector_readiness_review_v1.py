#!/usr/bin/env python3
"""Close the current KRK runtime-selector readiness branch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_REVIEW = Path("reports/krk_strategy_arbiter_runtime_test_review_v2.json")
OBJECTIVE_REVIEW = Path("reports/krk_arbitration_objective_review_v1.json")
NORMALIZED_PROBE = Path("reports/krk_normalized_strategy_selector_objective_probe_v1.json")
RANKED_PROBE = Path("reports/krk_ranked_strategy_proposal_frame_probe_v1.json")
CONTRAST_PROBE = Path("reports/krk_state_local_contrast_selector_probe_v1.json")
OUT_JSON = Path("reports/krk_runtime_selector_readiness_review_v1.json")
OUT_MD = Path("reports/krk_runtime_selector_readiness_review_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _status(payload: dict[str, Any]) -> str | None:
    decision = payload.get("decision")
    if isinstance(decision, dict):
        value = decision.get("status")
        return value if isinstance(value, str) else None
    return None


def build_review() -> dict[str, Any]:
    runtime = _load_json(RUNTIME_REVIEW)
    objective = _load_json(OBJECTIVE_REVIEW)
    normalized = _load_json(NORMALIZED_PROBE)
    ranked = _load_json(RANKED_PROBE)
    contrast = _load_json(CONTRAST_PROBE)

    artifacts = [runtime, objective, normalized, ranked, contrast]
    for payload in artifacts:
        for key in (
            "runtime_defaults_changed",
            "runtime_dtm_or_tablebase_lookup",
            "gameplay_topology_mutation",
            "stage7_promotion_allowed",
            "stage8_training_allowed",
        ):
            if payload.get(key) is not False:
                raise ValueError(f"{key} must be false in source artifact")

    review = {
        "schema_version": "krk_runtime_selector_readiness_review.v1",
        "causal_status": "non_causal_readiness_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_ready": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(RUNTIME_REVIEW),
            str(OBJECTIVE_REVIEW),
            str(NORMALIZED_PROBE),
            str(RANKED_PROBE),
            str(CONTRAST_PROBE),
        ],
        "evidence_statuses": {
            "runtime_test_review": _status(runtime),
            "objective_review": _status(objective),
            "normalized_objective_probe": _status(normalized),
            "ranked_frame_probe": _status(ranked),
            "state_local_contrast_probe": _status(contrast),
        },
        "positive_results": [
            "default-off sandbox mechanics are trace-visible and default-safe",
            "small protected-control runtime tests showed no conversion/no-move/draw regression",
            "Stage7 challenge contexts are blocked by default",
            "normalized rank/score proxy improved over provenance baseline in offline labels",
            "ranked StrategyProposalFrame rows can be exported replay-free",
        ],
        "blocking_results": [
            "broad additive support is not effective at low support and unsafe to scale blindly",
            "ranked-frame labels are frame-level and too coarse for owner selection",
            "state-local contrast labels are sparse and do not suppress negative forced providers under leave-state-out",
            "Stage7 remains held out and unresolved",
        ],
        "readiness_assessment": {
            "runtime_selector": "blocked",
            "more_additive_support_runtime_tests": "blocked",
            "normalized_selector_objective": "promising_but_needs_better_state_local_labels",
            "stage7_status": "local_valid_composition_quarantined",
            "stage8_training": "blocked",
        },
        "minimum_next_evidence": [
            "more diverse state-local contrast labels across protected Stage4/5/6 states",
            "negative labels that are not dominated by one repeated provider family/state",
            "proposal-level ownership labels, not only frame-level outcome labels",
            "held-out Stage7 challenge evaluation after protected evidence improves",
        ],
        "decision": {
            "status": "runtime_selector_not_ready_collect_better_contrast_labels",
            "recommended_next_step": "design_small_diverse_state_local_contrast_label_plan",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "blocked_next_steps": [
            "runtime_selector",
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
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_ready",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if review.get("decision", {}).get("runtime_test_allowed_next") is not False:
        raise ValueError("runtime tests remain blocked")


def render_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# KRK Runtime Selector Readiness Review v1",
        "",
        "This review closes the current runtime-selector evidence branch. It does not authorize runtime selector behavior.",
        "",
        "## Evidence Statuses",
        "",
    ]
    for key, value in review["evidence_statuses"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Positive Results", ""])
    for item in review["positive_results"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocking Results", ""])
    for item in review["blocking_results"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Readiness Assessment", ""])
    for key, value in review["readiness_assessment"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Minimum Next Evidence", ""])
    for item in review["minimum_next_evidence"]:
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
