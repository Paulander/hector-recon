#!/usr/bin/env python3
"""Evaluate Stage 7 family-specific adapter sandbox outcome.

This is a non-causal promotion/quarantine helper. It consumes family adapter
proposals, a default-off equivalence result, and an adapter-on diagnostic, then
updates candidate statuses without altering topology or runtime behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def evaluate_family_adapter_outcome(
    *,
    proposals_path: Path,
    default_off_equivalence_path: Path,
    adapter_on_diagnostic_path: Path,
) -> dict[str, Any]:
    proposals = _load_json(proposals_path)
    equivalence = _load_json(default_off_equivalence_path)
    diagnostic = _load_json(adapter_on_diagnostic_path)
    adapter_fire_count = int(diagnostic.get("adapter_fire_count", 0) or 0)
    provider_by_outcome = dict(diagnostic.get("adapter_supported_provider_by_outcome", {}) or {})
    mate_supported = sum(
        int(count)
        for key, count in provider_by_outcome.items()
        if str(key).endswith(":mate")
    )
    max_supported = sum(
        int(count)
        for key, count in provider_by_outcome.items()
        if str(key).endswith(":max_plies")
    )
    default_off_safe = bool(equivalence.get("equivalent", False))
    if not default_off_safe:
        status = "executor_semantics_violation"
        diagnosis = ["default_off_behavior_changed"]
        next_action = "stop_and_diagnose_topology_wiring"
    elif adapter_fire_count == 0:
        status = "inactive_candidate"
        diagnosis = ["adapter_did_not_fire"]
        next_action = "refine_required_terms_or_candidate_scope"
    elif mate_supported > 0 and max_supported == 0:
        status = "sandbox_validated_candidate"
        diagnosis = ["adapter_support_correlates_with_conversion"]
        next_action = "run_larger_target_and_guardrail_validation"
    elif mate_supported > 0:
        status = "mixed_candidate_needs_more_terms"
        diagnosis = ["adapter_support_mixed_outcomes", "needs_tighter_family_terms"]
        next_action = "derive_additional_visible_terms_before_m3"
    else:
        status = "overbroad_or_misdirected_candidate"
        diagnosis = [
            "adapter_fires_without_conversion",
            "do_not_run_m3_on_this_adapter",
            "needs_family_specific_or_move_shape_terms",
        ]
        next_action = "quarantine_candidate_and_collect_more_terms"

    updates = []
    for proposal in proposals.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        if proposal.get("proposal_status") != "sandbox_ready":
            updates.append({
                "candidate_id": proposal.get("candidate_id"),
                "previous_status": proposal.get("proposal_status"),
                "status": proposal.get("proposal_status"),
                "reason": "not_compiled_for_sandbox",
            })
            continue
        updates.append({
            "candidate_id": proposal.get("candidate_id"),
            "previous_status": proposal.get("proposal_status"),
            "status": status,
            "diagnosis": diagnosis,
            "next_action": next_action,
            "causal_status": "non_causal",
            "promotion_status": "quarantined" if status.startswith("overbroad") else "proposed",
        })

    return {
        "schema_version": "stage7_family_adapter_outcome.v1",
        "causal_status": "non_causal",
        "proposals_source": str(proposals_path),
        "default_off_equivalence_source": str(default_off_equivalence_path),
        "adapter_on_diagnostic_source": str(adapter_on_diagnostic_path),
        "default_off_safe": default_off_safe,
        "adapter_fire_count": adapter_fire_count,
        "adapter_supported_provider_by_outcome": provider_by_outcome,
        "adapter_supported_mate_count": mate_supported,
        "adapter_supported_max_plies_count": max_supported,
        "candidate_updates": updates,
        "hard_blocks": [
            "do_not_promote_stage7",
            "do_not_train_stage8",
            "do_not_run_m3_on_overbroad_adapter",
            "do_not_make_candidate_causal_without_guardrails",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Stage 7 family adapter outcome")
    parser.add_argument("--proposals", type=Path, required=True)
    parser.add_argument("--default-off-equivalence", type=Path, required=True)
    parser.add_argument("--adapter-on-diagnostic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = evaluate_family_adapter_outcome(
        proposals_path=args.proposals,
        default_off_equivalence_path=args.default_off_equivalence,
        adapter_on_diagnostic_path=args.adapter_on_diagnostic,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
