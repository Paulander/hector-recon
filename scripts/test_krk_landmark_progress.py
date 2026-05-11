"""Evaluate compiled KRK topology against explicit landmark rewards.

This is the Stage-2+ companion to test_stage1_backchain.py. It does not prove
full KRK conversion; it measures whether the currently selected stage-labelled
actuators improve a named landmark reward such as edge pressure, fence gain, box
shrinkage, opposition/tempo, or the blended full_krk score.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Optional

import chess

from recon_lite.engine import ReConEngine
from recon_lite.graph import Graph, NodeState
from recon_lite_chess.graph.builder import build_graph_from_topology
from recon_lite_chess.routing import HandoffPacket, ShadowStemCandidate, stable_record_id
from recon_lite_chess.training.krk_landmarks import (
    LANDMARK_LABELS,
    KRK_LANDMARK_STAGE_SPECS,
    select_stage_position,
    worst_reply_reward,
)


def generate_random_krk_position(rng: random.Random) -> chess.Board:
    """Generate a legal White-to-move KRK position with no initial check."""
    squares = list(chess.SQUARES)
    while True:
        wk, bk, wr = rng.sample(squares, 3)
        board = chess.Board(None)
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
        board.turn = chess.WHITE
        if chess.square_distance(wk, bk) <= 1:
            continue
        if not board.is_valid() or board.is_check():
            continue
        return board


def source_stage_names_for_label(label: str) -> tuple[str, ...]:
    if label == "edge_trap":
        return ("Edge_Trap_Close", "Edge_Trap_Enemy_Between", "Edge_Trap_Wrong_Tempo")
    for spec in KRK_LANDMARK_STAGE_SPECS:
        if spec.label == label:
            return spec.source_stage_names
    return ("Full_KRK",)


def canonical_skill_id(label: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in label.lower()).strip("_")
    return f"krk.{normalized or 'unknown'}"


def _top_route_scores(move_details: dict) -> dict:
    scores = {}
    for item in move_details.get("suggestions", [])[:5]:
        actuator = item.get("actuator")
        if actuator:
            scores[str(actuator)] = float(item.get("score", 0.0) or 0.0)
    return scores


def _skill_id_for_suggestion(item: dict) -> str:
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    label = meta.get("curriculum_label") or item.get("curriculum_label")
    if label:
        return canonical_skill_id(str(label))
    stage = item.get("stage") or meta.get("stage")
    return f"krk.stage_{stage}" if stage is not None else "krk.unknown"


def _successor_skill_summary(
    move_details: dict | None,
    *,
    affordance_threshold: float,
    route_conflict_delta: float,
) -> dict:
    """Summarize post-reply continuation options by canonical KRK skill.

    This is diagnostic only. It observes the engine suggestions that already
    exist; it does not feed back into scoring or routing.
    """
    if not move_details:
        return {
            "selected_skill": None,
            "best_score": None,
            "handoff_gap": True,
            "route_conflict": False,
            "skills": {},
            "exports": {},
            "visible_terms": {},
            "visible_successor_affordances": {},
            "missing_afforded_skills": {},
        }
    visible_terms = dict(move_details.get("visible_terms", {}) or {})
    visible_affordances = dict(move_details.get("successor_affordances", {}) or {})

    grouped: dict[str, dict] = {}
    for item in move_details.get("suggestions", []):
        skill_id = _skill_id_for_suggestion(item)
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        curriculum_label = meta.get("curriculum_label") or item.get("curriculum_label")
        visible_affordance = meta.get("visible_successor_affordance") or {}
        score = float(item.get("score", 0.0) or 0.0)
        entry = grouped.setdefault(
            skill_id,
            {
                "score": score,
                "count": 0,
                "best_move": item.get("move"),
                "best_actuator": item.get("actuator"),
                "stage": item.get("stage"),
                "curriculum_label": curriculum_label,
                "visible_successor_affordance": visible_affordance,
            },
        )
        entry["count"] += 1
        if score > float(entry["score"]):
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            curriculum_label = meta.get("curriculum_label") or item.get("curriculum_label")
            visible_affordance = meta.get("visible_successor_affordance") or {}
            entry.update({
                "score": score,
                "best_move": item.get("move"),
                "best_actuator": item.get("actuator"),
                "stage": item.get("stage"),
                "curriculum_label": curriculum_label,
                "visible_successor_affordance": visible_affordance,
            })

    ranked = sorted(grouped.items(), key=lambda kv: kv[1]["score"], reverse=True)
    selected_skill = ranked[0][0] if ranked else None
    best_score = float(ranked[0][1]["score"]) if ranked else None
    second_score = float(ranked[1][1]["score"]) if len(ranked) > 1 else None
    route_conflict = (
        best_score is not None
        and second_score is not None
        and abs(best_score - second_score) <= route_conflict_delta
    )
    route_margin = (
        float(best_score) - float(second_score)
        if best_score is not None and second_score is not None
        else None
    )
    handoff_gap = best_score is None or best_score <= affordance_threshold
    exports = {
        skill_id: max(0.0, min(1.0, float(entry["score"])))
        for skill_id, entry in grouped.items()
    }
    missing_afforded = {
        skill_id: payload
        for skill_id, payload in visible_affordances.items()
        if skill_id not in grouped and float(payload.get("score", 0.0) or 0.0) > affordance_threshold
    }
    selected_contract = _successor_contract_audit(
        selected_skill,
        visible_terms=visible_terms,
        visible_affordances=visible_affordances,
        grouped=grouped,
    )
    visible_eligible_successors = {
        skill_id: payload
        for skill_id, payload in visible_affordances.items()
        if _contract_met(payload, visible_terms)
        and float(payload.get("score", 0.0) or 0.0) > affordance_threshold
    }
    return {
        "selected_skill": selected_skill,
        "best_score": best_score,
        "second_score": second_score,
        "route_margin": route_margin,
        "handoff_gap": bool(handoff_gap),
        "route_conflict": bool(route_conflict),
        "skills": grouped,
        "exports": exports,
        "visible_terms": visible_terms,
        "visible_successor_affordances": visible_affordances,
        "visible_eligible_successors": visible_eligible_successors,
        "missing_afforded_skills": missing_afforded,
        **selected_contract,
    }


def _contract_met(payload: dict, visible_terms: dict) -> bool:
    required = list(payload.get("required_terms", []) or [])
    veto = list(payload.get("veto_terms", []) or [])
    return all(bool(visible_terms.get(term, False)) for term in required) and not any(
        bool(visible_terms.get(term, False)) for term in veto
    )


def _successor_contract_audit(
    selected_skill: str | None,
    *,
    visible_terms: dict,
    visible_affordances: dict,
    grouped: dict,
) -> dict:
    if not selected_skill:
        return {
            "selected_successor_visible_affordance": None,
            "selected_successor_required_terms": [],
            "selected_successor_missing_terms": [],
            "selected_successor_veto_terms": [],
            "selected_successor_contract_met": False,
            "selected_despite_contract_mismatch": False,
            "selected_skill_source": "none",
        }

    visible_payload = visible_affordances.get(selected_skill)
    selected_group = grouped.get(selected_skill, {})
    group_payload = selected_group.get("visible_successor_affordance") or {}
    payload = visible_payload or group_payload or {}
    required = list(payload.get("required_terms", []) or [])
    veto_terms = list(payload.get("veto_terms", []) or [])
    missing = [term for term in required if not bool(visible_terms.get(term, False))]
    active_veto = [term for term in veto_terms if bool(visible_terms.get(term, False))]
    contract_met = bool(payload) and not missing and not active_veto
    return {
        "selected_successor_visible_affordance": (
            float(payload.get("score", 0.0) or 0.0) if payload else None
        ),
        "selected_successor_required_terms": required,
        "selected_successor_missing_terms": missing,
        "selected_successor_veto_terms": active_veto,
        "selected_successor_contract_met": bool(contract_met),
        "selected_despite_contract_mismatch": bool(payload and not contract_met),
        "selected_skill_source": "visible_contract" if visible_payload else "actuator_score",
    }


def _krk_geometry(board: chess.Board) -> dict:
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
        }

    wk_file, wk_rank = chess.square_file(wk_sq), chess.square_rank(wk_sq)
    bk_file, bk_rank = chess.square_file(bk_sq), chess.square_rank(bk_sq)
    wr_file, wr_rank = chess.square_file(wr_sq), chess.square_rank(wr_sq)
    cut_axis = "file" if wr_file == bk_file else "rank" if wr_rank == bk_rank else "none"
    rook_safe = chess.square_distance(wr_sq, bk_sq) > 1 and not board.is_attacked_by(chess.BLACK, wr_sq)
    king_support = chess.square_distance(wk_sq, wr_sq) <= 2 or chess.square_distance(wk_sq, bk_sq) <= 2
    fence_exists = cut_axis != "none" and rook_safe
    box_width = abs(wk_file - bk_file) + 1
    box_height = abs(wk_rank - bk_rank) + 1
    edge_distance = min(bk_file, 7 - bk_file, bk_rank, 7 - bk_rank)
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


def _geometry_evidence(
    *,
    start_board: chess.Board,
    own_move: chess.Move,
    post_reply_fen: str | None,
) -> dict:
    after_own = start_board.copy()
    after_own.push(own_move)
    own = _krk_geometry(after_own)
    evidence = {
        "fence_exists_after_own_move": own["fence_exists"],
        "fence_stable_after_own_move": own["fence_stable"],
        "cut_axis_after_own_move": own["cut_axis"],
        "box_area_after_own_move": own["box_area"],
        "rook_safe_after_own_move": own["rook_safe"],
        "enemy_king_boxed_after_own_move": own["enemy_king_boxed"],
    }
    if post_reply_fen:
        try:
            after_reply = chess.Board(post_reply_fen)
            reply = _krk_geometry(after_reply)
            evidence.update({
                "fence_survived_reply": bool(own["fence_exists"] and reply["fence_exists"]),
                "fence_broken_by_reply": bool(own["fence_exists"] and not reply["fence_exists"]),
                "box_area_after_reply": reply["box_area"],
                "box_area_delta_after_reply": (
                    int(reply["box_area"] - own["box_area"])
                    if reply["box_area"] is not None and own["box_area"] is not None
                    else None
                ),
                "cut_axis_after_reply": reply["cut_axis"],
                "rook_safe_after_reply": reply["rook_safe"],
                "enemy_king_boxed_after_reply": reply["enemy_king_boxed"],
            })
        except Exception:
            evidence.update({
                "fence_survived_reply": None,
                "fence_broken_by_reply": None,
                "box_area_after_reply": None,
                "box_area_delta_after_reply": None,
                "cut_axis_after_reply": "invalid_fen",
            })
    return evidence


def _classify_successor_failure(
    *,
    parent_skill: str,
    local_confirmed: bool,
    conversion_result: str,
    successor_summary: dict,
    high_score_threshold: float,
) -> list[str]:
    if not local_confirmed or conversion_result == "mate":
        return []
    classes: list[str] = []
    selected = successor_summary.get("selected_skill")
    best_score = successor_summary.get("best_score")
    visible_terms = successor_summary.get("visible_terms", {}) or {}
    missing_afforded = successor_summary.get("missing_afforded_skills", {}) or {}
    if selected is None:
        classes.append("successor_absent")
    if successor_summary.get("route_conflict"):
        classes.append("successor_conflict")
    if selected == parent_skill:
        if visible_terms.get("fence_already_satisfied"):
            classes.append("same_skill_reselected_after_satisfaction")
        elif (
            visible_terms.get("fence_needs_repair")
            or not visible_terms.get("fence_exists", False)
            or "krk.fence_maintenance" in missing_afforded
        ):
            classes.append("maintenance_needed_but_not_detected")
    if successor_summary.get("handoff_gap"):
        classes.append("low_support_fallback")
    if best_score is not None and float(best_score) >= high_score_threshold:
        classes.append("selected_successor_miscalibrated")
    if selected == parent_skill and successor_summary.get("handoff_gap"):
        classes.append("maintenance_needed_but_not_detected")
    return classes or ["conversion_failure_unclassified"]


def _trigger_priority(trigger: str) -> int:
    priorities = {
        "repeated_conversion_failure": 1,
        "reward_contract_mismatch": 2,
        "same_skill_loop_after_confirmation": 2,
        "successor_absent": 3,
        "handoff_gap": 3,
        "maintenance_needed_but_not_detected": 3,
        "high_score_conversion_failure": 4,
        "route_conflict": 5,
        "low_affordance_state": 6,
    }
    return priorities.get(trigger, 99)


def _trigger_for_failure_class(failure_class: str) -> str | None:
    mapping = {
        "successor_absent": "successor_absent",
        "successor_conflict": "route_conflict",
        "same_skill_reselected_after_satisfaction": "same_skill_loop_after_confirmation",
        "selected_successor_miscalibrated": "high_score_conversion_failure",
        "low_support_fallback": "low_affordance_state",
        "maintenance_needed_but_not_detected": "maintenance_needed_but_not_detected",
    }
    return mapping.get(failure_class)


def _semantic_alignment_status(
    *,
    reward_confirmed: bool,
    visible_fence_exists: bool,
    fence_survived_reply: Optional[bool],
) -> str:
    if reward_confirmed and visible_fence_exists:
        if fence_survived_reply is True:
            return "reward_visible_fence_aligned_survived"
        if fence_survived_reply is False:
            return "reward_visible_fence_aligned_broken_by_reply"
        return "reward_visible_fence_aligned_reply_not_checked"
    if reward_confirmed and not visible_fence_exists:
        return "reward_contract_mismatch"
    if not reward_confirmed and visible_fence_exists:
        return "visible_contract_without_reward"
    return "neither_reward_nor_visible_contract"


def _semantic_confusion_key(
    *,
    reward_confirmed: bool,
    visible_fence_exists: bool,
    fence_survived_reply: Optional[bool],
    conversion_result: str,
) -> str:
    survived = (
        "not_checked"
        if fence_survived_reply is None
        else "true"
        if fence_survived_reply
        else "false"
    )
    return (
        f"reward={str(bool(reward_confirmed)).lower()}"
        f"|visible_fence={str(bool(visible_fence_exists)).lower()}"
        f"|fence_survived_reply={survived}"
        f"|conversion={conversion_result}"
    )


def _increment_nested_count(container: dict, outer: str, inner: str) -> None:
    bucket = container.setdefault(outer, {})
    bucket[inner] = bucket.get(inner, 0) + 1


def _append_semantic_snapshot(
    stats: dict,
    *,
    bucket: str,
    sample: int,
    start_fen: str,
    move: str,
    post_reply_fen: Optional[str],
    conversion_result: str,
    geometry: dict,
    limit: int = 20,
) -> None:
    snapshots = stats.setdefault("semantic_alignment_snapshots", {})
    records = snapshots.setdefault(bucket, [])
    if len(records) >= limit:
        return
    records.append({
        "sample": sample,
        "start_fen": start_fen,
        "move": move,
        "post_reply_fen": post_reply_fen,
        "conversion_result": conversion_result,
        "fence_exists_after_own_move": geometry.get("fence_exists_after_own_move"),
        "fence_stable_after_own_move": geometry.get("fence_stable_after_own_move"),
        "cut_axis_after_own_move": geometry.get("cut_axis_after_own_move"),
        "fence_survived_reply": geometry.get("fence_survived_reply"),
        "fence_broken_by_reply": geometry.get("fence_broken_by_reply"),
        "box_area_after_own_move": geometry.get("box_area_after_own_move"),
        "box_area_after_reply": geometry.get("box_area_after_reply"),
        "box_area_delta_after_reply": geometry.get("box_area_delta_after_reply"),
    })


def _append_packet(stats: dict, packet: HandoffPacket) -> None:
    stats.setdefault("handoff_packets", []).append(packet.to_dict())


def _append_shadow_candidate(
    stats: dict,
    *,
    trigger: str,
    parent_skill: str,
    board: chess.Board,
    move_details: dict,
    packet_id: str,
    observed_outcome: str,
    priority: int,
    route_scores: Optional[dict] = None,
) -> None:
    candidate = ShadowStemCandidate(
        trigger=trigger,
        owner_router="krk.skill_hub",
        scope="krk",
        parent_skill=parent_skill,
        state_signature=stable_record_id("state", board.board_fen(), board.turn),
        route_scores=route_scores if route_scores is not None else _top_route_scores(move_details),
        packet_id=packet_id,
        observed_outcome=observed_outcome,
        priority=priority,
    )
    stats.setdefault("shadow_candidates", []).append(candidate.to_dict())


def _count_by(records: list[dict], key: str) -> dict:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _count_handoff_packets(records: list[dict]) -> dict:
    counts: dict[str, dict[str, int]] = {}
    for record in records:
        phase = str(record.get("phase", "unknown"))
        status = str(record.get("status", "unknown"))
        by_status = counts.setdefault(phase, {})
        by_status[status] = by_status.get(status, 0) + 1
    return counts


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")


def choose_move_with_engine(
    graph: Graph,
    engine: ReConEngine,
    board: chess.Board,
    max_ticks: int = 200,
    stage_filter: Optional[int] = None,
    suggestion_limit: int = 10,
    successor_affordance_layer_enabled: bool = False,
    forced_successor_skill: Optional[str] = None,
) -> Optional[str]:
    return choose_move_details(
        graph,
        engine,
        board,
        max_ticks=max_ticks,
        stage_filter=stage_filter,
        suggestion_limit=suggestion_limit,
        successor_affordance_layer_enabled=successor_affordance_layer_enabled,
        forced_successor_skill=forced_successor_skill,
    ).get("move")


def choose_move_details(
    graph: Graph,
    engine: ReConEngine,
    board: chess.Board,
    max_ticks: int = 200,
    stage_filter: Optional[int] = None,
    suggestion_limit: int = 10,
    successor_affordance_layer_enabled: bool = False,
    forced_successor_skill: Optional[str] = None,
) -> dict:
    env = {
        "board": board,
        "chosen_move": None,
        "suggested_move": None,
        "blackboard": {"stage_filter": stage_filter} if stage_filter is not None else {},
        "successor_affordance_layer_enabled": successor_affordance_layer_enabled,
    }
    env["blackboard"]["successor_affordance_layer_enabled"] = successor_affordance_layer_enabled

    engine.reset_states()
    root_id = "krk_entry" if "krk_entry" in graph.nodes else None
    if root_id is None:
        for nid, node in graph.nodes.items():
            if node.ntype.name == "SCRIPT" and graph.parent_of(nid) is None:
                root_id = nid
                break
    if root_id:
        graph.nodes[root_id].state = NodeState.REQUESTED

    ticks = 0
    while ticks < max_ticks and env.get("chosen_move") is None:
        ticks += 1
        engine.step(env)
    suggestions = list(env.get("actuator_suggestions", []))
    suggestions.sort(key=lambda item: item.get("score", float("-inf")), reverse=True)
    selected_suggestion = suggestions[0] if suggestions else None
    forced_candidates = []
    if forced_successor_skill:
        forced_candidates = [
            item for item in suggestions
            if _skill_id_for_suggestion(item) == forced_successor_skill
        ]
        forced_candidates.sort(key=lambda item: item.get("score", float("-inf")), reverse=True)
        selected_suggestion = forced_candidates[0] if forced_candidates else None
    selected_move = None
    selected_confidence = None
    selected_actuator = None
    if selected_suggestion:
        raw_move = selected_suggestion.get("move")
        selected_move = raw_move.uci() if hasattr(raw_move, "uci") else raw_move
        selected_confidence = float(selected_suggestion.get("score", 0.0) or 0.0)
        selected_actuator = selected_suggestion.get("actuator")
    elif not forced_successor_skill:
        selected_move = env.get("chosen_move") or env.get("suggested_move")
        selected_confidence = (
            float(env["move_confidence"]) if env.get("move_confidence") is not None else None
        )
        selected_actuator = env.get("suggested_actuator")

    suggestion_source = forced_candidates if forced_successor_skill else suggestions
    clean_suggestions = []
    for item in suggestion_source[:max(0, suggestion_limit)]:
        move = item.get("move")
        clean = dict(item)
        clean["move"] = move.uci() if hasattr(move, "uci") else move
        if "score" in clean:
            clean["score"] = float(clean["score"])
        meta = clean.get("meta")
        if isinstance(meta, dict):
            clean["meta"] = {
                key: (float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value)
                for key, value in meta.items()
            }
        clean_suggestions.append(clean)
    return {
        "move": selected_move,
        "ticks": ticks,
        "confidence": selected_confidence,
        "suggested_actuator": selected_actuator,
        "suggestions": clean_suggestions,
        "forced_successor_skill": forced_successor_skill,
        "forced_successor_available": bool(forced_candidates) if forced_successor_skill else None,
        "visible_terms": dict(env.get("blackboard", {}).get("krk_visible_terms", {}) or {}),
        "successor_affordances": dict(
            env.get("blackboard", {}).get("krk_successor_affordances", {}) or {}
        ),
    }


def oracle_best_reward(board: chess.Board, label: str, lookahead_black: bool) -> float:
    best = -float("inf")
    for move in board.legal_moves:
        reward = worst_reply_reward(board, move, label, use_black_reply=lookahead_black)
        if reward > best:
            best = reward
    return best


def oracle_move_rewards(board: chess.Board, label: str, lookahead_black: bool) -> list[tuple[chess.Move, float]]:
    rewards = [
        (move, worst_reply_reward(board, move, label, use_black_reply=lookahead_black))
        for move in board.legal_moves
    ]
    rewards.sort(key=lambda item: item[1], reverse=True)
    return rewards


def choose_black_reply(
    rng: random.Random,
    board: chess.Board,
    label: str,
    policy: str,
) -> chess.Move | None:
    replies = list(board.legal_moves)
    if not replies:
        return None
    if policy == "random":
        return rng.choice(replies)

    # Adversarial Black chooses the reply that gives White the worst next
    # one-ply landmark opportunity. This is intentionally cheap, not tablebase.
    scored = []
    for reply in replies:
        b2 = board.copy()
        b2.push(reply)
        scored.append((oracle_best_reward(b2, label, lookahead_black=False), reply))
    return min(scored, key=lambda item: item[0])[1]


def play_to_mate(
    graph: Graph,
    engine: ReConEngine,
    board: chess.Board,
    rng: random.Random,
    label: str,
    stage_filter: Optional[int],
    max_plies: int,
    black_policy: str,
    trace: bool = False,
    max_ticks: int = 200,
    suggestion_limit: int = 10,
    trace_max_plies: Optional[int] = None,
    successor_affordance_layer_enabled: bool = False,
    forced_successor_skill: Optional[str] = None,
) -> dict:
    """Run a simple KRK playout using the compiled topology for White moves."""
    b = board.copy()
    white_moves = 0
    events = []
    trace_truncated_events = 0
    first_reply: dict | None = None
    first_successor: dict | None = None

    def record_event(event: dict) -> None:
        nonlocal trace_truncated_events
        if not trace:
            return
        if trace_max_plies is None or len(events) < trace_max_plies:
            events.append(event)
        else:
            trace_truncated_events += 1

    def finish(result: str, ply: int) -> dict:
        payload = {"result": result, "plies": ply}
        if first_reply is not None:
            payload["first_reply"] = first_reply
        if first_successor is not None:
            payload["first_successor"] = first_successor
        if trace:
            payload["final_fen"] = b.fen()
            payload["trace"] = events
            if trace_truncated_events:
                payload["trace_truncated_events"] = trace_truncated_events
        return payload

    for ply in range(max_plies):
        if b.is_checkmate():
            return finish("mate", ply)
        if b.is_stalemate() or b.is_insufficient_material():
            return finish("draw", ply)

        if b.turn == chess.WHITE:
            # Use the stage filter for the tested handoff move, then allow the
            # full topology to convert through lower-stage skills.
            active_stage_filter = stage_filter if white_moves == 0 else None
            active_forced_successor = forced_successor_skill if white_moves == 0 else None
            before_fen = b.fen()
            move_details = choose_move_details(
                graph,
                engine,
                b,
                max_ticks=max_ticks,
                stage_filter=active_stage_filter,
                suggestion_limit=suggestion_limit,
                successor_affordance_layer_enabled=successor_affordance_layer_enabled,
                forced_successor_skill=active_forced_successor,
            )
            move_uci = move_details.get("move")
            capture_successor_now = (
                (forced_successor_skill is not None and white_moves == 0)
                or (forced_successor_skill is None and white_moves == 1)
            )
            if capture_successor_now and first_successor is None:
                first_successor = {
                    "fen": before_fen,
                    "stage_filter": active_stage_filter,
                    "forced_successor_skill": active_forced_successor,
                    "move": move_uci,
                    "engine": move_details,
                }
            if not move_uci:
                record_event({
                    "ply": ply,
                    "turn": "white",
                    "fen": before_fen,
                    "stage_filter": active_stage_filter,
                    "move": None,
                    "engine": move_details,
                })
                return finish("no_move", ply)
            try:
                move = chess.Move.from_uci(move_uci)
            except ValueError:
                record_event({
                    "ply": ply,
                    "turn": "white",
                    "fen": before_fen,
                    "stage_filter": active_stage_filter,
                    "move": move_uci,
                    "engine": move_details,
                })
                return finish("illegal_move", ply)
            if move not in b.legal_moves:
                record_event({
                    "ply": ply,
                    "turn": "white",
                    "fen": before_fen,
                    "stage_filter": active_stage_filter,
                    "move": move_uci,
                    "engine": move_details,
                })
                return finish("illegal_move", ply)
            b.push(move)
            if first_successor is not None and first_successor.get("fen") == before_fen:
                first_successor["resulting_fen"] = b.fen()
            record_event({
                "ply": ply,
                "turn": "white",
                "fen": before_fen,
                "stage_filter": active_stage_filter,
                "move": move_uci,
                "resulting_fen": b.fen(),
                "is_checkmate": b.is_checkmate(),
                "is_stalemate": b.is_stalemate(),
                "engine": move_details,
            })
            white_moves += 1
        else:
            before_fen = b.fen()
            reply = choose_black_reply(rng, b, label, black_policy)
            if reply is None:
                record_event({
                    "ply": ply,
                    "turn": "black",
                    "fen": before_fen,
                    "move": None,
                })
                return finish("no_black_reply", ply)
            b.push(reply)
            if white_moves == 1 and first_reply is None:
                first_reply = {
                    "fen": before_fen,
                    "move": reply.uci(),
                    "resulting_fen": b.fen(),
                    "policy": black_policy,
                }
            record_event({
                "ply": ply,
                "turn": "black",
                "fen": before_fen,
                "move": reply.uci(),
                "resulting_fen": b.fen(),
                "is_checkmate": b.is_checkmate(),
                "is_stalemate": b.is_stalemate(),
            })

    return finish("max_plies", max_plies)


def select_eval_position(
    rng: random.Random,
    label: str,
    mode: str,
    source_stage_names: tuple[str, ...],
) -> chess.Board:
    if mode == "random":
        return generate_random_krk_position(rng)
    if mode == "hybrid" and rng.random() < 0.5:
        return generate_random_krk_position(rng)
    try:
        board = select_stage_position(source_stage_names)
        if board.turn != chess.WHITE or not board.is_valid() or board.is_game_over():
            raise ValueError("unsuitable curriculum position")
        return board
    except Exception:
        return generate_random_krk_position(rng)


def run_counterfactual_successor_sweep(
    graph: Graph,
    engine: ReConEngine,
    *,
    post_reply_fen: str,
    successors: tuple[str, ...],
    rng: random.Random,
    label: str,
    max_plies: int,
    black_policy: str,
    max_ticks: int,
    suggestion_limit: int,
    successor_affordance_layer_enabled: bool,
) -> dict:
    """Try existing successor skills from the same post-reply state.

    This is an offline audit. It forces only the first White move to belong to
    the requested successor skill, then releases control back to the normal
    topology for the rest of the playout.
    """
    board = chess.Board(post_reply_fen)
    results = {}
    for skill_id in successors:
        local_rng = random.Random(rng.randrange(2**32))
        result = play_to_mate(
            graph,
            engine,
            board,
            local_rng,
            label,
            None,
            max_plies,
            black_policy,
            trace=False,
            max_ticks=max_ticks,
            suggestion_limit=suggestion_limit,
            successor_affordance_layer_enabled=successor_affordance_layer_enabled,
            forced_successor_skill=skill_id,
        )
        first_successor = result.get("first_successor") if isinstance(result, dict) else None
        engine_details = (
            first_successor.get("engine")
            if isinstance(first_successor, dict) and isinstance(first_successor.get("engine"), dict)
            else {}
        )
        results[skill_id] = {
            "result": result.get("result"),
            "plies": int(result.get("plies", 0) or 0),
            "first_move": first_successor.get("move") if isinstance(first_successor, dict) else None,
            "forced_successor_available": engine_details.get("forced_successor_available"),
            "confidence": engine_details.get("confidence"),
            "suggested_actuator": engine_details.get("suggested_actuator"),
        }
    return results


def evaluate_landmark_progress(
    topology: Path,
    *,
    label: str = "edge_trap",
    samples: int = 100,
    seed: int = 7,
    stage_filter: int | None = None,
    eps: float = 1e-3,
    position_mode: str = "curriculum",
    source_stage_names: tuple[str, ...] | None = None,
    lookahead_black: bool = True,
    playout_max_plies: int = 0,
    black_policy: str = "adversarial",
    debug_failures: int = 0,
    debug_playouts: int = 0,
    max_ticks: int = 200,
    playout_max_ticks: Optional[int] = None,
    suggestion_limit: int = 10,
    debug_trace_max_plies: Optional[int] = None,
    stop_after_conversion_failures: int = 0,
    max_handoff_packets: int = 0,
    max_shadow_candidates: int = 0,
    shadow_candidates_output: Optional[Path] = None,
    successor_affordance_threshold: float = 0.0,
    route_conflict_delta: float = 0.01,
    high_successor_score_threshold: float = 0.5,
    successor_affordance_layer_enabled: bool = False,
    counterfactual_successors: tuple[str, ...] = (),
    max_counterfactual_sweeps: int = 0,
    verbose: bool = True,
) -> dict:
    rng = random.Random(seed)
    random.seed(seed)
    source_names = (
        source_stage_names
        if source_stage_names
        else source_stage_names_for_label(label)
    )

    graph = build_graph_from_topology(topology)
    engine = ReConEngine(graph)

    stats = {
        "total": 0,
        "no_move": 0,
        "improved": 0,
        "flat": 0,
        "worsened": 0,
        "optimal": 0,
        "avg_reward": 0.0,
        "avg_oracle_reward": 0.0,
        "playouts": {},
        "debug_failures": [],
        "debug_playouts": [],
        "handoff_packets": [],
        "shadow_candidates": [],
        "counterfactual_successor_sweeps": [],
        "one_ply_status_counts": {},
        "conversion_status_counts": {},
        "semantic_alignment_status_counts": {},
        "conversion_by_semantic_alignment_status": {},
        "semantic_alignment_confusion_counts": {},
        "semantic_alignment_snapshots": {},
        "one_ply_status": "not_checked",
        "conversion_status": "not_checked",
    }

    for i in range(samples):
        board = select_eval_position(rng, label, position_mode, source_names)
        move_details = choose_move_details(
            graph,
            engine,
            board,
            max_ticks=max_ticks,
            stage_filter=stage_filter,
            suggestion_limit=suggestion_limit,
            successor_affordance_layer_enabled=successor_affordance_layer_enabled,
        )
        move_uci = move_details.get("move")
        oracle_rewards = oracle_move_rewards(board, label, lookahead_black)
        best_reward = oracle_rewards[0][1] if oracle_rewards else -float("inf")

        stats["total"] += 1
        stats["avg_oracle_reward"] += best_reward
        if not move_uci:
            stats["no_move"] += 1
            stats["one_ply_status_counts"]["no_move"] = (
                stats["one_ply_status_counts"].get("no_move", 0) + 1
            )
            continue
        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            stats["no_move"] += 1
            stats["one_ply_status_counts"]["invalid_move"] = (
                stats["one_ply_status_counts"].get("invalid_move", 0) + 1
            )
            continue
        if move not in board.legal_moves:
            stats["no_move"] += 1
            stats["one_ply_status_counts"]["illegal_move"] = (
                stats["one_ply_status_counts"].get("illegal_move", 0) + 1
            )
            continue

        reward = worst_reply_reward(board, move, label, use_black_reply=lookahead_black)
        stats["avg_reward"] += reward
        local_confirmed = reward > eps
        sample_one_ply_status = (
            "passed" if local_confirmed and reward >= best_reward - eps else "failed"
        )
        stats["one_ply_status_counts"][sample_one_ply_status] = (
            stats["one_ply_status_counts"].get(sample_one_ply_status, 0) + 1
        )
        parent_skill = canonical_skill_id(label)
        own_geometry = _geometry_evidence(
            start_board=board,
            own_move=move,
            post_reply_fen=None,
        )
        visible_fence_exists_after_own = bool(own_geometry.get("fence_exists_after_own_move"))
        reward_term = f"reward_confirmed.{label}"
        post_own_achieved = [reward_term] if local_confirmed else []
        post_own_failed = [] if local_confirmed else [reward_term]
        if visible_fence_exists_after_own:
            post_own_achieved.append("visible_fence_contract_confirmed")
        else:
            post_own_failed.append("visible_fence_contract_confirmed")
        post_own_move_packet = HandoffPacket.create(
            from_skill=parent_skill,
            phase="post_own_move",
            status="confirmed" if local_confirmed else "failed",
            scope="krk.landmark_eval",
            evidence_terms={
                "label": label,
                "fen": board.fen(),
                "move": move_uci,
                "chosen_reward": float(reward),
                "oracle_reward": float(best_reward),
                "stage_filter": stage_filter,
                "reward_confirmed": bool(local_confirmed),
                "visible_fence_contract_confirmed": visible_fence_exists_after_own,
                "reward_contract_mismatch": bool(local_confirmed and not visible_fence_exists_after_own),
                **own_geometry,
            },
            achieved=post_own_achieved,
            failed=post_own_failed,
            continuation_exports={
                f"target_goal.{label}": max(0.0, float(reward)),
            },
            observed_outcome="local_landmark_confirmed" if local_confirmed else "local_landmark_failed",
        )
        _append_packet(stats, post_own_move_packet)
        if reward > eps:
            stats["improved"] += 1
        elif reward < -eps:
            stats["worsened"] += 1
        else:
            stats["flat"] += 1
        if reward >= best_reward - eps:
            stats["optimal"] += 1
        elif len(stats["debug_failures"]) < debug_failures:
            stats["debug_failures"].append({
                "sample": i,
                "fen": board.fen(),
                "board": str(board),
                "chosen_move": move_uci,
                "chosen_reward": reward,
                "oracle_moves": [
                    {"move": move.uci(), "reward": move_reward}
                    for move, move_reward in oracle_rewards[:5]
                ],
                "engine": move_details,
            })

        if verbose and (i + 1) % 10 == 0:
            print(f"{i + 1:4d}/{samples}: improved={stats['improved']} optimal={stats['optimal']}")

        if playout_max_plies > 0:
            result = play_to_mate(
                graph,
                engine,
                board,
                rng,
                label,
                stage_filter,
                playout_max_plies,
                black_policy,
                trace=len(stats["debug_playouts"]) < debug_playouts,
                max_ticks=playout_max_ticks if playout_max_ticks is not None else max_ticks,
                suggestion_limit=suggestion_limit,
                trace_max_plies=debug_trace_max_plies,
                successor_affordance_layer_enabled=successor_affordance_layer_enabled,
            )
            key = result["result"]
            stats["playouts"][key] = stats["playouts"].get(key, 0) + 1
            sample_conversion_status = "passed" if key == "mate" else "failed"
            stats["conversion_status_counts"][sample_conversion_status] = (
                stats["conversion_status_counts"].get(sample_conversion_status, 0) + 1
            )
            survived = key not in {"draw", "illegal_move", "no_move", "no_black_reply"}
            post_reply_fen = (
                result.get("first_reply", {}).get("resulting_fen")
                if isinstance(result.get("first_reply"), dict)
                else None
            )
            reply_geometry = _geometry_evidence(
                start_board=board,
                own_move=move,
                post_reply_fen=post_reply_fen,
            )
            fence_survived_reply = reply_geometry.get("fence_survived_reply")
            semantic_alignment_status = _semantic_alignment_status(
                reward_confirmed=local_confirmed,
                visible_fence_exists=visible_fence_exists_after_own,
                fence_survived_reply=fence_survived_reply,
            )
            stats["semantic_alignment_status_counts"][semantic_alignment_status] = (
                stats["semantic_alignment_status_counts"].get(semantic_alignment_status, 0) + 1
            )
            _increment_nested_count(
                stats["conversion_by_semantic_alignment_status"],
                semantic_alignment_status,
                key,
            )
            confusion_key = _semantic_confusion_key(
                reward_confirmed=local_confirmed,
                visible_fence_exists=visible_fence_exists_after_own,
                fence_survived_reply=fence_survived_reply,
                conversion_result=key,
            )
            stats["semantic_alignment_confusion_counts"][confusion_key] = (
                stats["semantic_alignment_confusion_counts"].get(confusion_key, 0) + 1
            )
            if semantic_alignment_status != "reward_visible_fence_aligned_survived":
                _append_semantic_snapshot(
                    stats,
                    bucket=semantic_alignment_status,
                    sample=i,
                    start_fen=board.fen(),
                    move=move_uci,
                    post_reply_fen=post_reply_fen,
                    conversion_result=key,
                    geometry=reply_geometry,
                )
            successor_summary = _successor_skill_summary(
                (
                    result.get("first_successor", {}).get("engine")
                    if isinstance(result.get("first_successor"), dict)
                    else None
                ),
                affordance_threshold=successor_affordance_threshold,
                route_conflict_delta=route_conflict_delta,
            )
            handoff_gap = bool(local_confirmed and survived and successor_summary["handoff_gap"])
            route_conflict = bool(local_confirmed and successor_summary["route_conflict"])
            failure_classes = _classify_successor_failure(
                parent_skill=parent_skill,
                local_confirmed=local_confirmed,
                conversion_result=key,
                successor_summary=successor_summary,
                high_score_threshold=high_successor_score_threshold,
            )
            post_reply_packet = HandoffPacket.create(
                from_skill=parent_skill,
                phase="post_opponent_reply",
                status="confirmed" if local_confirmed and survived and not handoff_gap else "failed",
                scope="krk.landmark_eval",
                evidence_terms={
                    "label": label,
                    "fen": board.fen(),
                    "move": move_uci,
                    "black_reply": (
                        result.get("first_reply", {}).get("move")
                        if isinstance(result.get("first_reply"), dict)
                        else None
                    ),
                    "post_reply_fen": (
                        post_reply_fen
                    ),
                    "survived": bool(survived),
                    "semantic_alignment_status": semantic_alignment_status,
                    "reward_confirmed": bool(local_confirmed),
                    "visible_fence_contract_confirmed": visible_fence_exists_after_own,
                    "reward_contract_mismatch": bool(local_confirmed and not visible_fence_exists_after_own),
                    "handoff_gap": handoff_gap,
                    "route_conflict": route_conflict,
                    "failure_classes": failure_classes,
                    "successor_selected_skill": successor_summary["selected_skill"],
                    "successor_best_score": successor_summary["best_score"],
                    "successor_second_score": successor_summary.get("second_score"),
                    "route_margin": successor_summary.get("route_margin"),
                    "selected_successor_visible_affordance": successor_summary.get("selected_successor_visible_affordance"),
                    "selected_successor_required_terms": successor_summary.get("selected_successor_required_terms"),
                    "selected_successor_missing_terms": successor_summary.get("selected_successor_missing_terms"),
                    "selected_successor_veto_terms": successor_summary.get("selected_successor_veto_terms"),
                    "selected_successor_contract_met": successor_summary.get("selected_successor_contract_met"),
                    "selected_despite_contract_mismatch": successor_summary.get("selected_despite_contract_mismatch"),
                    "selected_skill_source": successor_summary.get("selected_skill_source"),
                    "successor_skills": successor_summary["skills"],
                    "visible_terms": successor_summary["visible_terms"],
                    "visible_successor_affordances": successor_summary["visible_successor_affordances"],
                    "visible_eligible_successors": successor_summary["visible_eligible_successors"],
                    "missing_afforded_skills": successor_summary["missing_afforded_skills"],
                    "playout_result": key,
                    "plies": int(result.get("plies", 0) or 0),
                    "stage_filter": stage_filter,
                    **reply_geometry,
                },
                achieved=(
                    [
                        *(
                            ["survived_opponent_reply"]
                            if local_confirmed and survived
                            else []
                        ),
                        *(
                            ["visible_fence_survived_reply"]
                            if fence_survived_reply is True
                            else []
                        ),
                        *(
                            ["successor_affordance"]
                            if local_confirmed and survived and not handoff_gap
                            else []
                        ),
                    ]
                ),
                failed=(
                    [
                        *(
                            ["survived_opponent_reply"]
                            if not (local_confirmed and survived)
                            else []
                        ),
                        *(
                            ["visible_fence_survived_reply"]
                            if fence_survived_reply is False
                            else []
                        ),
                        *(
                            ["successor_affordance"]
                            if handoff_gap
                            else []
                        ),
                    ]
                ),
                continuation_exports=successor_summary["exports"]
                or {"krk.continue_conversion": 1.0 if survived else 0.0},
                observed_outcome=key,
            )
            _append_packet(stats, post_reply_packet)
            conversion_status = "passed" if key == "mate" else "failed"
            playout_packet = HandoffPacket.create(
                from_skill=parent_skill,
                phase="playout_summary",
                status="confirmed" if conversion_status == "passed" else "failed",
                scope="krk.landmark_eval",
                evidence_terms={
                    "label": label,
                    "fen": board.fen(),
                    "move": move_uci,
                    "conversion_status": conversion_status,
                    "semantic_alignment_status": semantic_alignment_status,
                    "failure_classes": failure_classes,
                    "playout_result": key,
                    "max_plies": playout_max_plies,
                    "plies": int(result.get("plies", 0) or 0),
                },
                achieved=["conversion_to_mate"] if conversion_status == "passed" else [],
                failed=[] if conversion_status == "passed" else ["conversion_to_mate"],
                observed_outcome=key,
            )
            _append_packet(stats, playout_packet)
            if local_confirmed and not visible_fence_exists_after_own:
                _append_shadow_candidate(
                    stats,
                    trigger="reward_contract_mismatch",
                    parent_skill=parent_skill,
                    board=board,
                    move_details=move_details,
                    packet_id=post_reply_packet.packet_id,
                    observed_outcome=key,
                    priority=_trigger_priority("reward_contract_mismatch"),
                    route_scores={
                        skill_id: float(entry.get("score", 0.0) or 0.0)
                        for skill_id, entry in successor_summary["skills"].items()
                    },
                )
            if (
                local_confirmed
                and key != "mate"
                and counterfactual_successors
                and (
                    max_counterfactual_sweeps <= 0
                    or len(stats["counterfactual_successor_sweeps"]) < max_counterfactual_sweeps
                )
                and post_reply_fen
            ):
                sweep = run_counterfactual_successor_sweep(
                    graph,
                    engine,
                    post_reply_fen=post_reply_fen,
                    successors=counterfactual_successors,
                    rng=rng,
                    label=label,
                    max_plies=playout_max_plies,
                    black_policy=black_policy,
                    max_ticks=playout_max_ticks if playout_max_ticks is not None else max_ticks,
                    suggestion_limit=suggestion_limit,
                    successor_affordance_layer_enabled=successor_affordance_layer_enabled,
                )
                stats["counterfactual_successor_sweeps"].append({
                    "sample": i,
                    "state_signature": stable_record_id("state", chess.Board(post_reply_fen).board_fen(), chess.WHITE),
                    "start_fen": board.fen(),
                    "post_reply_fen": post_reply_fen,
                    "actual_selected_successor": successor_summary["selected_skill"],
                    "actual_result": key,
                    "actual_route_scores": {
                        skill_id: float(entry.get("score", 0.0) or 0.0)
                        for skill_id, entry in successor_summary["skills"].items()
                    },
                    "counterfactual_results": sweep,
                    "failure_classes": failure_classes,
                })
            if local_confirmed and key != "mate":
                trigger = "repeated_conversion_failure" if key in {"draw", "max_plies"} else "handoff_gap"
                _append_shadow_candidate(
                    stats,
                    trigger=trigger,
                    parent_skill=parent_skill,
                    board=board,
                    move_details=move_details,
                    packet_id=playout_packet.packet_id,
                    observed_outcome=key,
                    priority=_trigger_priority(trigger),
                    route_scores={
                        skill_id: float(entry.get("score", 0.0) or 0.0)
                        for skill_id, entry in successor_summary["skills"].items()
                    },
                )
            if local_confirmed and key != "mate":
                emitted = set()
                for failure_class in failure_classes:
                    trigger = _trigger_for_failure_class(failure_class)
                    if not trigger or trigger in emitted:
                        continue
                    emitted.add(trigger)
                    _append_shadow_candidate(
                        stats,
                        trigger=trigger,
                        parent_skill=parent_skill,
                        board=board,
                        move_details=move_details,
                        packet_id=post_reply_packet.packet_id,
                        observed_outcome=key,
                        priority=_trigger_priority(trigger),
                        route_scores={
                            skill_id: float(entry.get("score", 0.0) or 0.0)
                            for skill_id, entry in successor_summary["skills"].items()
                        },
                    )
            if key != "mate" and len(stats["debug_playouts"]) < debug_playouts:
                stats["debug_playouts"].append({
                    "sample": i,
                    "start_fen": board.fen(),
                    "start_board": str(board),
                    **result,
                })
            if (
                local_confirmed
                and key != "mate"
                and stop_after_conversion_failures > 0
                and len(stats.get("shadow_candidates", [])) >= stop_after_conversion_failures
            ):
                if verbose:
                    print(
                        "Stopping early after "
                        f"{stop_after_conversion_failures} conversion failures."
                    )
                break

    if stats["total"]:
        stats["avg_reward"] /= stats["total"]
        stats["avg_oracle_reward"] /= stats["total"]

    stats["label"] = label
    stats["source_stage_names"] = list(source_names)
    stats["successor_affordance_layer_enabled"] = successor_affordance_layer_enabled
    evaluated = max(0, stats["total"] - stats["no_move"])
    stats["one_ply_status"] = (
        "passed"
        if evaluated > 0
        and stats["no_move"] == 0
        and stats["worsened"] == 0
        and stats["optimal"] == stats["total"]
        else "failed"
        if stats["total"] > 0
        else "not_checked"
    )

    playout_total = sum(int(value) for value in stats.get("playouts", {}).values())
    mate_total = int(stats.get("playouts", {}).get("mate", 0))
    if playout_max_plies <= 0 or playout_total == 0:
        stats["conversion_status"] = "not_checked"
    elif mate_total == playout_total:
        stats["conversion_status"] = "passed"
    else:
        stats["conversion_status"] = "failed"
    stats["conversion_failure_count"] = max(0, playout_total - mate_total)
    if playout_max_plies <= 0 and not stats["conversion_status_counts"]:
        stats["conversion_status_counts"]["not_checked"] = stats["total"]

    full_handoff_packets = list(stats.get("handoff_packets", []))
    full_shadow_candidates = list(stats.get("shadow_candidates", []))
    stats["handoff_packet_count"] = len(full_handoff_packets)
    stats["shadow_candidate_count"] = len(full_shadow_candidates)
    stats["counterfactual_successor_sweep_count"] = len(
        stats.get("counterfactual_successor_sweeps", [])
    )
    stats["handoff_packet_counts_by_phase"] = _count_handoff_packets(full_handoff_packets)
    stats["shadow_candidate_counts_by_trigger"] = _count_by(full_shadow_candidates, "trigger")
    if shadow_candidates_output is not None:
        _write_jsonl(shadow_candidates_output, full_shadow_candidates)
    if max_handoff_packets > 0:
        stats["handoff_packets"] = stats["handoff_packets"][:max_handoff_packets]
        stats["handoff_packets_truncated"] = max(
            0,
            stats["handoff_packet_count"] - len(stats["handoff_packets"]),
        )
    if max_shadow_candidates > 0:
        stats["shadow_candidates"] = stats["shadow_candidates"][:max_shadow_candidates]
        stats["shadow_candidates_truncated"] = max(
            0,
            stats["shadow_candidate_count"] - len(stats["shadow_candidates"]),
        )
    if not stats["debug_failures"]:
        stats.pop("debug_failures", None)
    if not stats["debug_playouts"]:
        stats.pop("debug_playouts", None)
    if not stats["handoff_packets"]:
        stats.pop("handoff_packets", None)
    if not stats["shadow_candidates"]:
        stats.pop("shadow_candidates", None)
    if not stats["counterfactual_successor_sweeps"]:
        stats.pop("counterfactual_successor_sweeps", None)
    return stats


def print_landmark_results(stats: dict, *, black_policy: str = "adversarial", playout_max_plies: int = 0) -> None:
    print("\nKRK Landmark Progress Evaluation")
    print("-" * 60)
    print(f"Label: {stats.get('label', '')}")
    print(f"Source stages: {', '.join(stats.get('source_stage_names', []))}")
    print(f"Total evaluated: {stats['total']}")
    print(f"No move: {stats['no_move']}")
    print(f"Improved: {stats['improved']} ({stats['improved']/stats['total']*100:.1f}%)")
    print(f"Flat:     {stats['flat']} ({stats['flat']/stats['total']*100:.1f}%)")
    print(f"Worsened: {stats['worsened']} ({stats['worsened']/stats['total']*100:.1f}%)")
    print(f"Optimal:  {stats['optimal']} ({stats['optimal']/stats['total']*100:.1f}%)")
    print(f"Avg chosen reward: {stats['avg_reward']:.4f}")
    print(f"Avg oracle reward: {stats['avg_oracle_reward']:.4f}")
    print(f"One-ply status: {stats.get('one_ply_status', 'not_checked')}")
    print(f"Conversion status: {stats.get('conversion_status', 'not_checked')}")
    if playout_max_plies > 0:
        print(f"Playout results ({black_policy} Black, max {playout_max_plies} plies): {stats['playouts']}")
    if "handoff_packet_count" in stats:
        print(f"Handoff packets: {stats['handoff_packet_count']}")
    if "shadow_candidate_count" in stats:
        print(f"Shadow candidates: {stats['shadow_candidate_count']}")
    if stats.get("counterfactual_successor_sweep_count"):
        print(f"Counterfactual successor sweeps: {stats['counterfactual_successor_sweep_count']}")
    if stats.get("semantic_alignment_status_counts"):
        print(f"Semantic alignment: {stats['semantic_alignment_status_counts']}")
    if stats.get("debug_failures"):
        print("\nDebug failures")
        print("-" * 60)
        for item in stats["debug_failures"]:
            print(f"Sample {item['sample']} FEN: {item['fen']}")
            print(item["board"])
            print(f"Chosen: {item['chosen_move']} reward={item['chosen_reward']:.4f}")
            print("Oracle:", ", ".join(
                f"{entry['move']}={entry['reward']:.4f}" for entry in item["oracle_moves"]
            ))
            print(
                "Engine:",
                f"actuator={item['engine'].get('suggested_actuator')}",
                f"confidence={item['engine'].get('confidence')}",
            )
    if stats.get("debug_playouts"):
        print("\nDebug playouts")
        print("-" * 60)
        for item in stats["debug_playouts"]:
            print(f"Sample {item['sample']} result={item['result']} plies={item['plies']}")
            print(f"Start FEN: {item['start_fen']}")
            print(item["start_board"])
            trace = item.get("trace", [])
            for event in trace[:12]:
                print(
                    f"  ply={event.get('ply')} {event.get('turn')} "
                    f"move={event.get('move')} stage_filter={event.get('stage_filter')}"
                )
                engine = event.get("engine")
                if isinstance(engine, dict):
                    print(
                        "    engine:",
                        f"actuator={engine.get('suggested_actuator')}",
                        f"confidence={engine.get('confidence')}",
                    )
    print(json.dumps(stats, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate KRK landmark reward progress")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--label", choices=LANDMARK_LABELS, default="edge_trap")
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--stage-filter", type=int, default=None)
    parser.add_argument("--eps", type=float, default=1e-3)
    parser.add_argument("--position-mode", choices=["curriculum", "random", "hybrid"], default="curriculum")
    parser.add_argument("--source-stage-names", type=str, default=None,
                        help="Comma-separated override for curriculum source stages")
    parser.add_argument("--lookahead-black", action="store_true", default=True)
    parser.add_argument("--no-lookahead-black", action="store_false", dest="lookahead_black")
    parser.add_argument("--playout-max-plies", type=int, default=0,
                        help="If >0, also run full KRK playouts up to this ply limit")
    parser.add_argument("--black-policy", choices=["random", "adversarial"], default="adversarial")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--debug-failures", type=int, default=0,
                        help="Include this many non-oracle selected positions with board/move diagnostics")
    parser.add_argument("--debug-playouts", type=int, default=0,
                        help="Include this many non-mating playout traces with move-by-move diagnostics")
    parser.add_argument("--max-ticks", type=int, default=200,
                        help="Max ReCoN ticks for the evaluated one-ply move")
    parser.add_argument("--playout-max-ticks", type=int, default=None,
                        help="Max ReCoN ticks for each White move inside playouts (default: --max-ticks)")
    parser.add_argument("--suggestion-limit", type=int, default=10,
                        help="Number of actuator suggestions retained per engine decision")
    parser.add_argument("--debug-trace-max-plies", type=int, default=None,
                        help="If set, truncate saved debug playout traces to this many ply events")
    parser.add_argument("--stop-after-conversion-failures", type=int, default=0,
                        help="If >0, stop after this many non-mating conversion failures")
    parser.add_argument("--max-handoff-packets", type=int, default=0,
                        help="If >0, truncate saved handoff packet records to this count")
    parser.add_argument("--max-shadow-candidates", type=int, default=0,
                        help="If >0, truncate saved shadow candidate records to this count")
    parser.add_argument("--shadow-candidates-output", type=Path, default=None,
                        help="Optional JSONL path for full shadow growth-candidate records")
    parser.add_argument("--successor-affordance-threshold", type=float, default=0.0,
                        help="Score threshold below which post-reply successor skill affordance is a handoff gap")
    parser.add_argument("--route-conflict-delta", type=float, default=0.01,
                        help="Top-two successor skill scores within this delta count as a route conflict")
    parser.add_argument("--high-successor-score-threshold", type=float, default=0.5,
                        help="Failed conversion with successor score at/above this threshold is miscalibrated")
    parser.add_argument("--enable-successor-affordance-layer", action="store_true",
                        help="Enable visible KRK successor-affordance layer as a causal score bias")
    parser.add_argument("--counterfactual-successors", type=str, default=None,
                        help="Comma-separated canonical successor skill IDs to force on failed post-reply states")
    parser.add_argument("--max-counterfactual-sweeps", type=int, default=0,
                        help="If >0, limit forced-successor sweeps to this many failed samples")
    args = parser.parse_args()

    source_names = (
        tuple(name.strip() for name in args.source_stage_names.split(",") if name.strip())
        if args.source_stage_names
        else None
    )
    stats = evaluate_landmark_progress(
        args.topology,
        label=args.label,
        samples=args.samples,
        seed=args.seed,
        stage_filter=args.stage_filter,
        eps=args.eps,
        position_mode=args.position_mode,
        source_stage_names=source_names,
        lookahead_black=args.lookahead_black,
        playout_max_plies=args.playout_max_plies,
        black_policy=args.black_policy,
        debug_failures=args.debug_failures,
        debug_playouts=args.debug_playouts,
        max_ticks=args.max_ticks,
        playout_max_ticks=args.playout_max_ticks,
        suggestion_limit=args.suggestion_limit,
        debug_trace_max_plies=args.debug_trace_max_plies,
        stop_after_conversion_failures=args.stop_after_conversion_failures,
        max_handoff_packets=args.max_handoff_packets,
        max_shadow_candidates=args.max_shadow_candidates,
        shadow_candidates_output=args.shadow_candidates_output,
        successor_affordance_threshold=args.successor_affordance_threshold,
        route_conflict_delta=args.route_conflict_delta,
        high_successor_score_threshold=args.high_successor_score_threshold,
        successor_affordance_layer_enabled=args.enable_successor_affordance_layer,
        counterfactual_successors=tuple(
            item.strip()
            for item in (args.counterfactual_successors or "").split(",")
            if item.strip()
        ),
        max_counterfactual_sweeps=args.max_counterfactual_sweeps,
        verbose=True,
    )
    print_landmark_results(stats, black_policy=args.black_policy, playout_max_plies=args.playout_max_plies)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
