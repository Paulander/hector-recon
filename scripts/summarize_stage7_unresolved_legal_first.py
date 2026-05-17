#!/usr/bin/env python3
"""Summarize Stage 7 unresolved-family legal-first probes.

This is a non-causal growth-monitor helper. It converts legal-first replay
evidence into candidate diagnoses without changing runtime behavior.
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


def _state_records(payloads: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    for payload in payloads:
        for record in payload.get("records") or []:
            if not isinstance(record, dict) or not record.get("state_id"):
                continue
            state_id = str(record["state_id"])
            target = states.setdefault(
                state_id,
                {
                    "state_id": state_id,
                    "post_reply_fen": record.get("post_reply_fen"),
                    "family_id": record.get("family_id"),
                    "source_diagnosis": record.get("diagnosis"),
                    "legal_first_probes": [],
                },
            )
            target["legal_first_probes"].extend(record.get("legal_first_probes") or [])
    return states


def _candidate_for_state(state: dict[str, Any]) -> dict[str, Any]:
    probes = [item for item in state.get("legal_first_probes") or [] if isinstance(item, dict)]
    outcome_counts: Counter[str] = Counter()
    mate_moves: list[dict[str, Any]] = []
    horizons: set[int] = set()
    for probe in probes:
        horizon = int(probe.get("horizon") or 0)
        if horizon:
            horizons.add(horizon)
        result = str(probe.get("result") or "unknown")
        outcome_counts[f"h{horizon}:{result}"] += 1
        if result == "mate":
            audit = probe.get("move_shape_audit") if isinstance(probe.get("move_shape_audit"), dict) else {}
            mate_moves.append(
                {
                    "move": probe.get("move"),
                    "horizon": horizon,
                    "plies": probe.get("plies"),
                    "move_shape_terms": list(audit.get("move_shape_terms") or []),
                    "post_move_terms": list(audit.get("post_move_terms") or []),
                    "current_terms": list(audit.get("current_terms") or []),
                }
            )
    state_id = str(state["state_id"])
    suffix = state_id.removeprefix("state.")
    if mate_moves:
        candidate_type = "move_shape_role_refinement"
        diagnosis = "legal_first_action_selection_gap"
        status = "sandbox_ready_if_terms_separate"
        proposed_change = {
            "kind": "visible_move_shape_role_candidate",
            "target_skill": "krk.box_shrink",
            "candidate_moves": mate_moves,
            "suggested_terms": sorted(
                {
                    term
                    for move in mate_moves
                    for term in (move.get("move_shape_terms") or []) + (move.get("post_move_terms") or [])
                }
            ),
        }
        trigger_failure_classes = [
            "selected_successor_miscalibrated",
            "legal_first_action_selection_gap",
        ]
    else:
        max_horizon = max(horizons) if horizons else None
        candidate_type = "continuation_capacity_probe"
        diagnosis = "no_legal_first_conversion_under_current_graph"
        status = "needs_longer_horizon_or_new_provider_probe"
        proposed_change = {
            "kind": "post_box_continuation_capacity_audit",
            "max_tested_horizon": max_horizon,
            "next_probe": "forced_deeper_continuation_or_new_overlay_provider_only_if_higher_horizon_fails",
        }
        trigger_failure_classes = [
            "selected_successor_miscalibrated",
            "no_legal_first_conversion_under_current_graph",
        ]
    return {
        "schema_version": "structural_candidate.v1",
        "candidate_id": f"cand.krk.box_shrink.unresolved_family_{suffix}.{candidate_type}.v1",
        "candidate_type": candidate_type,
        "source_monitor_script": "growth.monitor.stage7_unresolved_legal_first",
        "source_terms": trigger_failure_classes,
        "trigger_failure_classes": trigger_failure_classes,
        "target_skill": "krk.box_shrink",
        "parent_skill": "krk.drive_to_edge",
        "state_id": state_id,
        "post_reply_fen": state.get("post_reply_fen"),
        "diagnosis": diagnosis,
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "legal_first_mating_moves": mate_moves,
        "proposed_change": proposed_change,
        "promotion_status": status,
        "causal_status": "non_causal",
        "credit": 0.0,
    }


def summarize(inputs: list[Path]) -> dict[str, Any]:
    payloads = [_load_json(path) for path in inputs]
    states = _state_records(payloads)
    candidates = [_candidate_for_state(states[key]) for key in sorted(states)]
    return {
        "schema_version": "stage7_unresolved_legal_first_summary.v1",
        "causal_status": "non_causal",
        "inputs": [str(path) for path in inputs],
        "state_count": len(states),
        "candidate_count": len(candidates),
        "candidate_status_counts": dict(Counter(item["promotion_status"] for item in candidates)),
        "diagnosis_counts": dict(Counter(item["diagnosis"] for item in candidates)),
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Stage 7 unresolved legal-first probes")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()
    payload = summarize(args.inputs)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
