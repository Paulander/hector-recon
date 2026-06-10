#!/usr/bin/env python3
"""Audit Stage 7 structural candidates against box-shrink diagnostics.

This is an offline growth-lab tool. It reads non-causal StructuralCandidate
records and diagnostic traces, then writes an audit artifact that can guide the
next sandbox experiment. It does not alter topology or runtime routing.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import chess


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _counter_key(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "unknown"
    return str(value)


def _bucket_inc(table: dict[str, dict[str, int]], key: str, value: Any) -> None:
    bucket = table.setdefault(key, {"true": 0, "false": 0, "unknown": 0})
    bucket[_counter_key(value)] = bucket.get(_counter_key(value), 0) + 1


def _krk_geometry(board: chess.Board) -> dict[str, Any]:
    wk_sq = next(iter(board.pieces(chess.KING, chess.WHITE)), None)
    bk_sq = next(iter(board.pieces(chess.KING, chess.BLACK)), None)
    wr_sq = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    if wk_sq is None or bk_sq is None or wr_sq is None:
        return {
            "fence_exists": False,
            "fence_stable": False,
            "cut_axis": "none",
            "box_area": None,
            "rook_safe": False,
            "enemy_king_boxed": False,
            "enemy_king_edge_distance": None,
            "white_king_support_distance": None,
        }

    wk_file, wk_rank = chess.square_file(wk_sq), chess.square_rank(wk_sq)
    bk_file, bk_rank = chess.square_file(bk_sq), chess.square_rank(bk_sq)
    wr_file, wr_rank = chess.square_file(wr_sq), chess.square_rank(wr_sq)
    edge_distance = min(bk_file, 7 - bk_file, bk_rank, 7 - bk_rank)
    rook_king_distance = max(abs(wr_file - bk_file), abs(wr_rank - bk_rank))
    king_rook_distance = max(abs(wk_file - wr_file), abs(wk_rank - wr_rank))
    king_distance = max(abs(wk_file - bk_file), abs(wk_rank - bk_rank))
    cut_axis = "file" if wr_file == bk_file else "rank" if wr_rank == bk_rank else "edge" if edge_distance == 0 else "none"
    if rook_king_distance > 1:
        rook_safe = True
    else:
        capture = chess.Move(bk_sq, wr_sq)
        reply_board = board.copy(stack=False)
        reply_board.turn = chess.BLACK
        rook_safe = capture not in reply_board.legal_moves or king_rook_distance <= 1
    king_support = king_rook_distance <= 2 or king_distance <= 2
    fence_exists = rook_safe and (edge_distance == 0 or (cut_axis in {"file", "rank"} and rook_king_distance >= 2))
    box_width = wr_file if bk_file < wr_file else 7 - wr_file
    box_height = wr_rank if bk_rank < wr_rank else 7 - wr_rank
    box_width = max(1, box_width)
    box_height = max(1, box_height)
    return {
        "fence_exists": bool(fence_exists),
        "fence_stable": bool(fence_exists and king_support),
        "cut_axis": cut_axis,
        "box_area": int(box_width * box_height),
        "rook_safe": bool(rook_safe),
        "enemy_king_boxed": bool(fence_exists or edge_distance == 0),
        "enemy_king_edge_distance": int(edge_distance),
        "white_king_support_distance": int(min(
            chess.square_distance(wk_sq, wr_sq),
            chess.square_distance(wk_sq, bk_sq),
        )),
    }


def _enemy_king_mobility(board: chess.Board) -> int | None:
    bk_sq = next(iter(board.pieces(chess.KING, chess.BLACK)), None)
    if bk_sq is None:
        return None
    probe = board.copy(stack=False)
    probe.turn = chess.BLACK
    count = 0
    for move in probe.legal_moves:
        if move.from_square == bk_sq:
            count += 1
    return count


def _board_after_move(fen: str, move_uci: str) -> chess.Board | None:
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            return None
        board.push(move)
        return board
    except Exception:
        return None


def _derived_terms(evidence: dict[str, Any]) -> dict[str, Any]:
    fen = evidence.get("fen")
    move_uci = evidence.get("move")
    if not isinstance(fen, str) or not isinstance(move_uci, str):
        return {
            "box_area_decreased_after_own_move": None,
            "box_area_not_increased_after_reply": None,
            "fence_or_cut_preserved": None,
            "rook_safe_after_reply": evidence.get("rook_safe_after_reply"),
            "enemy_king_mobility_reduced": None,
        }

    try:
        start = chess.Board(fen)
    except Exception:
        start = None
    after_own = _board_after_move(fen, move_uci)
    start_geom = _krk_geometry(start) if start is not None else {}
    own_geom = _krk_geometry(after_own) if after_own is not None else {}

    post_reply_fen = evidence.get("post_reply_fen")
    reply_geom: dict[str, Any] = {}
    reply_board = None
    if isinstance(post_reply_fen, str):
        try:
            reply_board = chess.Board(post_reply_fen)
            reply_geom = _krk_geometry(reply_board)
        except Exception:
            reply_board = None
            reply_geom = {}

    own_box = own_geom.get("box_area")
    start_box = start_geom.get("box_area")
    reply_box = reply_geom.get("box_area", evidence.get("box_area_after_reply"))
    cut_preserved = (
        bool(own_geom.get("fence_exists"))
        or own_geom.get("cut_axis") in {"file", "rank", "edge"}
    )
    if reply_geom:
        cut_preserved = cut_preserved and (
            bool(reply_geom.get("fence_exists"))
            or reply_geom.get("cut_axis") in {"file", "rank", "edge"}
        )

    start_mobility = _enemy_king_mobility(start) if start is not None else None
    own_mobility = _enemy_king_mobility(after_own) if after_own is not None else None
    reply_mobility = _enemy_king_mobility(reply_board) if reply_board is not None else None
    mobility_after = reply_mobility if reply_mobility is not None else own_mobility

    return {
        "box_area_decreased_after_own_move": (
            own_box < start_box if isinstance(own_box, int) and isinstance(start_box, int) else None
        ),
        "box_area_not_increased_after_reply": (
            reply_box <= own_box if isinstance(reply_box, int) and isinstance(own_box, int) else None
        ),
        "fence_or_cut_preserved": bool(cut_preserved),
        "rook_safe_after_reply": evidence.get("rook_safe_after_reply"),
        "enemy_king_mobility_reduced": (
            mobility_after < start_mobility
            if isinstance(mobility_after, int) and isinstance(start_mobility, int)
            else None
        ),
        "box_area_before": start_box,
        "box_area_after_own_move": own_box,
        "box_area_after_reply": reply_box,
        "enemy_king_mobility_before": start_mobility,
        "enemy_king_mobility_after": mobility_after,
    }


def _packets_by_phase(diagnostic: dict[str, Any], phase: str) -> list[dict[str, Any]]:
    packets = diagnostic.get("handoff_packets")
    if not isinstance(packets, list):
        return []
    return [pkt for pkt in packets if isinstance(pkt, dict) and pkt.get("phase") == phase]


def _representative(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "fen": evidence.get("fen"),
        "move": evidence.get("move"),
        "black_reply": evidence.get("black_reply"),
        "post_reply_fen": evidence.get("post_reply_fen"),
        "playout_result": evidence.get("playout_result"),
        "semantic_alignment_status": evidence.get("semantic_alignment_status"),
        "successor_selected_skill": evidence.get("successor_selected_skill"),
        "failure_classes": evidence.get("failure_classes", []),
        "box_area_after_own_move": evidence.get("box_area_after_own_move"),
        "box_area_after_reply": evidence.get("box_area_after_reply"),
        "box_area_delta_after_reply": evidence.get("box_area_delta_after_reply"),
        "fence_survived_reply": evidence.get("fence_survived_reply"),
        "rook_safe_after_reply": evidence.get("rook_safe_after_reply"),
    }


def _candidate_governance(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "governor_status": candidate.get("governor_status", "settling"),
        "governor_metadata": candidate.get("governor_metadata", {}),
        "topology_weight_diagnosis": candidate.get("topology_weight_diagnosis", {}),
        "candidate_diagnostic_labels": candidate.get("candidate_diagnostic_labels", []),
    }


def _audit_reward_contract(candidate: dict[str, Any], diagnostic: dict[str, Any]) -> dict[str, Any]:
    term_counts: dict[str, dict[str, int]] = {}
    term_by_outcome: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    mismatch_examples: list[dict[str, Any]] = []
    post_reply_packets = _packets_by_phase(diagnostic, "post_opponent_reply")
    reward_confirmed_count = 0
    mismatch_count = 0
    conversion_by_mismatch = Counter()

    for packet in post_reply_packets:
        evidence = packet.get("evidence_terms") or {}
        if not isinstance(evidence, dict):
            continue
        reward_confirmed = bool(evidence.get("reward_confirmed"))
        if reward_confirmed:
            reward_confirmed_count += 1
        mismatch = bool(evidence.get("reward_contract_mismatch"))
        if mismatch:
            mismatch_count += 1
        outcome = str(evidence.get("playout_result") or "not_checked")
        if mismatch:
            conversion_by_mismatch[outcome] += 1
        terms = _derived_terms(evidence)
        for term in candidate.get("proposed_change", {}).get("suggested_terms", []):
            _bucket_inc(term_counts, term, terms.get(term))
            outcome_table = term_by_outcome.setdefault(term, {})
            _bucket_inc(outcome_table, outcome, terms.get(term))
        if mismatch and len(mismatch_examples) < 5:
            sample = _representative(evidence)
            sample["derived_terms"] = {key: terms.get(key) for key in candidate.get("proposed_change", {}).get("suggested_terms", [])}
            mismatch_examples.append(sample)

    findings: list[str] = []
    if mismatch_count:
        findings.append("box_shrink reward confirms in states where the current visible contract does not confirm")
    box_decrease = term_counts.get("box_area_decreased_after_own_move", {})
    if box_decrease.get("false", 0) > box_decrease.get("true", 0):
        findings.append("box_area_decreased_after_own_move is not consistently true under reward confirmation")
    not_increased = term_counts.get("box_area_not_increased_after_reply", {})
    if not_increased.get("true", 0) and box_decrease.get("true", 0) < not_increased.get("true", 0):
        findings.append("box_area_not_increased_after_reply is weaker than true box shrink and may only show non-expansion")
    cut_preserved = term_counts.get("fence_or_cut_preserved", {})
    if cut_preserved.get("false", 0):
        findings.append("some reward-confirmed samples lack visible fence/cut preservation")

    return {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_type": candidate.get("candidate_type"),
        "source_monitor_script": candidate.get("source_monitor_script"),
        **_candidate_governance(candidate),
        "audit_status": "needs_more_terms" if mismatch_count else "no_issue_detected",
        "candidate_update": {
            "from": candidate.get("promotion_status", "proposed"),
            "to": "needs_more_terms" if mismatch_count else candidate.get("promotion_status", "proposed"),
        },
        "reward_confirmed_samples": reward_confirmed_count,
        "reward_contract_mismatch_samples": mismatch_count,
        "conversion_by_reward_contract_mismatch": dict(conversion_by_mismatch),
        "suggested_term_counts": term_counts,
        "suggested_term_by_outcome": term_by_outcome,
        "representative_mismatch_fens": mismatch_examples,
        "findings": findings,
    }


def _audit_handoff_role(candidate: dict[str, Any], diagnostic: dict[str, Any]) -> dict[str, Any]:
    post_reply_packets = _packets_by_phase(diagnostic, "post_opponent_reply")
    successor_by_outcome = Counter()
    unlicensed_by_successor = Counter()
    miscalibrated_by_successor = Counter()
    role_examples: list[dict[str, Any]] = []
    max_plies_stage0 = 0
    stage0_total = 0

    for packet in post_reply_packets:
        evidence = packet.get("evidence_terms") or {}
        if not isinstance(evidence, dict):
            continue
        successor = str(evidence.get("successor_selected_skill") or "unknown")
        outcome = str(evidence.get("playout_result") or "not_checked")
        successor_by_outcome[f"{successor}:{outcome}"] += 1
        if successor == "krk.stage0_basin":
            stage0_total += 1
            if outcome == "max_plies":
                max_plies_stage0 += 1
        if evidence.get("provider_selected_without_role_license"):
            unlicensed_by_successor[successor] += 1
        failures = evidence.get("failure_classes") or []
        if "selected_successor_miscalibrated" in failures:
            miscalibrated_by_successor[successor] += 1
        if outcome == "max_plies" and len(role_examples) < 5:
            role_examples.append(_representative(evidence))

    findings = []
    if max_plies_stage0:
        findings.append("stage0_basin remains the dominant failed continuation after box_shrink")
    if unlicensed_by_successor:
        findings.append("some selected successors are not licensed by visible role evidence")
    if miscalibrated_by_successor:
        findings.append("high-score successor selections still fail conversion and need role/contract audit")

    return {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_type": candidate.get("candidate_type"),
        "source_monitor_script": candidate.get("source_monitor_script"),
        **_candidate_governance(candidate),
        "audit_status": "handoff_role_audit_required" if findings else "no_issue_detected",
        "candidate_update": {
            "from": candidate.get("promotion_status", "proposed"),
            "to": "sandbox_ready" if findings else candidate.get("promotion_status", "proposed"),
        },
        "successor_by_outcome": dict(successor_by_outcome),
        "provider_selected_without_role_license_by_successor": dict(unlicensed_by_successor),
        "selected_successor_miscalibrated_by_successor": dict(miscalibrated_by_successor),
        "stage0_basin_failure_ratio": {
            "max_plies": max_plies_stage0,
            "total": stage0_total,
        },
        "representative_failed_handoff_fens": role_examples,
        "findings": findings,
    }


def _audit_quarantine(candidate: dict[str, Any], diagnostic: dict[str, Any], promotion_eval: dict[str, Any] | None) -> dict[str, Any]:
    playouts = diagnostic.get("playouts") or {}
    shadow_count = int(diagnostic.get("shadow_candidate_count") or len(diagnostic.get("shadow_candidates") or []))
    promotion_status = str((promotion_eval or {}).get("promotion_status") or candidate.get("promotion_status") or "")
    failure_reasons = (promotion_eval or {}).get("failure_reasons") or []
    target_failed = int(playouts.get("max_plies", 0) or 0) > 0 or shadow_count > 0 or promotion_status == "quarantine"
    return {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_type": candidate.get("candidate_type"),
        "source_monitor_script": candidate.get("source_monitor_script"),
        **_candidate_governance(candidate),
        "audit_status": "quarantine_confirmed" if target_failed else "promotion_recheck_needed",
        "candidate_update": {
            "from": candidate.get("promotion_status", "quarantined"),
            "to": "quarantined" if target_failed else "proposed",
        },
        "playouts": playouts,
        "shadow_candidate_count": shadow_count,
        "promotion_eval_status": promotion_status,
        "promotion_failure_reasons": failure_reasons,
        "findings": [
            "overlay remains quarantined by target conversion/shadow evidence"
            if target_failed
            else "quarantine evidence was not reproduced in the supplied artifacts"
        ],
    }


def audit_stage7_candidates(
    *,
    candidates_path: Path,
    diagnostic_path: Path,
    promotion_eval_path: Path | None = None,
) -> dict[str, Any]:
    candidate_set = _load_json(candidates_path)
    diagnostic = _load_json(diagnostic_path)
    promotion_eval = _load_json(promotion_eval_path) if promotion_eval_path else None
    candidates = candidate_set.get("candidates") or []
    if not isinstance(candidates, list):
        raise ValueError("candidate set must contain a candidates list")

    audits: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        monitor = candidate.get("source_monitor_script")
        if monitor == "growth.monitor.reward_contract_mismatch":
            audits.append(_audit_reward_contract(candidate, diagnostic))
        elif monitor == "growth.monitor.successor_miscalibration":
            audits.append(_audit_handoff_role(candidate, diagnostic))
        elif monitor == "growth.monitor.stage_overlay_quarantine":
            audits.append(_audit_quarantine(candidate, diagnostic, promotion_eval))
        else:
            audits.append({
                "candidate_id": candidate.get("candidate_id"),
                "candidate_type": candidate.get("candidate_type"),
                "source_monitor_script": monitor,
                **_candidate_governance(candidate),
                "audit_status": "unsupported_monitor",
                "candidate_update": {
                    "from": candidate.get("promotion_status", "proposed"),
                    "to": candidate.get("promotion_status", "proposed"),
                },
                "findings": ["no audit implementation for this monitor"],
            })

    status_counts = Counter(str(audit.get("audit_status")) for audit in audits)
    return {
        "schema_version": "structural_candidate_audit.v1",
        "source_stage": candidate_set.get("source_stage", "stage7_box_shrink"),
        "causal_status": "non_causal",
        "candidate_source": str(candidates_path),
        "diagnostic_source": str(diagnostic_path),
        "promotion_eval_source": str(promotion_eval_path) if promotion_eval_path else None,
        "candidate_count": len(candidates),
        "audit_status_counts": dict(status_counts),
        "audits": audits,
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Structural Candidate Audit",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Candidates: `{payload['candidate_count']}`",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in sorted((payload.get("audit_status_counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Candidate Audits", ""])
    for audit in payload.get("audits", []):
        lines.append(f"### {audit.get('candidate_id')}")
        lines.append("")
        lines.append(f"- Type: `{audit.get('candidate_type')}`")
        lines.append(f"- Monitor: `{audit.get('source_monitor_script')}`")
        lines.append(f"- Audit status: `{audit.get('audit_status')}`")
        lines.append(f"- Growth Governor: `{audit.get('governor_status', 'settling')}`")
        labels = ", ".join(f"`{item}`" for item in audit.get("candidate_diagnostic_labels") or [])
        if labels:
            lines.append(f"- Diagnostic labels: {labels}")
        update = audit.get("candidate_update") or {}
        lines.append(f"- Candidate update: `{update.get('from')}` -> `{update.get('to')}`")
        for finding in audit.get("findings") or []:
            lines.append(f"- Finding: {finding}")
        if audit.get("stage0_basin_failure_ratio"):
            ratio = audit["stage0_basin_failure_ratio"]
            lines.append(f"- Stage0 max-plies ratio: `{ratio.get('max_plies')}/{ratio.get('total')}`")
        if audit.get("reward_contract_mismatch_samples") is not None:
            lines.append(f"- Reward mismatches: `{audit.get('reward_contract_mismatch_samples')}`")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Stage 7 structural candidates")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--promotion-eval", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = audit_stage7_candidates(
        candidates_path=args.candidates,
        diagnostic_path=args.diagnostic,
        promotion_eval_path=args.promotion_eval,
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
