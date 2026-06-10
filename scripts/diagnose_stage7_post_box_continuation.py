#!/usr/bin/env python3
"""Diagnose Stage 7 post-box-shrink continuation without changing behavior.

This is a replay-free Growth Governor/StructuralCandidate helper. It consumes a
Stage 7 landmark diagnostic artifact and extracts the post-box-shrink state
dataset requested by the Plasticity Balance Protocol:

    local box_shrink result -> post-reply state -> conversion outcome

The output is deliberately non-causal. It does not mutate topology, train
weights, or promote/quarantine by itself. Expensive forced-provider/M3 probes
are represented as pending follow-up work unless an external probe artifact is
provided later.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import chess

from recon_lite_chess.training.krk_landmarks import rich_feature_dict


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _packets_by_sample(diagnostic: dict[str, Any]) -> list[dict[str, dict[str, Any]]]:
    packets = [pkt for pkt in diagnostic.get("handoff_packets") or [] if isinstance(pkt, dict)]
    groups: list[dict[str, dict[str, Any]]] = []
    current: dict[str, dict[str, Any]] = {}
    for packet in packets:
        phase = str(packet.get("phase") or "")
        if phase == "post_own_move" and current:
            groups.append(current)
            current = {}
        if phase:
            current[phase] = packet
    if current:
        groups.append(current)
    return groups


def _bool_bucket(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "unknown"


def _feature_delta(before_fen: str | None, after_fen: str | None, key: str) -> float | None:
    if not before_fen or not after_fen:
        return None
    try:
        before = rich_feature_dict(chess.Board(before_fen))
        after = rich_feature_dict(chess.Board(after_fen))
    except Exception:
        return None
    return float(after.get(key, 0.0) - before.get(key, 0.0))


def _derive_record(index: int, group: dict[str, dict[str, Any]]) -> dict[str, Any]:
    own_packet = group.get("post_own_move", {})
    reply_packet = group.get("post_opponent_reply", {})
    summary_packet = group.get("playout_summary", {})
    own = own_packet.get("evidence_terms") if isinstance(own_packet.get("evidence_terms"), dict) else {}
    reply = reply_packet.get("evidence_terms") if isinstance(reply_packet.get("evidence_terms"), dict) else {}
    summary = (
        summary_packet.get("evidence_terms")
        if isinstance(summary_packet.get("evidence_terms"), dict)
        else {}
    )
    start_fen = own.get("fen") or reply.get("fen") or summary.get("fen")
    post_reply_fen = reply.get("post_reply_fen")
    post_own_fen = None
    if start_fen and own.get("move"):
        try:
            board = chess.Board(str(start_fen))
            move = chess.Move.from_uci(str(own.get("move")))
            if move in board.legal_moves:
                board.push(move)
                post_own_fen = board.fen()
        except Exception:
            post_own_fen = None
    box_area_delta_own = _feature_delta(start_fen, post_own_fen, "box_area")
    box_area_delta_reply = _feature_delta(post_own_fen, post_reply_fen, "box_area")
    enemy_mobility_delta = None
    if post_own_fen and post_reply_fen:
        try:
            before = chess.Board(post_own_fen)
            after = chess.Board(post_reply_fen)
            before.turn = chess.BLACK
            after.turn = chess.BLACK
            enemy_mobility_delta = float(after.legal_moves.count() - before.legal_moves.count())
        except Exception:
            enemy_mobility_delta = None
    selected_successor = (
        reply.get("successor_selected_skill")
        or reply.get("selected_successor")
        or reply.get("selected_skill")
    )
    selected_move = (
        (reply.get("visible_stage7_drive_repair_license") or {}).get("move")
        or (reply.get("visible_stage7_king_tempo_license") or {}).get("move")
        or (reply.get("visible_stage7_post_king_tempo_license") or {}).get("move")
        or reply.get("selected_move")
        or reply.get("move")
    )
    return {
        "sample_index": index,
        "start_fen": start_fen,
        "stage7_move": own.get("move"),
        "post_own_move_fen": post_own_fen,
        "black_reply": reply.get("black_reply"),
        "post_reply_fen": post_reply_fen,
        "reward_confirmed": bool(own.get("reward_confirmed", False)),
        "visible_box_area_decreased_after_own_move": (
            None if box_area_delta_own is None else bool(box_area_delta_own < 0)
        ),
        "visible_box_area_not_increased_after_reply": (
            None if box_area_delta_reply is None else bool(box_area_delta_reply <= 0)
        ),
        "fence_or_cut_preserved": bool(reply.get("fence_survived_reply", False)),
        "rook_safe_after_reply": bool(reply.get("rook_safe_after_reply", False)),
        "enemy_king_mobility_delta": enemy_mobility_delta,
        "selected_successor": selected_successor,
        "selected_move": selected_move,
        "conversion_result": summary.get("playout_result") or reply.get("playout_result"),
        "conversion_status": summary.get("conversion_status"),
        "plies": summary.get("plies") or reply.get("plies"),
        "semantic_alignment_status": (
            summary.get("semantic_alignment_status") or reply.get("semantic_alignment_status")
        ),
        "failure_classes": list(summary.get("failure_classes") or reply.get("failure_classes") or []),
        "shadow_triggers": [],
    }


def _bucket_record(record: dict[str, Any]) -> str:
    visible_shrink = record.get("visible_box_area_decreased_after_own_move") is True
    reward = record.get("reward_confirmed") is True
    result = str(record.get("conversion_result") or "unknown")
    successor = str(record.get("selected_successor") or "none")
    if visible_shrink and result == "mate":
        return "box_shrink_visible_confirmed_mate"
    if visible_shrink and result != "mate":
        return "box_shrink_visible_confirmed_max_plies"
    if reward and not visible_shrink and result == "mate":
        return "reward_confirmed_no_visible_shrink_mate"
    if reward and not visible_shrink and result != "mate":
        return "reward_confirmed_no_visible_shrink_max_plies"
    if successor == "krk.stage0_basin" and result != "mate":
        return "stage0_basin_max_plies"
    if successor == "krk.edge_trap_close" and result == "mate":
        return "edge_trap_close_mate"
    if successor == "none" and result == "mate":
        return "none_mate"
    return f"other_{result}"


def diagnose_stage7_post_box_continuation(
    *,
    diagnostic_path: Path,
) -> dict[str, Any]:
    diagnostic = _load_json(diagnostic_path)
    records = [
        _derive_record(index, group)
        for index, group in enumerate(_packets_by_sample(diagnostic))
        if "post_own_move" in group and "playout_summary" in group
    ]
    bucket_counts = Counter(_bucket_record(record) for record in records)
    outcome_by_alignment = defaultdict(Counter)
    successor_by_outcome = Counter()
    failure_classes = Counter()
    unique_failed_post_reply = {}
    for record in records:
        result = str(record.get("conversion_result") or "unknown")
        outcome_by_alignment[str(record.get("semantic_alignment_status") or "unknown")][result] += 1
        successor_by_outcome[f"{record.get('selected_successor') or 'none'}:{result}"] += 1
        for cls in record.get("failure_classes") or []:
            failure_classes[str(cls)] += 1
        if result != "mate" and record.get("post_reply_fen"):
            unique_failed_post_reply.setdefault(str(record["post_reply_fen"]), record)

    total = len(records)
    failed = sum(1 for record in records if record.get("conversion_result") != "mate")
    local_failed = sum(1 for record in records if not record.get("reward_confirmed"))
    visible_shrink_failures = bucket_counts.get("box_shrink_visible_confirmed_max_plies", 0)
    reward_mismatch_failures = bucket_counts.get("reward_confirmed_no_visible_shrink_max_plies", 0)
    diagnosis_labels: list[str] = []
    if local_failed:
        diagnosis_labels.append("local_policy_still_imperfect")
    if visible_shrink_failures:
        diagnosis_labels.append("post_box_shrink_continuation_gap")
    if reward_mismatch_failures:
        diagnosis_labels.append("reward_contract_mismatch_remaining")
    if failed and not local_failed:
        diagnosis_labels.append("topology_present_untrained_or_miscalibrated")
    elif failed:
        diagnosis_labels.append("mixed_local_and_continuation_failure")

    candidate_updates = [
        {
            "candidate_id": "cand.krk.box_shrink.handoff_role_refinement.v1",
            "status": "needs_bounded_forced_provider_probe",
            "candidate_role": "krk.post_box_shrink_continuation",
            "topology_weight_diagnosis": {
                "frozen_weight_probe_result": "not_completed_runtime_cost_blocked",
                "forced_oracle_probe_result": "pending",
                "bounded_m3_warmup_result": "not_run",
                "bounded_m4_consolidation_result": "not_run",
                "guardrail_delta": None,
                "weight_saturation": "unknown",
                "candidate_locality": "stage7_post_box_shrink",
                "candidate_complexity": "small_to_medium",
                "diagnostic_labels": diagnosis_labels,
            },
            "proposed_next_action": "run_targeted_forced_provider_probe_on_unique_failed_post_reply_states",
            "source_terms_to_validate": [
                "post_box_shrink_conversion_needed",
                "visible_box_area_decreased_after_own_move",
                "visible_box_area_not_increased_after_reply",
                "rook_safe_after_reply",
                "fence_or_cut_preserved",
                "safe_followup_available",
            ],
        },
        {
            "candidate_id": "cand.krk.box_shrink.overlay_quarantine_confirmed.v1",
            "status": "local_valid_composition_quarantined",
            "candidate_role": "krk.box_shrink",
            "topology_weight_diagnosis": {
                "frozen_weight_probe_result": "local_improved_conversion_failed",
                "forced_oracle_probe_result": "pending",
                "bounded_m3_warmup_result": "not_run",
                "bounded_m4_consolidation_result": "not_run",
                "guardrail_delta": None,
                "weight_saturation": "unknown",
                "candidate_locality": "stage7_box_shrink_overlay",
                "candidate_complexity": "existing_overlay",
                "diagnostic_labels": ["local_valid_composition_quarantined"],
            },
            "proposed_next_action": "do_not_promote_stage7_until_continuation_probe_or_repair_passes_guardrails",
            "source_terms_to_validate": [],
        },
    ]

    return {
        "schema_version": "stage7_post_box_continuation_diagnosis.v1",
        "causal_status": "non_causal",
        "diagnostic_source": str(diagnostic_path),
        "stage7_status": "local_valid_composition_quarantined",
        "record_count": total,
        "conversion_failed_count": failed,
        "bucket_counts": dict(bucket_counts),
        "outcome_by_semantic_alignment": {
            key: dict(value) for key, value in outcome_by_alignment.items()
        },
        "successor_by_outcome": dict(successor_by_outcome),
        "failure_class_counts": dict(failure_classes),
        "unique_failed_post_reply_state_count": len(unique_failed_post_reply),
        "unique_failed_post_reply_states": list(unique_failed_post_reply.values()),
        "records": records,
        "candidate_updates": candidate_updates,
        "recommended_next_action": (
            "targeted_forced_provider_probe_before_new_topology"
            if failed
            else "guardrail_validate_for_promotion"
        ),
        "hard_blocks": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_add_local_box_shrink_move_shape_patch",
            "do_not_make_packets_stats_or_candidates_causal",
        ],
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Post-Box-Shrink Continuation Diagnosis",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Stage 7 status: `{payload['stage7_status']}`",
        f"Records: `{payload['record_count']}`",
        f"Conversion failures: `{payload['conversion_failed_count']}`",
        f"Unique failed post-reply states: `{payload['unique_failed_post_reply_state_count']}`",
        "",
        "## Buckets",
        "",
    ]
    for key, value in sorted((payload.get("bucket_counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Candidate Updates", ""])
    for update in payload.get("candidate_updates") or []:
        lines.append(f"### {update.get('candidate_id')}")
        lines.append("")
        lines.append(f"- Status: `{update.get('status')}`")
        lines.append(f"- Role: `{update.get('candidate_role')}`")
        lines.append(f"- Next action: `{update.get('proposed_next_action')}`")
        labels = update.get("topology_weight_diagnosis", {}).get("diagnostic_labels", [])
        lines.append("- Diagnosis labels: " + ", ".join(f"`{label}`" for label in labels))
        lines.append("")
    lines.extend([
        "## Recommended Next Action",
        "",
        f"`{payload.get('recommended_next_action')}`",
        "",
        "Do not promote Stage 7 or train Stage 8 from this artifact. This is a",
        "non-causal diagnosis artifact for the next bounded forced-provider/M3 probe.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Stage 7 post-box-shrink continuation")
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = diagnose_stage7_post_box_continuation(diagnostic_path=args.diagnostic)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        _write_markdown(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
