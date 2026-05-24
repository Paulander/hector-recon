#!/usr/bin/env python3
"""Verify the clean KRK retrain package before any long run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXEC_MANIFEST = Path("reports/krk_clean_retrain_execution_manifest_v0.json")
COMPOSE_MANIFEST = Path("reports/krk_stage6_overlay_compose_manifest_v0.json")
OUT_JSON = Path("reports/krk_clean_retrain_preflight_v0.json")
OUT_MD = Path("reports/krk_clean_retrain_preflight_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _all_outputs(manifest: dict[str, Any]) -> list[str]:
    outputs: list[str] = []
    for step in manifest.get("steps") or []:
        if isinstance(step, dict):
            outputs.extend(str(item) for item in step.get("expected_outputs") or [])
    return outputs


def _command_mentions_forbidden(command: list[str]) -> list[str]:
    text = " ".join(str(part) for part in command)
    forbidden = []
    for needle in [
        "stage7",
        "stage8",
        "--enable-krk-candidate-generation-refresh",
        "--enable-krk-exact-trace-enrichment",
        "tablebase",
        "dtm",
    ]:
        if needle in text.lower():
            forbidden.append(needle)
    return forbidden


def build_payload() -> dict[str, Any]:
    execution = _load(EXEC_MANIFEST)
    compose = _load(COMPOSE_MANIFEST)
    output_root = Path(str(execution.get("checkpoint_root") or ""))
    outputs = _all_outputs(execution)
    output_collisions = [path for path in outputs if (ROOT / path).exists()]
    protected_overwrites = [
        path for path in outputs if not path.startswith(str(output_root))
    ]
    command_violations: list[dict[str, Any]] = []
    for step in execution.get("steps") or []:
        if not isinstance(step, dict):
            continue
        for command in step.get("commands") or []:
            if not isinstance(command, list):
                continue
            forbidden = _command_mentions_forbidden(command)
            if forbidden:
                command_violations.append(
                    {
                        "step_id": step.get("step_id"),
                        "command": command,
                        "forbidden_mentions": forbidden,
                    }
                )
    compose_outputs = [
        str(value) for value in (compose.get("fresh_outputs") or {}).values()
    ]
    compose_output_collisions = [path for path in compose_outputs if (ROOT / path).exists()]
    stage_chain = [step.get("step_id") for step in execution.get("steps") or []]
    required_chain = [
        "stage2a_edge_trap_close",
        "stage2b_enemy_between",
        "stage4_wrong_tempo",
        "stage5_fence_handoff",
        "stage6_drive_overlay_candidate",
        "stage6_overlay_composition_review",
    ]
    blockers = []
    if output_collisions:
        blockers.append("fresh_execution_output_collision")
    if compose_output_collisions:
        blockers.append("fresh_compose_output_collision")
    if protected_overwrites:
        blockers.append("expected_output_outside_fresh_root")
    if command_violations:
        blockers.append("forbidden_command_mentions")
    if stage_chain != required_chain:
        blockers.append("stage_chain_order_mismatch")
    if (execution.get("decision") or {}).get("full_run_authorized_by_this_manifest"):
        blockers.append("execution_manifest_unexpectedly_authorizes_full_run")
    if (compose.get("decision") or {}).get("compose_run_authorized_by_this_manifest"):
        blockers.append("compose_manifest_unexpectedly_authorizes_run")
    safe_to_request_run_review = not blockers
    return {
        "schema_version": "krk_clean_retrain_preflight.v0",
        "causal_status": "preflight_only_no_training",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(EXEC_MANIFEST), str(COMPOSE_MANIFEST)],
        "summary": {
            "checkpoint_root": str(output_root),
            "stage_chain": stage_chain,
            "execution_output_count": len(outputs),
            "execution_output_collision_count": len(output_collisions),
            "compose_output_count": len(compose_outputs),
            "compose_output_collision_count": len(compose_output_collisions),
            "protected_overwrite_count": len(protected_overwrites),
            "command_violation_count": len(command_violations),
            "blocker_count": len(blockers),
        },
        "output_collisions": output_collisions,
        "compose_output_collisions": compose_output_collisions,
        "protected_overwrites": protected_overwrites,
        "command_violations": command_violations,
        "blockers": blockers,
        "decision": {
            "status": (
                "clean_retrain_preflight_ready_for_run_review"
                if safe_to_request_run_review
                else "clean_retrain_preflight_blocked"
            ),
            "safe_to_request_run_review": safe_to_request_run_review,
            "training_started": False,
            "full_run_authorized_by_this_artifact": False,
            "runtime_selector_allowed": False,
            "recommended_next_step": (
                "request_explicit_run_approval_or_create_smoke_run_manifest"
                if safe_to_request_run_review
                else "fix_clean_retrain_manifest_blockers"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Clean Retrain Preflight v0",
        "",
        "This preflight validates the clean retrain manifest package without running training.",
        "",
        "## Decision",
        "",
    ]
    for key, value in payload["decision"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Blockers", ""])
    if payload["blockers"]:
        for blocker in payload["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "No training, composition, topology write, selector, Stage 7 promotion, or Stage 8 training was performed.",
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
