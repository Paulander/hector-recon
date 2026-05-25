#!/usr/bin/env python3
"""Adopt retry1 as the active protected Stage 5/6 stack by manifest.

This is rollback-aware and non-destructive: it writes active-stack and
post-adoption validation reports, but does not copy, delete, or overwrite
snapshot files.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PACKET = Path("reports/krk_clean_retrain_retry1_clean_stack_replacement_review_packet_v0.json")
SNAPSHOT_MANIFEST = Path("reports/krk_clean_retrain_retry1_protected_stack_snapshot_manifest_v0.json")
STAGE4_REVIEW = Path("reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json")
PRESERVATION_CHECKS = Path("reports/krk_clean_retrain_retry1_preservation_checks_v0.json")
ACTIVE_JSON = Path("reports/krk_active_protected_stack_v0.json")
ACTIVE_MD = Path("reports/krk_active_protected_stack_v0.md")
VALIDATION_JSON = Path("reports/krk_clean_stack_post_replacement_validation_v0.json")
VALIDATION_MD = Path("reports/krk_clean_stack_post_replacement_validation_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _load_artifact(path_str: str) -> dict[str, Any]:
    return _load(Path(path_str))


def _playouts(path_str: str) -> dict[str, int]:
    payload = _load_artifact(path_str)
    return {str(k): int(v) for k, v in (payload.get("playouts") or {}).items()}


def _shadow_count(path_str: str) -> int:
    payload = _load_artifact(path_str)
    if payload.get("shadow_candidate_count") is not None:
        return int(payload.get("shadow_candidate_count") or 0)
    if isinstance(payload.get("shadow_candidates"), list):
        return len(payload["shadow_candidates"])
    return 0


def _common_invariants(*, adopted: bool) -> dict[str, bool]:
    return {
        "active_stack_reference_updated": adopted,
        "files_copied_or_replaced": False,
        "rollback_paths_preserved": True,
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion": False,
        "stage8_training": False,
    }


def build_active_stack(now: str) -> dict[str, Any]:
    review = _load(REVIEW_PACKET)
    manifest = _load(SNAPSHOT_MANIFEST)
    decision = review.get("decision") or {}
    if not decision.get("replacement_review_ready"):
        raise ValueError("replacement review is not ready")
    if decision.get("implementation_allowed_by_this_packet") is not False:
        raise ValueError("review packet boundary must remain non-implementing")
    if not manifest.get("decision", {}).get("all_referenced_paths_exist"):
        raise ValueError("snapshot manifest paths must exist")

    return {
        "schema_version": "krk_active_protected_stack.v0",
        "created_at": now,
        "status": "retry1_protected_stage5_6_stack_adopted_manifest_only",
        "adoption_scope": {
            "stage5": "retry1_fence_handoff",
            "stage6": "retry1_drive_overlay_composed",
            "stage4": "unchanged_known_caveat_guardrail",
            "stage7": "unchanged_quarantined_held_out",
            "stage8": "unchanged_blocked",
        },
        "approval_record": {
            "approval_kind": "user_explicit_rollback_aware_adoption",
            "approval_date": now,
            "approval_text_summary": "User approved continuing with rollback-aware retry1 adoption path.",
        },
        "source_artifacts": [str(REVIEW_PACKET), str(SNAPSHOT_MANIFEST)],
        "active_protected_stack": manifest["retry1_candidate_stack"],
        "rollback_protected_stack": manifest["current_protected_stack"],
        "decision": {
            "clean_stack_adopted": True,
            "adoption_mechanism": "tracked_active_stack_manifest",
            "filesystem_snapshots_replaced": False,
            "post_adoption_validation_required": True,
            "recommended_next_step": "run_or_record_post_adoption_validation",
        },
        "rollback_requirements": manifest.get("rollback_requirements") or [],
        "invariants": _common_invariants(adopted=True),
    }


def build_validation(now: str, active: dict[str, Any]) -> dict[str, Any]:
    stack = active["active_protected_stack"]
    stage6_path = stack["stage6_drive_overlay"]["stage6_validation"]
    stage5_path = stack["stage6_drive_overlay"]["stage5_guardrail"]
    stage4_review = _load(STAGE4_REVIEW)
    preservation = _load(PRESERVATION_CHECKS)
    stage6_playouts = _playouts(stage6_path)
    stage5_playouts = _playouts(stage5_path)
    validation_passed = (
        stage6_playouts.get("mate") == 300
        and stage6_playouts.get("max_plies", 0) == 0
        and _shadow_count(stage6_path) == 0
        and stage5_playouts.get("mate") == 300
        and stage5_playouts.get("max_plies", 0) == 0
        and _shadow_count(stage5_path) == 0
        and stage4_review.get("decision", {}).get("stage4_caveat_reproduces_in_base_control")
        is True
        and preservation.get("decision", {}).get("m1_m4_preservation_passed") is True
        and preservation.get("decision", {}).get("kpk_kqk_bridge_preservation_passed") is True
    )
    return {
        "schema_version": "krk_clean_stack_post_replacement_validation.v0",
        "created_at": now,
        "status": (
            "clean_stack_adopted_and_validated"
            if validation_passed
            else "clean_stack_adopted_validation_failed"
        ),
        "source_artifacts": [
            str(ACTIVE_JSON),
            str(STAGE4_REVIEW),
            str(PRESERVATION_CHECKS),
            stage6_path,
            stage5_path,
        ],
        "validation": {
            "stage5_conversion_preservation_guardrail": {
                "path": stage5_path,
                "playouts": stage5_playouts,
                "shadow_candidate_count": _shadow_count(stage5_path),
                "passed": stage5_playouts.get("mate") == 300
                and stage5_playouts.get("max_plies", 0) == 0
                and _shadow_count(stage5_path) == 0,
            },
            "stage6_drive_h40_historical_bonus": {
                "path": stage6_path,
                "playouts": stage6_playouts,
                "shadow_candidate_count": _shadow_count(stage6_path),
                "passed": stage6_playouts.get("mate") == 300
                and stage6_playouts.get("max_plies", 0) == 0
                and _shadow_count(stage6_path) == 0,
            },
            "stage4_caveat_control_no_regression": {
                "path": str(STAGE4_REVIEW),
                "passed": stage4_review.get("decision", {}).get(
                    "stage4_caveat_reproduces_in_base_control"
                )
                is True
                and stage4_review.get("decision", {}).get("stage4_overlay_regressed_vs_base_control")
                is False,
            },
            "m1_m4_preservation": {
                "path": str(PRESERVATION_CHECKS),
                "passed": preservation.get("decision", {}).get("m1_m4_preservation_passed")
                is True,
            },
            "kpk_kqk_bridge_preservation": {
                "path": str(PRESERVATION_CHECKS),
                "passed": preservation.get("decision", {}).get(
                    "kpk_kqk_bridge_preservation_passed"
                )
                is True,
            },
        },
        "decision": {
            "clean_stack_adopted_and_validated": validation_passed,
            "stage7_status": "unchanged_quarantined_held_out",
            "stage8_status": "unchanged_blocked",
            "recommended_next_step": "continue_stage4_observation_scope_or_broader_stage7_sequence_control",
        },
        "invariants": _common_invariants(adopted=True),
    }


def render_active_md(payload: dict[str, Any]) -> str:
    return f"""# KRK Active Protected Stack v0

Status: `{payload['status']}`

## Decision

- Clean stack adopted: `{payload['decision']['clean_stack_adopted']}`
- Adoption mechanism: `{payload['decision']['adoption_mechanism']}`
- Filesystem snapshots replaced: `{payload['decision']['filesystem_snapshots_replaced']}`
- Post-adoption validation required: `{payload['decision']['post_adoption_validation_required']}`

## Scope

- Stage 5: `{payload['adoption_scope']['stage5']}`
- Stage 6: `{payload['adoption_scope']['stage6']}`
- Stage 4: `{payload['adoption_scope']['stage4']}`
- Stage 7: `{payload['adoption_scope']['stage7']}`
- Stage 8: `{payload['adoption_scope']['stage8']}`

## Boundary

This is a tracked active-stack reference update. It does not copy, delete, or overwrite snapshot files; rollback paths are preserved.
"""


def render_validation_md(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Clean Stack Post-Replacement Validation v0",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in payload["validation"].items():
        lines.append(f"- `{key}`: passed=`{value['passed']}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Clean stack adopted and validated: `{payload['decision']['clean_stack_adopted_and_validated']}`",
            f"- Stage 7 status: `{payload['decision']['stage7_status']}`",
            f"- Stage 8 status: `{payload['decision']['stage8_status']}`",
            f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
            "",
            "## Boundary",
            "",
            "No runtime behavior, default, topology mutation, Stage 7 promotion, or Stage 8 training is authorized by this validation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    active = build_active_stack(now)
    validation = build_validation(now, active)
    (ROOT / ACTIVE_JSON).write_text(json.dumps(active, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / ACTIVE_MD).write_text(render_active_md(active), encoding="utf-8")
    (ROOT / VALIDATION_JSON).write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / VALIDATION_MD).write_text(render_validation_md(validation), encoding="utf-8")
    print(json.dumps({"status": validation["status"], "json_output": str(VALIDATION_JSON)}, indent=2))


if __name__ == "__main__":
    main()
