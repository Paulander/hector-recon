#!/usr/bin/env python3
"""Integrate approved Stage 7 diverse-clean sampling outputs if present.

This script is intentionally passive: it reads the reviewed diverse-clean
sampling manifest and any already-created output JSON files, but it never runs
label jobs. It reports whether the Stage 7 clean success-control gap is closed
once those outputs exist.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
BASE_CONTROLS = ROOT / "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json"
OUTPUT_VALIDATION = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
)
OUTPUT_JSON = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
OUTPUT_MD = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.md"

SCHEMA_VERSION = "stage7_diverse_clean_sampling_integration.v0"

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_output_validation() -> dict[str, Any] | None:
    path = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
    if not path.exists():
        return None
    data = _load(path)
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _state_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}.{digest}"


def _term_key(terms: dict[str, Any]) -> tuple[str, str] | None:
    fen = terms.get("fen")
    move = terms.get("move")
    if not fen or not move:
        return None
    return str(fen), str(move)


def _best_move_for_provider(terms: dict[str, Any], provider: str | None) -> str | None:
    if not provider:
        return None
    skills = terms.get("successor_skills")
    if not isinstance(skills, dict):
        return None
    provider_payload = skills.get(provider)
    if not isinstance(provider_payload, dict):
        return None
    move = provider_payload.get("best_move")
    return str(move) if move else None


def _recover_controls_from_output(job: dict[str, Any], payload: dict[str, Any]) -> tuple[list[dict[str, Any]], Counter[str]]:
    skipped = Counter()
    companion_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "post_opponent_reply":
            continue
        terms = packet.get("evidence_terms") or {}
        if not isinstance(terms, dict) or terms.get("label") != "box_shrink":
            continue
        key = _term_key(terms)
        if key is not None:
            companion_by_key[key] = terms

    controls = []
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "playout_summary":
            continue
        terms = packet.get("evidence_terms") or {}
        if not isinstance(terms, dict) or terms.get("label") != "box_shrink":
            continue
        key = _term_key(terms)
        if key is None:
            skipped["missing_fen_or_move"] += 1
            continue
        result = terms.get("playout_result")
        max_plies = terms.get("max_plies")
        plies = terms.get("plies")
        if result not in {"mate", "max_plies", "draw"}:
            skipped["unsupported_result"] += 1
            continue
        if isinstance(max_plies, int) and max_plies > 40:
            skipped["horizon_above_h40"] += 1
            continue
        if result == "mate" and isinstance(plies, int) and plies > 40:
            skipped["mate_after_h40"] += 1
            continue
        if result != "mate" and max_plies != 40:
            skipped["non_mate_not_h40"] += 1
            continue
        companion = companion_by_key.get(key, {})
        selected_provider = companion.get("successor_selected_skill")
        controls.append(
            {
                "schema_version": "stage7_diverse_clean_integrated_control.v0",
                "state_id": _state_id(
                    "diverse_clean",
                    key[0],
                    key[1],
                    result,
                    selected_provider,
                    plies,
                    job.get("job_id"),
                ),
                "fen": key[0],
                "move_uci": key[1],
                "selected_provider": selected_provider,
                "selected_provider_move": _best_move_for_provider(
                    companion,
                    str(selected_provider) if selected_provider else None,
                ),
                "result": result,
                "control_role": "clean_sequence_success_control"
                if result == "mate"
                else "clean_sequence_hard_negative",
                "plies": plies,
                "max_plies": max_plies,
                "semantic_alignment_status": terms.get("semantic_alignment_status"),
                "source_job_id": job.get("job_id"),
                "source_artifact": job.get("json_output"),
                "source_stage_names": job.get("source_stage_names") or [],
                "stage7_heldout_challenge": True,
                "stage7_training_row": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "causal_status": "non_causal_diverse_clean_label_integration",
            }
        )
    return controls, skipped


def build_payload(
    *,
    manifest: dict[str, Any] | None = None,
    base_controls: dict[str, Any] | None = None,
    output_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    base_controls = base_controls or _load(BASE_CONTROLS)
    output_validation = output_validation if output_validation is not None else _load_output_validation()
    jobs = manifest.get("jobs") or []
    base_role_counts = Counter(
        row.get("control_role") for row in base_controls.get("controls") or []
    )
    success_required = int(
        base_controls.get("acceptance", {}).get("clean_sequence_success_controls_required", 5)
    )
    failure_required = int(
        base_controls.get("acceptance", {}).get("clean_sequence_hard_negatives_required", 5)
    )
    validation_status = None
    validation_blocks_integration = False
    if output_validation is not None:
        validation_status = (output_validation.get("decision") or {}).get("status")
        validation_blocks_integration = (
            validation_status
            == "stage7_diverse_clean_sampling_outputs_invalid_block_integration"
        )
    if validation_blocks_integration:
        checks = output_validation.get("output_checks")
        output_checks = checks if isinstance(checks, list) else []
        return {
            "schema_version": SCHEMA_VERSION,
            "causal_status": "non_causal_post_label_integration",
            **COMMON_FALSE_FLAGS,
            "source_artifacts": [
                "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json",
                "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
                "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json",
            ],
            "summary": {
                "job_count": len(jobs),
                "outputs_present_count": output_validation.get("summary", {}).get(
                    "output_exists_count", 0
                ),
                "all_outputs_present": output_validation.get("summary", {}).get(
                    "all_outputs_present", False
                ),
                "new_control_count": 0,
                "new_role_counts": {},
                "base_success_controls": base_role_counts.get(
                    "clean_sequence_success_control", 0
                ),
                "base_failure_controls": base_role_counts.get(
                    "clean_sequence_hard_negative", 0
                ),
                "combined_success_controls": base_role_counts.get(
                    "clean_sequence_success_control", 0
                ),
                "combined_failure_controls": base_role_counts.get(
                    "clean_sequence_hard_negative", 0
                ),
                "success_controls_required": success_required,
                "failure_controls_required": failure_required,
                "success_controls_met": base_role_counts.get(
                    "clean_sequence_success_control", 0
                )
                >= success_required,
                "failure_controls_met": base_role_counts.get(
                    "clean_sequence_hard_negative", 0
                )
                >= failure_required,
                "skipped_counts": {},
                "validation_status": validation_status,
                "validation_blocks_integration": True,
                "stage7_training_row_count": 0,
                "selector_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            },
            "output_checks": output_checks,
            "new_controls": [],
            "decision": {
                "status": "stage7_diverse_clean_sampling_integration_blocked_invalid_outputs",
                "recommended_next_step": "inspect_invalid_stage7_diverse_clean_outputs_before_integration",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
        }

    output_checks = []
    new_controls = []
    skipped = Counter()
    seen_keys: set[tuple[str, str, str]] = {
        (control["fen"], control["move_uci"], control["result"])
        for control in base_controls.get("controls") or []
        if control.get("fen") and control.get("move_uci") and control.get("result")
    }
    for job in jobs:
        output = job.get("json_output")
        output_path = ROOT / str(output) if output else None
        exists = bool(output_path and output_path.exists())
        parsed_count = 0
        if exists and output_path is not None:
            rows, row_skipped = _recover_controls_from_output(job, _load(output_path))
            skipped.update(row_skipped)
            parsed_count = len(rows)
            for control in rows:
                key = (control["fen"], control["move_uci"], control["result"])
                if key in seen_keys:
                    skipped["duplicate_base_or_diverse_control"] += 1
                    continue
                seen_keys.add(key)
                new_controls.append(control)
        output_checks.append(
            {
                "job_id": job.get("job_id"),
                "json_output": output,
                "output_exists": exists,
                "parsed_control_count": parsed_count,
                "stage7_training_row": False,
            }
        )

    new_role_counts = Counter(row.get("control_role") for row in new_controls)
    combined_success = int(base_role_counts.get("clean_sequence_success_control", 0)) + int(
        new_role_counts.get("clean_sequence_success_control", 0)
    )
    combined_failure = int(base_role_counts.get("clean_sequence_hard_negative", 0)) + int(
        new_role_counts.get("clean_sequence_hard_negative", 0)
    )
    success_met = combined_success >= success_required
    failure_met = combined_failure >= failure_required
    all_outputs_present = all(row["output_exists"] for row in output_checks)
    any_outputs_present = any(row["output_exists"] for row in output_checks)
    status = (
        "stage7_diverse_clean_sampling_integration_success_controls_met"
        if success_met and failure_met and any_outputs_present
        else "stage7_diverse_clean_sampling_outputs_pending"
        if not any_outputs_present
        else "stage7_diverse_clean_sampling_integration_gap_still_open"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_post_label_integration",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json",
            "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
        ],
        "summary": {
            "job_count": len(jobs),
            "outputs_present_count": sum(1 for row in output_checks if row["output_exists"]),
            "all_outputs_present": all_outputs_present,
            "new_control_count": len(new_controls),
            "new_role_counts": dict(new_role_counts),
            "base_success_controls": base_role_counts.get("clean_sequence_success_control", 0),
            "base_failure_controls": base_role_counts.get("clean_sequence_hard_negative", 0),
            "combined_success_controls": combined_success,
            "combined_failure_controls": combined_failure,
            "success_controls_required": success_required,
            "failure_controls_required": failure_required,
            "success_controls_met": success_met,
            "failure_controls_met": failure_met,
            "skipped_counts": dict(skipped),
            "validation_status": validation_status,
            "validation_blocks_integration": False,
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "output_checks": output_checks,
        "new_controls": new_controls,
        "decision": {
            "status": status,
            "recommended_next_step": (
                "refresh_sequence_policy_inputs_with_integrated_stage7_controls"
                if success_met and failure_met and any_outputs_present
                else "run_approved_diverse_clean_sampling_jobs"
                if not any_outputs_present
                else "review_remaining_stage7_success_gap"
            ),
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# Stage 7 Diverse Clean Sampling Integration v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This artifact integrates diverse-clean label outputs only if they already exist. It does not run labels, train, route, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Outputs", ""])
    for row in payload["output_checks"]:
        lines.append(
            f"- `{row['job_id']}` output_exists=`{row['output_exists']}` parsed_controls=`{row['parsed_control_count']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "outputs_present_count": payload["summary"]["outputs_present_count"],
                "combined_success_controls": payload["summary"]["combined_success_controls"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
