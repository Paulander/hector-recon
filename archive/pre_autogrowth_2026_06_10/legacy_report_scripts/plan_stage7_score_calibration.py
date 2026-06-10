#!/usr/bin/env python3
"""Plan bounded Stage 7 score/plasticity calibration from arbitration evidence.

This is a reporting-only helper. It converts arbitration evidence into a small
candidate-local calibration plan while preserving the Plasticity Balance
Protocol: try existing structure and bounded weight/score calibration before
proposing new topology.
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


def _provider_rows(arbitration: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in arbitration.get("records") or []:
        if not isinstance(record, dict):
            continue
        for row in record.get("provider_arbitration") or []:
            if not isinstance(row, dict):
                continue
            merged = dict(row)
            merged["state_id"] = record.get("state_id")
            merged["family_id"] = record.get("family_id")
            merged["normal_selected"] = record.get("normal_selected")
            rows.append(merged)
    return rows


def _classify_row(row: dict[str, Any], *, max_additive_support: float) -> dict[str, Any] | None:
    if row.get("forced_known_outcome") != "mate":
        return None
    provider = str(row.get("provider"))
    required = float(row.get("required_support_to_overtake_selected", 0.0) or 0.0)
    current_support = float(row.get("adapter_support_amount", 0.0) or 0.0)
    adapter_fired = bool(row.get("adapter_fired_under_forced_provider", False))
    if not adapter_fired:
        status = "needs_visible_support_before_calibration"
        diagnosis = [
            "forced_provider_can_convert",
            "no_visible_adapter_support_for_provider",
        ]
        next_action = "derive_family_specific_visible_support_terms_before_weight_probe"
    elif required > max_additive_support:
        status = "score_scale_normalization_probe_ready"
        diagnosis = [
            "forced_provider_can_convert",
            "visible_adapter_fires",
            "additive_support_required_is_too_large",
            "provider_scores_not_comparable_across_skills",
        ]
        next_action = "sandbox_score_normalization_or_candidate_local_calibration"
    else:
        status = "bounded_additive_calibration_probe_ready"
        diagnosis = [
            "forced_provider_can_convert",
            "visible_adapter_fires",
            "required_support_within_bounded_calibration_budget",
        ]
        next_action = "sandbox_candidate_local_support_weight_probe"
    return {
        "state_id": row.get("state_id"),
        "family_id": row.get("family_id"),
        "provider": provider,
        "status": status,
        "diagnosis": diagnosis,
        "next_action": next_action,
        "normal_selected": row.get("normal_selected"),
        "forced_best": row.get("forced_best"),
        "forced_known_outcome": row.get("forced_known_outcome"),
        "forced_known_plies": row.get("forced_known_plies"),
        "required_support_to_overtake_selected": required,
        "current_adapter_support_amount": current_support,
        "support_ratio_to_required": (
            current_support / required if required > 0 else None
        ),
        "max_additive_support_budget": max_additive_support,
        "adapter_fired_under_forced_provider": adapter_fired,
        "causal_status": "non_causal",
    }


def plan_stage7_score_calibration(
    *,
    arbitration_path: Path,
    max_additive_support: float = 1.0,
) -> dict[str, Any]:
    arbitration = _load_json(arbitration_path)
    candidates = [
        item
        for row in _provider_rows(arbitration)
        if (item := _classify_row(row, max_additive_support=max_additive_support)) is not None
    ]
    status_counts: dict[str, int] = {}
    for item in candidates:
        status = str(item["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    if status_counts.get("score_scale_normalization_probe_ready", 0):
        next_phase = "bounded_score_normalization_probe"
    elif status_counts.get("needs_visible_support_before_calibration", 0):
        next_phase = "visible_support_term_refinement"
    elif candidates:
        next_phase = "bounded_additive_calibration_probe"
    else:
        next_phase = "no_calibration_candidate_found"
    return {
        "schema_version": "stage7_score_calibration_plan.v1",
        "causal_status": "non_causal",
        "arbitration_source": str(arbitration_path),
        "max_additive_support_budget": float(max_additive_support),
        "next_phase": next_phase,
        "candidate_count": len(candidates),
        "status_counts": status_counts,
        "calibration_candidates": candidates,
        "growth_governor": {
            "stage": 7,
            "stage_status": "local_valid_composition_quarantined",
            "growth_status": "growth_blocked_by_weight_vs_topology_diagnosis",
            "reason": "existing_forced_providers_can_convert_some_families",
            "allowed_next_actions": [
                "bounded_score_normalization_probe",
                "visible_support_term_refinement",
                "guardrail_validation_after_sandbox_only",
            ],
            "blocked_actions": [
                "promote_stage7",
                "train_stage8",
                "add_broad_stage0_penalty",
                "new_post_box_topology_before_calibration_probe",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan Stage 7 score calibration")
    parser.add_argument("--arbitration", type=Path, required=True)
    parser.add_argument("--max-additive-support", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = plan_stage7_score_calibration(
        arbitration_path=args.arbitration,
        max_additive_support=args.max_additive_support,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
