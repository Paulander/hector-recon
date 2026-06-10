#!/usr/bin/env python3
"""Plan non-causal structural-candidate evaluation phases.

This is a Growth Governor tool. It consumes StructuralCandidate artifacts and
candidate-update evidence, then emits a bounded evaluation plan. It does not
change runtime routing, train weights, mutate topology, or promote candidates.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_RULES = {
    "schema_version": "growth_governor_rules.v0",
    "max_active_candidates_per_stage": 3,
    "max_promoted_overlays_per_stage_before_settling": 1,
    "require_candidate_resolution_before_next_overlay": True,
    "block_growth_if_guardrails_regress": True,
    "prefer_settling_if_conversion_rate_improving": True,
    "require_repeated_failure_family_before_growth": True,
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sandbox_smoke_summary(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {"available": False}
    role_met = 0
    role_selected = 0
    stage0_selected_with_role = 0
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "post_opponent_reply":
            continue
        evidence = packet.get("evidence_terms")
        if not isinstance(evidence, dict):
            continue
        licenses = evidence.get("visible_successor_provider_licenses")
        if not isinstance(licenses, dict):
            continue
        drive = licenses.get("krk.drive_to_edge")
        if not isinstance(drive, dict):
            continue
        role = drive.get("krk.box_shrink_to_drive_repair")
        if not isinstance(role, dict) or not role.get("contract_met"):
            continue
        role_met += 1
        selected = evidence.get("successor_selected_skill")
        if selected == "krk.drive_to_edge":
            role_selected += 1
        if selected == "krk.stage0_basin":
            stage0_selected_with_role += 1
    return {
        "available": True,
        "total": int(payload.get("total", 0) or 0),
        "playouts": payload.get("playouts") or {},
        "shadow_candidate_count": int(payload.get("shadow_candidate_count", 0) or 0),
        "role_contract_met_count": role_met,
        "role_selected_count": role_selected,
        "stage0_selected_with_role_count": stage0_selected_with_role,
    }


def _candidate_by_id(candidate_set: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for candidate in candidate_set.get("candidates") or []:
        if isinstance(candidate, dict) and candidate.get("candidate_id"):
            result[str(candidate["candidate_id"])] = candidate
    return result


def _plan_for_update(update: dict[str, Any], sandbox_summary: dict[str, Any]) -> dict[str, Any]:
    role = str(update.get("candidate_role") or "unknown")
    labels = list((update.get("topology_weight_diagnosis") or {}).get("diagnostic_labels") or [])
    status = str(update.get("status") or "unknown")
    support = int(update.get("support", 0) or 0)
    base = {
        "candidate_role": role,
        "input_status": status,
        "support": support,
        "diagnostic_labels": labels,
        "causal_status": "non_causal",
        "evaluation_phase": "phase_0_static_sanity",
        "governor_decision": "settling",
        "next_action": "collect_more_evidence",
        "blocked_reasons": [],
        "required_probes": [],
        "guardrails": [
            "stage7_box_shrink_target",
            "stage6_drive_overlay",
            "stage5_fence",
            "stage1_backchain",
            "krk_entry",
            "m1_m4_preservation",
        ],
    }

    if role == "krk.box_shrink_to_drive_repair":
        base["evaluation_phase"] = "phase_3_bounded_plasticity_warmup"
        base["governor_decision"] = "needs_more_weight_training"
        base["next_action"] = "run_candidate_local_m3_warmup_probe"
        base["required_probes"] = [
            "candidate_local_m3_only",
            "frozen_protected_providers",
            "stage7_target_smoke",
            "protected_guardrails",
        ]
        if sandbox_summary.get("available"):
            base["sandbox_smoke"] = {
                "role_contract_met_count": sandbox_summary.get("role_contract_met_count", 0),
                "role_selected_count": sandbox_summary.get("role_selected_count", 0),
                "stage0_selected_with_role_count": sandbox_summary.get("stage0_selected_with_role_count", 0),
                "playouts": sandbox_summary.get("playouts", {}),
                "shadow_candidate_count": sandbox_summary.get("shadow_candidate_count", 0),
            }
            if (
                sandbox_summary.get("role_contract_met_count", 0) > 0
                and sandbox_summary.get("role_selected_count", 0) == 0
            ):
                base["diagnostic_labels"] = sorted(set(labels + ["topology_present_untrained", "parameter_miscalibrated"]))
    elif role == "krk.box_shrink_post_reply_continuation":
        base["evaluation_phase"] = "phase_2_forced_oracle_probe"
        base["governor_decision"] = "growth_blocked_by_cooldown"
        base["next_action"] = "run_targeted_legal_first_or_longer_horizon_sweep"
        base["blocked_reasons"] = ["existing_provider_capacity_inconclusive"]
        base["required_probes"] = [
            "targeted_legal_first_filtered",
            "longer_horizon_for_unresolved_families",
        ]
    elif role == "krk.stage0_basin_after_box_shrink":
        base["evaluation_phase"] = "phase_1_frozen_weight_probe"
        base["governor_decision"] = "growth_blocked_by_guardrail"
        base["next_action"] = "do_not_sandbox_as_default_continuation"
        base["blocked_reasons"] = ["negative_counterfactual_evidence"]
    elif "counterfactual_supported" in status:
        base["evaluation_phase"] = "phase_3_bounded_plasticity_warmup"
        base["governor_decision"] = "needs_more_weight_training"
        base["next_action"] = "run_candidate_local_m3_warmup_probe"
        base["required_probes"] = ["candidate_local_m3_only", "protected_guardrails"]
    return base


def plan_candidate_evaluation(
    *,
    candidates_path: Path,
    counterfactual_update_path: Path,
    sandbox_smoke_path: Path | None = None,
) -> dict[str, Any]:
    candidate_set = _load_json(candidates_path)
    update = _load_json(counterfactual_update_path)
    sandbox_summary = _sandbox_smoke_summary(_load_json(sandbox_smoke_path) if sandbox_smoke_path else None)
    candidates = _candidate_by_id(candidate_set)
    candidate_count = len(candidates)
    governor_status_counts = Counter(
        str(candidate.get("governor_status") or "settling")
        for candidate in candidates.values()
    )
    active_limit = int(DEFAULT_RULES["max_active_candidates_per_stage"])
    active_limit_blocked = candidate_count > active_limit
    role_plans = [
        _plan_for_update(item, sandbox_summary)
        for item in update.get("candidate_updates") or []
        if isinstance(item, dict)
    ]
    if active_limit_blocked:
        for plan in role_plans:
            plan["governor_decision"] = "growth_blocked_by_active_candidate_limit"
            plan.setdefault("blocked_reasons", []).append("active_candidate_limit_exceeded")

    recommended = "run_candidate_local_m3_warmup_probe"
    if active_limit_blocked:
        recommended = "resolve_existing_candidates_before_new_growth"
    elif any(plan["candidate_role"] == "krk.box_shrink_to_drive_repair" for plan in role_plans):
        recommended = "bounded_m3_warmup_for_box_shrink_to_drive_repair"

    return {
        "schema_version": "growth_governor_evaluation_plan.v1",
        "causal_status": "non_causal",
        "candidate_source": str(candidates_path),
        "counterfactual_update_source": str(counterfactual_update_path),
        "sandbox_smoke_source": str(sandbox_smoke_path) if sandbox_smoke_path else None,
        "rules": DEFAULT_RULES,
        "candidate_count": candidate_count,
        "governor_status_counts": dict(governor_status_counts),
        "sandbox_smoke_summary": sandbox_summary,
        "role_plans": role_plans,
        "recommended_next_action": recommended,
        "hard_blocks": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_enable_stage7_repair_by_default",
            "do_not_make_packets_stats_or_candidates_causal",
        ],
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Growth Governor Evaluation Plan",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Candidate count: `{payload['candidate_count']}`",
        f"Recommended next action: `{payload['recommended_next_action']}`",
        "",
        "## Governor Status Counts",
        "",
    ]
    for key, value in sorted((payload.get("governor_status_counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Role Plans", ""])
    for plan in payload.get("role_plans") or []:
        lines.append(f"### {plan.get('candidate_role')}")
        lines.append("")
        lines.append(f"- Decision: `{plan.get('governor_decision')}`")
        lines.append(f"- Phase: `{plan.get('evaluation_phase')}`")
        lines.append(f"- Next action: `{plan.get('next_action')}`")
        if plan.get("diagnostic_labels"):
            labels = ", ".join(f"`{item}`" for item in plan["diagnostic_labels"])
            lines.append(f"- Labels: {labels}")
        if plan.get("blocked_reasons"):
            blocked = ", ".join(f"`{item}`" for item in plan["blocked_reasons"])
            lines.append(f"- Blocked reasons: {blocked}")
        lines.append("")
    lines.extend(["## Hard Blocks", ""])
    for item in payload.get("hard_blocks") or []:
        lines.append(f"- `{item}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan structural candidate evaluation phases")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--counterfactual-update", type=Path, required=True)
    parser.add_argument("--sandbox-smoke", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = plan_candidate_evaluation(
        candidates_path=args.candidates,
        counterfactual_update_path=args.counterfactual_update,
        sandbox_smoke_path=args.sandbox_smoke,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        _write_markdown(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
