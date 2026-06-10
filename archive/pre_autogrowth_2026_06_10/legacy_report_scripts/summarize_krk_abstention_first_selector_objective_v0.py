#!/usr/bin/env python3
"""Design an abstention-first KRK selector objective from current evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCH_REVIEW = Path("reports/krk_runtime_test_architecture_review_v3.json")
READINESS = Path("reports/krk_state_local_contrast_readiness_review_v2.json")
OUT_JSON = Path("reports/krk_abstention_first_selector_objective_v0.json")
OUT_MD = Path("reports/krk_abstention_first_selector_objective_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_objective() -> dict[str, Any]:
    arch = _load_json(ARCH_REVIEW)
    readiness = _load_json(READINESS)
    if arch.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("architecture review must remain non-causal")
    if readiness.get("causal_status") != "non_causal_readiness_review":
        raise ValueError("readiness review must remain non-causal")

    objective = {
        "schema_version": "krk_abstention_first_selector_objective.v0",
        "causal_status": "non_causal_design",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(ARCH_REVIEW), str(READINESS)],
        "problem_statement": (
            "Current selector probes can recover many converting providers but fail to reject negative ownership examples. "
            "The next selector objective should first decide whether any proposed owner is safe enough to select; only then should it rank owners."
        ),
        "objective_components": [
            {
                "component_id": "ownership_abstention_gate",
                "target": "reject unsafe or unsupported provider ownership",
                "positive_labels": [
                    "forced_provider_conversion=mate",
                    "selected_playout_success=mate",
                    "guardrail_safe_ownership=true",
                ],
                "negative_labels": [
                    "forced_provider_conversion=max_plies",
                    "selected_playout_success=max_plies",
                    "stagnation_or_loop_after_ownership=true",
                    "guardrail_safe_ownership=false",
                ],
                "required_metric": "negative_suppression",
                "minimum_before_runtime_review": 0.7,
            },
            {
                "component_id": "owner_ranking_after_pass",
                "target": "rank only proposals that pass the abstention gate",
                "positive_labels": ["shorter mate", "successful handoff", "lower stagnation"],
                "negative_labels": ["long max_plies", "no handoff", "post-plan stagnation"],
                "required_metric": "positive_precision",
                "minimum_before_runtime_review": 0.75,
            },
            {
                "component_id": "challenge_set_generalization",
                "target": "do not train on Stage7 residuals; use them as held-out rejection/challenge examples",
                "positive_labels": [],
                "negative_labels": ["stage7_forced_provider_max_plies"],
                "required_metric": "heldout_negative_suppression",
                "minimum_before_runtime_review": 0.7,
            },
        ],
        "feature_policy": {
            "allowed_non_causal_features": [
                "provider_family",
                "provider_maturity",
                "provider_source_stage",
                "provider_local_rank",
                "normalized_score_bucket",
                "active_landmark_label",
                "terminal_space_context",
                "internal_monitor_labels_as_metadata",
            ],
            "blocked_features": [
                "runtime DTM/tablebase",
                "state hash exceptions",
                "exact-move exceptions",
                "Stage7 training labels",
                "hidden Python routing",
            ],
        },
        "data_requirements_before_runtime_review": {
            "minimum_training_rows": 40,
            "minimum_negative_training_rows": 12,
            "minimum_training_states": 12,
            "required_stages": ["stage4", "stage5", "stage6"],
            "stage7_training_rows": 0,
            "heldout_stage7_rows_minimum": 8,
            "required_splits": ["leave_state_out", "leave_stage_out_if_data_allows"],
        },
        "evaluation_protocol": [
            "Train/evaluate the abstention gate on protected Stage4/5/6 only.",
            "Measure negative_suppression before positive owner ranking.",
            "If abstention fails, no runtime selector review is allowed.",
            "If abstention passes, evaluate owner ranking on pass-filtered proposals.",
            "Evaluate Stage7 residuals only as held-out challenge rows.",
        ],
        "decision": {
            "status": "abstention_first_selector_objective_defined",
            "recommended_next_step": "collect_or_reconstruct_protected_negative_controls_for_abstention_gate",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
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
    validate_objective(objective)
    return objective


def validate_objective(objective: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if objective.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if objective.get("causal_status") != "non_causal_design":
        raise ValueError("objective must remain design-only")


def render_markdown(objective: dict[str, Any]) -> str:
    lines = [
        "# KRK Abstention-First Selector Objective v0",
        "",
        "This design responds to the selector failure mode: current probes select positives too easily and do not suppress negative ownership examples. It is non-causal and does not implement a runtime selector.",
        "",
        "## Problem Statement",
        "",
        objective["problem_statement"],
        "",
        "## Objective Components",
        "",
    ]
    for component in objective["objective_components"]:
        lines.append(
            f"- `{component['component_id']}` target=`{component['target']}` "
            f"metric=`{component['required_metric']}` minimum=`{component['minimum_before_runtime_review']}`"
        )
    lines.extend(["", "## Data Requirements Before Runtime Review", ""])
    for key, value in objective["data_requirements_before_runtime_review"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Evaluation Protocol", ""])
    for item in objective["evaluation_protocol"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{objective['decision']['status']}`",
            f"- Recommended next step: `{objective['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{objective['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{objective['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{objective['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    objective = build_objective()
    (ROOT / OUT_JSON).write_text(json.dumps(objective, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(objective), encoding="utf-8")
    print(json.dumps(objective["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
