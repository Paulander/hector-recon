#!/usr/bin/env python3
"""Summarize Stage 7 counterfactual evidence for structural candidates.

The output is a non-causal candidate-update artifact. It helps decide which
candidate repair should be sandboxed next without changing runtime behavior.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def summarize_counterfactual_evidence(
    *,
    successor_audit_path: Path,
    sweep_path: Path,
) -> dict[str, Any]:
    successor_audit = _load_json(successor_audit_path)
    sweep = _load_json(sweep_path)
    sweeps = sweep.get("counterfactual_successor_sweeps") or []
    forced_outcomes = Counter()
    best_mating = Counter()
    first_moves = Counter()
    states_with_mate = 0
    states_without_mate = 0
    state_records: list[dict[str, Any]] = []

    for item in sweeps:
        if not isinstance(item, dict):
            continue
        results = item.get("counterfactual_results") or {}
        mating_successors = []
        for successor, result in results.items():
            if not isinstance(result, dict):
                continue
            outcome = str(result.get("result") or "unknown")
            forced_outcomes[f"{successor}:{outcome}"] += 1
            move = result.get("first_move")
            if move:
                first_moves[f"{successor}:{move}"] += 1
            if outcome == "mate":
                mating_successors.append(str(successor))
        if mating_successors:
            states_with_mate += 1
            for successor in sorted(mating_successors):
                best_mating[successor] += 1
        else:
            states_without_mate += 1
        state_records.append({
            "state_signature": item.get("state_signature"),
            "actual_selected_successor": item.get("actual_selected_successor"),
            "actual_result": item.get("actual_result"),
            "mating_successors": mating_successors,
            "forced_results": {
                successor: {
                    "result": result.get("result"),
                    "plies": result.get("plies"),
                    "first_move": result.get("first_move"),
                    "confidence": result.get("confidence"),
                    "forced_successor_available": result.get("forced_successor_available"),
                }
                for successor, result in results.items()
                if isinstance(result, dict)
            },
        })

    edge_trap_mates = best_mating.get("krk.edge_trap_close", 0)
    drive_mates = best_mating.get("krk.drive_to_edge", 0)
    stage0_mates = best_mating.get("krk.stage0_basin", 0)
    candidate_updates = []
    if drive_mates:
        candidate_updates.append({
            "candidate_role": "krk.box_shrink_to_drive_repair",
            "status": "counterfactual_supported",
            "support": int(drive_mates),
            "topology_weight_diagnosis": {
                "frozen_weight_probe_result": "partial_success",
                "forced_oracle_probe_result": "existing_provider_can_convert_some_families",
                "bounded_m3_warmup_result": "not_run",
                "bounded_m4_consolidation_result": "not_run",
                "guardrail_delta": None,
                "weight_saturation": "unknown",
                "candidate_locality": "stage7_box_shrink_to_drive_to_edge",
                "candidate_complexity": "small",
                "diagnostic_labels": ["topology_present_untrained", "trainable_candidate"],
            },
            "proposed_next_action": "sandbox_visible_drive_repair_role",
            "source_terms_to_validate": [
                "box_shrink_reward_confirmed",
                "fence_or_cut_not_preserved",
                "drive_to_edge_affordance_after_box_shrink",
                "repair_or_reestablish_cut_available",
            ],
        })
    if edge_trap_mates:
        candidate_updates.append({
            "candidate_role": "krk.box_shrink_to_edge_trap_handoff",
            "status": "counterfactual_supported",
            "support": int(edge_trap_mates),
            "topology_weight_diagnosis": {
                "frozen_weight_probe_result": "partial_success",
                "forced_oracle_probe_result": "existing_provider_can_convert_some_families",
                "bounded_m3_warmup_result": "not_run",
                "bounded_m4_consolidation_result": "not_run",
                "guardrail_delta": None,
                "weight_saturation": "unknown",
                "candidate_locality": "stage7_box_shrink_to_edge_trap",
                "candidate_complexity": "small",
                "diagnostic_labels": ["topology_present_untrained", "trainable_candidate"],
            },
            "proposed_next_action": "sandbox_visible_edge_trap_handoff_role",
            "source_terms_to_validate": [
                "box_area_not_increased_after_reply",
                "rook_safe_after_reply",
                "fence_or_cut_preserved",
                "successor_edge_trap_close_available",
            ],
        })
    if states_without_mate:
        candidate_updates.append({
            "candidate_role": "krk.box_shrink_post_reply_continuation",
            "status": "insufficient_existing_successor_capacity_in_quick_sweep",
            "support": int(states_without_mate),
            "topology_weight_diagnosis": {
                "frozen_weight_probe_result": "failed_for_some_families",
                "forced_oracle_probe_result": "inconclusive_quick_horizon",
                "bounded_m3_warmup_result": "not_run",
                "bounded_m4_consolidation_result": "not_run",
                "guardrail_delta": None,
                "weight_saturation": "unknown",
                "candidate_locality": "stage7_box_shrink_post_reply",
                "candidate_complexity": "unknown",
                "diagnostic_labels": ["provider_capacity_missing"],
            },
            "proposed_next_action": "run_targeted_legal_first_or_longer_horizon_sweep",
            "source_terms_to_validate": [
                "post_box_shrink_conversion_needed",
                "stage0_basin_fallback_detected",
                "edge_or_drive_repair_not_selected",
                "safe_alternative_first_move_exists",
            ],
        })
    if stage0_mates == 0:
        candidate_updates.append({
            "candidate_role": "krk.stage0_basin_after_box_shrink",
            "status": "negative_counterfactual_evidence",
            "support": int(len(sweeps)),
            "topology_weight_diagnosis": {
                "frozen_weight_probe_result": "failed",
                "forced_oracle_probe_result": "existing_provider_does_not_convert_quick_sweep",
                "bounded_m3_warmup_result": "not_run",
                "bounded_m4_consolidation_result": "not_run",
                "guardrail_delta": None,
                "weight_saturation": "unknown",
                "candidate_locality": "stage7_box_shrink_to_stage0",
                "candidate_complexity": "small",
                "diagnostic_labels": ["parameter_miscalibrated", "topology_overbroad"],
            },
            "proposed_next_action": "avoid_sandboxing_stage0_as_default_box_shrink_continuation",
            "source_terms_to_validate": [
                "stage0_basin_fallback_detected",
                "stage0_basin_unlicensed_after_box_shrink",
            ],
        })

    recommended = "sandbox_visible_drive_repair_role"
    if edge_trap_mates and drive_mates:
        recommended = "sandbox_drive_repair_and_edge_trap_handoff_ablation"
    elif not drive_mates and edge_trap_mates:
        recommended = "sandbox_visible_edge_trap_handoff_role"
    elif states_without_mate == len(sweeps):
        recommended = "run_longer_horizon_or_legal_first_sweep_before_sandboxing"

    return {
        "schema_version": "stage7_counterfactual_candidate_update.v1",
        "causal_status": "non_causal",
        "successor_audit_source": str(successor_audit_path),
        "counterfactual_sweep_source": str(sweep_path),
        "source_candidate_id": successor_audit.get("source_candidate_id"),
        "sweep_profile": {
            "playout_max_plies": 8,
            "max_ticks": 12,
            "interpretation": "quick triage only; not a validation result",
        },
        "performance": {
            "wall_time": sweep.get("wall_time"),
            "samples": len(sweeps),
            "workers": sweep.get("parallel_workers"),
            "cache_hits_misses": sweep.get("cache_hits_misses", {}),
            "engine_decisions": sweep.get("engine_decisions"),
            "engine_ticks": sweep.get("engine_ticks"),
            "teacher_features_calls": sweep.get("teacher_features_calls"),
            "goal_distance_calls": sweep.get("goal_distance_calls"),
            "worst_reply_reward_calls": sweep.get("worst_reply_reward_calls"),
            "trace_mode": "quick_forced_successor_sweep",
        },
        "state_count": len(sweeps),
        "states_with_any_forced_mate": states_with_mate,
        "states_without_any_forced_mate": states_without_mate,
        "forced_successor_outcome_counts": dict(forced_outcomes),
        "best_mating_successor_counts": dict(best_mating),
        "first_move_counts": dict(first_moves),
        "candidate_updates": candidate_updates,
        "state_records": state_records,
        "recommended_next_action": recommended,
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Counterfactual Candidate Update",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"State count: `{payload['state_count']}`",
        f"States with any forced mate: `{payload['states_with_any_forced_mate']}`",
        f"States without any forced mate: `{payload['states_without_any_forced_mate']}`",
        "",
        "## Forced Outcomes",
        "",
    ]
    for key, value in sorted((payload.get("forced_successor_outcome_counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Candidate Updates", ""])
    for update in payload.get("candidate_updates") or []:
        lines.append(f"### {update.get('candidate_role')}")
        lines.append("")
        lines.append(f"- Status: `{update.get('status')}`")
        lines.append(f"- Support: `{update.get('support')}`")
        lines.append(f"- Proposed next action: `{update.get('proposed_next_action')}`")
        lines.append("")
    lines.append(f"Recommended next action: `{payload.get('recommended_next_action')}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Stage 7 counterfactual candidate evidence")
    parser.add_argument("--successor-audit", type=Path, required=True)
    parser.add_argument("--sweep", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = summarize_counterfactual_evidence(
        successor_audit_path=args.successor_audit,
        sweep_path=args.sweep,
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
