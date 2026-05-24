#!/usr/bin/env python3
"""Write the Stage 6 overlay compose manifest for the clean retrain path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = Path("reports/krk_stage6_overlay_compose_manifest_v0.json")
OUT_MD = Path("reports/krk_stage6_overlay_compose_manifest_v0.md")
EXECUTION_MANIFEST = Path("reports/krk_clean_retrain_execution_manifest_v0.json")
CHECKPOINT_ROOT = Path("snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0")
COMPOSED_ROOT = CHECKPOINT_ROOT / "stage6_overlay_composed"


def _load_json(path: str | Path) -> dict[str, Any] | None:
    target = ROOT / path
    if not target.exists():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _playout_summary(path: str) -> dict[str, Any]:
    payload = _load_json(path) or {}
    return {
        "path": path,
        "exists": bool(payload),
        "playouts": payload.get("playouts") or payload.get("result_counts") or {},
        "shadow_candidates": len(payload.get("shadow_candidates") or []),
        "total": payload.get("total"),
    }


def build_payload() -> dict[str, Any]:
    execution = _load_json(EXECUTION_MANIFEST) or {}
    current_artifacts = {
        "stage6_candidate": _playout_summary(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage6_drive_overlay_300_seed7_h40.json"
        ),
        "stage5_guardrail": _playout_summary(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_overlay_300_seed7_h40.json"
        ),
        "stage4_overlay_probe": _playout_summary(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage4_wrong_tempo_overlay_300_seed7_h40.json"
        ),
        "promotion_eval": _load_json(
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json"
        )
        or {},
    }
    fresh_inputs = {
        "frozen_base_topology": str(
            CHECKPOINT_ROOT / "stage5_fence_handoff" / "topology" / "krk_entry_topology.json"
        ),
        "base_checkpoint": str(
            CHECKPOINT_ROOT
            / "stage5_fence_handoff"
            / "baseline"
            / "best_by_stage"
            / "fence_established.pkl"
        ),
        "overlay_learner": str(
            CHECKPOINT_ROOT / "stage6_drive_overlay_candidate" / "baseline" / "final_learner.pkl"
        ),
        "overlay_checkpoint": str(
            CHECKPOINT_ROOT
            / "stage6_drive_overlay_candidate"
            / "baseline"
            / "best_by_stage"
            / "drive_to_edge.pkl"
        ),
        "overlay_label": "drive_to_edge",
    }
    outputs = {
        "composed_topology": str(COMPOSED_ROOT / "topology" / "krk_entry_topology.json"),
        "stage6_candidate_eval": str(COMPOSED_ROOT / "stage6_drive_overlay_300_seed7_h40.json"),
        "stage5_guardrail_eval": str(COMPOSED_ROOT / "stage5_fence_overlay_300_seed7_h40.json"),
        "stage4_overlay_probe": str(COMPOSED_ROOT / "stage4_wrong_tempo_overlay_300_seed7_h40.json"),
        "stage5_base_control": str(
            COMPOSED_ROOT / "stage5_fence_stage5_base_control_300_seed7_h40.json"
        ),
        "stage4_base_control": str(
            COMPOSED_ROOT / "stage4_wrong_tempo_stage5_base_control_300_seed7_h40.json"
        ),
        "promotion_eval": str(COMPOSED_ROOT / "promotion_eval_stage6_overlay.json"),
    }
    compile_command = [
        "UV_CACHE_DIR=/tmp/uv-cache",
        "uv",
        "run",
        "python",
        "scripts/baseline_to_recon.py",
        "--base-topology",
        fresh_inputs["frozen_base_topology"],
        "--overlay-learner",
        fresh_inputs["overlay_learner"],
        "--overlay-label",
        fresh_inputs["overlay_label"],
        "--base-provider-version",
        "stage5_validated_v1",
        "--overlay-provider-version",
        "stage6_overlay_v1",
        "--base-source-checkpoint",
        fresh_inputs["base_checkpoint"],
        "--overlay-source-checkpoint",
        fresh_inputs["overlay_checkpoint"],
        "--validated-profile",
        "handoff_composition_v1",
        "--output",
        outputs["composed_topology"],
    ]
    promotion_eval_command = [
        "UV_CACHE_DIR=/tmp/uv-cache",
        "uv",
        "run",
        "python",
        "scripts/evaluate_provider_promotion.py",
        "--stage-artifact",
        outputs["stage6_candidate_eval"],
        "--guardrail-artifact",
        outputs["stage5_guardrail_eval"],
        "--min-mate-rate",
        "0.65",
        "--max-max-plies-rate",
        "0.25",
        "--max-shadow-candidates",
        "0",
        "--json-output",
        outputs["promotion_eval"],
    ]
    validation_commands = [
        [
            "UV_CACHE_DIR=/tmp/uv-cache",
            "uv",
            "run",
            "pytest",
            "tests/test_architecture_preservation.py",
            "tests/test_routing_contracts.py",
            "tests/test_endgame_components.py",
        ]
    ]
    return {
        "schema_version": "krk_stage6_overlay_compose_manifest.v0",
        "causal_status": "compose_execution_manifest_only_not_run",
        "source_artifacts": [
            str(EXECUTION_MANIFEST),
            "reports/stage6_overlay_validation_manifest.md",
            "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json",
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
        "selector_training_allowed": False,
        "composition_profile": "handoff_composition_v1",
        "base_provider_version": "stage5_validated_v1",
        "overlay_provider_version": "stage6_overlay_v1",
        "fresh_inputs": fresh_inputs,
        "fresh_outputs": outputs,
        "commands": {
            "compile_overlay_topology": compile_command,
            "promotion_eval": promotion_eval_command,
            "validation": validation_commands,
        },
        "current_reference_artifacts": current_artifacts,
        "preconditions": [
            "fresh Stage 5 fence/handoff step completed",
            "fresh Stage 6 drive overlay candidate step completed",
            "fresh output root is not an existing protected snapshot",
            "base and overlay checkpoints exist",
        ],
        "acceptance_criteria": [
            "composed topology exists",
            "Stage 6 candidate evaluation meets promotion thresholds",
            "Stage 5 guardrail evaluation preserves protected behavior",
            "Stage 4 overlay probe no worse than Stage 5 base-control caveat",
            "promotion_eval promotion_status is promoted",
            "M1-M4 and bridge/routing preservation tests pass",
            "no Stage 7 promotion or Stage 8 training",
        ],
        "stop_conditions": [
            "compile command fails",
            "base or overlay checkpoint missing",
            "Stage 5 guardrail regresses",
            "Stage 4 caveat worsens relative to base control",
            "promotion eval fails",
            "runtime selector/scoring/routing behavior appears",
            "runtime DTM/tablebase use appears",
            "gameplay topology mutation appears",
        ],
        "linked_execution_manifest_status": (execution.get("decision") or {}).get("status"),
        "decision": {
            "status": "stage6_overlay_compose_manifest_ready_not_run",
            "full_run_authorized_by_this_manifest": False,
            "compose_run_authorized_by_this_manifest": False,
            "stage7_remains_quarantined": True,
            "stage8_remains_blocked": True,
            "runtime_selector_allowed": False,
            "recommended_next_step": "review_manifest_then_run_only_after_fresh_stage5_stage6_artifacts_exist",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Stage 6 Overlay Compose Manifest v0",
        "",
        "This manifest formalizes the missing replayable Stage 6 overlay composition step for the clean retrain checkpoint. It does not run composition.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Fresh Inputs",
            "",
        ]
    )
    for key, value in payload["fresh_inputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Fresh Outputs", ""])
    for key, value in payload["fresh_outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Commands", ""])
    for key, command in payload["commands"].items():
        lines.append(f"- {key}:")
        if command and isinstance(command[0], list):
            for nested in command:
                lines.append("  - `" + " ".join(str(part) for part in nested) + "`")
        else:
            lines.append("  - `" + " ".join(str(part) for part in command) + "`")
    lines.extend(["", "## Current Reference Artifacts", ""])
    for key, value in payload["current_reference_artifacts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Acceptance Criteria", ""])
    for item in payload["acceptance_criteria"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Stop Conditions", ""])
    for item in payload["stop_conditions"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The compose step preserves frozen-provider plus overlay discipline. It must not promote Stage 7, train Stage 8, add a selector, change runtime defaults, use runtime DTM/tablebase, or mutate topology during gameplay.",
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
