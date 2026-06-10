#!/usr/bin/env python3
"""Summarize the next non-causal KRK self-expansion architecture gate.

This is an architecture review artifact. It does not implement runtime
arbitration, train Stage 8, promote Stage 7, use runtime DTM/tablebase, or
mutate topology.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROTECTED_STAGE_STATUS = Path("reports/krk_protected_stage_status.json")
STRATEGY_ARBITRATION_GATE = Path("reports/strategy_arbitration/krk_strategy_arbitration_decision_gate.json")
INTERNAL_TERMINAL_REVIEW = Path("reports/strategy_arbitration/krk_internal_terminal_design_review_v1.json")
TRAINING_OBJECTIVE_GATE = Path("reports/structural_candidates/stage7_training_objective_decision_gate.json")
SEQUENCE_POLICY_NOTE = Path("reports/structural_candidates/stage7_sequence_policy_redesign_note.json")
CURRENT_BRIEF = Path("reports/current_agent_brief.md")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    path = root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _require_false(payload: dict[str, Any], key: str, artifact: str) -> None:
    if payload.get(key) is not False:
        raise ValueError(f"{artifact} must keep {key}=False")


def _validate_non_causal_artifact(payload: dict[str, Any], artifact: str) -> None:
    causal_status = str(payload.get("causal_status") or "")
    if not causal_status.startswith("non_causal"):
        raise ValueError(f"{artifact} must remain non-causal, got {causal_status!r}")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if key in payload:
            _require_false(payload, key, artifact)


def build_gate(repo_root: Path) -> dict[str, Any]:
    protected = _load_json(repo_root, PROTECTED_STAGE_STATUS)
    arbitration_gate = _load_json(repo_root, STRATEGY_ARBITRATION_GATE)
    terminal_review = _load_json(repo_root, INTERNAL_TERMINAL_REVIEW)
    training_gate = _load_json(repo_root, TRAINING_OBJECTIVE_GATE)
    sequence_note = _load_json(repo_root, SEQUENCE_POLICY_NOTE)

    for artifact, payload in (
        (str(PROTECTED_STAGE_STATUS), protected),
        (str(STRATEGY_ARBITRATION_GATE), arbitration_gate),
        (str(INTERNAL_TERMINAL_REVIEW), terminal_review),
        (str(TRAINING_OBJECTIVE_GATE), training_gate),
        (str(SEQUENCE_POLICY_NOTE), sequence_note),
    ):
        _validate_non_causal_artifact(payload, artifact)

    protected_summary = protected.get("summary") or {}
    terminal_summary = terminal_review.get("summary") or {}
    training_decision = training_gate.get("selected_outcome")
    strategy_decision = arbitration_gate.get("selected_status")
    sequence_requirements = sequence_note.get("minimum_future_data_requirements") or []

    gate = {
        "schema_version": "krk_self_expansion_architecture_gate.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(PROTECTED_STAGE_STATUS),
            str(STRATEGY_ARBITRATION_GATE),
            str(INTERNAL_TERMINAL_REVIEW),
            str(TRAINING_OBJECTIVE_GATE),
            str(SEQUENCE_POLICY_NOTE),
            str(CURRENT_BRIEF),
        ],
        "current_architecture_state": {
            "validated_profile": protected_summary.get("current_architecture_profile"),
            "protected_or_promoted_stages": protected_summary.get("yes_protected_or_promoted") or [],
            "cleanest_solved_components": protected_summary.get("cleanest_solved_components") or [],
            "solved_with_caveat": protected_summary.get("solved_with_caveat") or [],
            "stage6_overlay_status": protected_summary.get("stage6_overlay_status"),
            "stage7_status": protected.get("stage7_status"),
        },
        "architecture_diagnosis": {
            "stage_stack_status": (
                "The current architecture preserves useful KRK subskills through Stage 6 when "
                "later stages are additive overlays on frozen provider packs."
            ),
            "stage7_boundary_status": (
                "Stage 7 is not a local move-shape task anymore; it is a challenge set exposing "
                "strategy ownership, sequence-policy expression, and monitor/ontology gaps."
            ),
            "strategy_arbitration_status": strategy_decision,
            "strategy_arbitration_interpretation": (
                "The first strategy-arbitration probe points to missing or immature visible "
                "monitor/feature terms before any runtime arbiter should be considered."
            ),
            "internal_terminal_status": terminal_summary.get("main_conclusion"),
            "sequence_policy_status": training_decision,
            "sequence_policy_interpretation": (
                "Simple visible/ranked objectives are insufficient; any future sequence learner "
                "needs state-local contrast, hard negatives, and closed-loop sequence supervision."
            ),
        },
        "selected_next_architecture_goal": {
            "goal_id": "krk_control_plane_evidence_contract_v0",
            "goal_type": "non_causal_data_contract_and_review",
            "why_this_goal": (
                "Strategy arbitration, internal monitors, and sequence-policy redesign need the "
                "same evidence boundary before any causal sandbox. A control-plane evidence "
                "contract prevents another Stage 7-specific repair loop."
            ),
            "must_include": [
                "protected_provider_provenance",
                "strategy_proposal_frames",
                "internal_monitor_records",
                "plan_capsule_window_records",
                "sequence_training_examples",
                "guardrail_result_summaries",
                "growth_governor_status",
                "promotion_gate_status",
            ],
            "must_remain_non_causal": True,
            "runtime_defaults_must_remain_unchanged": True,
        },
        "path_to_arbitrary_krk": [
            {
                "step": "preserve_validated_stack",
                "status": "complete_for_stage1_4_5_6_with_stage4_caveat",
                "purpose": "Keep solved subgraphs stable while adding later capacity as overlays.",
            },
            {
                "step": "build_control_plane_evidence_contract",
                "status": "next",
                "purpose": (
                    "Unify provider proposals, monitors, plan windows, sequence labels, and "
                    "guardrails into replay-free non-causal evidence records."
                ),
            },
            {
                "step": "collect_stratified_control_plane_evidence",
                "status": "future_non_causal",
                "purpose": (
                    "Cover Stage 5/6 successes, Stage 4 caveats, Stage 7 challenge families, "
                    "and future KRK/KQK/KPK analogues without overfitting to one stage."
                ),
            },
            {
                "step": "benchmark_strategy_selection_and_sequence_policy",
                "status": "future_non_causal",
                "purpose": (
                    "Separate owner selection from move-sequence expression before any causal "
                    "runtime mechanism is sandboxed."
                ),
            },
            {
                "step": "default_off_sandbox_candidate",
                "status": "future_requires_review",
                "purpose": (
                    "Only after offline evidence is strong, test a visible default-off strategy "
                    "monitor/arbiter or sequence policy with explicit traces."
                ),
            },
            {
                "step": "guardrail_aware_promotion",
                "status": "future_requires_sandbox_success",
                "purpose": (
                    "Promote only overlays that improve target coverage while preserving Stage "
                    "1/4/5/6, bridge tests, and M1-M4 semantics."
                ),
            },
            {
                "step": "cross_domain_transfer",
                "status": "future",
                "purpose": (
                    "Apply the same monitor -> candidate -> sandbox -> guardrail loop to KQK, "
                    "KPK->KQK, tactics, and similar domains."
                ),
            },
        ],
        "self_learning_recon_loop": [
            "visible_runtime_trace_and_provider_proposals",
            "non_causal_monitor_records",
            "structural_candidate_or_sequence_candidate",
            "growth_governor_plasticity_balance_check",
            "offline_supervision_or_bounded_weight_probe",
            "default_off_sandbox_only_after_review",
            "guardrail_validation",
            "overlay_promotion_or_quarantine",
            "protected_stack_update",
        ],
        "future_data_requirements": {
            "sequence_policy": sequence_requirements,
            "internal_monitors": terminal_review.get("answers", {}).get("safest_next_evidence_step"),
            "strategy_arbitration": arbitration_gate.get("missing_evidence") or [],
        },
        "forbidden_next_steps": [
            "stage7_runtime_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_arbiter",
            "runtime_internal_terminal",
            "support_adapter_or_score_bonus",
            "provider_penalty_or_stage0_suppression",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "monolithic_later_stage_replacement",
        ],
        "allowed_next_slices": [
            {
                "slice_id": "control_plane_schema_design_v0",
                "description": "Define non-causal ControlPlaneEvidenceFrame and validation requirements.",
                "allowed": True,
                "causal": False,
            },
            {
                "slice_id": "control_plane_manifest_from_existing_artifacts_v0",
                "description": "Map existing reports into the control-plane evidence fields replay-free.",
                "allowed": True,
                "causal": False,
            },
            {
                "slice_id": "stratified_gap_report_v0",
                "description": "List missing evidence needed before strategy arbiter or sequence-policy sandbox review.",
                "allowed": True,
                "causal": False,
            },
        ],
        "stop_conditions": [
            "any_runtime_behavior_change",
            "any_runtime_dtm_or_tablebase_use",
            "any_gameplay_topology_mutation",
            "any_stage7_promotion_or_stage8_training",
            "any_step_that_implements_a_runtime_arbiter_or_terminal",
            "any_step_that_reopens_stage7_micro_repair",
        ],
    }
    validate_gate(gate)
    return gate


def validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("gate must be non-causal architecture review")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if gate.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if gate["selected_next_architecture_goal"]["goal_id"] != "krk_control_plane_evidence_contract_v0":
        raise ValueError("unexpected selected architecture goal")
    if not gate["selected_next_architecture_goal"]["must_remain_non_causal"]:
        raise ValueError("next goal must remain non-causal")


def render_markdown(gate: dict[str, Any]) -> str:
    state = gate["current_architecture_state"]
    diagnosis = gate["architecture_diagnosis"]
    next_goal = gate["selected_next_architecture_goal"]
    lines = [
        "# KRK Self-Expansion Architecture Gate v0",
        "",
        "This is a non-causal architecture review. It does not implement runtime "
        "arbitration, runtime terminals, Stage 7 promotion, Stage 8 training, "
        "runtime DTM/tablebase use, or gameplay-time topology mutation.",
        "",
        "## Current State",
        "",
        f"- Validated profile: `{state.get('validated_profile')}`",
        f"- Protected/promoted stages: `{', '.join(state.get('protected_or_promoted_stages') or [])}`",
        f"- Cleanest solved components: `{', '.join(state.get('cleanest_solved_components') or [])}`",
        f"- Solved with caveat: `{', '.join(state.get('solved_with_caveat') or [])}`",
        f"- Stage 6 overlay status: `{state.get('stage6_overlay_status')}`",
        f"- Stage 7 status: `{state.get('stage7_status')}`",
        "",
        "## Diagnosis",
        "",
        f"- Stage stack: {diagnosis['stage_stack_status']}",
        f"- Stage 7 boundary: {diagnosis['stage7_boundary_status']}",
        f"- Strategy arbitration: `{diagnosis['strategy_arbitration_status']}`. "
        f"{diagnosis['strategy_arbitration_interpretation']}",
        f"- Internal terminals: {diagnosis['internal_terminal_status']}",
        f"- Sequence policy: `{diagnosis['sequence_policy_status']}`. "
        f"{diagnosis['sequence_policy_interpretation']}",
        "",
        "## Selected Next Architecture Goal",
        "",
        f"- Goal: `{next_goal['goal_id']}`",
        f"- Type: `{next_goal['goal_type']}`",
        f"- Reason: {next_goal['why_this_goal']}",
        "",
        "Required evidence fields:",
        "",
    ]
    lines.extend(f"- `{field}`" for field in next_goal["must_include"])
    lines.extend(
        [
            "",
            "## Path To Arbitrary KRK",
            "",
        ]
    )
    for step in gate["path_to_arbitrary_krk"]:
        lines.append(f"- `{step['step']}` (`{step['status']}`): {step['purpose']}")
    lines.extend(
        [
            "",
            "## Self-Learning ReCoN Loop",
            "",
        ]
    )
    lines.extend(f"- `{step}`" for step in gate["self_learning_recon_loop"])
    lines.extend(
        [
            "",
            "## Allowed Next Slices",
            "",
        ]
    )
    for item in gate["allowed_next_slices"]:
        lines.append(f"- `{item['slice_id']}`: {item['description']}")
    lines.extend(
        [
            "",
            "## Forbidden Next Steps",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in gate["forbidden_next_steps"])
    lines.extend(
        [
            "",
            "## Stop Conditions",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in gate["stop_conditions"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(gate: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_self_expansion_architecture_gate_v0.json").write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_self_expansion_architecture_gate_v0.md").write_text(
        render_markdown(gate), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    gate = build_gate(repo_root)
    write_outputs(gate, report_root)
    print(json.dumps(gate["selected_next_architecture_goal"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
