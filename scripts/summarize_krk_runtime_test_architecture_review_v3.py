#!/usr/bin/env python3
"""Architecture review after bounded runtime-test selector evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS = Path("reports/krk_state_local_contrast_readiness_review_v2.json")
LABELS = Path("reports/krk_state_local_contrast_labels_v2.json")
OUT_JSON = Path("reports/krk_runtime_test_architecture_review_v3.json")
OUT_MD = Path("reports/krk_runtime_test_architecture_review_v3.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    readiness = _load_json(READINESS)
    labels = _load_json(LABELS)
    if readiness.get("causal_status") != "non_causal_readiness_review":
        raise ValueError("readiness review must remain non-causal")
    if labels.get("causal_status") != "non_causal_state_local_contrast_dataset":
        raise ValueError("label dataset must remain non-causal")

    review = {
        "schema_version": "krk_runtime_test_architecture_review.v3",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(READINESS), str(LABELS)],
        "accepted_findings": [
            "Default-off observability and reporting infrastructure is useful and safe.",
            "Broad additive support is not a viable scaling mechanism.",
            "Normalized/provenance selector objectives are not runtime-ready.",
            "Diverse contrast labels confirm Stage7 residual providers remain max_plies under forced ownership.",
            "Protected non-Stage7 training evidence is still too sparse and positive-heavy.",
            "The best current contrast selector has negative_suppression=0.0.",
        ],
        "runtime_readiness": {
            "runtime_selector_ready": False,
            "runtime_internal_terminal_ready": False,
            "runtime_stage7_repair_ready": False,
            "reason": "No candidate can suppress known negative ownership examples in leave-state-out evaluation.",
        },
        "next_options": [
            {
                "option_id": "A",
                "name": "targeted_negative_control_evidence",
                "description": "Collect or reconstruct protected Stage4/5/6 negative ownership labels with the same semantics as positives.",
                "pros": ["Directly addresses negative_suppression=0.0", "Keeps Stage7 held out"],
                "cons": ["May require slow h40 traces unless a cheaper targeted runner is designed"],
                "causal_status": "non_causal_only",
            },
            {
                "option_id": "B",
                "name": "selector_objective_redesign",
                "description": "Redesign the selector target around abstention/risk detection before ownership selection.",
                "pros": ["Matches observed failure mode: inability to reject bad owners", "Could use existing negative evidence"],
                "cons": ["Still needs validation before runtime use"],
                "causal_status": "design_only",
            },
            {
                "option_id": "C",
                "name": "pause_runtime_selector_track",
                "description": "Stop selector work and return to broader curriculum integration / provider-capacity planning.",
                "pros": ["Avoids overfitting a small lab dataset", "Keeps architecture clean"],
                "cons": ["Does not move causal runtime behavior forward immediately"],
                "causal_status": "review_decision",
            },
        ],
        "recommended_next_class": {
            "status": "design_abstention_first_selector_objective",
            "rationale": (
                "The blocker is not selecting positives; it is failing to suppress negatives. "
                "Before collecting more expensive labels or implementing runtime behavior, define a selector objective "
                "that can abstain/reject unsafe ownership using non-causal protected controls."
            ),
            "next_artifacts": [
                "reports/krk_abstention_first_selector_objective_v0.json",
                "reports/krk_abstention_first_selector_objective_v0.md",
            ],
            "implementation_allowed": "design_only",
        },
        "blocked_next_steps": [
            "runtime_selector",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "m3_m4_arbitration_update",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# KRK Runtime-Test Architecture Review v3",
        "",
        "This review decides what to do after the bounded runtime-test selector evidence. It is non-causal and does not authorize a runtime selector.",
        "",
        "## Accepted Findings",
        "",
    ]
    for item in review["accepted_findings"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Runtime Readiness",
            "",
            f"- Runtime selector ready: `{review['runtime_readiness']['runtime_selector_ready']}`",
            f"- Runtime internal terminal ready: `{review['runtime_readiness']['runtime_internal_terminal_ready']}`",
            f"- Runtime Stage 7 repair ready: `{review['runtime_readiness']['runtime_stage7_repair_ready']}`",
            f"- Reason: {review['runtime_readiness']['reason']}",
            "",
            "## Next Options",
            "",
        ]
    )
    for option in review["next_options"]:
        lines.append(f"- `{option['option_id']}` {option['name']}: {option['description']}")
    lines.extend(
        [
            "",
            "## Recommended Next Class",
            "",
            f"- Status: `{review['recommended_next_class']['status']}`",
            f"- Rationale: {review['recommended_next_class']['rationale']}",
            f"- Implementation allowed: `{review['recommended_next_class']['implementation_allowed']}`",
            f"- Next artifacts: `{review['recommended_next_class']['next_artifacts']}`",
            "",
            "## Blocked Next Steps",
            "",
            f"`{review['blocked_next_steps']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["recommended_next_class"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
