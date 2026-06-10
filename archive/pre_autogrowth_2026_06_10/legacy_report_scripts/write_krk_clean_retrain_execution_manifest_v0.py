#!/usr/bin/env python3
"""Write an explicit clean KRK retrain execution manifest.

The manifest is a guarded launch plan only. It redirects all rebuild outputs to
a fresh checkpoint root and keeps Stage 7/8, selector, and runtime-sandbox
effects out of the training path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = Path("reports/krk_clean_retrain_execution_manifest_v0.json")
OUT_MD = Path("reports/krk_clean_retrain_execution_manifest_v0.md")
CHECKPOINT_PLAN = Path("reports/krk_clean_curriculum_checkpoint_plan_v0.json")
CHECKPOINT_ROOT = Path("snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0")
PYTHON = ".venv/bin/python3"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _train_cmd(
    *,
    stage_id: str,
    stage0_cycles: int,
    stage1_cycles: int,
    samples_per_cycle: int,
    device: str,
    max_curriculum_stage: int,
    start_curriculum_stage: int | None = None,
    load_learner: str | None = None,
    adaptive_playout_max_plies: int | None = None,
    adaptive_eval_samples: int = 100,
    adaptive_composition_profile: str | None = None,
    adaptive_use_profile_validation_defaults: bool = False,
    adaptive_stagnation_breaker_king_support_bonus: float | None = None,
) -> list[str]:
    output_dir = CHECKPOINT_ROOT / stage_id / "baseline"
    learner_path = output_dir / "final_learner.pkl"
    cmd = [
        PYTHON,
        "scripts/train_baseline_krk_chain.py",
        "--stage0-cycles",
        str(stage0_cycles),
        "--stage1-cycles",
        str(stage1_cycles),
        "--samples-per-cycle",
        str(samples_per_cycle),
        "--output-dir",
        str(output_dir),
        "--save-learner",
        str(learner_path),
        "--device",
        device,
        "--seed",
        "7",
        "--snapshot-every",
        "1",
        "--min-mature-for-goals",
        "6",
        "--feature-set",
        "krk_rich_v1",
        "--max-curriculum-stage",
        str(max_curriculum_stage),
        "--landmark-cycles",
        "10",
        "--stage1-position-mode",
        "mate_in_2",
        "--adaptive-curriculum",
        "--eval-every",
        "5",
        "--patience",
        "3",
        "--min-cycles-per-stage",
        "10",
        "--max-cycles-per-stage",
        "80",
        "--adaptive-eval-samples",
        str(adaptive_eval_samples),
        "--stage0-balance-corners",
    ]
    if start_curriculum_stage is not None:
        cmd.extend(["--start-curriculum-stage", str(start_curriculum_stage)])
    if load_learner:
        cmd.extend(["--load-learner", load_learner])
    if adaptive_playout_max_plies is not None:
        cmd.extend(["--adaptive-playout-max-plies", str(adaptive_playout_max_plies)])
    if adaptive_composition_profile:
        cmd.extend(["--adaptive-composition-profile", adaptive_composition_profile])
    if adaptive_use_profile_validation_defaults:
        cmd.append("--adaptive-use-profile-validation-defaults")
    if adaptive_stagnation_breaker_king_support_bonus:
        cmd.extend(
            [
                "--adaptive-stagnation-breaker-king-support-bonus",
                str(adaptive_stagnation_breaker_king_support_bonus),
            ]
        )
    return cmd


def _compile_cmd(stage_id: str) -> list[str]:
    return [
        PYTHON,
        "scripts/baseline_to_recon.py",
        "--learner",
        str(CHECKPOINT_ROOT / stage_id / "baseline" / "final_learner.pkl"),
        "--output",
        str(CHECKPOINT_ROOT / stage_id / "topology" / "krk_entry_topology.json"),
    ]


def _basic_eval_cmds(stage_id: str, samples: int = 100) -> list[list[str]]:
    topology = CHECKPOINT_ROOT / stage_id / "topology" / "krk_entry_topology.json"
    learner = CHECKPOINT_ROOT / stage_id / "baseline" / "final_learner.pkl"
    return [
        [
            PYTHON,
            "scripts/test_krk_entry.py",
            "--topology",
            str(topology),
            "--samples",
            str(samples),
        ],
        [
            PYTHON,
            "scripts/test_stage1_backchain.py",
            "--topology",
            str(topology),
            "--learner",
            str(learner),
            "--samples",
            str(samples),
            "--seed",
            "7",
            "--stage-filter",
            "1",
            "--position-mode",
            "mate_in_2",
        ],
    ]


def _step(
    *,
    step_id: str,
    stage_label: str,
    purpose: str,
    train_cmd: list[str],
    expected_best_by_stage: str | None,
    prerequisites: list[str],
    historical_source_manifest: str,
    samples: int = 100,
) -> dict[str, Any]:
    expected_outputs = [
        str(CHECKPOINT_ROOT / step_id / "baseline" / "final_learner.pkl"),
        str(CHECKPOINT_ROOT / step_id / "topology" / "krk_entry_topology.json"),
    ]
    if expected_best_by_stage:
        expected_outputs.append(
            str(CHECKPOINT_ROOT / step_id / "baseline" / "best_by_stage" / expected_best_by_stage)
        )
    return {
        "step_id": step_id,
        "stage_label": stage_label,
        "purpose": purpose,
        "execution_status": "not_run_by_manifest",
        "historical_source_manifest": historical_source_manifest,
        "prerequisites": prerequisites,
        "commands": [train_cmd, _compile_cmd(step_id), *_basic_eval_cmds(step_id, samples=samples)],
        "expected_outputs": expected_outputs,
        "stop_if": [
            "command exits nonzero",
            "expected output missing",
            "protected validation regression",
            "Stage 7 training/promotion appears",
            "Stage 8 training appears",
        ],
    }


def build_payload() -> dict[str, Any]:
    checkpoint = _load_json(CHECKPOINT_PLAN)
    stage2a = _step(
        step_id="stage2a_edge_trap_close",
        stage_label="stage2_edge_trap_close",
        purpose="Fresh Stage 0/1 plus edge-trap-close foundation from zero.",
        train_cmd=_train_cmd(
            stage_id="stage2a_edge_trap_close",
            stage0_cycles=40,
            stage1_cycles=20,
            samples_per_cycle=150,
            device="cpu",
            max_curriculum_stage=2,
            adaptive_eval_samples=100,
        ),
        expected_best_by_stage="edge_trap_close.pkl",
        prerequisites=[],
        historical_source_manifest=(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage2a_fixed2/run_manifest.json"
        ),
    )
    stage2b = _step(
        step_id="stage2b_enemy_between",
        stage_label="stage3_edge_trap_enemy_between",
        purpose="Fresh enemy-between edge-trap continuation using the fresh Stage 2A provider.",
        train_cmd=_train_cmd(
            stage_id="stage2b_enemy_between",
            stage0_cycles=0,
            stage1_cycles=0,
            samples_per_cycle=150,
            device="cpu",
            max_curriculum_stage=3,
            start_curriculum_stage=3,
            load_learner=str(
                CHECKPOINT_ROOT
                / "stage2a_edge_trap_close"
                / "baseline"
                / "best_by_stage"
                / "edge_trap_close.pkl"
            ),
            adaptive_playout_max_plies=0,
            adaptive_eval_samples=100,
        ),
        expected_best_by_stage="edge_trap_enemy_between.pkl",
        prerequisites=["stage2a_edge_trap_close"],
        historical_source_manifest=(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage2b_only/run_manifest.json"
        ),
    )
    stage4 = _step(
        step_id="stage4_wrong_tempo",
        stage_label="stage4_edge_trap_wrong_tempo",
        purpose="Fresh wrong-tempo profile using the fresh Stage 2B provider.",
        train_cmd=_train_cmd(
            stage_id="stage4_wrong_tempo",
            stage0_cycles=0,
            stage1_cycles=0,
            samples_per_cycle=150,
            device="cpu",
            max_curriculum_stage=4,
            start_curriculum_stage=4,
            load_learner=str(
                CHECKPOINT_ROOT
                / "stage2b_enemy_between"
                / "baseline"
                / "best_by_stage"
                / "edge_trap_enemy_between.pkl"
            ),
            adaptive_playout_max_plies=0,
            adaptive_eval_samples=100,
        ),
        expected_best_by_stage="edge_trap_wrong_tempo.pkl",
        prerequisites=["stage2b_enemy_between"],
        historical_source_manifest=(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/run_manifest.json"
        ),
    )
    stage5 = _step(
        step_id="stage5_fence_handoff",
        stage_label="stage5_fence_established",
        purpose="Fresh protected fence/handoff provider using the fresh Stage 4 provider.",
        train_cmd=_train_cmd(
            stage_id="stage5_fence_handoff",
            stage0_cycles=0,
            stage1_cycles=0,
            samples_per_cycle=150,
            device="cpu",
            max_curriculum_stage=5,
            start_curriculum_stage=5,
            load_learner=str(
                CHECKPOINT_ROOT
                / "stage4_wrong_tempo"
                / "baseline"
                / "best_by_stage"
                / "edge_trap_wrong_tempo.pkl"
            ),
            adaptive_playout_max_plies=0,
            adaptive_eval_samples=100,
        ),
        expected_best_by_stage="fence_established.pkl",
        prerequisites=["stage4_wrong_tempo"],
        historical_source_manifest=(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/run_manifest.json"
        ),
    )
    stage6 = _step(
        step_id="stage6_drive_overlay_candidate",
        stage_label="stage6_drive_to_edge",
        purpose="Fresh Stage 6 drive provider using handoff_composition_v1 and the fresh Stage 5 provider.",
        train_cmd=_train_cmd(
            stage_id="stage6_drive_overlay_candidate",
            stage0_cycles=0,
            stage1_cycles=0,
            samples_per_cycle=150,
            device="auto",
            max_curriculum_stage=6,
            start_curriculum_stage=6,
            load_learner=str(
                CHECKPOINT_ROOT
                / "stage5_fence_handoff"
                / "baseline"
                / "best_by_stage"
                / "fence_established.pkl"
            ),
            adaptive_playout_max_plies=40,
            adaptive_eval_samples=200,
            adaptive_composition_profile="handoff_composition_v1",
            adaptive_use_profile_validation_defaults=True,
            adaptive_stagnation_breaker_king_support_bonus=2.0,
        ),
        expected_best_by_stage="drive_to_edge.pkl",
        prerequisites=["stage5_fence_handoff"],
        historical_source_manifest=(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/run_manifest.json"
        ),
        samples=100,
    )
    overlay_step = {
        "step_id": "stage6_overlay_composition_review",
        "stage_label": "stage6_overlay_composed",
        "purpose": "Compose fresh Stage 6 overlay with fresh protected Stage 5 base after training artifacts exist.",
        "execution_status": "requires_dedicated_compose_script_or_manual_review",
        "prerequisites": ["stage5_fence_handoff", "stage6_drive_overlay_candidate"],
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
            str(CHECKPOINT_ROOT / "stage6_overlay_composed" / "topology" / "krk_entry_topology.json")
        ],
        "stop_if": [
            "dedicated compose path is ambiguous",
            "Stage 5 provider preservation cannot be verified",
            "Stage 4 guardrail caveat worsens",
        ],
        "readiness_note": "Current repo has a composed overlay artifact but no replayable compose run_manifest; this step needs a small compose-manifest package before execution.",
    }
    steps = [stage2a, stage2b, stage4, stage5, stage6, overlay_step]
    return {
        "schema_version": "krk_clean_retrain_execution_manifest.v0",
        "causal_status": "execution_manifest_only_not_run",
        "created_for": "clean_curriculum_checkpoint_plan_v0",
        "checkpoint_root": str(CHECKPOINT_ROOT),
        "source_artifacts": [
            str(CHECKPOINT_PLAN),
            "reports/current_agent_brief.md",
            "reports/recon_long_term_architecture_roadmap.md",
        ],
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "stage7_training_rows_allowed": False,
        "selector_training_allowed": False,
        "capacity_labels_as_ownership_labels_allowed": False,
        "preflight": {
            "fresh_output_root_required": True,
            "fresh_output_root_exists_now": (ROOT / CHECKPOINT_ROOT).exists(),
            "must_not_overwrite_protected_snapshots": True,
            "full_run_started_by_this_manifest": False,
            "requires_human_review_before_long_run": True,
            "checkpoint_plan_status": (checkpoint.get("decision") or {}).get("status"),
        },
        "steps": steps,
        "validation_after_each_step": [
            "command exit status zero",
            "expected_outputs_exist",
            "JSON artifacts parse where generated",
            "no Stage 7 training or promotion markers",
            "no Stage 8 training markers",
        ],
        "final_validation_commands": [
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
        ],
        "stop_conditions": [
            "any command projects to hours without explicit run approval",
            "fresh output root already exists with non-manifest-owned files",
            "protected Stage 5/6 behavior regresses",
            "M1-M4 preservation tests fail",
            "KPK->KQK bridge preservation fails",
            "Stage 7 training/promotion appears",
            "Stage 8 training appears",
            "runtime DTM/tablebase use appears",
            "candidate-generation observation affects selection/scoring/routing",
        ],
        "decision": {
            "status": "clean_retrain_execution_manifest_ready_not_run",
            "full_run_authorized_by_this_manifest": False,
            "stage7_remains_quarantined": True,
            "stage8_remains_blocked": True,
            "runtime_selector_allowed": False,
            "recommended_next_step": "review_manifest_then_optionally_run_stage2a_smoke_or_full_clean_retrain",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Clean Retrain Execution Manifest v0",
        "",
        "This manifest makes the clean rebuild path executable without overwriting protected snapshots. It does not run training.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- full run authorized by this manifest: `{payload['decision']['full_run_authorized_by_this_manifest']}`",
        f"- Stage 7 remains quarantined: `{payload['decision']['stage7_remains_quarantined']}`",
        f"- Stage 8 remains blocked: `{payload['decision']['stage8_remains_blocked']}`",
        f"- runtime selector allowed: `{payload['decision']['runtime_selector_allowed']}`",
        f"- recommended next step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Preflight",
        "",
    ]
    for key, value in payload["preflight"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Execution Steps", ""])
    for step in payload["steps"]:
        lines.extend(
            [
                f"### {step['step_id']}",
                "",
                f"- stage label: `{step['stage_label']}`",
                f"- purpose: {step['purpose']}",
                f"- execution status: `{step['execution_status']}`",
                f"- prerequisites: `{step.get('prerequisites') or []}`",
            ]
        )
        if step.get("historical_source_manifest"):
            lines.append(f"- historical source manifest: `{step['historical_source_manifest']}`")
        if step.get("readiness_note"):
            lines.append(f"- readiness note: {step['readiness_note']}")
        lines.append("- expected outputs:")
        for output in step.get("expected_outputs") or []:
            lines.append(f"  - `{output}`")
        lines.append("- commands:")
        for command in step.get("commands") or []:
            lines.append("  - `" + " ".join(str(part) for part in command) + "`")
        lines.append("- stop if:")
        for item in step.get("stop_if") or []:
            lines.append(f"  - `{item}`")
        lines.append("")
    lines.extend(["## Final Validation Commands", ""])
    for command in payload["final_validation_commands"]:
        lines.append("- `" + " ".join(str(part) for part in command) + "`")
    lines.extend(["", "## Global Stop Conditions", ""])
    for item in payload["stop_conditions"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This manifest preserves the current architecture boundaries: no Stage 7 promotion, no Stage 8 training, no selector, no score/routing changes, no runtime DTM/tablebase, and no gameplay-time topology mutation. Candidate-generation observation remains diagnostic only.",
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
