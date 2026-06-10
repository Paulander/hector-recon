#!/usr/bin/env python3
"""Run Stage 7 2cc protocol Phase 2 replay classification.

This is still non-causal. It consumes the Phase 0/1 frozen-model selection and
existing legal-first replay artifacts to classify whether the selected visible
first move is enough for the current graph to convert, or whether the remaining
problem is downstream multi-step continuation.
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


def _legal_first_probes(legal_first: dict[str, Any], target_fen: str) -> list[dict[str, Any]]:
    for record in legal_first.get("records") or []:
        if not isinstance(record, dict):
            continue
        if str(record.get("post_reply_fen") or "") == target_fen:
            return [item for item in record.get("legal_first_probes") or [] if isinstance(item, dict)]
    return []


def _alignment_by_move(alignment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for item in alignment.get("labeled_candidate_frames") or []:
        if isinstance(item, dict) and item.get("move"):
            rows[str(item["move"])] = {
                "forces_mate": bool(item.get("forces_mate", False)),
                "child_dtm": item.get("child_dtm"),
                "optimal_dtm_move": bool(item.get("optimal_dtm_move", False)),
            }
    return rows


def evaluate_phase02(
    *,
    phase01_path: Path,
    alignment_path: Path,
    legal_first_path: Path,
) -> dict[str, Any]:
    phase01 = _load_json(phase01_path)
    alignment = _load_json(alignment_path)
    legal_first = _load_json(legal_first_path)

    target_fen = str(alignment.get("target_fen") or "")
    selected_move = str(
        phase01.get("phase1_frozen_weight_probe", {}).get("selected_move") or ""
    )
    probes = _legal_first_probes(legal_first, target_fen)
    by_move = {str(item.get("move")): item for item in probes if item.get("move")}
    selected_probe = dict(by_move.get(selected_move, {}) or {})
    outcome_counts = Counter(
        f"h{item.get('horizon')}:{item.get('result')}"
        for item in probes
        if item.get("horizon") is not None and item.get("result")
    )
    mate_moves = sorted(str(item.get("move")) for item in probes if item.get("result") == "mate")
    dtm_rows = _alignment_by_move(alignment)
    selected_dtm = dtm_rows.get(selected_move, {})

    selected_current_graph_mates = selected_probe.get("result") == "mate"
    all_current_graph_fail = bool(probes) and not mate_moves
    selected_is_tablebase_winning = bool(selected_dtm.get("forces_mate", False))
    if selected_is_tablebase_winning and not selected_current_graph_mates and all_current_graph_fail:
        diagnosis = "visible_first_step_winning_but_current_graph_downstream_continuation_fails"
        next_action = "bounded candidate-local plasticity protocol or narrow continuation sandbox"
    elif selected_current_graph_mates:
        diagnosis = "visible_first_step_sufficient_under_current_graph"
        next_action = "run default-off target validation before any sandbox promotion"
    elif not selected_is_tablebase_winning:
        diagnosis = "frozen_model_first_step_not_tablebase_winning"
        next_action = "candidate-local calibration before runtime sandbox"
    else:
        diagnosis = "mixed_current_graph_replay_result"
        next_action = "inspect per-move replay traces before training"

    return {
        "schema_version": "stage7_2cc_protocol_phase02_replay_eval.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "sources": {
            "phase01": str(phase01_path),
            "alignment": str(alignment_path),
            "legal_first": str(legal_first_path),
        },
        "target_fen": target_fen,
        "selected_move": selected_move,
        "selected_move_dtm": selected_dtm,
        "selected_move_current_graph_replay": selected_probe,
        "legal_first_probe_count": len(probes),
        "legal_first_outcome_counts": dict(sorted(outcome_counts.items())),
        "legal_first_mating_moves": mate_moves,
        "diagnosis": diagnosis,
        "candidate_status_update": {
            "candidate_id": phase01.get("candidate_status_update", {}).get("candidate_id"),
            "phase2_status": "complete",
            "diagnosis": diagnosis,
            "next_action": next_action,
            "causal_status": "non_causal",
            "promotion_status": "sandbox_protocol_phase02_complete",
        },
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    update = payload["candidate_status_update"]
    selected_probe = payload["selected_move_current_graph_replay"]
    lines = [
        "# Stage 7 2cc Protocol Phase 2",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        "",
        "## Selected Move",
        "",
        f"Move: `{payload['selected_move']}`",
        f"DTM child: `{payload['selected_move_dtm'].get('child_dtm')}`",
        f"Tablebase-winning: `{payload['selected_move_dtm'].get('forces_mate')}`",
        f"Optimal DTM move: `{payload['selected_move_dtm'].get('optimal_dtm_move')}`",
        f"Current graph result: `{selected_probe.get('result')}`",
        f"Current graph horizon: `{selected_probe.get('horizon')}`",
        "",
        "## Legal-First Current Graph",
        "",
        f"Probe count: `{payload['legal_first_probe_count']}`",
        f"Outcome counts: `{payload['legal_first_outcome_counts']}`",
        f"Mating moves: `{payload['legal_first_mating_moves']}`",
        "",
        "## Candidate Update",
        "",
        f"Candidate: `{update['candidate_id']}`",
        f"Diagnosis: `{update['diagnosis']}`",
        f"Next action: `{update['next_action']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase01", type=Path, required=True)
    parser.add_argument("--alignment", type=Path, required=True)
    parser.add_argument("--legal-first", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = evaluate_phase02(
        phase01_path=args.phase01,
        alignment_path=args.alignment,
        legal_first_path=args.legal_first,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
