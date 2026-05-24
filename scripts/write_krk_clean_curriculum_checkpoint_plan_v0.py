#!/usr/bin/env python3
"""Write the clean KRK curriculum checkpoint plan.

This is a readiness artifact, not a training driver. It records the current
known clean rebuild path, validation gates, and blockers before launching any
long train-from-zero run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = Path("reports/krk_clean_curriculum_checkpoint_plan_v0.json")
OUT_MD = Path("reports/krk_clean_curriculum_checkpoint_plan_v0.md")


def _load_json(path: str) -> dict[str, Any] | None:
    target = ROOT / path
    if not target.exists():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _manifest_summary(path: str) -> dict[str, Any]:
    payload = _load_json(path) or {}
    training = payload.get("training") or {}
    return {
        "path": path,
        "exists": bool(payload),
        "purpose": payload.get("purpose"),
        "output_dir": payload.get("output_dir"),
        "learner_path": payload.get("learner_path"),
        "topology_path": payload.get("topology_path"),
        "load_learner": training.get("load_learner"),
        "feature_set": training.get("feature_set"),
        "adaptive_curriculum": training.get("adaptive_curriculum"),
        "adaptive_composition_profile": training.get("adaptive_composition_profile"),
        "max_curriculum_stage": training.get("max_curriculum_stage"),
        "start_curriculum_stage": training.get("start_curriculum_stage"),
        "adaptive_eval_samples": training.get("adaptive_eval_samples"),
        "adaptive_playout_max_plies": training.get("adaptive_playout_max_plies"),
        "commands": payload.get("commands") or [],
    }


def build_payload() -> dict[str, Any]:
    stage1 = _manifest_summary("snapshots/krk_triplet_pipeline/stage1_clean/run_manifest.json")
    stage4 = _manifest_summary(
        "snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/run_manifest.json"
    )
    stage5 = _manifest_summary(
        "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/run_manifest.json"
    )
    stage6 = _manifest_summary(
        "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/run_manifest.json"
    )
    refresh_sandbox = _load_json(
        "reports/strategy_arbitration/krk_candidate_generation_refresh_sandbox_v0.json"
    ) or {}
    refresh_coverage = _load_json(
        "reports/strategy_arbitration/krk_candidate_generation_refresh_coverage_analysis_v0.json"
    ) or {}
    dataset_v5 = _load_json("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json") or {}
    exact_trace = _load_json(
        "reports/strategy_arbitration/krk_exact_trace_enrichment_sandbox_v0.json"
    ) or {}

    command_sequence = [
        {
            "step_id": "stage1_foundation_clean",
            "purpose": "Train/rebuild Stage 0/1 foundation from zero.",
            "source_manifest": stage1["path"],
            "commands": stage1["commands"],
            "expected_outputs": [
                "snapshots/krk_triplet_pipeline/stage1_clean/baseline/final_learner.pkl",
                "snapshots/krk_triplet_pipeline/stage1_clean/topology/krk_entry_topology.json",
            ],
        },
        {
            "step_id": "stage4_wrong_tempo_profile",
            "purpose": "Train/rebuild wrong-tempo / edge-trap profile from the prior clean provider.",
            "source_manifest": stage4["path"],
            "commands": stage4["commands"],
            "expected_outputs": [
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/final_learner.pkl",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/topology/krk_entry_topology.json",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/best_by_stage/edge_trap_wrong_tempo.pkl",
            ],
        },
        {
            "step_id": "stage5_fence_handoff",
            "purpose": "Train/rebuild protected fence/handoff component.",
            "source_manifest": stage5["path"],
            "commands": stage5["commands"],
            "expected_outputs": [
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/final_learner.pkl",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl",
            ],
        },
        {
            "step_id": "stage6_drive_overlay",
            "purpose": "Train/rebuild Stage 6 drive overlay against handoff_composition_v1.",
            "source_manifest": stage6["path"],
            "commands": stage6["commands"],
            "expected_outputs": [
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/final_learner.pkl",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/topology/krk_entry_topology.json",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/best_by_stage/drive_to_edge.pkl",
            ],
        },
        {
            "step_id": "stage6_overlay_composition",
            "purpose": "Compose Stage 6 overlay with protected Stage 5 base and validate preservation.",
            "source_artifacts": [
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage6_drive_overlay_300_seed7_h40.json",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_overlay_300_seed7_h40.json",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40.json",
            ],
            "commands": [
                [
                    "UV_CACHE_DIR=/tmp/uv-cache",
                    "uv",
                    "run",
                    "pytest",
                    "tests/test_architecture_preservation.py",
                    "tests/test_routing_contracts.py",
                ]
            ],
            "expected_outputs": [
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json",
            ],
            "readiness_note": "Existing composed overlay artifact has no run_manifest; preserve current artifact paths until a dedicated compose script is formalized.",
        },
    ]

    validation_commands = [
        [
            "UV_CACHE_DIR=/tmp/uv-cache",
            "uv",
            "run",
            "pytest",
            "tests/test_krk_strategy_arbitration_dataset.py",
            "tests/test_krk_ownership_selection_recovery.py",
        ],
        [
            "UV_CACHE_DIR=/tmp/uv-cache",
            "uv",
            "run",
            "pytest",
            "tests/test_architecture_preservation.py",
            "tests/test_routing_contracts.py",
            "tests/test_endgame_components.py",
        ],
        [
            "UV_CACHE_DIR=/tmp/uv-cache",
            "uv",
            "run",
            "python",
            "scripts/run_krk_candidate_generation_refresh_sandbox_v0.py",
        ],
        [
            "UV_CACHE_DIR=/tmp/uv-cache",
            "uv",
            "run",
            "python",
            "scripts/analyze_krk_candidate_generation_refresh_coverage_v0.py",
        ],
    ]

    readiness_blockers = []
    if not all(item["exists"] for item in [stage1, stage4, stage5, stage6]):
        readiness_blockers.append("one_or_more_stage_run_manifests_missing")
    if not (ROOT / "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json").exists():
        readiness_blockers.append("stage6_overlay_composed_topology_missing")
    if not readiness_blockers:
        readiness_blockers.append("full_clean_retrain_not_launched_in_this_slice_requires_explicit_manifest_review")

    return {
        "schema_version": "krk_clean_curriculum_checkpoint_plan.v0",
        "causal_status": "plan_and_readiness_audit_only",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/current_agent_brief.md",
            "reports/recon_long_term_architecture_roadmap.md",
            "reports/strategy_arbitration/krk_candidate_generation_refresh_sandbox_v0.json",
            "reports/strategy_arbitration/krk_candidate_generation_refresh_coverage_analysis_v0.json",
            "reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json",
        ],
        "current_validated_stack": {
            "profile": "handoff_composition_v1",
            "protected_or_base_components": [
                "stage1_backchain",
                "stage5_fence_handoff",
                "stage6_drive_to_edge_overlay",
                "kpk_to_kqk_bridge_preservation",
            ],
            "stage4_status": "mostly_clean_with_separate_h40_overlay_control_caveat",
            "stage7_status": "local_valid_composition_quarantined_held_out_challenge",
            "stage8_status": "blocked_until_stage7_or_broader_control_plane_review",
            "control_plane_status": {
                "candidate_generation_refresh_sandbox": (
                    (refresh_sandbox.get("decision") or {}).get("status")
                ),
                "candidate_generation_refresh_coverage": (
                    (refresh_coverage.get("decision") or {}).get("status")
                ),
                "dataset_v5_status": (dataset_v5.get("decision") or {}).get("status"),
                "exact_trace_enrichment_status": (exact_trace.get("decision") or {}).get("status"),
            },
        },
        "command_sequence": command_sequence,
        "stage_checkpoints": [
            {
                "stage": "stage1",
                "role": "local/backchain foundation",
                "promotion_policy": "protected_if_clean_retrain_matches_current_stage1_guardrails",
                "expected_artifact": "snapshots/krk_triplet_pipeline/stage1_clean",
            },
            {
                "stage": "stage4",
                "role": "wrong-tempo / edge-trap profile",
                "promotion_policy": "protected_with_existing_h40_overlay_control_caveat",
                "expected_artifact": "snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean",
            },
            {
                "stage": "stage5",
                "role": "fence/handoff protected base",
                "promotion_policy": "protected_base_provider_pack",
                "expected_artifact": "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean",
            },
            {
                "stage": "stage6",
                "role": "drive_to_edge overlay",
                "promotion_policy": "overlay_preserved_if_stage5_and_stage4_guardrails_hold",
                "expected_artifact": "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support",
            },
            {
                "stage": "stage7",
                "role": "held-out challenge / local evidence / handoff trigger",
                "promotion_policy": "do_not_promote",
                "expected_artifact": "reports/structural_candidates/stage7_pause_and_architecture_review.md",
            },
        ],
        "provider_pack_and_overlay_rules": {
            "frozen_provider_pack_sources": [
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl",
                "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/best_by_stage/drive_to_edge.pkl",
            ],
            "overlay_rule": "later stages compose as overlays over frozen validated providers, never monolithic replacement",
            "handoff_profile": "handoff_composition_v1",
            "stage7_usage": "held_out_challenge_rows_only_no_training_or_promotion",
        },
        "candidate_generation_observation_policy": {
            "include_in_normal_clean_training": False,
            "include_in_diagnostic_validation": True,
            "flags": [
                "--enable-krk-candidate-generation-refresh",
                "--enable-krk-exact-trace-enrichment",
            ],
            "allowed_effect": "trace_or_candidate_generation_frames_only",
            "selector_allowed": False,
        },
        "validation_commands": validation_commands,
        "promotion_quarantine_criteria": {
            "promote_stage1_5_6_only_if": [
                "clean retrain artifacts exist",
                "protected guardrails match or improve current stack",
                "M1-M4 preservation tests pass",
                "KPK->KQK bridge preservation tests pass",
                "no default runtime behavior changes",
            ],
            "quarantine_if": [
                "Stage 5 or Stage 6 guardrail regression",
                "M1-M4 semantic regression",
                "KPK->KQK bridge regression",
                "Stage 7 treated as training/promotion row",
                "runtime observation frames affect selection/scoring/routing",
            ],
        },
        "readiness_review": {
            "can_run_full_clean_curriculum_now": False,
            "reason": "commands and artifacts are identified, but a full run may be long and should start from an explicit execution manifest with output paths to avoid overwriting protected snapshots",
            "can_run_tiny_smoke_now": True,
            "tiny_smoke_recommendation": "use existing stage smoke scripts and focused tests; do not launch full retrain from this artifact",
            "missing_or_stale_items": readiness_blockers,
            "estimated_runtime_class": "full_retrain_likely_long; smoke_tests_short",
            "invalid_run_conditions": [
                "overwriting protected snapshots without a new output directory",
                "training Stage 8",
                "promoting Stage 7",
                "using runtime DTM/tablebase",
                "enabling observation sandboxes as causal selectors",
            ],
        },
        "decision": {
            "status": "clean_curriculum_checkpoint_plan_ready_full_run_requires_review",
            "stage7_remains_quarantined": True,
            "stage8_remains_blocked": True,
            "runtime_selector_allowed": False,
            "recommended_next_step": "write_explicit_clean_retrain_execution_manifest_before_any_long_run",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    review = payload["readiness_review"]
    lines = [
        "# KRK Clean Curriculum Checkpoint Plan v0",
        "",
        "This is a readiness and execution-plan artifact. It does not launch a full retrain and does not change runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- Stage 7 remains quarantined: `{payload['decision']['stage7_remains_quarantined']}`",
        f"- Stage 8 remains blocked: `{payload['decision']['stage8_remains_blocked']}`",
        f"- runtime selector allowed: `{payload['decision']['runtime_selector_allowed']}`",
        f"- recommended next step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Validated Stack",
        "",
        f"- profile: `{payload['current_validated_stack']['profile']}`",
    ]
    for component in payload["current_validated_stack"]["protected_or_base_components"]:
        lines.append(f"- protected/base component: `{component}`")
    lines.extend(
        [
            f"- Stage 4 status: `{payload['current_validated_stack']['stage4_status']}`",
            f"- Stage 7 status: `{payload['current_validated_stack']['stage7_status']}`",
            f"- Stage 8 status: `{payload['current_validated_stack']['stage8_status']}`",
            "",
            "## Command Sequence",
            "",
        ]
    )
    for step in payload["command_sequence"]:
        lines.extend(
            [
                f"### {step['step_id']}",
                "",
                f"- purpose: `{step['purpose']}`",
            ]
        )
        if step.get("source_manifest"):
            lines.append(f"- source manifest: `{step['source_manifest']}`")
        if step.get("readiness_note"):
            lines.append(f"- readiness note: `{step['readiness_note']}`")
        lines.append("- expected outputs:")
        for output in step.get("expected_outputs") or []:
            lines.append(f"  - `{output}`")
        lines.append("- commands:")
        commands = step.get("commands") or []
        if not commands:
            lines.append("  - `missing_command_review_required`")
        for command in commands:
            lines.append("  - `" + " ".join(str(part) for part in command) + "`")
        lines.append("")
    lines.extend(
        [
            "## Stage Checkpoints",
            "",
        ]
    )
    for checkpoint in payload["stage_checkpoints"]:
        lines.append(
            f"- `{checkpoint['stage']}`: {checkpoint['role']} ({checkpoint['promotion_policy']})"
        )
    lines.extend(
        [
            "",
            "## Candidate-Generation Observation",
            "",
            f"- include in normal clean training: `{payload['candidate_generation_observation_policy']['include_in_normal_clean_training']}`",
            f"- include in diagnostic validation: `{payload['candidate_generation_observation_policy']['include_in_diagnostic_validation']}`",
            f"- allowed effect: `{payload['candidate_generation_observation_policy']['allowed_effect']}`",
            f"- selector allowed: `{payload['candidate_generation_observation_policy']['selector_allowed']}`",
            "",
            "## Validation Commands",
            "",
        ]
    )
    for command in payload["validation_commands"]:
        lines.append("- `" + " ".join(str(part) for part in command) + "`")
    lines.extend(
        [
            "",
            "## Readiness Review",
            "",
            f"- can run full clean curriculum now: `{review['can_run_full_clean_curriculum_now']}`",
            f"- reason: {review['reason']}",
            f"- can run tiny smoke now: `{review['can_run_tiny_smoke_now']}`",
            f"- estimated runtime class: `{review['estimated_runtime_class']}`",
            "- missing/stale items:",
        ]
    )
    for item in review["missing_or_stale_items"]:
        lines.append(f"  - `{item}`")
    lines.extend(
        [
            "- invalid run conditions:",
        ]
    )
    for item in review["invalid_run_conditions"]:
        lines.append(f"  - `{item}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This plan keeps Stage 7 as a held-out challenge, keeps Stage 8 blocked, and keeps candidate-generation observation separate from selector ownership labels. A full clean retrain should be launched only from a separate execution manifest with fresh output paths.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
