#!/usr/bin/env python3
"""Record the Stage 7 curriculum-boundary architecture decision."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = Path("reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_curriculum_boundary_decision_v0.md")


SOURCE_ARTIFACTS = [
    "reports/structural_candidates/stage7_post_decision_closure.json",
    "reports/structural_candidates/stage7_training_objective_decision_gate.json",
    "reports/structural_candidates/stage7_selected_path_architecture_review_v0.json",
    "reports/structural_candidates/stage7_clean_control_architecture_review_v0.json",
    "reports/krk_strategy_sequence_architecture_review_v0.json",
    "reports/krk_strategy_sequence_inventory_v0.json",
]


def _load_optional(path: str) -> dict:
    full = ROOT / path
    if not full.exists():
        return {}
    payload = json.loads(full.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_decision() -> dict:
    clean_review = _load_optional(
        "reports/structural_candidates/stage7_clean_control_architecture_review_v0.json"
    )
    inventory = _load_optional("reports/krk_strategy_sequence_inventory_v0.json")
    clean_review_decision = clean_review.get("decision") or {}
    inventory_decision = inventory.get("decision") or {}
    sequence_inventory = inventory.get("sequence_policy_inventory") or {}
    clean_gate_closed = clean_review_decision.get("status") == (
        "stage7_clean_control_collection_closed_heldout_only"
    )
    clean_review_next_step = (
        clean_review_decision.get("recommended_next_step")
        or "continue_protected_failure_contrast_sequence_policy_gate_review"
    )
    return {
        "schema_version": "stage7_curriculum_boundary_decision.v0",
        "causal_status": "non_causal_architecture_decision",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": SOURCE_ARTIFACTS,
        "decision": {
            "status": "box_shrink_reclassified_as_local_evidence_handoff_trigger",
            "stage7_status": "local_valid_composition_quarantined",
            "stage7_standalone_repair_target": False,
            "box_shrink_promotable_independent_stage": False,
            "runtime_work_allowed": False,
            "recommended_next_step": (
                clean_review_next_step
                if clean_gate_closed
                else "use_stage7_as_heldout_challenge_for_broader_krk_strategy_sequence_work"
            ),
        },
        "motivation": [
            "Stage 7 box_shrink can be locally useful, but repeated local, arbitration, support, candidate-move, Plan Capsule, and training-objective work did not produce reliable conversion.",
            "Selected-path evidence split the residuals into strategy-ownership gaps and sequence/continuation gaps, which means the failure is not one local move-shape defect.",
            (
                "Clean-control evidence now meets the Stage 7 held-out sequence threshold; this closes the local clean-control collection branch without authorizing Stage 7 promotion or Stage 8 training."
                if clean_gate_closed
                else "Clean-control collection has not closed the Stage 7 held-out sequence threshold, so Stage 7 remains unsuitable as a promotion or training gate."
            ),
            "Continuing to crack Stage 7 as a standalone problem risks overfitting the lab to a noisy curriculum boundary; the active sequence-policy gap is protected plan-window failure-contrast evidence.",
            "The better abstraction is to treat box_shrink as local evidence that can help trigger owner exit, handoff, or broader KRK strategy/sequence selection.",
        ],
        "current_evidence_state": {
            "stage7_clean_review_status": clean_review_decision.get("status"),
            "stage7_clean_review_next_step": clean_review_decision.get("recommended_next_step"),
            "strategy_sequence_inventory_status": inventory_decision.get("status"),
            "strategy_sequence_inventory_next_step": inventory_decision.get(
                "recommended_next_step"
            ),
            "stage7_clean_success_controls_met": sequence_inventory.get(
                "success_controls_met"
            ),
            "stage7_clean_hard_negatives_met": sequence_inventory.get("hard_negatives_met"),
        },
        "new_role_for_stage7": {
            "box_shrink_role": "local_evidence_handoff_trigger_phase_boundary_signal",
            "stage7_residuals_role": "heldout_challenge_set",
            "allowed_uses": [
                "diagnostic evidence for strategy-ownership failures",
                "diagnostic evidence for sequence-policy failures",
                "held-out challenge cases for broader KRK strategy/sequence learners",
                "non-causal feature/monitor evaluation",
            ],
            "blocked_uses": [
                "standalone promotion target",
                "Stage 8 training gate",
                "justification for local box_shrink runtime patches",
                "runtime selector tuning target without protected-stack evidence",
            ],
        },
        "architecture_implication": {
            "next_level_problem": "learn_when_each_KRK_strategy_or_sequence_should_own",
            "protected_base": ["stage1", "stage4_with_h40_caveat", "stage5", "stage6"],
            "next_tracks": [
                "strategy_ownership",
                "sequence_policy",
                "curriculum_boundary",
            ],
            "stage7_training_rows_allowed": False,
            "stage7_evaluation_rows_allowed": True,
        },
        "explicitly_rejected_next_steps": [
            "more Stage 7 local move-shape tuning",
            "more Stage 7 support adapters or score bonuses",
            "more Plan Capsule micro-tuning as a Stage 7 repair",
            "promoting Stage 7",
            "training Stage 8 from unresolved Stage 7",
            "runtime DTM/tablebase selector",
            "unreviewed additional Stage 7 labels",
        ],
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Stage 7 Curriculum Boundary Decision v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Stage 7 `box_shrink` is no longer treated as a standalone repair target. It remains useful as local evidence, handoff pressure, and a held-out challenge set for broader KRK strategy/sequence learning.",
        "",
        "## Motivation",
        "",
    ]
    for item in payload["motivation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Current Evidence State", ""])
    for key, value in payload["current_evidence_state"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## New Role", ""])
    for key, value in payload["new_role_for_stage7"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Architecture Implication", ""])
    for key, value in payload["architecture_implication"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Explicitly Rejected Next Steps", ""])
    for item in payload["explicitly_rejected_next_steps"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_decision()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
