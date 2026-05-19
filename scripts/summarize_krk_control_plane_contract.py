#!/usr/bin/env python3
"""Define the non-causal KRK control-plane evidence contract.

The contract unifies provider provenance, strategy proposals, internal monitors,
plan windows, sequence examples, guardrails, and promotion/growth status as
evidence records. It does not add runtime behavior or causal routing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ARCHITECTURE_GATE = Path("reports/krk_self_expansion_architecture_gate_v0.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def build_contract(repo_root: Path) -> dict[str, Any]:
    gate = _load_json(repo_root, ARCHITECTURE_GATE)
    if gate.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("architecture gate must be non-causal")
    next_goal = gate.get("selected_next_architecture_goal") or {}
    if next_goal.get("goal_id") != "krk_control_plane_evidence_contract_v0":
        raise ValueError("architecture gate does not select the control-plane contract")

    contract = {
        "schema_version": "krk_control_plane_evidence_contract.v0",
        "causal_status": "non_causal_schema_contract",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(ARCHITECTURE_GATE)],
        "purpose": (
            "Provide a shared non-causal data boundary for strategy arbitration, "
            "internal monitors, sequence-policy redesign, growth governance, and "
            "guardrail-aware promotion review."
        ),
        "primary_frame": {
            "name": "ControlPlaneEvidenceFrame",
            "schema_version": "control_plane_evidence_frame.v1",
            "causal_status": "non_causal",
            "required_fields": [
                "frame_id",
                "domain",
                "state_id",
                "fen",
                "source_stage",
                "active_landmark_label",
                "protected_provider_provenance",
                "strategy_proposal_frames",
                "internal_monitor_records",
                "plan_capsule_window_records",
                "sequence_training_examples",
                "outcome_labels",
                "guardrail_result_summaries",
                "growth_governor_status",
                "promotion_gate_status",
                "source_artifacts",
                "causal_status",
            ],
            "forbidden_fields": [
                "runtime_selected_provider_override",
                "runtime_move_override",
                "runtime_score_bonus",
                "runtime_provider_penalty",
                "runtime_dtm_or_tablebase_label",
                "gameplay_topology_patch",
            ],
        },
        "subschemas": [
            {
                "name": "ProtectedProviderProvenance",
                "schema_version": "protected_provider_provenance.v1",
                "purpose": "Identify which validated provider pack or overlay produced evidence.",
                "required_fields": [
                    "skill_id",
                    "provider_version",
                    "source_stage",
                    "source_checkpoint",
                    "validated_profile",
                    "provider_maturity",
                    "frozen_provider",
                    "overlay_provider",
                    "plasticity_scope",
                    "guardrail_status",
                ],
            },
            {
                "name": "StrategyProposalFrame",
                "schema_version": "strategy_proposal_frame.v1",
                "purpose": "Represent a provider's candidate move and evidence without selecting it.",
                "required_fields": [
                    "provider_id",
                    "skill_id",
                    "provider_version",
                    "move_uci",
                    "raw_score",
                    "provider_local_rank",
                    "normalized_score",
                    "source_terms",
                    "role_licenses",
                    "move_shape_terms",
                    "post_move_terms",
                    "safety_terms",
                    "known_outcome_label",
                    "causal_status",
                ],
            },
            {
                "name": "InternalMonitorEvidence",
                "schema_version": "internal_monitor_evidence.v1",
                "purpose": "Attach non-causal internal-terminal/monitor evidence to a state.",
                "required_fields": [
                    "terminal_id",
                    "monitor_type",
                    "source_terms_met",
                    "missing_terms",
                    "confidence",
                    "associated_outcome",
                    "maturity_status",
                    "causal_ready",
                    "causal_status",
                ],
            },
            {
                "name": "PlanCapsuleWindowEvidence",
                "schema_version": "plan_capsule_window_evidence.v1",
                "purpose": "Describe bounded plan ownership windows and progress/exit/abort evidence.",
                "required_fields": [
                    "plan_id",
                    "plan_status",
                    "ttl_white_moves",
                    "owned_white_move_count",
                    "entry_terms_confirmed",
                    "progress_terms_confirmed",
                    "exit_terms_confirmed",
                    "abort_terms_confirmed",
                    "handoff_target",
                    "window_outcome",
                    "causal_status",
                ],
            },
            {
                "name": "SequenceTrainingExample",
                "schema_version": "sequence_training_example.v1",
                "purpose": "Store offline labels for sequence-policy benchmarks without runtime oracle use.",
                "required_fields": [
                    "example_id",
                    "family_id",
                    "trajectory_id",
                    "ply_index",
                    "candidate_moves",
                    "positive_moves",
                    "hard_negative_moves",
                    "draw_or_safety_veto_moves",
                    "label_source",
                    "offline_only",
                    "causal_status",
                ],
            },
            {
                "name": "GuardrailResultSummary",
                "schema_version": "guardrail_result_summary.v1",
                "purpose": "Summarize protected-stage and bridge validations for promotion review.",
                "required_fields": [
                    "guardrail_id",
                    "stage_or_domain",
                    "sample_count",
                    "horizon",
                    "mate_count",
                    "max_plies_count",
                    "shadow_candidate_count",
                    "passed",
                    "source_artifact",
                ],
            },
            {
                "name": "GrowthGovernorStatus",
                "schema_version": "growth_governor_status.v1",
                "purpose": "Record whether structural growth is allowed, settling, or blocked.",
                "required_fields": [
                    "stage_or_provider",
                    "status",
                    "active_candidate_count",
                    "guardrail_pass_rate",
                    "plasticity_improvement_slope",
                    "repeated_failure_family_count",
                    "reason",
                ],
            },
            {
                "name": "PromotionGateStatus",
                "schema_version": "promotion_gate_status.v1",
                "purpose": "Record candidate promotion/quarantine state and non-regression evidence.",
                "required_fields": [
                    "candidate_id",
                    "promotion_status",
                    "target_validation_status",
                    "protected_guardrail_status",
                    "shadow_candidate_delta",
                    "causal_status",
                    "source_artifact",
                ],
            },
        ],
        "allowed_consumers": [
            "offline_strategy_arbitration_probe",
            "offline_sequence_policy_benchmark",
            "growth_monitor_candidate_generation",
            "guardrail_promotion_review",
            "architecture_review_reports",
        ],
        "forbidden_consumers": [
            "runtime_move_selector",
            "runtime_provider_router",
            "runtime_score_modifier",
            "runtime_topology_mutator",
            "runtime_dtm_or_tablebase_oracle",
        ],
        "validation_requirements": [
            "all_records_causal_status_non_causal",
            "all_runtime_behavior_flags_false",
            "no_runtime_dtm_or_tablebase_labels",
            "no_move_or_provider_override_fields",
            "offline_labels_marked_offline_only",
            "guardrail_sources_are_explicit",
            "provider_versions_are_explicit",
            "stage7_promotion_allowed_false",
            "stage8_training_allowed_false",
        ],
        "first_manifest_scope": {
            "records_from_existing_artifacts_only": True,
            "include_stage5_stage6_successes": True,
            "include_stage4_caveat": True,
            "include_stage7_challenge_families": True,
            "include_cross_domain_bridge_sanity": "source references only unless already summarized",
            "new_playouts_allowed": False,
        },
        "blocked_next_steps": gate.get("forbidden_next_steps") or [],
        "recommended_next_slice": "control_plane_manifest_from_existing_artifacts_v0",
    }
    validate_contract(contract)
    return contract


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("causal_status") != "non_causal_schema_contract":
        raise ValueError("contract must remain non-causal")
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
        if contract.get(key) is not False:
            raise ValueError(f"{key} must be false")
    required_subschemas = {
        "ProtectedProviderProvenance",
        "StrategyProposalFrame",
        "InternalMonitorEvidence",
        "PlanCapsuleWindowEvidence",
        "SequenceTrainingExample",
        "GuardrailResultSummary",
        "GrowthGovernorStatus",
        "PromotionGateStatus",
    }
    actual = {item["name"] for item in contract.get("subschemas") or []}
    if actual != required_subschemas:
        raise ValueError(f"unexpected subschemas: {actual}")
    if "runtime_move_selector" not in contract.get("forbidden_consumers", []):
        raise ValueError("runtime move selector must be forbidden")
    if contract.get("recommended_next_slice") != "control_plane_manifest_from_existing_artifacts_v0":
        raise ValueError("unexpected next slice")


def render_markdown(contract: dict[str, Any]) -> str:
    frame = contract["primary_frame"]
    lines = [
        "# KRK Control-Plane Evidence Contract v0",
        "",
        "This is a non-causal schema contract. It does not add runtime terminals, "
        "runtime arbitration, score changes, topology mutation, Stage 7 promotion, "
        "or Stage 8 training.",
        "",
        "## Purpose",
        "",
        contract["purpose"],
        "",
        "## Primary Frame",
        "",
        f"- Name: `{frame['name']}`",
        f"- Schema: `{frame['schema_version']}`",
        f"- Causal status: `{frame['causal_status']}`",
        "",
        "Required fields:",
        "",
    ]
    lines.extend(f"- `{field}`" for field in frame["required_fields"])
    lines.extend(["", "Forbidden fields:", ""])
    lines.extend(f"- `{field}`" for field in frame["forbidden_fields"])
    lines.extend(["", "## Subschemas", ""])
    for schema in contract["subschemas"]:
        lines.extend(
            [
                f"### {schema['name']}",
                "",
                f"- Schema: `{schema['schema_version']}`",
                f"- Purpose: {schema['purpose']}",
                "- Required fields: "
                + ", ".join(f"`{field}`" for field in schema["required_fields"]),
                "",
            ]
        )
    lines.extend(["## Allowed Consumers", ""])
    lines.extend(f"- `{item}`" for item in contract["allowed_consumers"])
    lines.extend(["", "## Forbidden Consumers", ""])
    lines.extend(f"- `{item}`" for item in contract["forbidden_consumers"])
    lines.extend(["", "## Validation Requirements", ""])
    lines.extend(f"- `{item}`" for item in contract["validation_requirements"])
    lines.extend(
        [
            "",
            "## First Manifest Scope",
            "",
            f"- Existing artifacts only: `{contract['first_manifest_scope']['records_from_existing_artifacts_only']}`",
            f"- Include Stage 5/6 successes: `{contract['first_manifest_scope']['include_stage5_stage6_successes']}`",
            f"- Include Stage 4 caveat: `{contract['first_manifest_scope']['include_stage4_caveat']}`",
            f"- Include Stage 7 challenge families: `{contract['first_manifest_scope']['include_stage7_challenge_families']}`",
            f"- New playouts allowed: `{contract['first_manifest_scope']['new_playouts_allowed']}`",
            "",
            "## Recommended Next Slice",
            "",
            f"`{contract['recommended_next_slice']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(contract: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_evidence_contract_v0.json").write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_evidence_contract_v0.md").write_text(
        render_markdown(contract), encoding="utf-8"
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
    contract = build_contract(repo_root)
    write_outputs(contract, report_root)
    print(json.dumps({"recommended_next_slice": contract["recommended_next_slice"]}, indent=2))


if __name__ == "__main__":
    main()
