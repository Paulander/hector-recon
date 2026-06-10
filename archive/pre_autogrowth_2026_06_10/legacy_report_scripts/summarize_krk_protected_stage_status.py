#!/usr/bin/env python3
"""Summarize protected KRK stage status from existing artifacts.

This is a replay-free status audit. It does not run playouts, alter runtime
behavior, train stages, promote Stage 7, or mutate topology.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STAGE1_MANIFEST = Path("snapshots/krk_triplet_pipeline/stage1_clean/run_manifest.json")
STAGE4_PROFILE = Path(
    "snapshots/krk_triplet_pipeline/handoff_observability_check/"
    "slice47_profile_stage4_wrong_tempo_500_seed7_h40.json"
)
STAGE5_PROFILE = Path(
    "snapshots/krk_triplet_pipeline/handoff_observability_check/"
    "slice47_profile_stage5_1000_seed7_h40.json"
)
STAGE6_CANDIDATE = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/"
    "stage6_drive_overlay_300_seed7_h40.json"
)
STAGE5_OVERLAY_GUARD = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/"
    "stage5_fence_overlay_300_seed7_h40.json"
)
STAGE4_OVERLAY_PROBE = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/"
    "stage4_wrong_tempo_overlay_300_seed7_h40.json"
)
STAGE4_BASE_CONTROL = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/"
    "stage4_wrong_tempo_stage5_base_control_300_seed7_h40.json"
)
STAGE6_PROMOTION = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/"
    "promotion_eval_stage6_overlay.json"
)
HANDOFF_NOTES = Path("reports/krk_handoff_counterfactual_notes.md")
ACTIVE_STACK = Path("reports/krk_active_protected_stack_v0.json")
RETRY1_STAGE4_REVIEW = Path("reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    path = root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_optional_json(root: Path, relative_path: Path) -> dict[str, Any]:
    path = root / relative_path
    if not path.exists():
        return {}
    return _load_json(root, relative_path)


def _load_optional_text(root: Path, relative_path: Path) -> str:
    path = root / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _playouts(payload: dict[str, Any]) -> dict[str, int]:
    playouts = payload.get("playouts") or {}
    if not isinstance(playouts, dict):
        return {}
    return {str(key): int(value) for key, value in playouts.items()}


def _shadow_count(payload: dict[str, Any]) -> int:
    if isinstance(payload.get("shadow_candidates"), list):
        return len(payload["shadow_candidates"])
    if payload.get("shadow_candidate_count") is not None:
        return int(payload["shadow_candidate_count"])
    return 0


def _profile_id(payload: dict[str, Any]) -> str | None:
    profile = payload.get("composition_profile")
    if isinstance(profile, dict):
        value = profile.get("profile_id")
        return str(value) if value else None
    return str(profile) if profile else None


def _validation_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": payload.get("total"),
        "improved": payload.get("improved"),
        "optimal": payload.get("optimal"),
        "worsened": payload.get("worsened"),
        "no_move": payload.get("no_move"),
        "playouts": _playouts(payload),
        "one_ply_status_counts": payload.get("one_ply_status_counts") or {},
        "conversion_status_counts": payload.get("conversion_status_counts") or {},
        "shadow_candidate_count": _shadow_count(payload),
        "composition_profile": _profile_id(payload),
    }


def _manifest_summary(payload: dict[str, Any]) -> dict[str, Any]:
    validation = payload.get("formal_validation") or {}
    evaluation = payload.get("evaluation") or {}
    readiness = payload.get("learner_readiness") or {}
    return {
        "formal_validation": {
            "mode": validation.get("mode"),
            "validated": bool(validation.get("validated")),
            "nodes": validation.get("nodes"),
            "edges": validation.get("edges"),
        },
        "evaluation": evaluation,
        "learner_readiness": readiness,
    }


def _notes_stage1_500_present(notes: str) -> bool:
    return (
        "Stage 1 regression:" in notes
        and "samples: 500" in notes
        and "result: 500/500 improved, 500/500 optimal, 0 worsened, 0 no-move" in notes
    )


def _stage6_promotion_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "promotion_status": payload.get("promotion_status"),
        "promotion_status_semantics": payload.get("promotion_status_semantics"),
        "stage": payload.get("stage") or {},
        "guardrails": payload.get("guardrails") or [],
        "guardrail_semantics": payload.get("guardrail_semantics") or {},
    }


def _active_stack_paths(repo_root: Path) -> tuple[dict[str, Path], dict[str, Any]]:
    active = _load_optional_json(repo_root, ACTIVE_STACK)
    if active.get("status") != "retry1_protected_stage5_6_stack_adopted_manifest_only":
        return (
            {
                "stage6_candidate": STAGE6_CANDIDATE,
                "stage5_overlay_guard": STAGE5_OVERLAY_GUARD,
                "stage4_overlay_probe": STAGE4_OVERLAY_PROBE,
                "stage4_base_control": STAGE4_BASE_CONTROL,
                "stage6_promotion": STAGE6_PROMOTION,
            },
            {},
        )

    stack = active.get("active_protected_stack") or {}
    stage6 = stack.get("stage6_drive_overlay") or {}
    stage4_review = _load_optional_json(repo_root, RETRY1_STAGE4_REVIEW)
    stage4_sources = stage4_review.get("source_artifacts") or {}
    stage4_overlay = stage4_sources.get("stage4_overlay")
    paths = {
        "stage6_candidate": Path(stage6["stage6_validation"]),
        "stage5_overlay_guard": Path(stage6["stage5_guardrail"]),
        "stage4_overlay_probe": Path(stage4_overlay) if stage4_overlay else STAGE4_OVERLAY_PROBE,
        "stage4_base_control": Path(stage6["stage4_caveat_control"]),
        "stage6_promotion": Path(stage6["promotion_eval"]),
    }
    return paths, active


def _stage6_promotion_valid(promotion_summary: dict[str, Any]) -> bool:
    if promotion_summary.get("promotion_status") == "promoted":
        return True
    if (
        promotion_summary.get("promotion_status") == "overlay_only"
        and promotion_summary.get("promotion_status_semantics")
        == "overlay_only_due_to_guardrail_control_debt"
    ):
        stage = promotion_summary.get("stage") or {}
        guardrail_semantics = promotion_summary.get("guardrail_semantics") or {}
        conversion = guardrail_semantics.get("conversion_preservation") or []
        return bool(stage.get("passed")) and all(item.get("passed") is True for item in conversion)
    return False


def build_status(repo_root: Path) -> dict[str, Any]:
    notes = _load_optional_text(repo_root, HANDOFF_NOTES)
    active_paths, active_stack = _active_stack_paths(repo_root)
    stage1_manifest = _load_json(repo_root, STAGE1_MANIFEST)
    stage4_profile = _load_json(repo_root, STAGE4_PROFILE)
    stage5_profile = _load_json(repo_root, STAGE5_PROFILE)
    stage6_candidate = _load_json(repo_root, active_paths["stage6_candidate"])
    stage5_overlay_guard = _load_json(repo_root, active_paths["stage5_overlay_guard"])
    stage4_overlay_probe = _load_json(repo_root, active_paths["stage4_overlay_probe"])
    stage4_base_control = _load_json(repo_root, active_paths["stage4_base_control"])
    promotion = _load_json(repo_root, active_paths["stage6_promotion"])

    stage4_overlay_summary = _validation_summary(stage4_overlay_probe)
    stage4_base_summary = _validation_summary(stage4_base_control)
    stage4_overlay_playouts = stage4_overlay_summary["playouts"]
    stage4_base_playouts = stage4_base_summary["playouts"]
    stage4_caveat_reproduces_on_base = (
        stage4_overlay_playouts.get("max_plies", 0) > 0
        and stage4_overlay_playouts == stage4_base_playouts
    )

    stage4_mate = stage4_overlay_playouts.get("mate", 0)
    stage4_max_plies = stage4_overlay_playouts.get("max_plies", 0)
    active_stack_enabled = bool(active_stack)
    stage6_promotion_summary = _stage6_promotion_summary(promotion)
    stage6_status = (
        "active_retry1_overlay_solved_with_guardrail_control_debt"
        if active_stack_enabled
        else "promoted_overlay_solved_against_stage5_guardrail"
    )

    status = {
        "schema_version": "krk_protected_stage_status.v1",
        "causal_status": "non_causal_status_audit",
        "active_stack_artifact": str(ACTIVE_STACK) if active_stack_enabled else None,
        "active_stack_status": active_stack.get("status") if active_stack_enabled else "legacy_protected_stack",
        "protected_stack_reference_mode": (
            "retry1_manifest_active" if active_stack_enabled else "legacy_hardcoded_paths"
        ),
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(STAGE1_MANIFEST),
            str(STAGE4_PROFILE),
            str(STAGE5_PROFILE),
            str(active_paths["stage6_candidate"]),
            str(active_paths["stage5_overlay_guard"]),
            str(active_paths["stage4_overlay_probe"]),
            str(active_paths["stage4_base_control"]),
            str(active_paths["stage6_promotion"]),
            str(HANDOFF_NOTES),
        ],
        "stage_statuses": [
            {
                "stage": "stage1_backchain",
                "status": "protected_solved_local_regression",
                "solved_under_current_architecture": True,
                "scope": "local/backchain regression; not a complete KRK policy by itself",
                "evidence": {
                    "manifest": _manifest_summary(stage1_manifest),
                    "documented_500_sample_regression": _notes_stage1_500_present(notes),
                    "documented_500_sample_result": (
                        "500/500 improved, 500/500 optimal, 0 worsened, 0 no-move"
                    ),
                },
                "caveat": "Evidence is local/backchain-focused; Stage 1 is protected as a subskill.",
            },
            {
                "stage": "stage4_wrong_tempo",
                "status": "protected_profile_solved_with_overlay_guardrail_caveat",
                "solved_under_current_architecture": True,
                "scope": "wrong-tempo local/conversion profile; current overlay-control h40 caveat remains separate",
                "evidence": {
                    "profile_500_seed7_h40": _validation_summary(stage4_profile),
                    "overlay_probe_300_seed7_h40": stage4_overlay_summary,
                    "base_control_300_seed7_h40": stage4_base_summary,
                    "overlay_caveat_reproduces_on_base_control": stage4_caveat_reproduces_on_base,
                },
                "caveat": (
                    "The 500-sample handoff_composition_v1 profile is clean, but the later "
                    f"300-sample overlay/control guardrail has {stage4_mate} mate / {stage4_max_plies} max_plies on both "
                    "overlay and frozen Stage 5 base. This is not Stage 6 overlay interference; "
                    "it remains a candidate-generation/horizon guardrail diagnostic."
                ),
            },
            {
                "stage": "stage5_fence",
                "status": "protected_solved_conversion_profile",
                "solved_under_current_architecture": True,
                "scope": "protected Stage 5 fence/handoff provider pack",
                "evidence": {
                    "profile_1000_seed7_h40": _validation_summary(stage5_profile),
                    "stage6_overlay_guard_300_seed7_h40": _validation_summary(stage5_overlay_guard),
                },
                "caveat": "Opt-in experimental profile; default policy remains unchanged.",
            },
            {
                "stage": "stage6_drive_overlay",
                "status": stage6_status,
                "solved_under_current_architecture": True,
                "scope": "additive Stage 6 overlay on frozen Stage 5 provider pack",
                "evidence": {
                    "stage6_candidate_300_seed7_h40": _validation_summary(stage6_candidate),
                    "stage5_guardrail_300_seed7_h40": _validation_summary(stage5_overlay_guard),
                    "promotion_eval": stage6_promotion_summary,
                },
                "caveat": (
                    "Stage 6 is solved as an overlay, not as a monolithic replacement topology. "
                    "Use frozen-provider plus overlay composition for later stages. "
                    "If active retry1 is selected, Stage 5 conversion is preserved while local "
                    "reward/contract debt remains explicitly recorded as guardrail-control debt."
                ),
            },
        ],
        "summary": {
            "yes_protected_or_promoted": [
                "stage1_backchain",
                "stage4_wrong_tempo",
                "stage5_fence",
                "stage6_drive_overlay",
            ],
            "cleanest_solved_components": [
                "stage1_backchain",
                "stage5_fence",
                "stage6_drive_overlay",
            ],
            "solved_with_caveat": ["stage4_wrong_tempo"],
            "current_architecture_profile": "handoff_composition_v1",
            "stage6_overlay_status": stage6_status,
            "next_investigation_class": (
                "architecture-level sequence-policy or strategy-arbitration review; "
                "do not reopen Stage 7 micro-repairs without review"
            ),
        },
        "blocked_next_steps": [
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "monolithic_stage6_replacement",
            "stage7_runtime_micro_repair_without_architecture_review",
        ],
    }
    validate_status(status)
    return status


def validate_status(status: dict[str, Any]) -> None:
    if status.get("causal_status") != "non_causal_status_audit":
        raise ValueError("protected stage status must remain non-causal")
    for flag in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if status.get(flag) is not False:
            raise ValueError(f"{flag} must be false")
    stages = {item.get("stage"): item for item in status.get("stage_statuses") or []}
    required = {
        "stage1_backchain",
        "stage4_wrong_tempo",
        "stage5_fence",
        "stage6_drive_overlay",
    }
    if set(stages) != required:
        raise ValueError(f"unexpected protected stage set: {set(stages)}")
    if not _stage6_promotion_valid(stages["stage6_drive_overlay"]["evidence"]["promotion_eval"]):
        raise ValueError("Stage 6 overlay promotion artifact must remain promoted or active retry1 overlay-only with conversion preservation")
    if not stages["stage4_wrong_tempo"]["evidence"][
        "overlay_caveat_reproduces_on_base_control"
    ]:
        raise ValueError("Stage 4 caveat must reproduce on the frozen base control")


def _format_playouts(summary: dict[str, Any]) -> str:
    playouts = summary.get("playouts") or {}
    if not playouts:
        return "no playout counts"
    return ", ".join(f"{key}: {value}" for key, value in sorted(playouts.items()))


def render_markdown(status: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Stage Status",
        "",
        "This is a replay-free, non-causal status audit of the protected KRK stages. "
        "It does not change runtime behavior, defaults, topology, training, or promotion state.",
        "",
        "## Active Stack",
        "",
        f"- Reference mode: `{status.get('protected_stack_reference_mode')}`",
        f"- Active stack status: `{status.get('active_stack_status')}`",
        f"- Active stack artifact: `{status.get('active_stack_artifact')}`",
        "",
        "## Short Answer",
        "",
        "- Stage 1 is solved/protected as a backchain/local regression subskill.",
        "- Stage 5 is solved/protected as the current fence/handoff provider pack.",
        "- Stage 6 is solved/promoted as an additive overlay on frozen Stage 5 providers.",
        "- Stage 4 is solved in the clean 500-sample `handoff_composition_v1` profile, "
        "but carries a separate 300-sample h40 overlay-control caveat that reproduces "
        "identically on the frozen Stage 5 base.",
        "",
        "So the current architecture has validated/protected Stages 1, 4, 5, and 6, "
        "but Stage 4 should not be described as an unconditional strict h40 conversion "
        "guarantee under every guardrail configuration.",
        "",
        "## Stage Details",
        "",
    ]
    for item in status["stage_statuses"]:
        lines.extend(
            [
                f"### {item['stage']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Solved under current architecture: `{item['solved_under_current_architecture']}`",
                f"- Scope: {item['scope']}",
                f"- Caveat: {item['caveat']}",
                "",
            ]
        )
        evidence = item["evidence"]
        for key, value in evidence.items():
            if isinstance(value, dict) and "playouts" in value:
                lines.append(f"- `{key}`: total `{value.get('total')}`, {_format_playouts(value)}, "
                             f"shadow `{value.get('shadow_candidate_count')}`")
            elif isinstance(value, dict) and key == "promotion_eval":
                lines.append(
                    f"- `{key}`: promotion_status `{value.get('promotion_status')}`, "
                    f"semantics `{value.get('promotion_status_semantics')}`"
                )
            elif isinstance(value, dict) and key == "manifest":
                formal = value.get("formal_validation") or {}
                lines.append(
                    f"- `{key}`: formal validation `{formal.get('validated')}` "
                    f"({formal.get('nodes')} nodes, {formal.get('edges')} edges)"
                )
            else:
                lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    lines.extend(
        [
            "## Current Boundary",
            "",
            "- `handoff_composition_v1` remains an opt-in experimental KRK profile.",
            "- Stage 6 must remain an overlay, not a monolithic replacement for validated lower providers.",
            "- Stage 7 remains `local_valid_composition_quarantined` and must not be promoted.",
            "- Stage 8 remains blocked until an explicit architecture decision allows it.",
            "",
            "## Next Investigation Class",
            "",
            status["summary"]["next_investigation_class"],
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(status: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    json_path = report_root / "krk_protected_stage_status.json"
    md_path = report_root / "krk_protected_stage_status.md"
    json_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(status), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    status = build_status(repo_root)
    write_outputs(status, report_root)
    print(json.dumps(status["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
