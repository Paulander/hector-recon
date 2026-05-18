"""Evaluate compiled KRK topology against explicit landmark rewards.

This is the Stage-2+ companion to test_stage1_backchain.py. It does not prove
full KRK conversion; it measures whether the currently selected stage-labelled
actuators improve a named landmark reward such as edge pressure, fence gain, box
shrinkage, opposition/tempo, or the blended full_krk score.
"""

from __future__ import annotations

import argparse
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
import json
import random
import sys
import time
from pathlib import Path
from typing import Optional

import chess

from recon_lite.engine import ReConEngine
from recon_lite.graph import Graph, NodeState
from recon_lite_chess.graph.builder import build_graph_from_topology
from recon_lite_chess.routing import (
    CandidateMoveFrame,
    HandoffPacket,
    MoveShapeRoleSpec,
    ShadowStemCandidate,
    stable_record_id,
)
from recon_lite_chess.training.krk_landmarks import (
    LANDMARK_LABELS,
    KRK_LANDMARK_STAGE_SPECS,
    select_stage_position,
    worst_reply_reward,
)


def _materialize_explicit_support_roles(graph: Graph, env: dict) -> None:
    """Materialize compiled visible role SCRIPTs for explicit support tests.

    The executor may evaluate actuator terminals before successor-role SCRIPTs
    in short diagnostic runs. For the opt-in support-adapter sandbox, we make
    the visible role terms available by running only compiled
    `visible_successor_affordance` SCRIPT predicates. This does not request any
    provider and is disabled unless explicit role-provider support is enabled.
    """
    blackboard = env.get("blackboard", {})
    if not blackboard.get("explicit_role_provider_support_enabled", False):
        return
    board = env.get("board")
    if board is None:
        return
    try:
        from recon_lite_chess.krk_baseline_nodes import _compute_krk_context_terms
    except Exception:
        return
    terms = dict(_compute_krk_context_terms(board) or {})
    terms.update(blackboard.get("krk_dynamic_context_terms", {}) or {})
    blackboard.setdefault("krk_visible_terms", {}).update(terms)
    for node in graph.nodes.values():
        meta = getattr(node, "meta", {}) or {}
        if not meta.get("visible_successor_affordance"):
            continue
        predicate = getattr(node, "predicate", None)
        if predicate is None:
            continue
        try:
            predicate(node, env)
        except Exception:
            continue


def _materialize_stage7_sandbox_providers(graph: Graph, env: dict) -> None:
    """Materialize compiled opt-in Stage 7 provider terminals once per decision.

    These terminals are ordinary visible ReCoN nodes, but in short diagnostic
    runs they may be reached after learned actuator suggestions have already
    stabilized. Running only the explicitly compiled Stage 7 sandbox provider
    predicates here makes their visible licenses available to the same
    suggestion competition without directly selecting or requesting a provider.
    """
    blackboard = env.get("blackboard", {})
    if not (
        blackboard.get("stage7_king_tempo_enabled", False)
        or blackboard.get("stage7_drive_repair_enabled", False)
        or blackboard.get("stage7_post_king_tempo_enabled", False)
        or blackboard.get("stage7_post_box_continuation_enabled", False)
    ):
        return
    for node in graph.nodes.values():
        meta = getattr(node, "meta", {}) or {}
        if not (
            meta.get("stage7_king_tempo_provider")
            or meta.get("stage7_drive_repair_provider")
            or meta.get("stage7_post_king_tempo_provider")
            or meta.get("stage7_post_box_continuation_provider")
        ):
            continue
        predicate = getattr(node, "predicate", None)
        if predicate is None:
            continue
        try:
            predicate(node, env)
        except Exception:
            continue


def _materialize_plan_capsule_markers(graph: Graph, env: dict) -> None:
    """Materialize opt-in Plan Capsule marker predicates for diagnostics.

    These markers are non-requesting audit nodes. They only record visible
    entry/progress/exit/abort evidence when `plan_capsule_sandbox_enabled` is
    explicitly true.
    """
    blackboard = env.get("blackboard", {})
    if not blackboard.get("plan_capsule_sandbox_enabled", False):
        return
    try:
        from recon_lite_chess.krk_baseline_nodes import _compute_krk_context_terms
    except Exception:
        return
    board = env.get("board")
    if board is not None:
        terms = dict(_compute_krk_context_terms(board) or {})
        terms.update(blackboard.get("krk_dynamic_context_terms", {}) or {})
        blackboard.setdefault("krk_visible_terms", {}).update(terms)
    for node in graph.nodes.values():
        meta = getattr(node, "meta", {}) or {}
        if not meta.get("plan_capsule_marker"):
            continue
        predicate = getattr(node, "predicate", None)
        if predicate is None:
            continue
        try:
            predicate(node, env)
        except Exception:
            continue


def _stage7_plan_capsule_default_state(*, ttl: int) -> dict:
    return {
        "plan_id": "krk.post_box_shrink_continuation",
        "plan_status": "candidate",
        "plan_started_ply": None,
        "ttl_remaining": int(ttl),
        "ttl_white_moves": int(ttl),
        "owned_white_move_count": 0,
        "progress_terms_confirmed": [],
        "entry_terms_confirmed": [],
        "exit_terms_confirmed": [],
        "abort_terms_confirmed": [],
        "selected_owned_provider": None,
        "selected_owned_move": None,
        "owned_roles": [
            "krk.post_box_shrink_continuation",
            "krk.box_shrink_to_drive_repair",
            "krk.box_shrink_to_fence_repair",
        ],
        "owned_providers": [
            "krk.post_box_shrink_continuation",
            "krk.drive_to_edge",
            "krk.fence_established",
            "krk.edge_trap_close",
            "krk.edge_trap_enemy_between",
            "krk.edge_trap_wrong_tempo",
        ],
        "handoff_exports": {
            "krk.drive_to_edge": 1.0,
            "krk.fence_established": 0.75,
            "krk.edge_trap_close": 0.75,
        },
        "handoff_target": None,
        "abort_reason": None,
        "exit_reason": None,
        "causal_status": "sandbox_opt_in",
        "self_model": {
            "reliability_by_context": {},
            "avg_plies_to_exit": None,
            "avg_progress_per_owned_move": None,
            "abort_rate": None,
            "handoff_success_rate": None,
            "overcommitment_rate": None,
            "premature_abort_rate": None,
            "short_term_reward_weight": 0.25,
            "long_term_conversion_weight": 0.75,
            "commitment_bias": 0.0,
            "confidence": 0.0,
        },
    }


def _prepare_stage7_plan_capsule_state(
    *,
    current_state: dict | None,
    marker: dict | None,
    ttl: int,
    current_ply: int | None = None,
) -> dict:
    state = dict(current_state or _stage7_plan_capsule_default_state(ttl=ttl))
    state.setdefault("plan_id", "krk.post_box_shrink_continuation")
    state.setdefault("ttl_white_moves", int(ttl))
    state.setdefault("ttl_remaining", int(ttl))
    state.setdefault("owned_white_move_count", 0)
    marker = marker if isinstance(marker, dict) else {}
    state["entry_terms_confirmed"] = list(marker.get("entry_terms_met", []) or [])
    state["exit_terms_confirmed"] = list(marker.get("exit_terms_met", []) or [])
    state["abort_terms_confirmed"] = list(marker.get("abort_terms_met", []) or [])
    status = str(state.get("plan_status") or "candidate")
    if status in {"exited", "aborted", "expired"}:
        return state
    entry_confirmed = bool(marker.get("entry_confirmed"))
    exit_terms_met = list(marker.get("exit_terms_met", []) or [])
    owned_count = int(state.get("owned_white_move_count", 0) or 0)
    strong_exit = bool(
        {
            "mate_in_one_available",
            "mate_basin_or_stage0_finish_visibly_licensed",
        }.intersection(exit_terms_met)
    )
    exit_allowed = (
        bool(exit_terms_met)
        and (
            (status == "candidate" and not entry_confirmed and strong_exit)
            or (
                status in {"active", "progress_confirmed"}
                and (owned_count > 0 or strong_exit)
            )
        )
    )
    if exit_allowed:
        state["plan_status"] = "exited"
        state["exit_reason"] = "exit_terms_confirmed"
        state["handoff_target"] = ",".join(exit_terms_met)
        return state
    if marker.get("abort_terms_met") or marker.get("abort_confirmed"):
        state["plan_status"] = "aborted"
        state["abort_reason"] = "abort_terms_confirmed"
        return state
    if int(state.get("ttl_remaining", 0) or 0) <= 0 and status != "candidate":
        state["plan_status"] = "expired"
        state["exit_reason"] = "ttl_expired"
        return state
    if status == "candidate" and entry_confirmed:
        state["plan_status"] = "active"
        state["plan_started_ply"] = current_ply
        state["ttl_remaining"] = int(ttl)
        state["ttl_white_moves"] = int(ttl)
    return state


def _advance_stage7_plan_capsule_state_after_decision(
    state: dict | None,
    move_details: dict,
    *,
    current_ply: int,
) -> dict | None:
    if not state:
        return state
    updated = dict(state)
    if updated.get("plan_status") not in {"active", "progress_confirmed"}:
        return updated
    selected = move_details.get("selected_suggestion")
    meta = selected.get("meta", {}) if isinstance(selected, dict) else {}
    if not isinstance(meta, dict):
        meta = {}
    license_payload = (
        meta.get("visible_stage7_plan_capsule_license")
        or (
            selected.get("visible_stage7_plan_capsule_license")
            if isinstance(selected, dict)
            else None
        )
        or {}
    )
    if not isinstance(license_payload, dict) or not license_payload:
        updated["last_unowned_ply"] = current_ply
        return updated
    updated["plan_status"] = "progress_confirmed"
    updated["owned_white_move_count"] = int(updated.get("owned_white_move_count", 0) or 0) + 1
    updated["ttl_remaining"] = max(0, int(updated.get("ttl_remaining", 0) or 0) - 1)
    updated["selected_owned_provider"] = license_payload.get("provider_skill_id")
    updated["selected_owned_move"] = license_payload.get("move")
    progress_terms = list(updated.get("progress_terms_confirmed", []) or [])
    for term in license_payload.get("progress_terms", []) or []:
        if term not in progress_terms:
            progress_terms.append(term)
    updated["progress_terms_confirmed"] = progress_terms
    updated["last_owned_ply"] = current_ply
    if updated["ttl_remaining"] <= 0:
        updated["plan_status"] = "expired"
        updated["exit_reason"] = "ttl_expired_after_owned_window"
    return updated


PROFILE_TIMER_KEYS = (
    "total_wall_time",
    "choose_move_details_time",
    "engine_step_time",
    "actuator_scoring_time",
    "teacher_features_time",
    "goal_distance_time",
    "worst_reply_reward_time",
    "choose_black_reply_time",
    "move_shape_audit_time",
    "stagnation_summary_time",
    "json_trace_serialization_time",
)

PROFILE_COUNT_KEYS = (
    "samples",
    "playout_decisions",
    "engine_ticks",
    "actuator_evaluations",
    "legal_moves_scored",
    "board_copy_calls",
    "teacher_features_calls",
    "worst_reply_reward_calls",
    "oracle_best_reward_calls",
    "cache_hits",
    "cache_misses",
)

COMPOSITION_PROFILE_NONE = "none"
COMPOSITION_PROFILE_HANDOFF_V1 = "handoff_composition_v1"

HANDOFF_COMPOSITION_V1_SETTINGS = {
    "successor_affordance_layer_enabled": True,
    "successor_role_license_enabled": True,
    "successor_role_scoped_move_shape_enabled": True,
    "successor_role_scoped_move_shape_bonus": 0.05,
    "stagnation_breaker_enabled": True,
    "stagnation_breaker_bonus": 0.5,
    "post_break_continuation_enabled": True,
    "post_break_continuation_bonus": 0.25,
    "successor_stage0_drift_penalty": 6.0,
}

HANDOFF_COMPOSITION_V1_VALIDATION_DEFAULTS = {
    "enable_diagnostic_caches": True,
    "parallel_workers": 8,
    "chunk_size": 25,
}

COMPOSITION_PROFILES = {
    COMPOSITION_PROFILE_HANDOFF_V1: {
        "schema_version": "composition_profile.v1",
        "profile_id": COMPOSITION_PROFILE_HANDOFF_V1,
        "domain": "KRK",
        "experimental_profile": True,
        "default_policy": False,
        "description": (
            "Stable experimental KRK handoff-composition profile: visible "
            "successor affordances, role licenses, role-scoped move shapes, "
            "stagnation breaker, post-break continuation, and stage0 drift "
            "penalty. This is opt-in and domain-scoped, not the universal "
            "Hector default policy."
        ),
        "settings": HANDOFF_COMPOSITION_V1_SETTINGS,
        "recommended_validation_defaults": HANDOFF_COMPOSITION_V1_VALIDATION_DEFAULTS,
        "non_causal_records": [
            "handoff_packets",
            "shadow_candidates",
            "skill_contract_stats",
        ],
    },
}


def _composition_profile_metadata(profile_id: str | None) -> dict | None:
    if not profile_id or profile_id == COMPOSITION_PROFILE_NONE:
        return None
    if profile_id not in COMPOSITION_PROFILES:
        raise ValueError(f"unknown composition profile: {profile_id}")
    return copy.deepcopy(COMPOSITION_PROFILES[profile_id])


def _apply_composition_profile_to_eval_kwargs(
    eval_kwargs: dict,
    profile_id: str | None,
    *,
    use_validation_defaults: bool = False,
) -> tuple[dict, dict]:
    """Apply a named opt-in profile without changing default policy semantics."""
    profile = _composition_profile_metadata(profile_id)
    updated = dict(eval_kwargs)
    runtime_overrides: dict = {}
    if profile is None:
        updated["composition_profile"] = None
        return updated, runtime_overrides

    updated.update(profile["settings"])
    updated["composition_profile"] = profile["profile_id"]
    if use_validation_defaults:
        defaults = dict(profile.get("recommended_validation_defaults", {}) or {})
        if defaults.get("enable_diagnostic_caches"):
            updated["enable_diagnostic_caches"] = True
        for key in ("parallel_workers", "chunk_size"):
            if key in defaults:
                runtime_overrides[key] = int(defaults[key])
    return updated, runtime_overrides


def _cli_option_provided(option: str, argv: list[str] | None = None) -> bool:
    argv = list(sys.argv[1:] if argv is None else argv)
    return any(item == option or item.startswith(f"{option}=") for item in argv)


def _new_perf_profile(enabled: bool, *, diagnostic_caches_enabled: bool = False) -> dict | None:
    if not enabled and not diagnostic_caches_enabled:
        return None
    return {
        "enabled": bool(enabled),
        "diagnostic_caches_enabled": bool(diagnostic_caches_enabled),
        "timers": {key: 0.0 for key in PROFILE_TIMER_KEYS},
        "counts": {key: 0 for key in PROFILE_COUNT_KEYS},
        "cache": {
            "context_terms": {"hits": 0, "misses": 0},
            "move_shape_audit": {"hits": 0, "misses": 0},
            "worst_reply_reward": {"hits": 0, "misses": 0},
            "oracle_best_reward": {"hits": 0, "misses": 0},
            "black_reply": {"hits": 0, "misses": 0},
        },
        "runtime_caches": {},
    }


def _profile_add_time(profile: dict | None, key: str, seconds: float) -> None:
    if not profile or not profile.get("enabled"):
        return
    timers = profile.setdefault("timers", {})
    timers[key] = float(timers.get(key, 0.0) or 0.0) + float(seconds)


def _profile_add_count(profile: dict | None, key: str, amount: int = 1) -> None:
    if not profile or not profile.get("enabled"):
        return
    counts = profile.setdefault("counts", {})
    counts[key] = int(counts.get(key, 0) or 0) + int(amount)


@contextmanager
def _profile_timer(profile: dict | None, key: str):
    if not profile or not profile.get("enabled"):
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        _profile_add_time(profile, key, time.perf_counter() - start)


def _profile_cache_delta(profile: dict | None, move_details: dict) -> None:
    if not profile or not profile.get("enabled"):
        return
    cache = profile.setdefault("cache", {})
    context = cache.setdefault("context_terms", {"hits": 0, "misses": 0})
    shape = cache.setdefault("move_shape_audit", {"hits": 0, "misses": 0})
    context["hits"] = int(context.get("hits", 0) or 0) + int(
        move_details.get("context_terms_cache_hits", 0) or 0
    )
    context["misses"] = int(context.get("misses", 0) or 0) + int(
        move_details.get("context_terms_cache_misses", 0) or 0
    )
    shape["hits"] = int(shape.get("hits", 0) or 0) + int(
        move_details.get("move_shape_audit_cache_hits", 0) or 0
    )
    shape["misses"] = int(shape.get("misses", 0) or 0) + int(
        move_details.get("move_shape_audit_cache_misses", 0) or 0
    )
    _profile_add_count(
        profile,
        "cache_hits",
        int(move_details.get("context_terms_cache_hits", 0) or 0)
        + int(move_details.get("move_shape_audit_cache_hits", 0) or 0),
    )
    _profile_add_count(
        profile,
        "cache_misses",
        int(move_details.get("context_terms_cache_misses", 0) or 0)
        + int(move_details.get("move_shape_audit_cache_misses", 0) or 0),
    )


def _profile_cache_event(profile: dict | None, cache_name: str, hit: bool) -> None:
    if not profile:
        return
    cache = profile.setdefault("cache", {}).setdefault(cache_name, {"hits": 0, "misses": 0})
    key = "hits" if hit else "misses"
    cache[key] = int(cache.get(key, 0) or 0) + 1
    _profile_add_count(profile, "cache_hits" if hit else "cache_misses")


def _diagnostic_cache(profile: dict | None, cache_name: str) -> dict | None:
    if not profile or not profile.get("diagnostic_caches_enabled"):
        return None
    return profile.setdefault("runtime_caches", {}).setdefault(cache_name, {})


def _board_cache_key(board: chess.Board) -> tuple:
    transposition_key = getattr(board, "transposition_key", None)
    if callable(transposition_key):
        try:
            return ("tk", transposition_key(), bool(board.turn))
        except Exception:
            pass
    private_key = getattr(board, "_transposition_key", None)
    if callable(private_key):
        try:
            return ("tk", private_key(), bool(board.turn))
        except Exception:
            pass
    return ("fen", board.board_fen(), bool(board.turn))


def _finalize_perf_profile(profile: dict | None) -> dict | None:
    if not profile or not profile.get("enabled"):
        return None
    timers = {
        key: round(float(profile.get("timers", {}).get(key, 0.0) or 0.0), 6)
        for key in PROFILE_TIMER_KEYS
    }
    counts = {
        key: int(profile.get("counts", {}).get(key, 0) or 0)
        for key in PROFILE_COUNT_KEYS
    }
    total = timers.get("total_wall_time", 0.0)
    percentages = {
        key: round((value / total * 100.0), 3) if total > 0 else 0.0
        for key, value in timers.items()
    }
    return {
        "schema_version": "krk_performance_profile.v1",
        "timers_sec": timers,
        "timer_percentages_of_total": percentages,
        "counts": counts,
        "cache": profile.get("cache", {}),
        "diagnostic_caches_enabled": bool(profile.get("diagnostic_caches_enabled", False)),
    }


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


def _suggestion_stability_signature(
    suggestions: list[dict],
    *,
    forced_successor_skill: Optional[str] = None,
    limit: int = 1,
) -> tuple | None:
    source = list(suggestions)
    if forced_successor_skill:
        source = [
            item for item in source
            if _skill_id_for_suggestion(item) == forced_successor_skill
        ]
    if not source:
        return None
    source.sort(key=lambda item: item.get("score", float("-inf")), reverse=True)
    rows = []
    for item in source[:max(1, limit)]:
        move = item.get("move")
        rows.append((
            _skill_id_for_suggestion(item),
            move.uci() if hasattr(move, "uci") else move,
            item.get("actuator"),
        ))
    return tuple(rows)


def _adapter_support_summary_for_suggestions(suggestions: list[dict]) -> dict:
    provider_counts: dict[str, int] = {}
    move_counts: dict[str, int] = {}
    supported = 0
    for item in suggestions:
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        adapter = meta.get("visible_role_provider_support_adapter")
        if not isinstance(adapter, dict) or not adapter.get("enabled"):
            continue
        supported += 1
        provider = str(adapter.get("provider_id") or _skill_id_for_suggestion(item))
        move = item.get("move")
        move_uci = move.uci() if hasattr(move, "uci") else str(move)
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        move_counts[move_uci] = move_counts.get(move_uci, 0) + 1
    return {
        "adapter_supported_suggestion_count": supported,
        "adapter_supported_provider_counts": provider_counts,
        "adapter_supported_move_counts": move_counts,
    }


def _candidate_move_role_summary_for_suggestions(
    suggestions: list[dict],
    *,
    selected_suggestion: dict | None = None,
) -> dict:
    role_counts: dict[str, int] = {}
    move_counts: dict[str, int] = {}
    supported = 0
    selected_supported = False
    selected_payload: dict = {}
    for item in suggestions:
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        payload = meta.get("visible_role_scoped_candidate_move_actuator")
        if not isinstance(payload, dict) or not payload.get("enabled"):
            continue
        if payload.get("direct_request"):
            continue
        supported += 1
        role_id = str(payload.get("role_id") or "unknown")
        move = item.get("move")
        move_uci = move.uci() if hasattr(move, "uci") else str(move)
        role_counts[role_id] = role_counts.get(role_id, 0) + 1
        move_counts[move_uci] = move_counts.get(move_uci, 0) + 1
    if isinstance(selected_suggestion, dict):
        selected_meta = (
            selected_suggestion.get("meta")
            if isinstance(selected_suggestion.get("meta"), dict)
            else {}
        )
        selected_payload = dict(
            selected_meta.get("visible_role_scoped_candidate_move_actuator", {}) or {}
        )
        selected_supported = bool(selected_payload) and not bool(
            selected_payload.get("direct_request")
        )
    return {
        "candidate_move_role_supported_suggestion_count": supported,
        "candidate_move_role_supported_role_counts": role_counts,
        "candidate_move_role_supported_move_counts": move_counts,
        "candidate_move_role_selected_supported": selected_supported,
        "candidate_move_role_selected_payload": selected_payload,
    }


def _frozen_model_candidate_summary_for_suggestions(
    suggestions: list[dict],
    *,
    selected_suggestion: dict | None = None,
) -> dict:
    move_counts: dict[str, int] = {}
    supported = 0
    selected_supported = False
    selected_payload: dict = {}
    for item in suggestions:
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        payload = meta.get("visible_stage7_post_box_frozen_model_candidate")
        if not isinstance(payload, dict) or not payload.get("enabled"):
            continue
        if payload.get("direct_request"):
            continue
        supported += 1
        move = item.get("move")
        move_uci = move.uci() if hasattr(move, "uci") else str(move)
        move_counts[move_uci] = move_counts.get(move_uci, 0) + 1
    if isinstance(selected_suggestion, dict):
        selected_meta = (
            selected_suggestion.get("meta")
            if isinstance(selected_suggestion.get("meta"), dict)
            else {}
        )
        selected_payload = dict(
            selected_meta.get("visible_stage7_post_box_frozen_model_candidate", {}) or {}
        )
        selected_supported = bool(selected_payload) and not bool(
            selected_payload.get("direct_request")
        )
    return {
        "stage7_post_box_frozen_model_candidate_supported_suggestion_count": supported,
        "stage7_post_box_frozen_model_candidate_supported_move_counts": move_counts,
        "stage7_post_box_frozen_model_candidate_selected_supported": selected_supported,
        "stage7_post_box_frozen_model_candidate_selected_payload": selected_payload,
    }


def _plan_capsule_support_summary_for_suggestions(
    suggestions: list[dict],
    *,
    selected_suggestion: dict | None = None,
    plan_state: dict | None = None,
) -> dict:
    provider_counts: dict[str, int] = {}
    move_counts: dict[str, int] = {}
    supported = 0
    max_supported_score = None
    max_supported_provider = None
    max_supported_move = None
    selected_license = {}
    selected_supported = False
    for item in suggestions:
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        license_payload = meta.get("visible_stage7_plan_capsule_license")
        if not isinstance(license_payload, dict) or not license_payload:
            continue
        if license_payload.get("direct_request"):
            continue
        supported += 1
        provider = str(license_payload.get("provider_skill_id") or _skill_id_for_suggestion(item))
        move = item.get("move")
        move_uci = move.uci() if hasattr(move, "uci") else str(move)
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        move_counts[move_uci] = move_counts.get(move_uci, 0) + 1
        score = float(item.get("score", 0.0) or 0.0)
        if max_supported_score is None or score > max_supported_score:
            max_supported_score = score
            max_supported_provider = provider
            max_supported_move = move_uci
    if isinstance(selected_suggestion, dict):
        selected_meta = (
            selected_suggestion.get("meta")
            if isinstance(selected_suggestion.get("meta"), dict)
            else {}
        )
        selected_license = dict(selected_meta.get("visible_stage7_plan_capsule_license", {}) or {})
        selected_supported = bool(selected_license) and not bool(selected_license.get("direct_request"))
    active = bool((plan_state or {}).get("plan_status") in {"active", "progress_confirmed"})
    return {
        "plan_capsule_active": active,
        "plan_capsule_supported_suggestion_count": supported,
        "plan_capsule_supported_provider_counts": provider_counts,
        "plan_capsule_supported_move_counts": move_counts,
        "plan_capsule_selected_supported": selected_supported,
        "plan_capsule_selected_license": selected_license,
        "plan_capsule_max_supported_score": max_supported_score,
        "plan_capsule_max_supported_provider": max_supported_provider,
        "plan_capsule_max_supported_move": max_supported_move,
    }


def _adapter_supported_role_owned_candidates(suggestions: list[dict]) -> list[dict]:
    """Return visible adapter-supported suggestions eligible for role-owned arbitration."""
    candidates: list[dict] = []
    for item in suggestions:
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        adapter = meta.get("visible_role_provider_support_adapter")
        if not isinstance(adapter, dict) or not adapter.get("enabled"):
            continue
        if adapter.get("direct_request"):
            continue
        # Stage 7 score-normalization experiments are intentionally narrower
        # than provider-level support: only move-shape-confirmed adapters can
        # own arbitration over raw cross-skill scores.
        if not adapter.get("move_shape_gated"):
            continue
        candidates.append(item)
    candidates.sort(
        key=lambda item: (
            float(
                (
                    (item.get("meta") or {}).get("visible_role_provider_support_adapter", {})
                    if isinstance(item.get("meta"), dict)
                    else {}
                ).get("support_amount", 0.0)
                or 0.0
            ),
            float(item.get("score", 0.0) or 0.0),
        ),
        reverse=True,
    )
    return candidates


def _plan_capsule_supported_owned_candidates(suggestions: list[dict]) -> list[dict]:
    """Return suggestions licensed by an active Plan Capsule window."""
    candidates: list[dict] = []
    for item in suggestions:
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        license_payload = meta.get("visible_stage7_plan_capsule_license")
        if not isinstance(license_payload, dict) or not license_payload:
            continue
        if license_payload.get("direct_request"):
            continue
        if license_payload.get("plan_status") not in {"active", "progress_confirmed"}:
            continue
        candidates.append(item)
    candidates.sort(
        key=lambda item: (
            float(
                (
                    (item.get("meta") or {}).get("visible_stage7_plan_capsule_license", {})
                    if isinstance(item.get("meta"), dict)
                    else {}
                ).get("support_amount", 0.0)
                or 0.0
            ),
            float(item.get("score", 0.0) or 0.0),
        ),
        reverse=True,
    )
    return candidates


def _stage7_0926_move_shape_role_spec() -> MoveShapeRoleSpec:
    return MoveShapeRoleSpec(
        role_id="krk.post_box.king_support_fence_stabilizer",
        source_candidate_id="cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1",
        source_monitor_script="growth.monitor.stage7_plan_capsule_residual_family_split",
        source_terms=[
            "legal_first_move_converts_h40",
            "candidate_is_king_move",
            "king_moves_toward_enemy",
            "king_moves_toward_rook_support",
            "fence_stable_after_move",
            "cut_preserved_after_move",
        ],
        domain="krk",
        target_skill="krk.box_shrink",
        parent_capsule="krk.post_box_shrink_continuation",
        scope_terms=[
            "active_landmark_label.box_shrink",
            "plan_capsule_entry_confirmed",
            "post_reply_state_reached",
        ],
        required_current_terms=[
            "rook_safe",
            "conversion_not_immediate",
            "no_mate_in_one_available",
        ],
        entry_terms=[
            "active_landmark_label.box_shrink",
            "post_reply_state_reached",
            "conversion_not_immediate",
            "rook_safe",
            "plan_capsule_entry_confirmed",
            "no_mate_in_one_available",
        ],
        move_shape_required_terms=[
            "candidate_is_king_move",
            "king_moves_toward_enemy",
            "king_moves_toward_rook_support",
        ],
        post_move_required_terms=[
            "rook_safe_after_move",
            "box_area_not_increased_after_move",
            "fence_exists_after_move",
            "fence_stable_after_move",
            "cut_preserved_after_move",
            "white_king_distance_to_enemy_decreases",
            "white_king_distance_to_rook_decreases",
        ],
        veto_terms=[
            "mate_in_one_available",
            "rook_unsafe_after_move",
            "draw_or_stalemate_risk",
            "box_area_increases_after_move",
            "cut_or_fence_lost_without_repair",
        ],
        promotion_status="proposed",
    )


def _candidate_frame_for_move(
    board: chess.Board,
    move: chess.Move,
    *,
    blackboard: dict,
    include_worst_reply: bool = False,
    causal_status: str = "non_causal",
) -> CandidateMoveFrame:
    from recon_lite_chess.krk_baseline_nodes import krk_move_shape_audit

    audit = krk_move_shape_audit(
        board,
        move,
        blackboard,
        include_worst_reply=include_worst_reply,
    )
    post = board.copy(stack=False)
    post.push(move)
    safety_terms: list[str] = []
    veto_terms: list[str] = []
    post_terms = set(audit.get("post_move_terms", []) or [])
    worst_terms = set(audit.get("worst_reply_terms", []) or [])
    if "rook_safe_after_move" in post_terms:
        safety_terms.append("rook_safe_after_move")
    if post.is_stalemate() or post.is_insufficient_material() or post.can_claim_draw():
        veto_terms.append("draw_or_stalemate_risk")
    if "no_draw_after_worst_reply" in worst_terms:
        safety_terms.append("no_draw_after_worst_reply")
    board_key = f"{board.board_fen()}:{'w' if board.turn == chess.WHITE else 'b'}"
    return CandidateMoveFrame(
        move_uci=move.uci(),
        legal=move in board.legal_moves,
        current_terms=list(audit.get("current_terms", []) or []),
        move_shape_terms=list(audit.get("move_shape_terms", []) or []),
        post_move_terms=list(audit.get("post_move_terms", []) or []),
        worst_reply_terms=list(audit.get("worst_reply_terms", []) or []),
        safety_terms=safety_terms,
        veto_terms=veto_terms,
        source_terms=list(audit.get("current_terms", []) or []),
        source_terminal="terminal.krk.candidate_move_enumerator",
        board_key=board_key,
        fen=board.fen(),
        causal_status=causal_status,  # type: ignore[arg-type]
    )


def _candidate_frame_role_match(
    frame: CandidateMoveFrame,
    role: MoveShapeRoleSpec,
    *,
    visible_terms: dict,
    plan_marker: dict,
) -> dict | None:
    current_terms = set(frame.current_terms) | {
        term for term, value in visible_terms.items() if bool(value)
    }
    if plan_marker.get("entry_confirmed"):
        current_terms.add("plan_capsule_entry_confirmed")
    move_terms = set(frame.move_shape_terms)
    post_terms = set(frame.post_move_terms)
    worst_terms = set(frame.worst_reply_terms)
    all_terms = current_terms | move_terms | post_terms | worst_terms | set(frame.veto_terms)
    missing_current = sorted(set(role.required_current_terms) - current_terms)
    missing_scope = sorted(set(role.scope_terms) - current_terms)
    missing_move = sorted(set(role.move_shape_required_terms) - move_terms)
    missing_post = sorted(set(role.post_move_required_terms) - post_terms)
    missing_worst = sorted(set(role.required_worst_reply_terms) - worst_terms)
    veto_met = sorted(set(role.veto_terms) & all_terms)
    if missing_current or missing_scope or missing_move or missing_post or missing_worst or veto_met:
        return None
    matched_terms = sorted(
        set(role.required_current_terms)
        | set(role.scope_terms)
        | set(role.move_shape_required_terms)
        | set(role.post_move_required_terms)
        | set(role.required_worst_reply_terms)
    )
    return {
        "schema_version": "candidate_move_role_match.v1",
        "role_id": role.role_id,
        "source_candidate_id": role.source_candidate_id,
        "matched_terms": matched_terms,
        "source_terms": sorted(set(role.source_terms) | set(matched_terms)),
        "veto_terms_met": [],
        "causal_status": "sandbox_opt_in",
        "direct_request": False,
    }


def _enumerate_candidate_move_frames(
    board: chess.Board,
    *,
    blackboard: dict,
    include_worst_reply: bool = False,
    causal_status: str = "non_causal",
) -> list[CandidateMoveFrame]:
    frames = [
        _candidate_frame_for_move(
            board,
            move,
            blackboard=blackboard,
            include_worst_reply=include_worst_reply,
            causal_status=causal_status,
        )
        for move in sorted(board.legal_moves, key=lambda item: item.uci())
    ]
    blackboard["krk_candidate_move_frames"] = [frame.to_dict() for frame in frames]
    blackboard["krk_candidate_move_enumerator"] = {
        "schema_version": "candidate_move_enumerator_trace.v1",
        "source_terminal": "terminal.krk.candidate_move_enumerator",
        "frame_count": len(frames),
        "causal_status": causal_status,
        "direct_request": False,
    }
    return frames


def _apply_stage7_candidate_move_layer(
    env: dict,
    *,
    role_enabled: bool,
    support_amount: float,
    include_worst_reply: bool = False,
) -> None:
    blackboard = env.get("blackboard", {})
    board = env.get("board")
    if board is None or not blackboard.get("candidate_move_layer_enabled", False):
        return
    frames = _enumerate_candidate_move_frames(
        board,
        blackboard=blackboard,
        include_worst_reply=include_worst_reply,
        causal_status="sandbox_opt_in" if role_enabled else "non_causal",
    )
    if not role_enabled:
        return
    role = _stage7_0926_move_shape_role_spec()
    visible_terms = dict(blackboard.get("krk_visible_terms", {}) or {})
    visible_terms.update(dict(blackboard.get("krk_dynamic_context_terms", {}) or {}))
    marker = (
        blackboard.get("krk_plan_capsule_markers", {})
        .get("krk.post_box_shrink_continuation", {})
        if isinstance(blackboard.get("krk_plan_capsule_markers"), dict)
        else {}
    )
    suggestions = env.setdefault("actuator_suggestions", [])
    match_count = 0
    for frame in frames:
        match = _candidate_frame_role_match(
            frame,
            role,
            visible_terms=visible_terms,
            plan_marker=marker,
        )
        if not match:
            continue
        frame_payload = frame.to_dict()
        frame_payload["role_matches"] = [match]
        match_count += 1
        suggestions.append(
            {
                "move": chess.Move.from_uci(frame.move_uci),
                "score": float(support_amount),
                "actuator": "terminal.krk.role_scoped_candidate_move_actuator",
                "stage": 7,
                "curriculum_label": "candidate_move_role",
                "meta": {
                    "curriculum_label": "candidate_move_role",
                    "stage": 7,
                    "visible_role_scoped_candidate_move_actuator": {
                        "schema_version": "role_scoped_candidate_move_suggestion.v1",
                        "enabled": True,
                        "role_id": role.role_id,
                        "plan_capsule_id": role.parent_capsule,
                        "move": frame.move_uci,
                        "source_terms": match["source_terms"],
                        "matched_terms": match["matched_terms"],
                        "support_amount": float(support_amount),
                        "direct_request": False,
                        "causal_status": "sandbox_opt_in",
                        "source_terminal": "terminal.krk.role_scoped_candidate_move_actuator",
                        "candidate_frame": frame_payload,
                    },
                },
            }
        )
    blackboard["krk_candidate_move_role_matches"] = {
        "schema_version": "candidate_move_role_match_summary.v1",
        "role_id": role.role_id,
        "match_count": match_count,
        "causal_status": "sandbox_opt_in",
        "direct_request": False,
    }


def _candidate_frame_model_features(board: chess.Board, frame: CandidateMoveFrame) -> set[str]:
    move = chess.Move.from_uci(frame.move_uci)
    piece = board.piece_at(move.from_square)
    features: set[str] = set()
    if piece is not None:
        features.add(f"piece:{piece.symbol().upper()}")
        if piece.piece_type == chess.KING:
            features.add("piece_type:king")
        if piece.piece_type == chess.ROOK:
            features.add("piece_type:rook")
    from_file = chess.square_file(move.from_square)
    from_rank = chess.square_rank(move.from_square)
    to_file = chess.square_file(move.to_square)
    to_rank = chess.square_rank(move.to_square)
    delta_file = to_file - from_file
    delta_rank = to_rank - from_rank
    for term in (
        f"piece.{piece.symbol().upper() if piece else 'unknown'}",
        f"from_file.{from_file}",
        f"from_rank.{from_rank}",
        f"to_file.{to_file}",
        f"to_rank.{to_rank}",
        f"delta_file_sign.{0 if delta_file == 0 else 1 if delta_file > 0 else -1}",
        f"delta_rank_sign.{0 if delta_rank == 0 else 1 if delta_rank > 0 else -1}",
        f"delta_file_abs.{abs(delta_file)}",
        f"delta_rank_abs.{abs(delta_rank)}",
    ):
        features.add(f"coord:{term}")
    for term in frame.move_shape_terms:
        features.add(f"move_shape:{term}")
    for term in frame.post_move_terms:
        features.add(f"post_move:{term}")
    return features


def _apply_stage7_post_box_frozen_model_candidate_layer(
    env: dict,
    *,
    model: dict | None,
    support_amount: float,
) -> None:
    blackboard = env.get("blackboard", {})
    board = env.get("board")
    if board is None or not blackboard.get("candidate_move_layer_enabled", False):
        return
    if not blackboard.get("stage7_post_box_frozen_model_candidate_enabled", False):
        return
    if not blackboard.get("stage7_post_box_post_reply_context", False):
        return
    if not isinstance(model, dict) or model.get("causal_status") != "sandbox_model_non_promoted":
        blackboard["stage7_post_box_frozen_model_candidate"] = {
            "schema_version": "stage7_post_box_frozen_model_candidate_trace.v1",
            "enabled": True,
            "emitted": False,
            "reason": "missing_or_non_sandbox_model",
            "direct_request": False,
            "causal_status": "sandbox_opt_in",
        }
        return
    constraints = set(model.get("constraints") or [])
    forbidden_terms = set(model.get("runtime_forbidden_terms") or [])
    if "do_not_enable_by_default" not in constraints or not {
        "tablebase_lookup",
        "dtm_oracle_move_selection",
        "state_hash_exception",
    } <= forbidden_terms:
        blackboard["stage7_post_box_frozen_model_candidate"] = {
            "schema_version": "stage7_post_box_frozen_model_candidate_trace.v1",
            "enabled": True,
            "emitted": False,
            "reason": "model_boundary_check_failed",
            "direct_request": False,
            "causal_status": "sandbox_opt_in",
        }
        return
    frames_payload = blackboard.get("krk_candidate_move_frames")
    frames = [
        CandidateMoveFrame.from_dict(item)
        for item in frames_payload
        if isinstance(item, dict)
    ] if isinstance(frames_payload, list) else _enumerate_candidate_move_frames(
        board,
        blackboard=blackboard,
        causal_status="sandbox_opt_in",
    )
    weights = {str(key): float(value) for key, value in (model.get("weights") or {}).items()}
    bias = float(model.get("bias", 0.0) or 0.0)
    scored = []
    for frame in frames:
        if not frame.legal:
            continue
        features = _candidate_frame_model_features(board, frame)
        model_score = bias + sum(weights.get(term, 0.0) for term in features)
        matched_terms = sorted(term for term in features if term in weights)
        scored.append((model_score, frame.move_uci, frame, matched_terms))
    if not scored:
        blackboard["stage7_post_box_frozen_model_candidate"] = {
            "schema_version": "stage7_post_box_frozen_model_candidate_trace.v1",
            "enabled": True,
            "emitted": False,
            "reason": "no_legal_candidate_frames",
            "direct_request": False,
            "causal_status": "sandbox_opt_in",
        }
        return
    model_score, _, frame, matched_terms = max(scored, key=lambda item: (item[0], item[1]))
    payload = {
        "schema_version": "stage7_post_box_frozen_model_candidate_suggestion.v1",
        "enabled": True,
        "provider_skill_id": model.get("provider_skill_id", "krk.stage7_post_box_learned_continuation"),
        "role_id": model.get("role_id", "krk.post_box_shrink_continuation"),
        "move": frame.move_uci,
        "model_score": float(model_score),
        "support_amount": float(support_amount),
        "matched_weighted_terms": matched_terms,
        "source_terms": sorted(set(frame.current_terms) | set(frame.move_shape_terms) | set(frame.post_move_terms)),
        "candidate_frame": frame.to_dict(),
        "direct_request": False,
        "causal_status": "sandbox_opt_in",
        "runtime_forbidden_terms": sorted(forbidden_terms),
        "source_terminal": "terminal.krk.stage7_post_box_frozen_model_candidate",
    }
    env.setdefault("actuator_suggestions", []).append(
        {
            "move": chess.Move.from_uci(frame.move_uci),
            "score": float(support_amount),
            "actuator": "terminal.krk.stage7_post_box_frozen_model_candidate",
            "stage": 7,
            "curriculum_label": "stage7_post_box_frozen_model_candidate",
            "meta": {
                "curriculum_label": "stage7_post_box_frozen_model_candidate",
                "stage": 7,
                "visible_stage7_post_box_frozen_model_candidate": payload,
            },
        }
    )
    blackboard["stage7_post_box_frozen_model_candidate"] = {
        "schema_version": "stage7_post_box_frozen_model_candidate_trace.v1",
        "enabled": True,
        "emitted": True,
        "move": frame.move_uci,
        "model_score": float(model_score),
        "support_amount": float(support_amount),
        "direct_request": False,
        "causal_status": "sandbox_opt_in",
    }


def _compact_selected_suggestion(item: dict | None) -> dict:
    if not isinstance(item, dict):
        return {}
    move = item.get("move")
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    return {
        "move": move.uci() if hasattr(move, "uci") else move,
        "skill_id": _skill_id_for_suggestion(item),
        "score": float(item.get("score", 0.0) or 0.0),
        "actuator": item.get("actuator"),
        "curriculum_label": meta.get("curriculum_label") or item.get("curriculum_label"),
        "stage": meta.get("stage") or item.get("stage"),
        "visible_role_provider_support_adapter": dict(
            meta.get("visible_role_provider_support_adapter", {}) or {}
        ),
        "visible_role_owned_score_normalization": dict(
            meta.get("visible_role_owned_score_normalization", {}) or {}
        ),
        "visible_stage7_plan_capsule_owned_arbitration": dict(
            meta.get("visible_stage7_plan_capsule_owned_arbitration", {}) or {}
        ),
        "visible_stage7_plan_capsule_license": dict(
            meta.get("visible_stage7_plan_capsule_license", {}) or {}
        ),
        "visible_stage7_post_box_frozen_model_candidate": dict(
            meta.get("visible_stage7_post_box_frozen_model_candidate", {}) or {}
        ),
    }


def _suggestion_role_trace(meta: dict) -> dict:
    return {
        "visible_role_licenses": list(meta.get("visible_role_licenses", []) or []),
        "visible_role_license_bonus": float(meta.get("visible_role_license_bonus", 0.0) or 0.0),
        "raw_score_before_role_bonus": (
            float(meta.get("raw_score_before_role_bonus"))
            if meta.get("raw_score_before_role_bonus") is not None
            else None
        ),
        "score_after_role_bonus": (
            float(meta.get("score_after_role_bonus"))
            if meta.get("score_after_role_bonus") is not None
            else None
        ),
        "role_bonus_total": float(meta.get("role_bonus_total", 0.0) or 0.0),
        "role_bonus_by_role": dict(meta.get("role_bonus_by_role", {}) or {}),
        "visible_role_provider_support_adapter": dict(
            meta.get("visible_role_provider_support_adapter", {}) or {}
        ),
        "visible_role_owned_score_normalization": dict(
            meta.get("visible_role_owned_score_normalization", {}) or {}
        ),
        "visible_role_scoped_move_shape_bonus": float(
            meta.get("visible_role_scoped_move_shape_bonus", 0.0) or 0.0
        ),
        "visible_role_scoped_move_shape_licenses": list(
            meta.get("visible_role_scoped_move_shape_licenses", []) or []
        ),
        "visible_move_shape_audit": dict(meta.get("visible_move_shape_audit", {}) or {}),
        "visible_role_scoped_move_shape_require_worst_reply": bool(
            meta.get("visible_role_scoped_move_shape_require_worst_reply", False)
        ),
        "score_after_role_scoped_move_shape_bonus": (
            float(meta.get("score_after_role_scoped_move_shape_bonus"))
            if meta.get("score_after_role_scoped_move_shape_bonus") is not None
            else None
        ),
        "visible_stage0_drift_penalty": float(
            meta.get("visible_stage0_drift_penalty", 0.0) or 0.0
        ),
        "visible_stage0_drift_reason": dict(
            meta.get("visible_stage0_drift_reason", {}) or {}
        ),
        "visible_stagnation_breaker_bonus": float(
            meta.get("visible_stagnation_breaker_bonus", 0.0) or 0.0
        ),
        "visible_stagnation_breaker_license": dict(
            meta.get("visible_stagnation_breaker_license", {}) or {}
        ),
        "visible_stagnation_breaker_king_support_bonus": float(
            meta.get("visible_stagnation_breaker_king_support_bonus", 0.0) or 0.0
        ),
        "visible_stagnation_breaker_king_support_license": dict(
            meta.get("visible_stagnation_breaker_king_support_license", {}) or {}
        ),
        "score_after_stagnation_breaker_bonus": (
            float(meta.get("score_after_stagnation_breaker_bonus"))
            if meta.get("score_after_stagnation_breaker_bonus") is not None
            else None
        ),
        "visible_post_break_continuation_bonus": float(
            meta.get("visible_post_break_continuation_bonus", 0.0) or 0.0
        ),
        "visible_post_break_continuation_license": dict(
            meta.get("visible_post_break_continuation_license", {}) or {}
        ),
        "score_after_post_break_continuation_bonus": (
            float(meta.get("score_after_post_break_continuation_bonus"))
            if meta.get("score_after_post_break_continuation_bonus") is not None
            else None
        ),
        "visible_stage7_king_tempo_bonus": float(
            meta.get("visible_stage7_king_tempo_bonus", 0.0) or 0.0
        ),
        "visible_stage7_king_tempo_license": dict(
            meta.get("visible_stage7_king_tempo_license", {}) or {}
        ),
        "visible_stage7_drive_repair_bonus": float(
            meta.get("visible_stage7_drive_repair_bonus", 0.0) or 0.0
        ),
        "visible_stage7_drive_repair_license": dict(
            meta.get("visible_stage7_drive_repair_license", {}) or {}
        ),
        "visible_stage7_post_king_tempo_bonus": float(
            meta.get("visible_stage7_post_king_tempo_bonus", 0.0) or 0.0
        ),
        "visible_stage7_post_king_tempo_license": dict(
            meta.get("visible_stage7_post_king_tempo_license", {}) or {}
        ),
        "visible_stage7_post_box_continuation_bonus": float(
            meta.get("visible_stage7_post_box_continuation_bonus", 0.0) or 0.0
        ),
        "visible_stage7_post_box_continuation_license": dict(
            meta.get("visible_stage7_post_box_continuation_license", {}) or {}
        ),
        "visible_stage7_learned_post_box_continuation_bonus": float(
            meta.get("visible_stage7_learned_post_box_continuation_bonus", 0.0) or 0.0
        ),
        "visible_stage7_learned_post_box_continuation_license": dict(
            meta.get("visible_stage7_learned_post_box_continuation_license", {}) or {}
        ),
        "visible_stage7_post_box_frozen_model_candidate": dict(
            meta.get("visible_stage7_post_box_frozen_model_candidate", {}) or {}
        ),
        "visible_stage7_plan_capsule_bonus": float(
            meta.get("visible_stage7_plan_capsule_bonus", 0.0) or 0.0
        ),
        "visible_stage7_plan_capsule_license": dict(
            meta.get("visible_stage7_plan_capsule_license", {}) or {}
        ),
        "visible_stage7_plan_capsule_owned_arbitration": dict(
            meta.get("visible_stage7_plan_capsule_owned_arbitration", {}) or {}
        ),
        "score_after_stage7_plan_capsule_bonus": (
            float(meta.get("score_after_stage7_plan_capsule_bonus"))
            if meta.get("score_after_stage7_plan_capsule_bonus") is not None
            else None
        ),
    }


def _accumulate_engine_perf(stats: dict, move_details: dict, *, prefix: str = "engine") -> None:
    stats[f"{prefix}_decision_count"] = int(stats.get(f"{prefix}_decision_count", 0)) + 1
    ticks = int(move_details.get("ticks", 0) or 0)
    stats[f"{prefix}_ticks_total"] = int(stats.get(f"{prefix}_ticks_total", 0)) + ticks
    stats[f"{prefix}_ticks_max"] = max(int(stats.get(f"{prefix}_ticks_max", 0)), ticks)
    if bool(move_details.get("early_stopped", False)):
        stats[f"{prefix}_early_stop_count"] = int(stats.get(f"{prefix}_early_stop_count", 0)) + 1


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
            "visible_successor_provider_licenses": {},
            "visible_eligible_successors": {},
            "role_license_present_but_provider_absent": {},
            "role_contract_met_but_provider_not_selected": {},
            "missing_afforded_skills": {},
            "adapter_supported_suggestion_count": 0,
            "adapter_supported_provider_counts": {},
            "adapter_supported_move_counts": {},
            "candidate_move_role_supported_suggestion_count": 0,
            "candidate_move_role_supported_role_counts": {},
            "candidate_move_role_supported_move_counts": {},
            "candidate_move_role_selected_supported": False,
            "candidate_move_role_selected_payload": {},
            "stage7_post_box_frozen_model_candidate_supported_suggestion_count": 0,
            "stage7_post_box_frozen_model_candidate_supported_move_counts": {},
            "stage7_post_box_frozen_model_candidate_selected_supported": False,
            "stage7_post_box_frozen_model_candidate_selected_payload": {},
            "plan_capsule_active": False,
            "plan_capsule_supported_suggestion_count": 0,
            "plan_capsule_supported_provider_counts": {},
            "plan_capsule_supported_move_counts": {},
            "plan_capsule_selected_supported": False,
            "plan_capsule_selected_license": {},
            "plan_capsule_max_supported_score": None,
            "plan_capsule_max_supported_provider": None,
            "plan_capsule_max_supported_move": None,
            "plan_capsule_markers": {},
            "visible_stage7_king_tempo_bonus": 0.0,
            "visible_stage7_king_tempo_license": {},
        }
    visible_terms = dict(move_details.get("visible_terms", {}) or {})
    visible_affordances = dict(move_details.get("successor_affordances", {}) or {})
    provider_licenses = dict(move_details.get("successor_provider_licenses", {}) or {})

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
                **_suggestion_role_trace(meta),
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
                **_suggestion_role_trace(meta),
            })

    ranked = sorted(grouped.items(), key=lambda kv: kv[1]["score"], reverse=True)
    raw_selected_skill = ranked[0][0] if ranked else None
    raw_best_score = float(ranked[0][1]["score"]) if ranked else None
    selected_suggestion = (
        move_details.get("selected_suggestion")
        if isinstance(move_details.get("selected_suggestion"), dict)
        else {}
    )
    selected_skill = (
        str(selected_suggestion.get("skill_id"))
        if (
            move_details.get("selected_by_role_owned_score_normalization")
            or move_details.get("selected_by_stage7_plan_capsule_owned_arbitration")
        )
        and selected_suggestion.get("skill_id")
        else raw_selected_skill
    )
    best_score = (
        float(selected_suggestion.get("score"))
        if selected_skill != raw_selected_skill and selected_suggestion.get("score") is not None
        else raw_best_score
    )
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
    role_license_present_but_provider_absent = {}
    role_contract_met_but_provider_not_selected = {}
    for role_id, payload in visible_eligible_successors.items():
        providers = list(payload.get("provider_skill_ids", []) or [])
        absent = [provider for provider in providers if provider not in grouped]
        if absent:
            role_license_present_but_provider_absent[role_id] = absent
        not_selected = [provider for provider in providers if provider != selected_skill]
        if not_selected:
            role_contract_met_but_provider_not_selected[role_id] = not_selected
    return {
        "selected_skill": selected_skill,
        "best_score": best_score,
        "raw_selected_skill": raw_selected_skill,
        "raw_best_score": raw_best_score,
        "second_score": second_score,
        "route_margin": route_margin,
        "handoff_gap": bool(handoff_gap),
        "route_conflict": bool(route_conflict),
        "skills": grouped,
        "exports": exports,
        "visible_terms": visible_terms,
        "visible_successor_affordances": visible_affordances,
        "visible_successor_provider_licenses": provider_licenses,
        "visible_eligible_successors": visible_eligible_successors,
        "role_license_present_but_provider_absent": role_license_present_but_provider_absent,
        "role_contract_met_but_provider_not_selected": role_contract_met_but_provider_not_selected,
        "missing_afforded_skills": missing_afforded,
        "adapter_supported_suggestion_count": int(
            move_details.get("adapter_supported_suggestion_count", 0) or 0
        ),
        "adapter_supported_provider_counts": dict(
            move_details.get("adapter_supported_provider_counts", {}) or {}
        ),
        "adapter_supported_move_counts": dict(
            move_details.get("adapter_supported_move_counts", {}) or {}
        ),
        "candidate_move_role_supported_suggestion_count": int(
            move_details.get("candidate_move_role_supported_suggestion_count", 0) or 0
        ),
        "candidate_move_role_supported_role_counts": dict(
            move_details.get("candidate_move_role_supported_role_counts", {}) or {}
        ),
        "candidate_move_role_supported_move_counts": dict(
            move_details.get("candidate_move_role_supported_move_counts", {}) or {}
        ),
        "candidate_move_role_selected_supported": bool(
            move_details.get("candidate_move_role_selected_supported", False)
        ),
        "candidate_move_role_selected_payload": dict(
            move_details.get("candidate_move_role_selected_payload", {}) or {}
        ),
        "stage7_post_box_frozen_model_candidate_supported_suggestion_count": int(
            move_details.get(
                "stage7_post_box_frozen_model_candidate_supported_suggestion_count",
                0,
            )
            or 0
        ),
        "stage7_post_box_frozen_model_candidate_supported_move_counts": dict(
            move_details.get(
                "stage7_post_box_frozen_model_candidate_supported_move_counts",
                {},
            )
            or {}
        ),
        "stage7_post_box_frozen_model_candidate_selected_supported": bool(
            move_details.get(
                "stage7_post_box_frozen_model_candidate_selected_supported",
                False,
            )
        ),
        "stage7_post_box_frozen_model_candidate_selected_payload": dict(
            move_details.get(
                "stage7_post_box_frozen_model_candidate_selected_payload",
                {},
            )
            or {}
        ),
        "plan_capsule_active": bool(move_details.get("plan_capsule_active", False)),
        "plan_capsule_supported_suggestion_count": int(
            move_details.get("plan_capsule_supported_suggestion_count", 0) or 0
        ),
        "plan_capsule_supported_provider_counts": dict(
            move_details.get("plan_capsule_supported_provider_counts", {}) or {}
        ),
        "plan_capsule_supported_move_counts": dict(
            move_details.get("plan_capsule_supported_move_counts", {}) or {}
        ),
        "plan_capsule_selected_supported": bool(
            move_details.get("plan_capsule_selected_supported", False)
        ),
        "plan_capsule_selected_license": dict(
            move_details.get("plan_capsule_selected_license", {}) or {}
        ),
        "plan_capsule_max_supported_score": move_details.get("plan_capsule_max_supported_score"),
        "plan_capsule_max_supported_provider": move_details.get(
            "plan_capsule_max_supported_provider"
        ),
        "plan_capsule_max_supported_move": move_details.get("plan_capsule_max_supported_move"),
        "plan_capsule_markers": dict(move_details.get("plan_capsule_markers", {}) or {}),
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
            "selected_provider_role_licenses": [],
            "provider_selected_without_role_license": False,
            "role_bonus_total": 0.0,
            "role_bonus_by_role": {},
            "visible_role_provider_support_adapter": {},
            "visible_role_owned_score_normalization": {},
            "visible_stage7_plan_capsule_owned_arbitration": {},
            "raw_score_before_role_bonus": None,
            "score_after_role_bonus": None,
            "visible_role_scoped_move_shape_bonus": 0.0,
            "visible_role_scoped_move_shape_licenses": [],
            "visible_move_shape_audit": {},
            "visible_role_scoped_move_shape_require_worst_reply": False,
            "score_after_role_scoped_move_shape_bonus": None,
            "visible_stage0_drift_penalty": 0.0,
            "visible_stage0_drift_reason": {},
            "visible_stage7_king_tempo_bonus": 0.0,
            "visible_stage7_king_tempo_license": {},
            "selected_skill_source": "none",
        }

    visible_payload = visible_affordances.get(selected_skill)
    selected_group = grouped.get(selected_skill, {})
    group_payload = selected_group.get("visible_successor_affordance") or {}
    role_licenses = list(selected_group.get("visible_role_licenses", []) or [])
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
        "selected_despite_contract_mismatch": bool(payload and not contract_met and not role_licenses),
        "selected_provider_role_licenses": role_licenses,
        "selected_skill_source": (
            "visible_role_license"
            if role_licenses
            else "visible_contract"
            if visible_payload
            else "actuator_score"
        ),
        "provider_selected_without_role_license": bool(not role_licenses),
        "role_bonus_total": float(selected_group.get("role_bonus_total", 0.0) or 0.0),
        "role_bonus_by_role": dict(selected_group.get("role_bonus_by_role", {}) or {}),
        "visible_role_provider_support_adapter": dict(
            selected_group.get("visible_role_provider_support_adapter", {}) or {}
        ),
        "visible_role_owned_score_normalization": dict(
            selected_group.get("visible_role_owned_score_normalization", {}) or {}
        ),
        "visible_stage7_plan_capsule_owned_arbitration": dict(
            selected_group.get("visible_stage7_plan_capsule_owned_arbitration", {}) or {}
        ),
        "raw_score_before_role_bonus": selected_group.get("raw_score_before_role_bonus"),
        "score_after_role_bonus": selected_group.get("score_after_role_bonus"),
        "visible_role_scoped_move_shape_bonus": float(
            selected_group.get("visible_role_scoped_move_shape_bonus", 0.0) or 0.0
        ),
        "visible_role_scoped_move_shape_licenses": list(
            selected_group.get("visible_role_scoped_move_shape_licenses", []) or []
        ),
        "visible_move_shape_audit": dict(selected_group.get("visible_move_shape_audit", {}) or {}),
        "visible_role_scoped_move_shape_require_worst_reply": bool(
            selected_group.get("visible_role_scoped_move_shape_require_worst_reply", False)
        ),
        "score_after_role_scoped_move_shape_bonus": selected_group.get(
            "score_after_role_scoped_move_shape_bonus"
        ),
        "visible_stage0_drift_penalty": float(
            selected_group.get("visible_stage0_drift_penalty", 0.0) or 0.0
        ),
        "visible_stage0_drift_reason": dict(
            selected_group.get("visible_stage0_drift_reason", {}) or {}
        ),
        "visible_stagnation_breaker_bonus": float(
            selected_group.get("visible_stagnation_breaker_bonus", 0.0) or 0.0
        ),
        "visible_stagnation_breaker_license": dict(
            selected_group.get("visible_stagnation_breaker_license", {}) or {}
        ),
        "visible_stagnation_breaker_king_support_bonus": float(
            selected_group.get("visible_stagnation_breaker_king_support_bonus", 0.0) or 0.0
        ),
        "visible_stagnation_breaker_king_support_license": dict(
            selected_group.get("visible_stagnation_breaker_king_support_license", {}) or {}
        ),
        "score_after_stagnation_breaker_bonus": selected_group.get(
            "score_after_stagnation_breaker_bonus"
        ),
        "visible_post_break_continuation_bonus": float(
            selected_group.get("visible_post_break_continuation_bonus", 0.0) or 0.0
        ),
        "visible_post_break_continuation_license": dict(
            selected_group.get("visible_post_break_continuation_license", {}) or {}
        ),
        "score_after_post_break_continuation_bonus": selected_group.get(
            "score_after_post_break_continuation_bonus"
        ),
        "visible_stage7_king_tempo_bonus": float(
            selected_group.get("visible_stage7_king_tempo_bonus", 0.0) or 0.0
        ),
        "visible_stage7_king_tempo_license": dict(
            selected_group.get("visible_stage7_king_tempo_license", {}) or {}
        ),
        "visible_stage7_drive_repair_bonus": float(
            selected_group.get("visible_stage7_drive_repair_bonus", 0.0) or 0.0
        ),
        "visible_stage7_drive_repair_license": dict(
            selected_group.get("visible_stage7_drive_repair_license", {}) or {}
        ),
        "visible_stage7_post_king_tempo_bonus": float(
            selected_group.get("visible_stage7_post_king_tempo_bonus", 0.0) or 0.0
        ),
        "visible_stage7_post_king_tempo_license": dict(
            selected_group.get("visible_stage7_post_king_tempo_license", {}) or {}
        ),
        "visible_stage7_post_box_continuation_bonus": float(
            selected_group.get("visible_stage7_post_box_continuation_bonus", 0.0) or 0.0
        ),
        "visible_stage7_post_box_continuation_license": dict(
            selected_group.get("visible_stage7_post_box_continuation_license", {}) or {}
        ),
        "visible_stage7_learned_post_box_continuation_bonus": float(
            selected_group.get("visible_stage7_learned_post_box_continuation_bonus", 0.0) or 0.0
        ),
        "visible_stage7_learned_post_box_continuation_license": dict(
            selected_group.get("visible_stage7_learned_post_box_continuation_license", {}) or {}
        ),
        "visible_stage7_plan_capsule_bonus": float(
            selected_group.get("visible_stage7_plan_capsule_bonus", 0.0) or 0.0
        ),
        "visible_stage7_plan_capsule_license": dict(
            selected_group.get("visible_stage7_plan_capsule_license", {}) or {}
        ),
        "score_after_stage7_plan_capsule_bonus": selected_group.get(
            "score_after_stage7_plan_capsule_bonus"
        ),
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
    final_mate_in_one_available: bool = False,
    rook_oscillation_detected: bool = False,
) -> list[str]:
    if not local_confirmed or conversion_result == "mate":
        return []
    classes: list[str] = []
    if conversion_result == "max_plies" and final_mate_in_one_available:
        classes.append("horizon_mate_in_one")
    if conversion_result == "max_plies" and rook_oscillation_detected:
        classes.append("rook_oscillation_loop")
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
        "horizon_mate_in_one": 4,
        "rook_oscillation_loop": 4,
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
        "horizon_mate_in_one": "horizon_mate_in_one",
        "rook_oscillation_loop": "stagnation_loop",
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


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def choose_move_with_engine(
    graph: Graph,
    engine: ReConEngine,
    board: chess.Board,
    max_ticks: int = 200,
    stage_filter: Optional[int] = None,
    suggestion_limit: int = 10,
    successor_affordance_layer_enabled: bool = False,
    successor_contract_gate_enabled: bool = False,
    successor_role_license_enabled: bool = False,
    explicit_role_provider_support_enabled: bool = False,
    role_owned_score_normalization_enabled: bool = False,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_context: Optional[dict] = None,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    stagnation_breaker_king_support_bonus: float = 0.0,
    post_break_continuation_enabled: bool = False,
    post_break_continuation_bonus: float = 0.0,
    stage7_king_tempo_enabled: bool = False,
    stage7_king_tempo_score: float = 25.0,
    stage7_drive_repair_enabled: bool = False,
    stage7_drive_repair_score: float = 28.0,
    stage7_post_king_tempo_enabled: bool = False,
    stage7_post_king_tempo_score: float = 30.0,
    stage7_post_box_continuation_enabled: bool = False,
    stage7_post_box_continuation_score: float = 32.0,
    stage7_learned_post_box_continuation_enabled: bool = False,
    stage7_learned_post_box_continuation_bonus: float = 0.0,
    stage7_post_box_frozen_model_candidate_enabled: bool = False,
    stage7_post_box_frozen_model_candidate_support: float = 0.0,
    stage7_post_box_frozen_model: dict | None = None,
    plan_capsule_sandbox_enabled: bool = False,
    stage7_plan_capsule_enabled: bool = False,
    stage7_plan_capsule_ttl: int = 3,
    stage7_plan_capsule_support_bonus: float = 0.0,
    stage7_plan_capsule_owned_arbitration_enabled: bool = False,
    candidate_move_layer_enabled: bool = False,
    stage7_king_support_fence_stabilizer_enabled: bool = False,
    candidate_move_role_support: float = 0.0,
    stage7_plan_capsule_state: dict | None = None,
    current_ply: int | None = None,
    stage7_provider_scope_label: str = "box_shrink",
    active_landmark_label: str | None = None,
    early_stop_stable_suggestions: int = 0,
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
        successor_contract_gate_enabled=successor_contract_gate_enabled,
        successor_role_license_enabled=successor_role_license_enabled,
        explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
        role_owned_score_normalization_enabled=role_owned_score_normalization_enabled,
        successor_role_veto_penalty=successor_role_veto_penalty,
        successor_stage0_drift_penalty=successor_stage0_drift_penalty,
        successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
        successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
        successor_role_scoped_move_shape_require_worst_reply=successor_role_scoped_move_shape_require_worst_reply,
        stagnation_context=stagnation_context,
        stagnation_breaker_enabled=stagnation_breaker_enabled,
        stagnation_breaker_bonus=stagnation_breaker_bonus,
        stagnation_breaker_king_support_bonus=stagnation_breaker_king_support_bonus,
        post_break_continuation_enabled=post_break_continuation_enabled,
        post_break_continuation_bonus=post_break_continuation_bonus,
        stage7_king_tempo_enabled=stage7_king_tempo_enabled,
        stage7_king_tempo_score=stage7_king_tempo_score,
        stage7_drive_repair_enabled=stage7_drive_repair_enabled,
        stage7_drive_repair_score=stage7_drive_repair_score,
        stage7_post_king_tempo_enabled=stage7_post_king_tempo_enabled,
        stage7_post_king_tempo_score=stage7_post_king_tempo_score,
        stage7_post_box_continuation_enabled=stage7_post_box_continuation_enabled,
        stage7_post_box_continuation_score=stage7_post_box_continuation_score,
        stage7_learned_post_box_continuation_enabled=stage7_learned_post_box_continuation_enabled,
        stage7_learned_post_box_continuation_bonus=stage7_learned_post_box_continuation_bonus,
        plan_capsule_sandbox_enabled=plan_capsule_sandbox_enabled,
        stage7_plan_capsule_enabled=stage7_plan_capsule_enabled,
        stage7_plan_capsule_ttl=stage7_plan_capsule_ttl,
        stage7_plan_capsule_support_bonus=stage7_plan_capsule_support_bonus,
        stage7_plan_capsule_owned_arbitration_enabled=(
            stage7_plan_capsule_owned_arbitration_enabled
        ),
        candidate_move_layer_enabled=candidate_move_layer_enabled,
        stage7_king_support_fence_stabilizer_enabled=(
            stage7_king_support_fence_stabilizer_enabled
        ),
        candidate_move_role_support=candidate_move_role_support,
        stage7_plan_capsule_state=stage7_plan_capsule_state,
        current_ply=current_ply,
        stage7_provider_scope_label=stage7_provider_scope_label,
        active_landmark_label=active_landmark_label,
        early_stop_stable_suggestions=early_stop_stable_suggestions,
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
    successor_contract_gate_enabled: bool = False,
    successor_role_license_enabled: bool = False,
    explicit_role_provider_support_enabled: bool = False,
    role_owned_score_normalization_enabled: bool = False,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_context: Optional[dict] = None,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    stagnation_breaker_king_support_bonus: float = 0.0,
    post_break_continuation_enabled: bool = False,
    post_break_continuation_bonus: float = 0.0,
    stage7_king_tempo_enabled: bool = False,
    stage7_king_tempo_score: float = 25.0,
    stage7_drive_repair_enabled: bool = False,
    stage7_drive_repair_score: float = 28.0,
    stage7_post_king_tempo_enabled: bool = False,
    stage7_post_king_tempo_score: float = 30.0,
    stage7_post_box_continuation_enabled: bool = False,
    stage7_post_box_continuation_score: float = 32.0,
    stage7_learned_post_box_continuation_enabled: bool = False,
    stage7_learned_post_box_continuation_bonus: float = 0.0,
    stage7_post_box_frozen_model_candidate_enabled: bool = False,
    stage7_post_box_frozen_model_candidate_support: float = 0.0,
    stage7_post_box_frozen_model: dict | None = None,
    plan_capsule_sandbox_enabled: bool = False,
    stage7_plan_capsule_enabled: bool = False,
    stage7_plan_capsule_ttl: int = 3,
    stage7_plan_capsule_support_bonus: float = 0.0,
    stage7_plan_capsule_owned_arbitration_enabled: bool = False,
    candidate_move_layer_enabled: bool = False,
    stage7_king_support_fence_stabilizer_enabled: bool = False,
    candidate_move_role_support: float = 0.0,
    stage7_plan_capsule_state: dict | None = None,
    current_ply: int | None = None,
    stage7_provider_scope_label: str = "box_shrink",
    active_landmark_label: str | None = None,
    early_stop_stable_suggestions: int = 0,
    forced_successor_skill: Optional[str] = None,
    stage7_king_tempo_already_used: bool = False,
    stage7_drive_repair_already_used: bool = False,
    stage7_drive_repair_post_reply_context: bool = False,
    stage7_post_king_tempo_already_used: bool = False,
    stage7_post_box_post_reply_context: bool = False,
    perf_profile: dict | None = None,
    enable_diagnostic_caches: bool = False,
) -> dict:
    with _profile_timer(perf_profile, "choose_move_details_time"):
        return _choose_move_details_impl(
            graph,
            engine,
            board,
            max_ticks=max_ticks,
            stage_filter=stage_filter,
            suggestion_limit=suggestion_limit,
            successor_affordance_layer_enabled=successor_affordance_layer_enabled,
            successor_contract_gate_enabled=successor_contract_gate_enabled,
            successor_role_license_enabled=successor_role_license_enabled,
            explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
            role_owned_score_normalization_enabled=role_owned_score_normalization_enabled,
            successor_role_veto_penalty=successor_role_veto_penalty,
            successor_stage0_drift_penalty=successor_stage0_drift_penalty,
            successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
            successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
            successor_role_scoped_move_shape_require_worst_reply=successor_role_scoped_move_shape_require_worst_reply,
            stagnation_context=stagnation_context,
            stagnation_breaker_enabled=stagnation_breaker_enabled,
            stagnation_breaker_bonus=stagnation_breaker_bonus,
            stagnation_breaker_king_support_bonus=stagnation_breaker_king_support_bonus,
            post_break_continuation_enabled=post_break_continuation_enabled,
            post_break_continuation_bonus=post_break_continuation_bonus,
            stage7_king_tempo_enabled=stage7_king_tempo_enabled,
            stage7_king_tempo_score=stage7_king_tempo_score,
            stage7_drive_repair_enabled=stage7_drive_repair_enabled,
            stage7_drive_repair_score=stage7_drive_repair_score,
            stage7_post_king_tempo_enabled=stage7_post_king_tempo_enabled,
            stage7_post_king_tempo_score=stage7_post_king_tempo_score,
            stage7_post_box_continuation_enabled=stage7_post_box_continuation_enabled,
            stage7_post_box_continuation_score=stage7_post_box_continuation_score,
            stage7_learned_post_box_continuation_enabled=stage7_learned_post_box_continuation_enabled,
            stage7_learned_post_box_continuation_bonus=stage7_learned_post_box_continuation_bonus,
            stage7_post_box_frozen_model_candidate_enabled=(
                stage7_post_box_frozen_model_candidate_enabled
            ),
            stage7_post_box_frozen_model_candidate_support=(
                stage7_post_box_frozen_model_candidate_support
            ),
            stage7_post_box_frozen_model=stage7_post_box_frozen_model,
            plan_capsule_sandbox_enabled=plan_capsule_sandbox_enabled,
            stage7_plan_capsule_enabled=stage7_plan_capsule_enabled,
            stage7_plan_capsule_ttl=stage7_plan_capsule_ttl,
            stage7_plan_capsule_support_bonus=stage7_plan_capsule_support_bonus,
            stage7_plan_capsule_owned_arbitration_enabled=(
                stage7_plan_capsule_owned_arbitration_enabled
            ),
            candidate_move_layer_enabled=candidate_move_layer_enabled,
            stage7_king_support_fence_stabilizer_enabled=(
                stage7_king_support_fence_stabilizer_enabled
            ),
            candidate_move_role_support=candidate_move_role_support,
            stage7_plan_capsule_state=stage7_plan_capsule_state,
            current_ply=current_ply,
            stage7_provider_scope_label=stage7_provider_scope_label,
            active_landmark_label=active_landmark_label,
            early_stop_stable_suggestions=early_stop_stable_suggestions,
            forced_successor_skill=forced_successor_skill,
            stage7_king_tempo_already_used=stage7_king_tempo_already_used,
            stage7_drive_repair_already_used=stage7_drive_repair_already_used,
            stage7_drive_repair_post_reply_context=stage7_drive_repair_post_reply_context,
            stage7_post_king_tempo_already_used=stage7_post_king_tempo_already_used,
            stage7_post_box_post_reply_context=stage7_post_box_post_reply_context,
            perf_profile=perf_profile,
            enable_diagnostic_caches=enable_diagnostic_caches,
        )


def _choose_move_details_impl(
    graph: Graph,
    engine: ReConEngine,
    board: chess.Board,
    max_ticks: int = 200,
    stage_filter: Optional[int] = None,
    suggestion_limit: int = 10,
    successor_affordance_layer_enabled: bool = False,
    successor_contract_gate_enabled: bool = False,
    successor_role_license_enabled: bool = False,
    explicit_role_provider_support_enabled: bool = False,
    role_owned_score_normalization_enabled: bool = False,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_context: Optional[dict] = None,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    stagnation_breaker_king_support_bonus: float = 0.0,
    post_break_continuation_enabled: bool = False,
    post_break_continuation_bonus: float = 0.0,
    stage7_king_tempo_enabled: bool = False,
    stage7_king_tempo_score: float = 25.0,
    stage7_drive_repair_enabled: bool = False,
    stage7_drive_repair_score: float = 28.0,
    stage7_post_king_tempo_enabled: bool = False,
    stage7_post_king_tempo_score: float = 30.0,
    stage7_post_box_continuation_enabled: bool = False,
    stage7_post_box_continuation_score: float = 32.0,
    stage7_learned_post_box_continuation_enabled: bool = False,
    stage7_learned_post_box_continuation_bonus: float = 0.0,
    plan_capsule_sandbox_enabled: bool = False,
    stage7_plan_capsule_enabled: bool = False,
    stage7_plan_capsule_ttl: int = 3,
    stage7_plan_capsule_support_bonus: float = 0.0,
    stage7_plan_capsule_owned_arbitration_enabled: bool = False,
    candidate_move_layer_enabled: bool = False,
    stage7_king_support_fence_stabilizer_enabled: bool = False,
    candidate_move_role_support: float = 0.0,
    stage7_post_box_frozen_model_candidate_enabled: bool = False,
    stage7_post_box_frozen_model_candidate_support: float = 0.0,
    stage7_post_box_frozen_model: dict | None = None,
    stage7_plan_capsule_state: dict | None = None,
    current_ply: int | None = None,
    stage7_provider_scope_label: str = "box_shrink",
    active_landmark_label: str | None = None,
    early_stop_stable_suggestions: int = 0,
    forced_successor_skill: Optional[str] = None,
    stage7_king_tempo_already_used: bool = False,
    stage7_drive_repair_already_used: bool = False,
    stage7_drive_repair_post_reply_context: bool = False,
    stage7_post_king_tempo_already_used: bool = False,
    stage7_post_box_post_reply_context: bool = False,
    perf_profile: dict | None = None,
    enable_diagnostic_caches: bool = False,
) -> dict:
    env = {
        "board": board,
        "chosen_move": None,
        "suggested_move": None,
        "__graph__": graph,
        "blackboard": {"stage_filter": stage_filter} if stage_filter is not None else {},
        "successor_affordance_layer_enabled": successor_affordance_layer_enabled,
        "successor_contract_gate_enabled": successor_contract_gate_enabled,
        "successor_role_license_enabled": successor_role_license_enabled,
    }
    if perf_profile:
        env["blackboard"]["perf_profile"] = perf_profile
    env["blackboard"]["diagnostic_caches_enabled"] = bool(enable_diagnostic_caches)
    env["blackboard"]["successor_affordance_layer_enabled"] = successor_affordance_layer_enabled
    env["blackboard"]["successor_contract_gate_enabled"] = successor_contract_gate_enabled
    env["blackboard"]["successor_role_license_enabled"] = successor_role_license_enabled
    env["blackboard"]["explicit_role_provider_support_enabled"] = explicit_role_provider_support_enabled
    env["blackboard"]["role_owned_score_normalization_enabled"] = (
        role_owned_score_normalization_enabled
    )
    env["blackboard"]["successor_role_veto_penalty"] = successor_role_veto_penalty
    env["blackboard"]["successor_stage0_drift_penalty"] = successor_stage0_drift_penalty
    env["blackboard"]["successor_role_scoped_move_shape_enabled"] = successor_role_scoped_move_shape_enabled
    env["blackboard"]["successor_role_scoped_move_shape_bonus"] = successor_role_scoped_move_shape_bonus
    env["blackboard"]["successor_role_scoped_move_shape_require_worst_reply"] = (
        successor_role_scoped_move_shape_require_worst_reply
    )
    if stagnation_context:
        dynamic_terms = {
            "repeated_abstract_state": bool(stagnation_context.get("repeated_abstract_state_count", 0)),
            "rook_oscillation_loop": bool(stagnation_context.get("rook_oscillation_loop", False)),
            "no_box_progress_recently": bool(stagnation_context.get("no_box_progress_recently", False)),
            "no_edge_progress_recently": bool(stagnation_context.get("no_edge_progress_recently", False)),
            "no_mate_progress_recently": bool(stagnation_context.get("no_mate_progress_recently", False)),
            "safe_loop_breaking_move_available": bool(stagnation_context.get("safe_loop_breaking_move_available", False)),
            "loop_breaking_rook_transfer_available": bool(stagnation_context.get("loop_breaking_rook_transfer_available", False)),
            "loop_breaking_check_or_cut_available": bool(stagnation_context.get("loop_breaking_check_or_cut_available", False)),
            "rook_oscillation_loop_recently_broken": bool(stagnation_context.get("rook_oscillation_loop_recently_broken", False)),
            "confinement_preserved_after_break": bool(stagnation_context.get("confinement_preserved_after_break", False)),
            "enemy_king_edge_control_preserved": bool(stagnation_context.get("enemy_king_edge_control_preserved", False)),
            "post_stagnation_break_continuation_needed": bool(stagnation_context.get("post_stagnation_break_continuation_needed", False)),
            "safe_followup_available": bool(stagnation_context.get("safe_followup_available", False)),
        }
        env["blackboard"]["krk_dynamic_context_terms"] = dynamic_terms
        env["blackboard"].setdefault("krk_visible_terms", {}).update(dynamic_terms)
        env["blackboard"]["krk_stagnation_context"] = dict(stagnation_context)
        env["blackboard"]["krk_post_break_continuation_context"] = dict(
            stagnation_context.get("post_break_continuation_context", {}) or {}
        )
    env["blackboard"]["stagnation_breaker_enabled"] = bool(stagnation_breaker_enabled)
    env["blackboard"]["stagnation_breaker_bonus"] = float(stagnation_breaker_bonus)
    env["blackboard"]["stagnation_breaker_king_support_bonus"] = float(
        stagnation_breaker_king_support_bonus
    )
    env["blackboard"]["post_break_continuation_enabled"] = bool(post_break_continuation_enabled)
    env["blackboard"]["post_break_continuation_bonus"] = float(post_break_continuation_bonus)
    env["blackboard"]["stage7_king_tempo_enabled"] = bool(stage7_king_tempo_enabled)
    env["blackboard"]["stage7_king_tempo_score"] = float(stage7_king_tempo_score)
    env["blackboard"]["stage7_king_tempo_already_used"] = bool(stage7_king_tempo_already_used)
    env["blackboard"]["stage7_drive_repair_enabled"] = bool(stage7_drive_repair_enabled)
    env["blackboard"]["stage7_drive_repair_score"] = float(stage7_drive_repair_score)
    env["blackboard"]["stage7_drive_repair_already_used"] = bool(stage7_drive_repair_already_used)
    env["blackboard"]["stage7_drive_repair_post_reply_context"] = bool(
        stage7_drive_repair_post_reply_context
    )
    env["blackboard"]["stage7_post_king_tempo_enabled"] = bool(stage7_post_king_tempo_enabled)
    env["blackboard"]["stage7_post_king_tempo_score"] = float(stage7_post_king_tempo_score)
    env["blackboard"]["stage7_post_king_tempo_already_used"] = bool(
        stage7_post_king_tempo_already_used
    )
    env["blackboard"]["stage7_post_box_continuation_enabled"] = bool(
        stage7_post_box_continuation_enabled
    )
    env["blackboard"]["stage7_post_box_continuation_score"] = float(
        stage7_post_box_continuation_score
    )
    env["blackboard"]["stage7_learned_post_box_continuation_enabled"] = bool(
        stage7_learned_post_box_continuation_enabled
    )
    env["blackboard"]["stage7_learned_post_box_continuation_bonus"] = float(
        stage7_learned_post_box_continuation_bonus
    )
    env["blackboard"]["stage7_post_box_post_reply_context"] = bool(
        stage7_post_box_post_reply_context
    )
    env["blackboard"]["plan_capsule_sandbox_enabled"] = bool(plan_capsule_sandbox_enabled)
    env["blackboard"]["stage7_plan_capsule_enabled"] = bool(stage7_plan_capsule_enabled)
    env["blackboard"]["stage7_plan_capsule_ttl"] = int(stage7_plan_capsule_ttl)
    env["blackboard"]["stage7_plan_capsule_support_bonus"] = float(stage7_plan_capsule_support_bonus)
    env["blackboard"]["stage7_plan_capsule_owned_arbitration_enabled"] = bool(
        stage7_plan_capsule_owned_arbitration_enabled
    )
    env["blackboard"]["candidate_move_layer_enabled"] = bool(candidate_move_layer_enabled)
    env["blackboard"]["stage7_king_support_fence_stabilizer_enabled"] = bool(
        stage7_king_support_fence_stabilizer_enabled
    )
    env["blackboard"]["candidate_move_role_support"] = float(candidate_move_role_support)
    env["blackboard"]["stage7_post_box_frozen_model_candidate_enabled"] = bool(
        stage7_post_box_frozen_model_candidate_enabled
    )
    env["blackboard"]["stage7_post_box_frozen_model_candidate_support"] = float(
        stage7_post_box_frozen_model_candidate_support
    )
    if stage7_plan_capsule_state:
        env["blackboard"]["stage7_plan_capsule_state"] = dict(stage7_plan_capsule_state)
    env["blackboard"]["stage7_provider_scope_label"] = str(stage7_provider_scope_label or "box_shrink")
    if active_landmark_label:
        env["blackboard"]["active_landmark_label"] = str(active_landmark_label)
        env["blackboard"].setdefault("krk_visible_terms", {})[
            f"active_landmark_label.{active_landmark_label}"
        ] = True
    if stage7_post_box_post_reply_context:
        dynamic_terms = env["blackboard"].setdefault("krk_dynamic_context_terms", {})
        visible_terms = env["blackboard"].setdefault("krk_visible_terms", {})
        for term in (
            "post_reply_state_reached",
            "box_shrink_attempt_confirmed_or_candidate_confirmed",
        ):
            dynamic_terms[term] = True
            visible_terms[term] = True
        try:
            no_mate_in_one = not bool(_mate_in_one_available(board))
        except Exception:
            no_mate_in_one = True
        dynamic_terms["conversion_not_immediate"] = no_mate_in_one
        dynamic_terms["no_mate_in_one_available"] = no_mate_in_one
        dynamic_terms["no_stronger_mate_or_tactic_interrupt_available"] = no_mate_in_one
        visible_terms["conversion_not_immediate"] = no_mate_in_one
        visible_terms["no_mate_in_one_available"] = no_mate_in_one
        visible_terms["no_stronger_mate_or_tactic_interrupt_available"] = no_mate_in_one
    if forced_successor_skill:
        env["blackboard"]["forced_successor_skill"] = forced_successor_skill

    _materialize_explicit_support_roles(graph, env)
    _materialize_stage7_sandbox_providers(graph, env)
    _materialize_plan_capsule_markers(graph, env)
    if stage7_plan_capsule_enabled:
        marker = (
            env.get("blackboard", {})
            .get("krk_plan_capsule_markers", {})
            .get("krk.post_box_shrink_continuation", {})
        )
        plan_state = _prepare_stage7_plan_capsule_state(
            current_state=stage7_plan_capsule_state,
            marker=marker,
            ttl=int(stage7_plan_capsule_ttl),
            current_ply=current_ply,
        )
        env["blackboard"]["stage7_plan_capsule_state"] = plan_state
        env["blackboard"].setdefault("krk_plan_capsule_markers", {}).setdefault(
            "krk.post_box_shrink_continuation", {}
        )["plan_state"] = dict(plan_state)

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
    early_stopped = False
    stable_suggestion_ticks = 0
    last_suggestion_signature = None
    while ticks < max_ticks and env.get("chosen_move") is None:
        ticks += 1
        _profile_add_count(perf_profile, "engine_ticks")
        with _profile_timer(perf_profile, "engine_step_time"):
            engine.step(env)
        if early_stop_stable_suggestions > 0:
            signature = _suggestion_stability_signature(
                list(env.get("actuator_suggestions", []) or []),
                forced_successor_skill=forced_successor_skill,
            )
            if signature is None:
                stable_suggestion_ticks = 0
                last_suggestion_signature = None
                continue
            if signature == last_suggestion_signature:
                stable_suggestion_ticks += 1
            else:
                stable_suggestion_ticks = 1
                last_suggestion_signature = signature
            if stable_suggestion_ticks >= early_stop_stable_suggestions:
                early_stopped = True
                break
    _materialize_plan_capsule_markers(graph, env)
    if stage7_plan_capsule_enabled:
        marker = (
            env.get("blackboard", {})
            .get("krk_plan_capsule_markers", {})
            .get("krk.post_box_shrink_continuation", {})
        )
        plan_state = _prepare_stage7_plan_capsule_state(
            current_state=env.get("blackboard", {}).get("stage7_plan_capsule_state", {}),
            marker=marker,
            ttl=int(stage7_plan_capsule_ttl),
            current_ply=current_ply,
        )
        env["blackboard"]["stage7_plan_capsule_state"] = plan_state
        env["blackboard"].setdefault("krk_plan_capsule_markers", {}).setdefault(
            "krk.post_box_shrink_continuation", {}
        )["plan_state"] = dict(plan_state)
    _apply_stage7_candidate_move_layer(
        env,
        role_enabled=bool(stage7_king_support_fence_stabilizer_enabled),
        support_amount=float(candidate_move_role_support),
    )
    _apply_stage7_post_box_frozen_model_candidate_layer(
        env,
        model=stage7_post_box_frozen_model,
        support_amount=float(stage7_post_box_frozen_model_candidate_support),
    )
    suggestions = list(env.get("actuator_suggestions", []))
    suggestions.sort(key=lambda item: item.get("score", float("-inf")), reverse=True)
    selected_suggestion = suggestions[0] if suggestions else None
    raw_selected_suggestion = selected_suggestion
    selected_by_role_owned_score_normalization = False
    selected_by_stage7_plan_capsule_owned_arbitration = False
    forced_candidates = []
    if forced_successor_skill:
        forced_candidates = [
            item for item in suggestions
            if _skill_id_for_suggestion(item) == forced_successor_skill
        ]
        forced_candidates.sort(key=lambda item: item.get("score", float("-inf")), reverse=True)
        selected_suggestion = forced_candidates[0] if forced_candidates else None
    elif role_owned_score_normalization_enabled:
        adapter_candidates = _adapter_supported_role_owned_candidates(suggestions)
        if adapter_candidates:
            selected_suggestion = adapter_candidates[0]
            selected_by_role_owned_score_normalization = True
            selected_meta = selected_suggestion.setdefault("meta", {})
            if isinstance(selected_meta, dict):
                selected_meta["visible_role_owned_score_normalization"] = {
                    "enabled": True,
                    "mode": "adapter_role_priority",
                    "raw_selected_skill": _skill_id_for_suggestion(raw_selected_suggestion or {}),
                    "raw_selected_move": (
                        (raw_selected_suggestion or {}).get("move").uci()
                        if hasattr((raw_selected_suggestion or {}).get("move"), "uci")
                        else (raw_selected_suggestion or {}).get("move")
                    ),
                    "raw_selected_score": float(
                        (raw_selected_suggestion or {}).get("score", 0.0) or 0.0
                    ),
                    "selected_skill": _skill_id_for_suggestion(selected_suggestion),
                    "selected_move": (
                        selected_suggestion.get("move").uci()
                        if hasattr(selected_suggestion.get("move"), "uci")
                        else selected_suggestion.get("move")
                    ),
                    "selected_score": float(selected_suggestion.get("score", 0.0) or 0.0),
                    "candidate_count": len(adapter_candidates),
                    "causal_status": "sandbox_opt_in",
                    "direct_request": False,
                }
    if (
        not forced_successor_skill
        and stage7_plan_capsule_owned_arbitration_enabled
    ):
        plan_candidates = _plan_capsule_supported_owned_candidates(suggestions)
        if plan_candidates:
            selected_suggestion = plan_candidates[0]
            selected_by_stage7_plan_capsule_owned_arbitration = True
            selected_meta = selected_suggestion.setdefault("meta", {})
            if isinstance(selected_meta, dict):
                selected_meta["visible_stage7_plan_capsule_owned_arbitration"] = {
                    "enabled": True,
                    "mode": "bounded_plan_capsule_owned_window",
                    "plan_id": (
                        selected_meta.get("visible_stage7_plan_capsule_license", {})
                        if isinstance(
                            selected_meta.get("visible_stage7_plan_capsule_license"), dict
                        )
                        else {}
                    ).get("plan_id", "krk.post_box_shrink_continuation"),
                    "raw_selected_skill": _skill_id_for_suggestion(raw_selected_suggestion or {}),
                    "raw_selected_move": (
                        (raw_selected_suggestion or {}).get("move").uci()
                        if hasattr((raw_selected_suggestion or {}).get("move"), "uci")
                        else (raw_selected_suggestion or {}).get("move")
                    ),
                    "raw_selected_score": float(
                        (raw_selected_suggestion or {}).get("score", 0.0) or 0.0
                    ),
                    "selected_skill": _skill_id_for_suggestion(selected_suggestion),
                    "selected_move": (
                        selected_suggestion.get("move").uci()
                        if hasattr(selected_suggestion.get("move"), "uci")
                        else selected_suggestion.get("move")
                    ),
                    "selected_score": float(selected_suggestion.get("score", 0.0) or 0.0),
                    "candidate_count": len(plan_candidates),
                    "causal_status": "sandbox_opt_in",
                    "direct_request": False,
                }
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
    adapter_support_summary = _adapter_support_summary_for_suggestions(suggestion_source)
    candidate_move_role_summary = _candidate_move_role_summary_for_suggestions(
        suggestion_source,
        selected_suggestion=selected_suggestion,
    )
    frozen_model_candidate_summary = _frozen_model_candidate_summary_for_suggestions(
        suggestion_source,
        selected_suggestion=selected_suggestion,
    )
    plan_capsule_support_summary = _plan_capsule_support_summary_for_suggestions(
        suggestion_source,
        selected_suggestion=selected_suggestion,
        plan_state=env.get("blackboard", {}).get("stage7_plan_capsule_state", {}) or {},
    )
    clean_suggestions = []
    clean_source = list(suggestion_source)
    if (
        selected_by_role_owned_score_normalization
        and selected_suggestion is not None
        and selected_suggestion not in clean_source[:max(0, suggestion_limit)]
    ):
        clean_source = [selected_suggestion] + clean_source
    for item in clean_source[:max(0, suggestion_limit)]:
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
    result = {
        "move": selected_move,
        "ticks": ticks,
        "confidence": selected_confidence,
        "suggested_actuator": selected_actuator,
        "selected_suggestion": _compact_selected_suggestion(selected_suggestion),
        "suggestions": clean_suggestions,
        "forced_successor_skill": forced_successor_skill,
        "forced_successor_available": bool(forced_candidates) if forced_successor_skill else None,
        "successor_contract_gate_enabled": successor_contract_gate_enabled,
        "successor_role_license_enabled": successor_role_license_enabled,
        "successor_role_veto_penalty": successor_role_veto_penalty,
        "successor_stage0_drift_penalty": successor_stage0_drift_penalty,
        "successor_role_scoped_move_shape_enabled": successor_role_scoped_move_shape_enabled,
        "successor_role_scoped_move_shape_bonus": successor_role_scoped_move_shape_bonus,
        "successor_role_scoped_move_shape_require_worst_reply": successor_role_scoped_move_shape_require_worst_reply,
        "stagnation_breaker_enabled": bool(stagnation_breaker_enabled),
        "stagnation_breaker_bonus": float(stagnation_breaker_bonus),
        "stagnation_breaker_king_support_bonus": float(stagnation_breaker_king_support_bonus),
        "post_break_continuation_enabled": bool(post_break_continuation_enabled),
        "post_break_continuation_bonus": float(post_break_continuation_bonus),
        "stage7_king_tempo_enabled": bool(stage7_king_tempo_enabled),
        "stage7_king_tempo_score": float(stage7_king_tempo_score),
        "stage7_king_tempo_already_used": bool(stage7_king_tempo_already_used),
        "stage7_drive_repair_enabled": bool(stage7_drive_repair_enabled),
        "stage7_drive_repair_score": float(stage7_drive_repair_score),
        "stage7_drive_repair_already_used": bool(stage7_drive_repair_already_used),
        "stage7_drive_repair_post_reply_context": bool(stage7_drive_repair_post_reply_context),
        "stage7_post_king_tempo_enabled": bool(stage7_post_king_tempo_enabled),
        "stage7_post_king_tempo_score": float(stage7_post_king_tempo_score),
        "stage7_post_king_tempo_already_used": bool(stage7_post_king_tempo_already_used),
        "stage7_post_box_continuation_enabled": bool(stage7_post_box_continuation_enabled),
        "stage7_post_box_continuation_score": float(stage7_post_box_continuation_score),
        "stage7_learned_post_box_continuation_enabled": bool(stage7_learned_post_box_continuation_enabled),
        "stage7_learned_post_box_continuation_bonus": float(stage7_learned_post_box_continuation_bonus),
        "stage7_post_box_frozen_model_candidate_enabled": bool(
            stage7_post_box_frozen_model_candidate_enabled
        ),
        "stage7_post_box_frozen_model_candidate_support": float(
            stage7_post_box_frozen_model_candidate_support
        ),
        "stage7_post_box_frozen_model_candidate": dict(
            env.get("blackboard", {}).get("stage7_post_box_frozen_model_candidate", {}) or {}
        ),
        "plan_capsule_sandbox_enabled": bool(plan_capsule_sandbox_enabled),
        "stage7_plan_capsule_enabled": bool(stage7_plan_capsule_enabled),
        "stage7_plan_capsule_ttl": int(stage7_plan_capsule_ttl),
        "stage7_plan_capsule_support_bonus": float(stage7_plan_capsule_support_bonus),
        "stage7_plan_capsule_owned_arbitration_enabled": bool(
            stage7_plan_capsule_owned_arbitration_enabled
        ),
        "candidate_move_layer_enabled": bool(candidate_move_layer_enabled),
        "stage7_king_support_fence_stabilizer_enabled": bool(
            stage7_king_support_fence_stabilizer_enabled
        ),
        "candidate_move_role_support": float(candidate_move_role_support),
        "candidate_move_frames": list(
            env.get("blackboard", {}).get("krk_candidate_move_frames", []) or []
        ),
        "candidate_move_enumerator": dict(
            env.get("blackboard", {}).get("krk_candidate_move_enumerator", {}) or {}
        ),
        "candidate_move_role_matches": dict(
            env.get("blackboard", {}).get("krk_candidate_move_role_matches", {}) or {}
        ),
        "stage7_plan_capsule_state": dict(
            env.get("blackboard", {}).get("stage7_plan_capsule_state", {}) or {}
        ),
        "plan_capsule_markers": dict(
            env.get("blackboard", {}).get("krk_plan_capsule_markers", {}) or {}
        ),
        "stage7_post_box_post_reply_context": bool(stage7_post_box_post_reply_context),
        "stage7_provider_scope_label": str(stage7_provider_scope_label or "box_shrink"),
        "active_landmark_label": str(active_landmark_label or ""),
        "stagnation_context": dict(stagnation_context or {}),
        "early_stop_stable_suggestions": int(early_stop_stable_suggestions),
        "early_stopped": bool(early_stopped),
        "stable_suggestion_ticks": int(stable_suggestion_ticks),
        "role_owned_score_normalization_enabled": bool(role_owned_score_normalization_enabled),
        "selected_by_role_owned_score_normalization": bool(
            selected_by_role_owned_score_normalization
        ),
        "selected_by_stage7_plan_capsule_owned_arbitration": bool(
            selected_by_stage7_plan_capsule_owned_arbitration
        ),
        "role_owned_raw_selected": _compact_selected_suggestion(raw_selected_suggestion),
        "visible_terms": dict(env.get("blackboard", {}).get("krk_visible_terms", {}) or {}),
        "successor_affordances": dict(
            env.get("blackboard", {}).get("krk_successor_affordances", {}) or {}
        ),
        "successor_role_affordances": dict(
            env.get("blackboard", {}).get("krk_successor_role_affordances", {}) or {}
        ),
        "successor_provider_licenses": dict(
            env.get("blackboard", {}).get("krk_successor_provider_licenses", {}) or {}
        ),
        "explicit_role_provider_supports": dict(
            env.get("blackboard", {}).get("krk_explicit_role_provider_supports", {}) or {}
        ),
        **adapter_support_summary,
        **candidate_move_role_summary,
        **frozen_model_candidate_summary,
        **plan_capsule_support_summary,
        "context_terms_cache_hits": int(
            env.get("blackboard", {}).get("krk_context_terms_cache_hits", 0) or 0
        ),
        "context_terms_cache_misses": int(
            env.get("blackboard", {}).get("krk_context_terms_cache_misses", 0) or 0
        ),
        "move_shape_audit_cache_hits": int(
            env.get("blackboard", {}).get("krk_move_shape_audit_cache_hits", 0) or 0
        ),
        "move_shape_audit_cache_misses": int(
            env.get("blackboard", {}).get("krk_move_shape_audit_cache_misses", 0) or 0
        ),
    }
    return result


def oracle_best_reward(
    board: chess.Board,
    label: str,
    lookahead_black: bool,
    perf_profile: dict | None = None,
) -> float:
    cache = _diagnostic_cache(perf_profile, "oracle_best_reward")
    cache_key = (_board_cache_key(board), label, bool(lookahead_black))
    if cache is not None and cache_key in cache:
        _profile_cache_event(perf_profile, "oracle_best_reward", True)
        return float(cache[cache_key])
    if cache is not None:
        _profile_cache_event(perf_profile, "oracle_best_reward", False)
    _profile_add_count(perf_profile, "oracle_best_reward_calls")
    best = -float("inf")
    for move in board.legal_moves:
        reward = _profiled_worst_reply_reward(
            board,
            move,
            label,
            use_black_reply=lookahead_black,
            perf_profile=perf_profile,
        )
        if reward > best:
            best = reward
    if cache is not None:
        cache[cache_key] = float(best)
    return best


def oracle_move_rewards(
    board: chess.Board,
    label: str,
    lookahead_black: bool,
    perf_profile: dict | None = None,
) -> list[tuple[chess.Move, float]]:
    rewards = [
        (
            move,
            _profiled_worst_reply_reward(
                board,
                move,
                label,
                use_black_reply=lookahead_black,
                perf_profile=perf_profile,
            ),
        )
        for move in board.legal_moves
    ]
    rewards.sort(key=lambda item: item[1], reverse=True)
    return rewards


def _profiled_worst_reply_reward(
    board: chess.Board,
    move: chess.Move,
    label: str,
    *,
    use_black_reply: bool,
    perf_profile: dict | None = None,
) -> float:
    cache = _diagnostic_cache(perf_profile, "worst_reply_reward")
    cache_key = (
        _board_cache_key(board),
        move.uci(),
        label,
        bool(use_black_reply),
    )
    if cache is not None and cache_key in cache:
        _profile_cache_event(perf_profile, "worst_reply_reward", True)
        return float(cache[cache_key])
    if cache is not None:
        _profile_cache_event(perf_profile, "worst_reply_reward", False)
    _profile_add_count(perf_profile, "worst_reply_reward_calls")
    with _profile_timer(perf_profile, "worst_reply_reward_time"):
        reward = worst_reply_reward(
            board,
            move,
            label,
            use_black_reply=use_black_reply,
        )
    if cache is not None:
        cache[cache_key] = float(reward)
    return reward


def choose_black_reply(
    rng: random.Random,
    board: chess.Board,
    label: str,
    policy: str,
    perf_profile: dict | None = None,
) -> chess.Move | None:
    with _profile_timer(perf_profile, "choose_black_reply_time"):
        cache = _diagnostic_cache(perf_profile, "black_reply")
        cache_key = (_board_cache_key(board), label, policy)
        if cache is not None and cache_key in cache:
            _profile_cache_event(perf_profile, "black_reply", True)
            cached = cache[cache_key]
            return chess.Move.from_uci(cached) if cached else None
        if cache is not None:
            _profile_cache_event(perf_profile, "black_reply", False)
        replies = list(board.legal_moves)
        if not replies:
            if cache is not None:
                cache[cache_key] = None
            return None
        if policy == "random":
            return rng.choice(replies)

        # Adversarial Black chooses the reply that gives White the worst next
        # one-ply landmark opportunity. This is intentionally cheap, not tablebase.
        scored = []
        for reply in replies:
            _profile_add_count(perf_profile, "board_copy_calls")
            b2 = board.copy()
            b2.push(reply)
            scored.append((
                oracle_best_reward(
                    b2,
                    label,
                    lookahead_black=False,
                    perf_profile=perf_profile,
                ),
                reply,
            ))
        reply = min(scored, key=lambda item: item[0])[1]
        if cache is not None:
            cache[cache_key] = reply.uci()
        return reply


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
    successor_contract_gate_enabled: bool = False,
    successor_role_license_enabled: bool = False,
    explicit_role_provider_support_enabled: bool = False,
    role_owned_score_normalization_enabled: bool = False,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    stagnation_breaker_king_support_bonus: float = 0.0,
    post_break_continuation_enabled: bool = False,
    post_break_continuation_bonus: float = 0.0,
    stage7_king_tempo_enabled: bool = False,
    stage7_king_tempo_score: float = 25.0,
    stage7_drive_repair_enabled: bool = False,
    stage7_drive_repair_score: float = 28.0,
    stage7_post_king_tempo_enabled: bool = False,
    stage7_post_king_tempo_score: float = 30.0,
    stage7_post_box_continuation_enabled: bool = False,
    stage7_post_box_continuation_score: float = 32.0,
    stage7_learned_post_box_continuation_enabled: bool = False,
    stage7_learned_post_box_continuation_bonus: float = 0.0,
    plan_capsule_sandbox_enabled: bool = False,
    stage7_plan_capsule_enabled: bool = False,
    stage7_plan_capsule_ttl: int = 3,
    stage7_plan_capsule_support_bonus: float = 0.0,
    stage7_plan_capsule_owned_arbitration_enabled: bool = False,
    candidate_move_layer_enabled: bool = False,
    stage7_king_support_fence_stabilizer_enabled: bool = False,
    candidate_move_role_support: float = 0.0,
    stage7_post_box_frozen_model_candidate_enabled: bool = False,
    stage7_post_box_frozen_model_candidate_support: float = 0.0,
    stage7_post_box_frozen_model: dict | None = None,
    early_stop_stable_suggestions: int = 0,
    lock_stage_filter_through_playout: bool = False,
    forced_successor_skill: Optional[str] = None,
    perf_profile: dict | None = None,
    enable_diagnostic_caches: bool = False,
    initial_white_moves: int = 0,
) -> dict:
    """Run a simple KRK playout using the compiled topology for White moves."""
    _profile_add_count(perf_profile, "board_copy_calls")
    b = board.copy()
    white_moves = int(initial_white_moves)
    events = []
    all_events = []
    trace_truncated_events = 0
    first_reply: dict | None = None
    first_successor: dict | None = None
    engine_perf: dict = {}
    stage7_king_tempo_used = False
    stage7_drive_repair_used = False
    stage7_post_king_tempo_used = False
    stage7_plan_capsule_state = _stage7_plan_capsule_default_state(
        ttl=int(stage7_plan_capsule_ttl)
    )

    def record_event(event: dict) -> None:
        nonlocal trace_truncated_events
        all_events.append(event)
        if not trace:
            return
        if trace_max_plies is None or len(events) < trace_max_plies:
            events.append(event)
        else:
            trace_truncated_events += 1

    def finish(result: str, ply: int) -> dict:
        payload = {"result": result, "plies": ply}
        payload.update({
            "engine_decision_count": int(engine_perf.get("engine_decision_count", 0)),
            "engine_ticks_total": int(engine_perf.get("engine_ticks_total", 0)),
            "engine_ticks_max": int(engine_perf.get("engine_ticks_max", 0)),
            "engine_early_stop_count": int(engine_perf.get("engine_early_stop_count", 0)),
            "stage7_plan_capsule_state": dict(stage7_plan_capsule_state),
            "final_turn": "white" if b.turn == chess.WHITE else "black",
            "final_mate_in_one_available": _mate_in_one_available(b),
        })
        if first_reply is not None:
            payload["first_reply"] = first_reply
        if first_successor is not None:
            payload["first_successor"] = first_successor
        if trace:
            payload["final_fen"] = b.fen()
            payload["trace"] = events
            with _profile_timer(perf_profile, "stagnation_summary_time"):
                payload["stagnation_summary"] = _playout_stagnation_summary(
                    all_events,
                    current_board=b,
                )
            if trace_truncated_events:
                payload["trace_truncated_events"] = trace_truncated_events
        return payload

    for ply in range(max_plies):
        if b.is_checkmate():
            return finish("mate", ply)
        if b.is_stalemate() or b.is_insufficient_material():
            return finish("draw", ply)

        if b.turn == chess.WHITE:
            # Default: use the stage filter for the tested handoff move, then
            # allow the full topology to convert through lower-stage skills.
            # Guardrail diagnostics can opt into keeping the protected provider
            # version locked for the full playout so later overlays cannot
            # silently interfere with validated lower-stage ownership.
            active_stage_filter = (
                stage_filter
                if (white_moves == 0 or lock_stage_filter_through_playout)
                else None
            )
            active_forced_successor = forced_successor_skill if white_moves == 0 else None
            before_fen = b.fen()
            with _profile_timer(perf_profile, "stagnation_summary_time"):
                stagnation_context = _playout_stagnation_summary(
                    all_events,
                    current_board=b,
                )
                stagnation_context = _with_post_break_continuation_context(
                    stagnation_context,
                    all_events=all_events,
                    current_board=b,
                )
            _profile_add_count(perf_profile, "playout_decisions")
            move_details = choose_move_details(
                graph,
                engine,
                b,
                max_ticks=max_ticks,
                stage_filter=active_stage_filter,
                suggestion_limit=suggestion_limit,
                successor_affordance_layer_enabled=successor_affordance_layer_enabled,
                successor_contract_gate_enabled=successor_contract_gate_enabled,
                successor_role_license_enabled=successor_role_license_enabled,
                explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
                role_owned_score_normalization_enabled=role_owned_score_normalization_enabled,
                successor_role_veto_penalty=successor_role_veto_penalty,
                successor_stage0_drift_penalty=successor_stage0_drift_penalty,
                successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
                successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
                successor_role_scoped_move_shape_require_worst_reply=(
                    successor_role_scoped_move_shape_require_worst_reply
                ),
                stagnation_context=stagnation_context,
                stagnation_breaker_enabled=stagnation_breaker_enabled,
                stagnation_breaker_bonus=stagnation_breaker_bonus,
                stagnation_breaker_king_support_bonus=stagnation_breaker_king_support_bonus,
                post_break_continuation_enabled=post_break_continuation_enabled,
                post_break_continuation_bonus=post_break_continuation_bonus,
                stage7_king_tempo_enabled=stage7_king_tempo_enabled,
                stage7_king_tempo_score=stage7_king_tempo_score,
                stage7_drive_repair_enabled=stage7_drive_repair_enabled,
                stage7_drive_repair_score=stage7_drive_repair_score,
                stage7_post_king_tempo_enabled=stage7_post_king_tempo_enabled,
                stage7_post_king_tempo_score=stage7_post_king_tempo_score,
                stage7_post_box_continuation_enabled=stage7_post_box_continuation_enabled,
                stage7_post_box_continuation_score=stage7_post_box_continuation_score,
                stage7_learned_post_box_continuation_enabled=stage7_learned_post_box_continuation_enabled,
                stage7_learned_post_box_continuation_bonus=stage7_learned_post_box_continuation_bonus,
                plan_capsule_sandbox_enabled=plan_capsule_sandbox_enabled,
                stage7_plan_capsule_enabled=stage7_plan_capsule_enabled,
                stage7_plan_capsule_ttl=stage7_plan_capsule_ttl,
                stage7_plan_capsule_support_bonus=stage7_plan_capsule_support_bonus,
                stage7_plan_capsule_owned_arbitration_enabled=(
                    stage7_plan_capsule_owned_arbitration_enabled
                ),
                candidate_move_layer_enabled=candidate_move_layer_enabled,
                stage7_king_support_fence_stabilizer_enabled=(
                    stage7_king_support_fence_stabilizer_enabled
                ),
                candidate_move_role_support=candidate_move_role_support,
                stage7_post_box_frozen_model_candidate_enabled=(
                    stage7_post_box_frozen_model_candidate_enabled
                ),
                stage7_post_box_frozen_model_candidate_support=(
                    stage7_post_box_frozen_model_candidate_support
                ),
                stage7_post_box_frozen_model=stage7_post_box_frozen_model,
                stage7_plan_capsule_state=stage7_plan_capsule_state,
                current_ply=ply,
                active_landmark_label=label,
                stage7_king_tempo_already_used=stage7_king_tempo_used,
                stage7_drive_repair_already_used=stage7_drive_repair_used,
                stage7_drive_repair_post_reply_context=white_moves > 0,
                stage7_post_king_tempo_already_used=stage7_post_king_tempo_used,
                stage7_post_box_post_reply_context=white_moves > 0,
                early_stop_stable_suggestions=early_stop_stable_suggestions,
                forced_successor_skill=active_forced_successor,
                perf_profile=perf_profile,
                enable_diagnostic_caches=enable_diagnostic_caches,
            )
            _accumulate_engine_perf(engine_perf, move_details, prefix="engine")
            returned_plan_state = move_details.get("stage7_plan_capsule_state")
            if isinstance(returned_plan_state, dict) and returned_plan_state:
                stage7_plan_capsule_state = dict(returned_plan_state)
            stage7_plan_capsule_state = _advance_stage7_plan_capsule_state_after_decision(
                stage7_plan_capsule_state,
                move_details,
                current_ply=ply,
            ) or stage7_plan_capsule_state
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
                    "stagnation_context": stagnation_context,
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
                    "stagnation_context": stagnation_context,
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
                    "stagnation_context": stagnation_context,
                    "engine": move_details,
                })
                return finish("illegal_move", ply)
            b.push(move)
            selected_suggestion = _selected_engine_suggestion(move_details)
            if (
                selected_suggestion
                and _skill_id_for_suggestion(selected_suggestion) == "krk.stage7_king_tempo"
            ):
                stage7_king_tempo_used = True
            if (
                selected_suggestion
                and _skill_id_for_suggestion(selected_suggestion) == "krk.stage7_drive_repair"
                and white_moves > 0
            ):
                stage7_drive_repair_used = True
            if (
                selected_suggestion
                and _skill_id_for_suggestion(selected_suggestion) == "krk.stage7_post_king_tempo"
            ):
                stage7_post_king_tempo_used = True
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
                "stagnation_context": stagnation_context,
                "engine": move_details,
            })
            white_moves += 1
        else:
            before_fen = b.fen()
            reply = choose_black_reply(
                rng,
                b,
                label,
                black_policy,
                perf_profile=perf_profile,
            )
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

    if b.is_checkmate():
        return finish("mate", max_plies)
    if b.is_stalemate() or b.is_insufficient_material():
        return finish("draw", max_plies)
    return finish("max_plies", max_plies)


def _move_checkmates(board: chess.Board, move: chess.Move) -> bool:
    b = board.copy(stack=False)
    b.push(move)
    return b.is_checkmate()


def _mate_in_one_available(board: chess.Board) -> bool:
    if board.turn != chess.WHITE:
        return False
    return any(_move_checkmates(board, move) for move in board.legal_moves)


def _compact_playout_trace(trace: list[dict]) -> list[dict]:
    compact: list[dict] = []
    for event in trace:
        if not isinstance(event, dict):
            continue
        item = {
            "ply": event.get("ply"),
            "turn": event.get("turn"),
            "fen": event.get("fen"),
            "move": event.get("move"),
            "resulting_fen": event.get("resulting_fen"),
            "is_checkmate": bool(event.get("is_checkmate", False)),
            "is_stalemate": bool(event.get("is_stalemate", False)),
        }
        if isinstance(event.get("stagnation_context"), dict):
            ctx = event["stagnation_context"]
            item["stagnation_context"] = {
                "stagnation_loop": bool(ctx.get("stagnation_loop", False)),
                "rook_oscillation_loop": bool(ctx.get("rook_oscillation_loop", False)),
                "repeated_abstract_state_count": int(ctx.get("repeated_abstract_state_count", 0) or 0),
                "no_progress_plies": int(ctx.get("no_progress_plies", 0) or 0),
                "legal_loop_breaking_moves": list(ctx.get("legal_loop_breaking_moves", []) or []),
            }
        engine = event.get("engine") if isinstance(event.get("engine"), dict) else None
        if engine:
            suggestions = list(engine.get("suggestions", []) or [])
            selected_move = engine.get("move")
            selected = next(
                (
                    suggestion
                    for suggestion in suggestions
                    if suggestion.get("move") == selected_move
                ),
                suggestions[0] if suggestions else {},
            )
            item.update({
                "selected_skill": _skill_id_for_suggestion(selected) if selected else None,
                "confidence": engine.get("confidence"),
                "ticks": engine.get("ticks"),
                "early_stopped": bool(engine.get("early_stopped", False)),
                "top_suggestions": [
                    {
                        "move": suggestion.get("move"),
                        "skill_id": _skill_id_for_suggestion(suggestion),
                        "score": suggestion.get("score"),
                    }
                    for suggestion in suggestions[:5]
                ],
            })
            meta = selected.get("meta") if isinstance(selected, dict) and isinstance(selected.get("meta"), dict) else {}
            if meta.get("visible_stagnation_breaker_license"):
                item["visible_stagnation_breaker_license"] = meta.get(
                    "visible_stagnation_breaker_license"
                )
                item["visible_stagnation_breaker_bonus"] = meta.get(
                    "visible_stagnation_breaker_bonus"
                )
            if meta.get("visible_stagnation_breaker_king_support_license"):
                item["visible_stagnation_breaker_king_support_license"] = meta.get(
                    "visible_stagnation_breaker_king_support_license"
                )
                item["visible_stagnation_breaker_king_support_bonus"] = meta.get(
                    "visible_stagnation_breaker_king_support_bonus"
                )
            if meta.get("visible_post_break_continuation_license"):
                item["visible_post_break_continuation_license"] = meta.get(
                    "visible_post_break_continuation_license"
                )
                item["visible_post_break_continuation_bonus"] = meta.get(
                    "visible_post_break_continuation_bonus"
                )
        compact.append(item)
    return compact


def _fen_state_key(fen: str) -> str | None:
    try:
        board = chess.Board(fen)
    except Exception:
        return None
    return f"{board.board_fen()} {'w' if board.turn == chess.WHITE else 'b'}"


def _krk_squares(board: chess.Board) -> tuple[int | None, int | None, int | None]:
    wk_sq = next(iter(board.pieces(chess.KING, chess.WHITE)), None)
    bk_sq = next(iter(board.pieces(chess.KING, chess.BLACK)), None)
    wr_sq = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    return wk_sq, bk_sq, wr_sq


def _krk_box_area_and_edge(board: chess.Board) -> tuple[int | None, int | None]:
    wk_sq, bk_sq, wr_sq = _krk_squares(board)
    if wk_sq is None or bk_sq is None or wr_sq is None:
        return None, None
    bk_file, bk_rank = chess.square_file(bk_sq), chess.square_rank(bk_sq)
    wr_file, wr_rank = chess.square_file(wr_sq), chess.square_rank(wr_sq)
    edge_distance = min(bk_file, 7 - bk_file, bk_rank, 7 - bk_rank)
    box_width = max(1, wr_file if bk_file < wr_file else 7 - wr_file)
    box_height = max(1, wr_rank if bk_rank < wr_rank else 7 - wr_rank)
    return int(box_width * box_height), int(edge_distance)


def _krk_abstract_state_signature(board: chess.Board) -> str | None:
    wk_sq, bk_sq, wr_sq = _krk_squares(board)
    if wk_sq is None or bk_sq is None or wr_sq is None:
        return None
    wk_file, wk_rank = chess.square_file(wk_sq), chess.square_rank(wk_sq)
    bk_file, bk_rank = chess.square_file(bk_sq), chess.square_rank(bk_sq)
    wr_file, wr_rank = chess.square_file(wr_sq), chess.square_rank(wr_sq)
    box_area, edge_distance = _krk_box_area_and_edge(board)
    if wr_file == bk_file:
        cut_axis = "file"
    elif wr_rank == bk_rank:
        cut_axis = "rank"
    else:
        cut_axis = "off"
    rook_relation = (
        "same_file" if wr_file == bk_file
        else "same_rank" if wr_rank == bk_rank
        else f"df{_sign(wr_file - bk_file)}_dr{_sign(wr_rank - bk_rank)}"
    )
    return "|".join([
        f"wk={chess.square_name(wk_sq)}",
        f"bk={chess.square_name(bk_sq)}",
        f"wr_rel={rook_relation}",
        f"wr_edge={int(wr_file in (0, 7) or wr_rank in (0, 7))}",
        f"box={box_area}",
        f"edge={edge_distance}",
        f"cut={cut_axis}",
        f"turn={'w' if board.turn == chess.WHITE else 'b'}",
    ])


def _sign(value: int) -> int:
    return -1 if value < 0 else 1 if value > 0 else 0


def _boards_from_trace(trace: list[dict], current_board: chess.Board | None = None) -> list[chess.Board]:
    boards: list[chess.Board] = []
    seen: set[str] = set()
    for event in trace:
        if not isinstance(event, dict):
            continue
        for key in ("fen", "resulting_fen"):
            fen = event.get(key)
            if not isinstance(fen, str) or fen in seen:
                continue
            try:
                board = chess.Board(fen)
            except Exception:
                continue
            boards.append(board)
            seen.add(fen)
    if current_board is not None:
        fen = current_board.fen()
        if fen not in seen:
            boards.append(current_board.copy(stack=False))
    return boards


def _rook_safe_after_move(board: chess.Board, move: chess.Move) -> bool:
    b = board.copy(stack=False)
    b.push(move)
    wr_sq = next(iter(b.pieces(chess.ROOK, chess.WHITE)), None)
    bk_sq = next(iter(b.pieces(chess.KING, chess.BLACK)), None)
    wk_sq = next(iter(b.pieces(chess.KING, chess.WHITE)), None)
    if wr_sq is None or bk_sq is None or wk_sq is None:
        return False
    if chess.square_distance(wr_sq, bk_sq) > 1:
        return True
    reply_board = b.copy(stack=False)
    reply_board.turn = chess.BLACK
    capture = chess.Move(bk_sq, wr_sq)
    return capture not in reply_board.legal_moves or chess.square_distance(wk_sq, wr_sq) <= 1


def _loop_breaking_move_audit(
    board: chess.Board,
    move: chess.Move,
    *,
    oscillation_squares: set[str],
    last_rook_move: str | None = None,
) -> dict:
    if move not in board.legal_moves:
        return {"move": move.uci(), "legal": False, "loop_breaking": False}
    current_box, current_edge = _krk_box_area_and_edge(board)
    b = board.copy(stack=False)
    b.push(move)
    post_box, post_edge = _krk_box_area_and_edge(b)
    is_rook_move = bool(board.piece_at(move.from_square) == chess.Piece(chess.ROOK, chess.WHITE))
    to_square = chess.square_name(move.to_square)
    escapes_oscillation_pair = not is_rook_move or to_square not in oscillation_squares
    is_immediate_rook_reverse = bool(
        is_rook_move
        and last_rook_move
        and _reverse_uci(last_rook_move, move.uci())
    )
    no_draw = not (b.is_stalemate() or b.is_insufficient_material())
    rook_safe = _rook_safe_after_move(board, move)
    preserves_box = (
        current_box is not None
        and post_box is not None
        and post_box <= current_box
    )
    improves_box = (
        current_box is not None
        and post_box is not None
        and post_box < current_box
    )
    preserves_edge = (
        current_edge is not None
        and post_edge is not None
        and post_edge <= current_edge
    )
    creates_check = board.gives_check(move)
    loop_breaking = bool(
        escapes_oscillation_pair
        and not is_immediate_rook_reverse
        and no_draw
        and rook_safe
        and (preserves_box or preserves_edge or creates_check or b.is_checkmate())
    )
    terms = []
    if is_rook_move:
        terms.append("candidate_is_rook_move")
        if chess.square_distance(move.from_square, move.to_square) >= 2:
            terms.append("candidate_is_rook_transfer")
    else:
        terms.append("candidate_is_king_move")
    if escapes_oscillation_pair:
        terms.append("escapes_rook_oscillation_pair")
    if not is_immediate_rook_reverse:
        terms.append("not_immediate_rook_reverse")
    if rook_safe:
        terms.append("rook_safe_after_move")
    if no_draw:
        terms.append("no_draw_after_move")
    if preserves_box:
        terms.append("box_area_not_increased_after_move")
    if improves_box:
        terms.append("box_area_decreases_after_move")
    if preserves_edge:
        terms.append("enemy_edge_distance_not_increased_after_move")
    if creates_check:
        terms.append("checking_line_created")
    return {
        "move": move.uci(),
        "legal": True,
        "loop_breaking": loop_breaking,
        "source_terms": sorted(set(terms)),
        "current_box_area": current_box,
        "post_box_area": post_box,
        "current_enemy_edge_distance": current_edge,
        "post_enemy_edge_distance": post_edge,
    }


def _reverse_uci(move_a: str, move_b: str) -> bool:
    if len(move_a) < 4 or len(move_b) < 4:
        return False
    return move_a[:2] == move_b[2:4] and move_a[2:4] == move_b[:2]


def _playout_stagnation_summary(
    trace: list[dict],
    *,
    current_board: chess.Board | None = None,
) -> dict:
    state_counts: dict[str, int] = {}
    abstract_counts: dict[str, int] = {}
    white_moves: list[str] = []
    reverse_pairs: dict[str, int] = {}
    boards = _boards_from_trace(trace, current_board)
    abstract_history: list[str] = []
    rook_history: list[str] = []
    wk_history: list[str] = []
    bk_history: list[str] = []
    box_history: list[int | None] = []
    edge_history: list[int | None] = []
    mate_one_history: list[bool] = []
    safe_check_history: list[bool] = []
    for board in boards:
        abstract = _krk_abstract_state_signature(board)
        if abstract:
            abstract_history.append(abstract)
            abstract_counts[abstract] = abstract_counts.get(abstract, 0) + 1
        wk_sq, bk_sq, wr_sq = _krk_squares(board)
        rook_history.append(chess.square_name(wr_sq) if wr_sq is not None else "missing")
        wk_history.append(chess.square_name(wk_sq) if wk_sq is not None else "missing")
        bk_history.append(chess.square_name(bk_sq) if bk_sq is not None else "missing")
        box_area, edge_distance = _krk_box_area_and_edge(board)
        box_history.append(box_area)
        edge_history.append(edge_distance)
        mate_one_history.append(_mate_in_one_available(board))
        safe_check_history.append(_safe_check_available_local(board))
    for event in trace:
        if not isinstance(event, dict):
            continue
        for key in ("fen", "resulting_fen"):
            fen = event.get(key)
            if isinstance(fen, str):
                state_key = _fen_state_key(fen)
                if state_key:
                    state_counts[state_key] = state_counts.get(state_key, 0) + 1
        if event.get("turn") == "white" and isinstance(event.get("move"), str):
            white_moves.append(str(event["move"]))
    for previous, current in zip(white_moves, white_moves[1:]):
        if _reverse_uci(previous, current):
            pair = " / ".join(sorted([previous, current]))
            reverse_pairs[pair] = reverse_pairs.get(pair, 0) + 1
    oscillation_squares: set[str] = set()
    for pair in reverse_pairs:
        for move in pair.split(" / "):
            oscillation_squares.add(move[:2])
            oscillation_squares.add(move[2:4])
    repeated_states = {
        state: count
        for state, count in state_counts.items()
        if count >= 2
    }
    repeated_abstract = {
        state: count
        for state, count in abstract_counts.items()
        if count >= 2
    }
    no_box_progress = _no_recent_decrease(box_history)
    no_edge_progress = _no_recent_decrease(edge_history)
    no_mate_progress = not any(mate_one_history[-8:])
    no_progress_plies = _recent_no_progress_plies(
        box_history=box_history,
        edge_history=edge_history,
        mate_one_history=mate_one_history,
    )
    loop_breaking_audits = []
    last_rook_move = white_moves[-1] if white_moves else None
    if current_board is not None and current_board.turn == chess.WHITE:
        loop_breaking_audits = [
            _loop_breaking_move_audit(
                current_board,
                move,
                oscillation_squares=oscillation_squares,
                last_rook_move=last_rook_move,
            )
            for move in current_board.legal_moves
        ]
    legal_loop_breaking_moves = [
        item["move"] for item in loop_breaking_audits if item.get("loop_breaking")
    ]
    top_repeated = sorted(
        repeated_states.items(),
        key=lambda item: (-item[1], item[0]),
    )[:5]
    top_reverse_pairs = sorted(
        reverse_pairs.items(),
        key=lambda item: (-item[1], item[0]),
    )[:5]
    rook_reversal_count = sum(reverse_pairs.values())
    rook_oscillation_loop = rook_reversal_count >= 2
    stagnation_loop = bool(
        rook_oscillation_loop
        and no_box_progress
        and no_edge_progress
        and no_mate_progress
        and repeated_abstract
    )
    return {
        "max_state_repetition": max(state_counts.values(), default=0),
        "repeated_state_count": len(repeated_states),
        "repeated_state_examples": [
            {"state": state, "count": count}
            for state, count in top_repeated
        ],
        "rook_oscillation_detected": bool(top_reverse_pairs),
        "rook_oscillation_loop": rook_oscillation_loop,
        "rook_reversal_count": int(rook_reversal_count),
        "rook_oscillation_pairs": [
            {"moves": pair, "count": count}
            for pair, count in top_reverse_pairs
        ],
        "abstract_state_signature": abstract_history[-1] if abstract_history else None,
        "abstract_state_history": abstract_history,
        "repeated_abstract_state_count": len(repeated_abstract),
        "repeated_abstract_state_examples": [
            {"state": state, "count": count}
            for state, count in sorted(
                repeated_abstract.items(),
                key=lambda item: (-item[1], item[0]),
            )[:5]
        ],
        "rook_square_history": rook_history,
        "king_square_history": {
            "white": wk_history,
            "black": bk_history,
        },
        "box_area_history": box_history,
        "enemy_king_edge_distance_history": edge_history,
        "mate_in_one_history": mate_one_history,
        "safe_check_available_history": safe_check_history,
        "no_box_progress_recently": bool(no_box_progress),
        "no_edge_progress_recently": bool(no_edge_progress),
        "no_mate_progress_recently": bool(no_mate_progress),
        "no_progress_plies": int(no_progress_plies),
        "stagnation_loop": stagnation_loop,
        "safe_loop_breaking_move_available": bool(legal_loop_breaking_moves),
        "loop_breaking_rook_transfer_available": any(
            item.get("loop_breaking")
            and "candidate_is_rook_transfer" in item.get("source_terms", [])
            for item in loop_breaking_audits
        ),
        "loop_breaking_check_or_cut_available": any(
            item.get("loop_breaking")
            and (
                "checking_line_created" in item.get("source_terms", [])
                or "box_area_decreases_after_move" in item.get("source_terms", [])
            )
            for item in loop_breaking_audits
        ),
        "legal_loop_breaking_moves": legal_loop_breaking_moves,
        "legal_loop_breaking_move_audits": [
            item for item in loop_breaking_audits if item.get("loop_breaking")
        ],
        "legal_loop_breaking_moves_that_convert": [],
    }


def _with_post_break_continuation_context(
    stagnation_summary: dict,
    *,
    all_events: list[dict],
    current_board: chess.Board,
) -> dict:
    """Add non-causal visible context for follow-up after a loop break."""
    summary = dict(stagnation_summary)
    if current_board.turn != chess.WHITE:
        return summary
    breaker_event = _last_stagnation_breaker_event(all_events)
    if not breaker_event:
        return summary
    try:
        pre_break_board = chess.Board(str(breaker_event.get("fen")))
        break_board = chess.Board(str(breaker_event.get("resulting_fen")))
    except Exception:
        return summary

    pre_box, pre_edge = _krk_box_area_and_edge(pre_break_board)
    break_box, break_edge = _krk_box_area_and_edge(break_board)
    current_box, current_edge = _krk_box_area_and_edge(current_board)
    confinement_preserved = (
        pre_box is not None and current_box is not None and current_box <= pre_box
    )
    edge_control_preserved = (
        pre_edge is not None and current_edge is not None and current_edge <= pre_edge
    )
    followup_audits = [
        _post_break_followup_move_audit(current_board, move)
        for move in current_board.legal_moves
    ]
    legal_followups = [
        item["move"] for item in followup_audits if item.get("post_break_followup")
    ]
    context = {
        "breaker_ply": breaker_event.get("ply"),
        "breaker_move": breaker_event.get("move"),
        "breaker_fen": breaker_event.get("fen"),
        "breaker_resulting_fen": breaker_event.get("resulting_fen"),
        "pre_break_box_area": pre_box,
        "break_box_area": break_box,
        "current_box_area": current_box,
        "pre_break_enemy_edge_distance": pre_edge,
        "break_enemy_edge_distance": break_edge,
        "current_enemy_edge_distance": current_edge,
        "confinement_preserved_after_break": confinement_preserved,
        "enemy_king_edge_control_preserved": edge_control_preserved,
        "legal_post_break_followup_moves": legal_followups,
        "legal_post_break_followup_move_audits": [
            item for item in followup_audits if item.get("post_break_followup")
        ],
    }
    summary.update({
        "rook_oscillation_loop_recently_broken": True,
        "confinement_preserved_after_break": confinement_preserved,
        "enemy_king_edge_control_preserved": edge_control_preserved,
        "post_stagnation_break_continuation_needed": not _mate_in_one_available(current_board),
        "safe_followup_available": bool(legal_followups),
        "post_break_continuation_context": context,
    })
    return summary


def _last_stagnation_breaker_event(events: list[dict], *, window: int = 6) -> dict | None:
    for event in reversed(events[-window:]):
        if not isinstance(event, dict) or event.get("turn") != "white":
            continue
        if event.get("visible_stagnation_breaker_license"):
            return event
        engine = event.get("engine") if isinstance(event.get("engine"), dict) else {}
        selected = _selected_engine_suggestion(engine)
        meta = selected.get("meta") if isinstance(selected.get("meta"), dict) else {}
        if meta.get("visible_stagnation_breaker_license"):
            return event
    return None


def _selected_engine_suggestion(engine: dict) -> dict:
    suggestions = list(engine.get("suggestions", []) or [])
    selected_move = engine.get("move")
    return next(
        (item for item in suggestions if item.get("move") == selected_move),
        suggestions[0] if suggestions else {},
    )


def _post_break_followup_move_audit(board: chess.Board, move: chess.Move) -> dict:
    if move not in board.legal_moves:
        return {"move": move.uci(), "legal": False, "post_break_followup": False}
    current_box, current_edge = _krk_box_area_and_edge(board)
    b = board.copy(stack=False)
    b.push(move)
    post_box, post_edge = _krk_box_area_and_edge(b)
    no_draw = not (b.is_stalemate() or b.is_insufficient_material())
    rook_safe = _rook_safe_after_move(board, move)
    preserves_box = current_box is not None and post_box is not None and post_box <= current_box
    improves_box = current_box is not None and post_box is not None and post_box < current_box
    preserves_edge = current_edge is not None and post_edge is not None and post_edge <= current_edge
    is_king_move = bool(board.piece_at(move.from_square) == chess.Piece(chess.KING, chess.WHITE))
    is_rook_move = bool(board.piece_at(move.from_square) == chess.Piece(chess.ROOK, chess.WHITE))
    support_improves = _king_support_improves_after_move(board, move) if is_king_move else False
    creates_check = board.gives_check(move)
    terms = []
    if is_king_move:
        terms.append("candidate_is_king_move")
    if is_rook_move:
        terms.append("candidate_is_rook_move")
        if chess.square_distance(move.from_square, move.to_square) >= 2:
            terms.append("candidate_is_rook_transfer")
    if rook_safe:
        terms.append("rook_safe_after_move")
    if no_draw:
        terms.append("no_draw_after_move")
    if preserves_box:
        terms.append("box_area_not_increased_after_move")
    if improves_box:
        terms.append("box_area_decreases_after_move")
    if preserves_edge:
        terms.append("enemy_edge_distance_not_increased_after_move")
    if support_improves:
        terms.append("white_king_support_improves_after_move")
    if creates_check:
        terms.append("checking_line_created")
    post_break_followup = bool(
        rook_safe
        and no_draw
        and preserves_box
        and is_king_move
        and (support_improves or preserves_edge)
    )
    return {
        "move": move.uci(),
        "legal": True,
        "post_break_followup": post_break_followup,
        "source_terms": sorted(set(terms)),
        "current_box_area": current_box,
        "post_box_area": post_box,
        "current_enemy_edge_distance": current_edge,
        "post_enemy_edge_distance": post_edge,
    }


def _king_support_improves_after_move(board: chess.Board, move: chess.Move) -> bool:
    if board.piece_at(move.from_square) != chess.Piece(chess.KING, chess.WHITE):
        return False
    bk_sq = next(iter(board.pieces(chess.KING, chess.BLACK)), None)
    wr_sq = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    if bk_sq is None or wr_sq is None:
        return False
    before_enemy = chess.square_distance(move.from_square, bk_sq)
    before_rook = chess.square_distance(move.from_square, wr_sq)
    after_enemy = chess.square_distance(move.to_square, bk_sq)
    after_rook = chess.square_distance(move.to_square, wr_sq)
    return after_enemy < before_enemy or after_rook < before_rook


def _safe_check_available_local(board: chess.Board) -> bool:
    if board.turn != chess.WHITE:
        return False
    for move in board.legal_moves:
        if not board.gives_check(move):
            continue
        if _rook_safe_after_move(board, move):
            return True
    return False


def _no_recent_decrease(values: list[int | None], *, window: int = 8) -> bool:
    clean = [value for value in values[-window:] if value is not None]
    if len(clean) < 3:
        return False
    return min(clean[1:]) >= clean[0]


def _recent_no_progress_plies(
    *,
    box_history: list[int | None],
    edge_history: list[int | None],
    mate_one_history: list[bool],
) -> int:
    limit = min(len(box_history), len(edge_history), len(mate_one_history))
    if limit < 2:
        return 0
    count = 0
    best_box = box_history[max(0, limit - 10)]
    best_edge = edge_history[max(0, limit - 10)]
    for idx in range(max(1, limit - 9), limit):
        box = box_history[idx]
        edge = edge_history[idx]
        mate = mate_one_history[idx]
        improved = False
        if box is not None and best_box is not None and box < best_box:
            improved = True
        if edge is not None and best_edge is not None and edge < best_edge:
            improved = True
        if mate:
            improved = True
        if improved:
            count = 0
        else:
            count += 1
        if box is not None and (best_box is None or box < best_box):
            best_box = box
        if edge is not None and (best_edge is None or edge < best_edge):
            best_edge = edge
    return count


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
    successor_contract_gate_enabled: bool,
    successor_role_license_enabled: bool,
    explicit_role_provider_support_enabled: bool = False,
    role_owned_score_normalization_enabled: bool = False,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    stagnation_breaker_king_support_bonus: float = 0.0,
    post_break_continuation_enabled: bool = False,
    post_break_continuation_bonus: float = 0.0,
    stage7_king_tempo_enabled: bool = False,
    stage7_king_tempo_score: float = 25.0,
    stage7_drive_repair_enabled: bool = False,
    stage7_drive_repair_score: float = 28.0,
    stage7_post_king_tempo_enabled: bool = False,
    stage7_post_king_tempo_score: float = 30.0,
    stage7_post_box_continuation_enabled: bool = False,
    stage7_post_box_continuation_score: float = 32.0,
    stage7_learned_post_box_continuation_enabled: bool = False,
    stage7_learned_post_box_continuation_bonus: float = 0.0,
    plan_capsule_sandbox_enabled: bool = False,
    stage7_plan_capsule_enabled: bool = False,
    stage7_plan_capsule_ttl: int = 3,
    stage7_plan_capsule_support_bonus: float = 0.0,
    stage7_plan_capsule_owned_arbitration_enabled: bool = False,
    candidate_move_layer_enabled: bool = False,
    stage7_king_support_fence_stabilizer_enabled: bool = False,
    candidate_move_role_support: float = 0.0,
    stage7_post_box_frozen_model_candidate_enabled: bool = False,
    stage7_post_box_frozen_model_candidate_support: float = 0.0,
    stage7_post_box_frozen_model: dict | None = None,
    early_stop_stable_suggestions: int = 0,
    step_output: Optional[Path] = None,
    step_context: Optional[dict] = None,
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
            successor_contract_gate_enabled=successor_contract_gate_enabled,
            successor_role_license_enabled=successor_role_license_enabled,
            explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
            role_owned_score_normalization_enabled=role_owned_score_normalization_enabled,
            successor_role_veto_penalty=successor_role_veto_penalty,
            successor_stage0_drift_penalty=successor_stage0_drift_penalty,
            successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
            successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
            successor_role_scoped_move_shape_require_worst_reply=(
                successor_role_scoped_move_shape_require_worst_reply
            ),
            stagnation_breaker_enabled=stagnation_breaker_enabled,
            stagnation_breaker_bonus=stagnation_breaker_bonus,
            stagnation_breaker_king_support_bonus=stagnation_breaker_king_support_bonus,
            post_break_continuation_enabled=post_break_continuation_enabled,
            post_break_continuation_bonus=post_break_continuation_bonus,
            stage7_king_tempo_enabled=stage7_king_tempo_enabled,
            stage7_king_tempo_score=stage7_king_tempo_score,
            stage7_drive_repair_enabled=stage7_drive_repair_enabled,
            stage7_drive_repair_score=stage7_drive_repair_score,
            stage7_post_king_tempo_enabled=stage7_post_king_tempo_enabled,
            stage7_post_king_tempo_score=stage7_post_king_tempo_score,
            early_stop_stable_suggestions=early_stop_stable_suggestions,
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
        if step_output is not None:
            _append_jsonl(
                step_output,
                {
                    **(step_context or {}),
                    "forced_successor": skill_id,
                    "counterfactual_result": results[skill_id],
                },
            )
    return results


def summarize_counterfactual_successor_sweeps(sweeps: list[dict]) -> dict:
    """Aggregate forced-successor audit records.

    This is diagnostic-only. It answers whether existing compiled successor
    skills could convert failed post-reply states if granted first ownership.
    """
    summary = {
        "total_sweeps": len(sweeps),
        "sweeps_with_any_mate": 0,
        "sweeps_without_any_mate": 0,
        "forced_successor_outcome_counts": {},
        "forced_successor_available_counts": {},
        "actual_to_forced_outcome_counts": {},
        "best_mating_successor_counts": {},
    }
    for sweep in sweeps:
        actual = str(sweep.get("actual_selected_successor") or "unknown")
        results = sweep.get("counterfactual_results") or {}
        if not isinstance(results, dict):
            continue
        mating_successors: list[str] = []
        for skill_id, result in results.items():
            if not isinstance(result, dict):
                continue
            forced = str(skill_id)
            outcome = str(result.get("result") or "unknown")
            available = bool(result.get("forced_successor_available"))
            outcome_key = f"{forced}:{outcome}"
            availability_key = f"{forced}:{'available' if available else 'unavailable'}"
            actual_key = f"{actual}->{forced}:{outcome}"
            summary["forced_successor_outcome_counts"][outcome_key] = (
                summary["forced_successor_outcome_counts"].get(outcome_key, 0) + 1
            )
            summary["forced_successor_available_counts"][availability_key] = (
                summary["forced_successor_available_counts"].get(availability_key, 0) + 1
            )
            summary["actual_to_forced_outcome_counts"][actual_key] = (
                summary["actual_to_forced_outcome_counts"].get(actual_key, 0) + 1
            )
            if outcome == "mate":
                mating_successors.append(forced)
        if mating_successors:
            summary["sweeps_with_any_mate"] += 1
            for forced in sorted(mating_successors):
                summary["best_mating_successor_counts"][forced] = (
                    summary["best_mating_successor_counts"].get(forced, 0) + 1
                )
        else:
            summary["sweeps_without_any_mate"] += 1
    return summary


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
    target_failure_trace_state_signatures: tuple[str, ...] = (),
    max_target_failure_traces: int = 0,
    target_failure_traces_output: Optional[Path] = None,
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
    successor_contract_gate_enabled: bool = False,
    successor_role_license_enabled: bool = False,
    explicit_role_provider_support_enabled: bool = False,
    role_owned_score_normalization_enabled: bool = False,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    stagnation_breaker_king_support_bonus: float = 0.0,
    post_break_continuation_enabled: bool = False,
    post_break_continuation_bonus: float = 0.0,
    stage7_king_tempo_enabled: bool = False,
    stage7_king_tempo_score: float = 25.0,
    stage7_drive_repair_enabled: bool = False,
    stage7_drive_repair_score: float = 28.0,
    stage7_post_king_tempo_enabled: bool = False,
    stage7_post_king_tempo_score: float = 30.0,
    stage7_post_box_continuation_enabled: bool = False,
    stage7_post_box_continuation_score: float = 32.0,
    stage7_learned_post_box_continuation_enabled: bool = False,
    stage7_learned_post_box_continuation_bonus: float = 0.0,
    plan_capsule_sandbox_enabled: bool = False,
    stage7_plan_capsule_enabled: bool = False,
    stage7_plan_capsule_ttl: int = 3,
    stage7_plan_capsule_support_bonus: float = 0.0,
    stage7_plan_capsule_owned_arbitration_enabled: bool = False,
    candidate_move_layer_enabled: bool = False,
    stage7_king_support_fence_stabilizer_enabled: bool = False,
    candidate_move_role_support: float = 0.0,
    stage7_post_box_frozen_model_candidate_enabled: bool = False,
    stage7_post_box_frozen_model_candidate_support: float = 0.0,
    stage7_post_box_frozen_model: dict | None = None,
    early_stop_stable_suggestions: int = 0,
    lock_stage_filter_through_playout: bool = False,
    counterfactual_successors: tuple[str, ...] = (),
    max_counterfactual_sweeps: int = 0,
    counterfactual_sweeps_output: Optional[Path] = None,
    counterfactual_steps_output: Optional[Path] = None,
    profile_performance: bool = False,
    enable_diagnostic_caches: bool = False,
    composition_profile: str | None = None,
    sample_indices: tuple[int, ...] | None = None,
    deterministic_sample_seeds: bool = False,
    verbose: bool = True,
) -> dict:
    profile_meta = _composition_profile_metadata(composition_profile)
    if profile_meta is not None:
        settings = dict(profile_meta.get("settings", {}) or {})
        successor_affordance_layer_enabled = bool(
            settings.get("successor_affordance_layer_enabled", successor_affordance_layer_enabled)
        )
        successor_role_license_enabled = bool(
            settings.get("successor_role_license_enabled", successor_role_license_enabled)
        )
        successor_role_scoped_move_shape_enabled = bool(
            settings.get(
                "successor_role_scoped_move_shape_enabled",
                successor_role_scoped_move_shape_enabled,
            )
        )
        successor_role_scoped_move_shape_bonus = float(
            settings.get(
                "successor_role_scoped_move_shape_bonus",
                successor_role_scoped_move_shape_bonus,
            )
        )
        stagnation_breaker_enabled = bool(
            settings.get("stagnation_breaker_enabled", stagnation_breaker_enabled)
        )
        stagnation_breaker_bonus = float(
            settings.get("stagnation_breaker_bonus", stagnation_breaker_bonus)
        )
        post_break_continuation_enabled = bool(
            settings.get("post_break_continuation_enabled", post_break_continuation_enabled)
        )
        post_break_continuation_bonus = float(
            settings.get("post_break_continuation_bonus", post_break_continuation_bonus)
        )
        successor_stage0_drift_penalty = float(
            settings.get("successor_stage0_drift_penalty", successor_stage0_drift_penalty)
        )
    perf_profile = _new_perf_profile(
        profile_performance,
        diagnostic_caches_enabled=enable_diagnostic_caches,
    )
    total_start = time.perf_counter() if profile_performance else None
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
        "target_failure_traces": [],
        "handoff_packets": [],
        "shadow_candidates": [],
        "counterfactual_successor_sweeps": [],
        "one_ply_status_counts": {},
        "conversion_status_counts": {},
        "semantic_alignment_status_counts": {},
        "conversion_by_semantic_alignment_status": {},
        "semantic_alignment_confusion_counts": {},
        "semantic_alignment_snapshots": {},
        "one_ply_engine_decision_count": 0,
        "one_ply_engine_ticks_total": 0,
        "one_ply_engine_ticks_max": 0,
        "one_ply_engine_early_stop_count": 0,
        "playout_engine_decision_count": 0,
        "playout_engine_ticks_total": 0,
        "playout_engine_ticks_max": 0,
        "playout_engine_early_stop_count": 0,
        "adapter_fire_count": 0,
        "adapter_supported_provider_by_outcome": {},
        "adapter_supported_move_by_outcome": {},
        "candidate_move_frame_count": 0,
        "candidate_move_role_match_count": 0,
        "candidate_move_role_supported_suggestion_count": 0,
        "candidate_move_role_supported_role_by_outcome": {},
        "candidate_move_role_supported_move_by_outcome": {},
        "candidate_move_role_selected_supported_count": 0,
        "candidate_move_role_selected_by_outcome": {},
        "stage7_post_box_frozen_model_candidate_supported_suggestion_count": 0,
        "stage7_post_box_frozen_model_candidate_supported_move_by_outcome": {},
        "stage7_post_box_frozen_model_candidate_selected_supported_count": 0,
        "stage7_post_box_frozen_model_candidate_selected_by_outcome": {},
        "plan_capsule_marker_count": 0,
        "plan_capsule_marker_by_outcome": {},
        "plan_capsule_entry_count": 0,
        "plan_capsule_exit_count": 0,
        "plan_capsule_abort_count": 0,
        "plan_capsule_expired_count": 0,
        "plan_capsule_progress_confirmed_count": 0,
        "plan_capsule_status_by_outcome": {},
        "plan_capsule_active_decision_count": 0,
        "plan_capsule_supported_suggestion_count": 0,
        "plan_capsule_selected_supported_count": 0,
        "plan_capsule_active_without_support_count": 0,
        "plan_capsule_owned_arbitration_selected_count": 0,
        "plan_capsule_supported_provider_by_outcome": {},
        "plan_capsule_supported_move_by_outcome": {},
        "plan_capsule_selected_supported_by_outcome": {},
        "plan_capsule_owned_arbitration_provider_by_outcome": {},
        "role_owned_score_normalization_selected_count": 0,
        "role_owned_score_normalization_provider_by_outcome": {},
        "one_ply_status": "not_checked",
        "conversion_status": "not_checked",
    }
    if profile_meta is not None:
        stats["composition_profile"] = profile_meta

    indices = tuple(range(samples)) if sample_indices is None else tuple(sample_indices)
    samples = len(indices)

    for local_i, sample_index in enumerate(indices):
        _profile_add_count(perf_profile, "samples")
        if deterministic_sample_seeds:
            sample_seed = int(seed) * 1_000_000 + int(sample_index)
            sample_rng = random.Random(sample_seed)
            random.seed(sample_seed)
        else:
            sample_rng = rng
        board = select_eval_position(sample_rng, label, position_mode, source_names)
        move_details = choose_move_details(
            graph,
            engine,
            board,
            max_ticks=max_ticks,
            stage_filter=stage_filter,
            suggestion_limit=suggestion_limit,
            successor_affordance_layer_enabled=successor_affordance_layer_enabled,
            successor_contract_gate_enabled=successor_contract_gate_enabled,
            successor_role_license_enabled=successor_role_license_enabled,
            explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
            role_owned_score_normalization_enabled=role_owned_score_normalization_enabled,
            successor_role_veto_penalty=successor_role_veto_penalty,
            successor_stage0_drift_penalty=successor_stage0_drift_penalty,
            successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
            successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
            successor_role_scoped_move_shape_require_worst_reply=(
                successor_role_scoped_move_shape_require_worst_reply
            ),
            stage7_king_tempo_enabled=stage7_king_tempo_enabled,
            stage7_king_tempo_score=stage7_king_tempo_score,
            stage7_drive_repair_enabled=stage7_drive_repair_enabled,
            stage7_drive_repair_score=stage7_drive_repair_score,
            stage7_post_king_tempo_enabled=stage7_post_king_tempo_enabled,
            stage7_post_king_tempo_score=stage7_post_king_tempo_score,
            stage7_post_box_continuation_enabled=stage7_post_box_continuation_enabled,
            stage7_post_box_continuation_score=stage7_post_box_continuation_score,
            stage7_learned_post_box_continuation_enabled=stage7_learned_post_box_continuation_enabled,
            stage7_learned_post_box_continuation_bonus=stage7_learned_post_box_continuation_bonus,
            stage7_post_box_frozen_model_candidate_enabled=(
                stage7_post_box_frozen_model_candidate_enabled
            ),
            stage7_post_box_frozen_model_candidate_support=(
                stage7_post_box_frozen_model_candidate_support
            ),
            stage7_post_box_frozen_model=stage7_post_box_frozen_model,
            plan_capsule_sandbox_enabled=plan_capsule_sandbox_enabled,
            stage7_plan_capsule_enabled=stage7_plan_capsule_enabled,
            stage7_plan_capsule_ttl=stage7_plan_capsule_ttl,
            stage7_plan_capsule_support_bonus=stage7_plan_capsule_support_bonus,
            stage7_plan_capsule_owned_arbitration_enabled=(
                stage7_plan_capsule_owned_arbitration_enabled
            ),
            candidate_move_layer_enabled=candidate_move_layer_enabled,
            stage7_king_support_fence_stabilizer_enabled=(
                stage7_king_support_fence_stabilizer_enabled
            ),
            candidate_move_role_support=candidate_move_role_support,
            active_landmark_label=label,
            early_stop_stable_suggestions=early_stop_stable_suggestions,
            perf_profile=perf_profile,
            enable_diagnostic_caches=enable_diagnostic_caches,
        )
        stats["candidate_move_frame_count"] = (
            int(stats.get("candidate_move_frame_count", 0) or 0)
            + len(move_details.get("candidate_move_frames", []) or [])
        )
        match_summary = dict(move_details.get("candidate_move_role_matches", {}) or {})
        stats["candidate_move_role_match_count"] = (
            int(stats.get("candidate_move_role_match_count", 0) or 0)
            + int(match_summary.get("match_count", 0) or 0)
        )
        _accumulate_engine_perf(stats, move_details, prefix="one_ply_engine")
        move_uci = move_details.get("move")
        oracle_rewards = oracle_move_rewards(
            board,
            label,
            lookahead_black,
            perf_profile=perf_profile,
        )
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

        reward = _profiled_worst_reply_reward(
            board,
            move,
            label,
            use_black_reply=lookahead_black,
            perf_profile=perf_profile,
        )
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
                "sample": sample_index,
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

        if verbose and (local_i + 1) % 10 == 0:
            print(
                f"{local_i + 1:4d}/{samples}: improved={stats['improved']} optimal={stats['optimal']}",
                flush=True,
            )

        if playout_max_plies > 0:
            target_trace_budget_open = (
                bool(target_failure_trace_state_signatures)
                and (
                    max_target_failure_traces <= 0
                    or len(stats["target_failure_traces"]) < max_target_failure_traces
                )
            )
            result = play_to_mate(
                graph,
                engine,
                board,
                sample_rng,
                label,
                stage_filter,
                playout_max_plies,
                black_policy,
                trace=(
                    len(stats["debug_playouts"]) < debug_playouts
                    or target_trace_budget_open
                ),
                max_ticks=playout_max_ticks if playout_max_ticks is not None else max_ticks,
                suggestion_limit=suggestion_limit,
                trace_max_plies=debug_trace_max_plies,
                successor_affordance_layer_enabled=successor_affordance_layer_enabled,
                successor_contract_gate_enabled=successor_contract_gate_enabled,
                successor_role_license_enabled=successor_role_license_enabled,
                explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
                role_owned_score_normalization_enabled=role_owned_score_normalization_enabled,
                successor_role_veto_penalty=successor_role_veto_penalty,
                successor_stage0_drift_penalty=successor_stage0_drift_penalty,
                successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
                successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
                successor_role_scoped_move_shape_require_worst_reply=(
                    successor_role_scoped_move_shape_require_worst_reply
                ),
                stagnation_breaker_enabled=stagnation_breaker_enabled,
                stagnation_breaker_bonus=stagnation_breaker_bonus,
                stagnation_breaker_king_support_bonus=stagnation_breaker_king_support_bonus,
                post_break_continuation_enabled=post_break_continuation_enabled,
                post_break_continuation_bonus=post_break_continuation_bonus,
                stage7_king_tempo_enabled=stage7_king_tempo_enabled,
                stage7_king_tempo_score=stage7_king_tempo_score,
                stage7_drive_repair_enabled=stage7_drive_repair_enabled,
                stage7_drive_repair_score=stage7_drive_repair_score,
                stage7_post_king_tempo_enabled=stage7_post_king_tempo_enabled,
                stage7_post_king_tempo_score=stage7_post_king_tempo_score,
                stage7_post_box_continuation_enabled=stage7_post_box_continuation_enabled,
                stage7_post_box_continuation_score=stage7_post_box_continuation_score,
                stage7_learned_post_box_continuation_enabled=stage7_learned_post_box_continuation_enabled,
                stage7_learned_post_box_continuation_bonus=stage7_learned_post_box_continuation_bonus,
                stage7_post_box_frozen_model_candidate_enabled=(
                    stage7_post_box_frozen_model_candidate_enabled
                ),
                stage7_post_box_frozen_model_candidate_support=(
                    stage7_post_box_frozen_model_candidate_support
                ),
                stage7_post_box_frozen_model=stage7_post_box_frozen_model,
                plan_capsule_sandbox_enabled=plan_capsule_sandbox_enabled,
                stage7_plan_capsule_enabled=stage7_plan_capsule_enabled,
                stage7_plan_capsule_ttl=stage7_plan_capsule_ttl,
                stage7_plan_capsule_support_bonus=stage7_plan_capsule_support_bonus,
                stage7_plan_capsule_owned_arbitration_enabled=(
                    stage7_plan_capsule_owned_arbitration_enabled
                ),
                candidate_move_layer_enabled=candidate_move_layer_enabled,
                stage7_king_support_fence_stabilizer_enabled=(
                    stage7_king_support_fence_stabilizer_enabled
                ),
                candidate_move_role_support=candidate_move_role_support,
                early_stop_stable_suggestions=early_stop_stable_suggestions,
                lock_stage_filter_through_playout=lock_stage_filter_through_playout,
                perf_profile=perf_profile,
                enable_diagnostic_caches=enable_diagnostic_caches,
            )
            key = result["result"]
            stats["playout_engine_decision_count"] += int(result.get("engine_decision_count", 0) or 0)
            stats["playout_engine_ticks_total"] += int(result.get("engine_ticks_total", 0) or 0)
            stats["playout_engine_ticks_max"] = max(
                int(stats.get("playout_engine_ticks_max", 0) or 0),
                int(result.get("engine_ticks_max", 0) or 0),
            )
            stats["playout_engine_early_stop_count"] += int(result.get("engine_early_stop_count", 0) or 0)
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
            post_reply_state_signature = (
                stable_record_id("state", chess.Board(post_reply_fen).board_fen(), chess.WHITE)
                if post_reply_fen
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
                    sample=sample_index,
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
                final_mate_in_one_available=bool(result.get("final_mate_in_one_available", False)),
                rook_oscillation_detected=bool(
                    (result.get("stagnation_summary") or {}).get("rook_oscillation_loop")
                ),
            )
            adapter_support = dict(
                successor_summary.get("visible_role_provider_support_adapter", {}) or {}
            )
            plan_capsule_markers = dict(successor_summary.get("plan_capsule_markers", {}) or {})
            if plan_capsule_markers:
                stats["plan_capsule_marker_count"] = (
                    int(stats.get("plan_capsule_marker_count", 0) or 0)
                    + len(plan_capsule_markers)
                )
                for capsule_id, marker in plan_capsule_markers.items():
                    marker_key = f"{capsule_id}:{key}"
                    stats["plan_capsule_marker_by_outcome"][marker_key] = (
                        stats["plan_capsule_marker_by_outcome"].get(marker_key, 0) + 1
                    )
            plan_state = dict(result.get("stage7_plan_capsule_state", {}) or {})
            plan_status = str(plan_state.get("plan_status") or "")
            if plan_status in {"active", "progress_confirmed", "exited", "aborted", "expired"}:
                stats["plan_capsule_entry_count"] = int(stats.get("plan_capsule_entry_count", 0) or 0) + 1
            if plan_status == "progress_confirmed" or plan_state.get("progress_terms_confirmed"):
                stats["plan_capsule_progress_confirmed_count"] = (
                    int(stats.get("plan_capsule_progress_confirmed_count", 0) or 0) + 1
                )
            if plan_status == "exited":
                stats["plan_capsule_exit_count"] = int(stats.get("plan_capsule_exit_count", 0) or 0) + 1
            if plan_status == "aborted":
                stats["plan_capsule_abort_count"] = int(stats.get("plan_capsule_abort_count", 0) or 0) + 1
            if plan_status == "expired":
                stats["plan_capsule_expired_count"] = int(stats.get("plan_capsule_expired_count", 0) or 0) + 1
            if plan_status:
                plan_key = f"{plan_status}:{key}"
                stats["plan_capsule_status_by_outcome"][plan_key] = (
                    stats["plan_capsule_status_by_outcome"].get(plan_key, 0) + 1
                )
            if successor_summary.get("plan_capsule_active"):
                stats["plan_capsule_active_decision_count"] = (
                    int(stats.get("plan_capsule_active_decision_count", 0) or 0) + 1
                )
            plan_supported_count = int(
                successor_summary.get("plan_capsule_supported_suggestion_count", 0) or 0
            )
            if plan_supported_count:
                stats["plan_capsule_supported_suggestion_count"] = (
                    int(stats.get("plan_capsule_supported_suggestion_count", 0) or 0)
                    + plan_supported_count
                )
                for provider, count in (
                    successor_summary.get("plan_capsule_supported_provider_counts", {}) or {}
                ).items():
                    provider_key = f"{provider}:{key}"
                    stats["plan_capsule_supported_provider_by_outcome"][provider_key] = (
                        stats["plan_capsule_supported_provider_by_outcome"].get(provider_key, 0)
                        + int(count or 0)
                    )
                for move_name, count in (
                    successor_summary.get("plan_capsule_supported_move_counts", {}) or {}
                ).items():
                    move_key = f"{move_name}:{key}"
                    stats["plan_capsule_supported_move_by_outcome"][move_key] = (
                        stats["plan_capsule_supported_move_by_outcome"].get(move_key, 0)
                        + int(count or 0)
                    )
            elif successor_summary.get("plan_capsule_active"):
                stats["plan_capsule_active_without_support_count"] = (
                    int(stats.get("plan_capsule_active_without_support_count", 0) or 0) + 1
                )
            if successor_summary.get("plan_capsule_selected_supported"):
                stats["plan_capsule_selected_supported_count"] = (
                    int(stats.get("plan_capsule_selected_supported_count", 0) or 0) + 1
                )
                selected_key = f"{successor_summary.get('selected_skill', 'unknown')}:{key}"
                stats["plan_capsule_selected_supported_by_outcome"][selected_key] = (
                    stats["plan_capsule_selected_supported_by_outcome"].get(selected_key, 0) + 1
                )
            plan_owned_arbitration = dict(
                successor_summary.get("visible_stage7_plan_capsule_owned_arbitration", {}) or {}
            )
            if plan_owned_arbitration.get("enabled"):
                stats["plan_capsule_owned_arbitration_selected_count"] = (
                    int(stats.get("plan_capsule_owned_arbitration_selected_count", 0) or 0) + 1
                )
                provider_key = f"{plan_owned_arbitration.get('selected_skill', 'unknown')}:{key}"
                stats["plan_capsule_owned_arbitration_provider_by_outcome"][provider_key] = (
                    stats["plan_capsule_owned_arbitration_provider_by_outcome"].get(
                        provider_key, 0
                    )
                    + 1
                )
            role_owned_support = dict(
                successor_summary.get("visible_role_owned_score_normalization", {}) or {}
            )
            if role_owned_support.get("enabled"):
                stats["role_owned_score_normalization_selected_count"] = (
                    int(stats.get("role_owned_score_normalization_selected_count", 0) or 0) + 1
                )
                provider_key = f"{role_owned_support.get('selected_skill', 'unknown')}:{key}"
                stats["role_owned_score_normalization_provider_by_outcome"][provider_key] = (
                    stats["role_owned_score_normalization_provider_by_outcome"].get(provider_key, 0)
                    + 1
                )
            candidate_supported_count = int(
                successor_summary.get("candidate_move_role_supported_suggestion_count", 0) or 0
            )
            if candidate_supported_count:
                stats["candidate_move_role_supported_suggestion_count"] = (
                    int(stats.get("candidate_move_role_supported_suggestion_count", 0) or 0)
                    + candidate_supported_count
                )
                for role_id, count in (
                    successor_summary.get("candidate_move_role_supported_role_counts", {}) or {}
                ).items():
                    role_key = f"{role_id}:{key}"
                    stats["candidate_move_role_supported_role_by_outcome"][role_key] = (
                        stats["candidate_move_role_supported_role_by_outcome"].get(role_key, 0)
                        + int(count or 0)
                    )
                for move_name, count in (
                    successor_summary.get("candidate_move_role_supported_move_counts", {}) or {}
                ).items():
                    move_key = f"{move_name}:{key}"
                    stats["candidate_move_role_supported_move_by_outcome"][move_key] = (
                        stats["candidate_move_role_supported_move_by_outcome"].get(move_key, 0)
                        + int(count or 0)
                    )
            if successor_summary.get("candidate_move_role_selected_supported"):
                stats["candidate_move_role_selected_supported_count"] = (
                    int(stats.get("candidate_move_role_selected_supported_count", 0) or 0) + 1
                )
                selected_payload = dict(
                    successor_summary.get("candidate_move_role_selected_payload", {}) or {}
                )
                selected_key = f"{selected_payload.get('role_id', 'unknown')}:{key}"
                stats["candidate_move_role_selected_by_outcome"][selected_key] = (
                    stats["candidate_move_role_selected_by_outcome"].get(selected_key, 0) + 1
                )
            frozen_candidate_count = int(
                successor_summary.get(
                    "stage7_post_box_frozen_model_candidate_supported_suggestion_count",
                    0,
                )
                or 0
            )
            if frozen_candidate_count:
                stats["stage7_post_box_frozen_model_candidate_supported_suggestion_count"] = (
                    int(
                        stats.get(
                            "stage7_post_box_frozen_model_candidate_supported_suggestion_count",
                            0,
                        )
                        or 0
                    )
                    + frozen_candidate_count
                )
                for move_name, count in (
                    successor_summary.get(
                        "stage7_post_box_frozen_model_candidate_supported_move_counts",
                        {},
                    )
                    or {}
                ).items():
                    move_key = f"{move_name}:{key}"
                    stats[
                        "stage7_post_box_frozen_model_candidate_supported_move_by_outcome"
                    ][move_key] = (
                        stats[
                            "stage7_post_box_frozen_model_candidate_supported_move_by_outcome"
                        ].get(move_key, 0)
                        + int(count or 0)
                    )
            if successor_summary.get("stage7_post_box_frozen_model_candidate_selected_supported"):
                stats["stage7_post_box_frozen_model_candidate_selected_supported_count"] = (
                    int(
                        stats.get(
                            "stage7_post_box_frozen_model_candidate_selected_supported_count",
                            0,
                        )
                        or 0
                    )
                    + 1
                )
                selected_payload = dict(
                    successor_summary.get(
                        "stage7_post_box_frozen_model_candidate_selected_payload",
                        {},
                    )
                    or {}
                )
                selected_key = f"{selected_payload.get('move', 'unknown')}:{key}"
                stats[
                    "stage7_post_box_frozen_model_candidate_selected_by_outcome"
                ][selected_key] = (
                    stats["stage7_post_box_frozen_model_candidate_selected_by_outcome"].get(
                        selected_key,
                        0,
                    )
                    + 1
                )
            adapter_supported_suggestion_count = int(
                successor_summary.get("adapter_supported_suggestion_count", 0) or 0
            )
            if adapter_supported_suggestion_count:
                stats["adapter_fire_count"] = (
                    int(stats.get("adapter_fire_count", 0) or 0)
                    + adapter_supported_suggestion_count
                )
                for provider, count in (
                    successor_summary.get("adapter_supported_provider_counts", {}) or {}
                ).items():
                    provider_key = f"{provider}:{key}"
                    stats["adapter_supported_provider_by_outcome"][provider_key] = (
                        stats["adapter_supported_provider_by_outcome"].get(provider_key, 0)
                        + int(count or 0)
                    )
                for move_name, count in (
                    successor_summary.get("adapter_supported_move_counts", {}) or {}
                ).items():
                    move_key = f"{move_name}:{key}"
                    stats["adapter_supported_move_by_outcome"][move_key] = (
                        stats["adapter_supported_move_by_outcome"].get(move_key, 0)
                        + int(count or 0)
                    )
            elif adapter_support:
                stats["adapter_fire_count"] = int(stats.get("adapter_fire_count", 0) or 0) + 1
                provider_key = f"{adapter_support.get('provider_id', 'unknown')}:{key}"
                move_key = f"{move_uci}:{key}"
                stats["adapter_supported_provider_by_outcome"][provider_key] = (
                    stats["adapter_supported_provider_by_outcome"].get(provider_key, 0) + 1
                )
                stats["adapter_supported_move_by_outcome"][move_key] = (
                    stats["adapter_supported_move_by_outcome"].get(move_key, 0) + 1
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
                    "post_reply_state_signature": post_reply_state_signature,
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
                    "successor_raw_selected_skill": successor_summary.get("raw_selected_skill"),
                    "successor_raw_best_score": successor_summary.get("raw_best_score"),
                    "successor_second_score": successor_summary.get("second_score"),
                    "route_margin": successor_summary.get("route_margin"),
                    "selected_successor_visible_affordance": successor_summary.get("selected_successor_visible_affordance"),
                    "selected_successor_required_terms": successor_summary.get("selected_successor_required_terms"),
                    "selected_successor_missing_terms": successor_summary.get("selected_successor_missing_terms"),
                    "selected_successor_veto_terms": successor_summary.get("selected_successor_veto_terms"),
                    "selected_successor_contract_met": successor_summary.get("selected_successor_contract_met"),
                    "selected_despite_contract_mismatch": successor_summary.get("selected_despite_contract_mismatch"),
                    "selected_provider_role_licenses": successor_summary.get("selected_provider_role_licenses"),
                    "provider_selected_without_role_license": successor_summary.get("provider_selected_without_role_license"),
                    "role_bonus_total": successor_summary.get("role_bonus_total"),
                    "role_bonus_by_role": successor_summary.get("role_bonus_by_role"),
                    "visible_role_provider_support_adapter": adapter_support,
                    "plan_capsule_markers": plan_capsule_markers,
                    "stage7_plan_capsule_enabled": bool(stage7_plan_capsule_enabled),
                    "stage7_plan_capsule_state": plan_state,
                    "plan_capsule_active": successor_summary.get("plan_capsule_active"),
                    "plan_capsule_supported_suggestion_count": successor_summary.get(
                        "plan_capsule_supported_suggestion_count"
                    ),
                    "plan_capsule_supported_provider_counts": successor_summary.get(
                        "plan_capsule_supported_provider_counts"
                    ),
                    "plan_capsule_supported_move_counts": successor_summary.get(
                        "plan_capsule_supported_move_counts"
                    ),
                    "plan_capsule_selected_supported": successor_summary.get(
                        "plan_capsule_selected_supported"
                    ),
                    "plan_capsule_selected_license": successor_summary.get(
                        "plan_capsule_selected_license"
                    ),
                    "plan_capsule_max_supported_score": successor_summary.get(
                        "plan_capsule_max_supported_score"
                    ),
                    "plan_capsule_max_supported_provider": successor_summary.get(
                        "plan_capsule_max_supported_provider"
                    ),
                    "plan_capsule_max_supported_move": successor_summary.get(
                        "plan_capsule_max_supported_move"
                    ),
                    "visible_stage7_plan_capsule_owned_arbitration": successor_summary.get(
                        "visible_stage7_plan_capsule_owned_arbitration"
                    ),
                    "visible_stage7_plan_capsule_bonus": successor_summary.get(
                        "visible_stage7_plan_capsule_bonus"
                    ),
                    "visible_stage7_plan_capsule_license": successor_summary.get(
                        "visible_stage7_plan_capsule_license"
                    ),
                    "score_after_stage7_plan_capsule_bonus": successor_summary.get(
                        "score_after_stage7_plan_capsule_bonus"
                    ),
                    "visible_role_owned_score_normalization": successor_summary.get(
                        "visible_role_owned_score_normalization", {}
                    ),
                    "selected_by_role_owned_score_normalization": bool(
                        (
                            successor_summary.get("visible_role_owned_score_normalization", {})
                            or {}
                        ).get("enabled", False)
                    ),
                    "candidate_move_role_supported_suggestion_count": candidate_supported_count,
                    "candidate_move_role_supported_role_counts": successor_summary.get(
                        "candidate_move_role_supported_role_counts", {}
                    ),
                    "candidate_move_role_supported_move_counts": successor_summary.get(
                        "candidate_move_role_supported_move_counts", {}
                    ),
                    "candidate_move_role_selected_supported": successor_summary.get(
                        "candidate_move_role_selected_supported"
                    ),
                    "candidate_move_role_selected_payload": successor_summary.get(
                        "candidate_move_role_selected_payload", {}
                    ),
                    "adapter_supported_suggestion_count": adapter_supported_suggestion_count,
                    "adapter_supported_provider_counts": successor_summary.get(
                        "adapter_supported_provider_counts", {}
                    ),
                    "adapter_supported_move_counts": successor_summary.get(
                        "adapter_supported_move_counts", {}
                    ),
                    "raw_score_before_role_bonus": successor_summary.get("raw_score_before_role_bonus"),
                    "score_after_role_bonus": successor_summary.get("score_after_role_bonus"),
                    "visible_role_scoped_move_shape_bonus": successor_summary.get(
                        "visible_role_scoped_move_shape_bonus"
                    ),
                    "visible_role_scoped_move_shape_licenses": successor_summary.get(
                        "visible_role_scoped_move_shape_licenses"
                    ),
                    "visible_move_shape_audit": successor_summary.get("visible_move_shape_audit"),
                    "visible_role_scoped_move_shape_require_worst_reply": successor_summary.get(
                        "visible_role_scoped_move_shape_require_worst_reply"
                    ),
                    "score_after_role_scoped_move_shape_bonus": successor_summary.get(
                        "score_after_role_scoped_move_shape_bonus"
                    ),
                    "visible_stage0_drift_penalty": successor_summary.get(
                        "visible_stage0_drift_penalty"
                    ),
                    "visible_stage0_drift_reason": successor_summary.get(
                        "visible_stage0_drift_reason"
                    ),
                    "visible_stagnation_breaker_bonus": successor_summary.get(
                        "visible_stagnation_breaker_bonus"
                    ),
                    "visible_stagnation_breaker_license": successor_summary.get(
                        "visible_stagnation_breaker_license"
                    ),
                    "score_after_stagnation_breaker_bonus": successor_summary.get(
                        "score_after_stagnation_breaker_bonus"
                    ),
                    "visible_post_break_continuation_bonus": successor_summary.get(
                        "visible_post_break_continuation_bonus"
                    ),
                    "visible_post_break_continuation_license": successor_summary.get(
                        "visible_post_break_continuation_license"
                    ),
                    "score_after_post_break_continuation_bonus": successor_summary.get(
                        "score_after_post_break_continuation_bonus"
                    ),
                    "visible_stage7_king_tempo_bonus": successor_summary.get(
                        "visible_stage7_king_tempo_bonus"
                    ),
                    "visible_stage7_king_tempo_license": successor_summary.get(
                        "visible_stage7_king_tempo_license"
                    ),
                    "visible_stage7_drive_repair_bonus": successor_summary.get(
                        "visible_stage7_drive_repair_bonus"
                    ),
                    "visible_stage7_drive_repair_license": successor_summary.get(
                        "visible_stage7_drive_repair_license"
                    ),
                    "visible_stage7_post_king_tempo_bonus": successor_summary.get(
                        "visible_stage7_post_king_tempo_bonus"
                    ),
                    "visible_stage7_post_king_tempo_license": successor_summary.get(
                        "visible_stage7_post_king_tempo_license"
                    ),
                    "selected_skill_source": successor_summary.get("selected_skill_source"),
                    "successor_skills": successor_summary["skills"],
                    "visible_terms": successor_summary["visible_terms"],
                    "visible_successor_affordances": successor_summary["visible_successor_affordances"],
                    "visible_successor_provider_licenses": successor_summary.get("visible_successor_provider_licenses", {}),
                    "visible_eligible_successors": successor_summary["visible_eligible_successors"],
                    "role_license_present_but_provider_absent": successor_summary.get("role_license_present_but_provider_absent", {}),
                    "role_contract_met_but_provider_not_selected": successor_summary.get("role_contract_met_but_provider_not_selected", {}),
                    "missing_afforded_skills": successor_summary["missing_afforded_skills"],
                    "playout_result": key,
                    "plies": int(result.get("plies", 0) or 0),
                    "final_turn": result.get("final_turn"),
                    "final_mate_in_one_available": result.get("final_mate_in_one_available"),
                    "stagnation_summary": result.get("stagnation_summary"),
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
                    "final_turn": result.get("final_turn"),
                    "final_mate_in_one_available": result.get("final_mate_in_one_available"),
                    "stagnation_summary": result.get("stagnation_summary"),
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
                step_context = {
                    "sample": sample_index,
                    "state_signature": stable_record_id("state", chess.Board(post_reply_fen).board_fen(), chess.WHITE),
                    "start_fen": board.fen(),
                    "post_reply_fen": post_reply_fen,
                    "actual_selected_successor": successor_summary["selected_skill"],
                    "actual_result": key,
                    "failure_classes": failure_classes,
                }
                sweep = run_counterfactual_successor_sweep(
                    graph,
                    engine,
                    post_reply_fen=post_reply_fen,
                    successors=counterfactual_successors,
                    rng=sample_rng,
                    label=label,
                    max_plies=playout_max_plies,
                    black_policy=black_policy,
                    max_ticks=playout_max_ticks if playout_max_ticks is not None else max_ticks,
                    suggestion_limit=suggestion_limit,
                    successor_affordance_layer_enabled=successor_affordance_layer_enabled,
                    successor_contract_gate_enabled=successor_contract_gate_enabled,
                    successor_role_license_enabled=successor_role_license_enabled,
                    explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
                    role_owned_score_normalization_enabled=role_owned_score_normalization_enabled,
                    successor_role_veto_penalty=successor_role_veto_penalty,
                    successor_stage0_drift_penalty=successor_stage0_drift_penalty,
                    successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
                    successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
                    successor_role_scoped_move_shape_require_worst_reply=(
                        successor_role_scoped_move_shape_require_worst_reply
                    ),
                    stagnation_breaker_enabled=stagnation_breaker_enabled,
                    stagnation_breaker_bonus=stagnation_breaker_bonus,
                    stagnation_breaker_king_support_bonus=stagnation_breaker_king_support_bonus,
                    post_break_continuation_enabled=post_break_continuation_enabled,
                    post_break_continuation_bonus=post_break_continuation_bonus,
                    stage7_king_tempo_enabled=stage7_king_tempo_enabled,
                    stage7_king_tempo_score=stage7_king_tempo_score,
                    stage7_drive_repair_enabled=stage7_drive_repair_enabled,
                    stage7_drive_repair_score=stage7_drive_repair_score,
                    stage7_post_king_tempo_enabled=stage7_post_king_tempo_enabled,
                    stage7_post_king_tempo_score=stage7_post_king_tempo_score,
                    early_stop_stable_suggestions=early_stop_stable_suggestions,
                    step_output=counterfactual_steps_output,
                    step_context=step_context,
                )
                sweep_record = {
                    **step_context,
                    "actual_route_scores": {
                        skill_id: float(entry.get("score", 0.0) or 0.0)
                        for skill_id, entry in successor_summary["skills"].items()
                    },
                    "counterfactual_results": sweep,
                }
                stats["counterfactual_successor_sweeps"].append(sweep_record)
                if counterfactual_sweeps_output is not None:
                    _append_jsonl(counterfactual_sweeps_output, sweep_record)
                if verbose:
                    print(
                        "  counterfactual sweep "
                        f"{len(stats['counterfactual_successor_sweeps'])}: "
                        f"sample={sample_index} actual={successor_summary['selected_skill']} "
                        f"result={key}",
                        flush=True,
                    )
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
                    "sample": sample_index,
                    "start_fen": board.fen(),
                    "start_board": str(board),
                    **result,
                })
            if (
                key != "mate"
                and post_reply_state_signature
                and post_reply_state_signature in set(target_failure_trace_state_signatures)
                and (
                    max_target_failure_traces <= 0
                    or len(stats["target_failure_traces"]) < max_target_failure_traces
                )
            ):
                record = {
                    "sample": sample_index,
                    "state_signature": post_reply_state_signature,
                    "start_fen": board.fen(),
                    "post_reply_fen": post_reply_fen,
                    "selected_successor": successor_summary.get("selected_skill"),
                    "playout_result": key,
                    "plies": int(result.get("plies", 0) or 0),
                    "first_move": move_uci,
                    "first_reply": result.get("first_reply"),
                    "first_successor": result.get("first_successor"),
                    "trace": _compact_playout_trace(result.get("trace", []) or []),
                    "trace_truncated_events": result.get("trace_truncated_events", 0),
                    "final_fen": result.get("final_fen"),
                    "final_turn": result.get("final_turn"),
                    "final_mate_in_one_available": result.get("final_mate_in_one_available"),
                    "stagnation_summary": result.get("stagnation_summary"),
                }
                stats["target_failure_traces"].append(record)
                if target_failure_traces_output is not None:
                    _append_jsonl(target_failure_traces_output, record)
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
    stats["successor_contract_gate_enabled"] = successor_contract_gate_enabled
    stats["successor_role_license_enabled"] = successor_role_license_enabled
    stats["role_owned_score_normalization_enabled"] = role_owned_score_normalization_enabled
    stats["successor_role_veto_penalty"] = successor_role_veto_penalty
    stats["successor_stage0_drift_penalty"] = successor_stage0_drift_penalty
    stats["successor_role_scoped_move_shape_enabled"] = successor_role_scoped_move_shape_enabled
    stats["successor_role_scoped_move_shape_bonus"] = successor_role_scoped_move_shape_bonus
    stats["successor_role_scoped_move_shape_require_worst_reply"] = (
        successor_role_scoped_move_shape_require_worst_reply
    )
    stats["stagnation_breaker_enabled"] = stagnation_breaker_enabled
    stats["stagnation_breaker_bonus"] = stagnation_breaker_bonus
    stats["stagnation_breaker_king_support_bonus"] = stagnation_breaker_king_support_bonus
    stats["post_break_continuation_enabled"] = post_break_continuation_enabled
    stats["post_break_continuation_bonus"] = post_break_continuation_bonus
    stats["stage7_king_tempo_enabled"] = stage7_king_tempo_enabled
    stats["stage7_king_tempo_score"] = stage7_king_tempo_score
    stats["stage7_drive_repair_enabled"] = stage7_drive_repair_enabled
    stats["stage7_drive_repair_score"] = stage7_drive_repair_score
    stats["stage7_post_king_tempo_enabled"] = stage7_post_king_tempo_enabled
    stats["stage7_post_king_tempo_score"] = stage7_post_king_tempo_score
    stats["stage7_post_box_continuation_enabled"] = stage7_post_box_continuation_enabled
    stats["stage7_post_box_continuation_score"] = stage7_post_box_continuation_score
    stats["stage7_learned_post_box_continuation_enabled"] = stage7_learned_post_box_continuation_enabled
    stats["stage7_learned_post_box_continuation_bonus"] = stage7_learned_post_box_continuation_bonus
    stats["stage7_post_box_frozen_model_candidate_enabled"] = (
        stage7_post_box_frozen_model_candidate_enabled
    )
    stats["stage7_post_box_frozen_model_candidate_support"] = (
        stage7_post_box_frozen_model_candidate_support
    )
    stats["early_stop_stable_suggestions"] = int(early_stop_stable_suggestions)
    stats["lock_stage_filter_through_playout"] = bool(lock_stage_filter_through_playout)
    stats["diagnostic_caches_enabled"] = bool(enable_diagnostic_caches)
    stats["deterministic_sample_seeds"] = bool(deterministic_sample_seeds)
    if sample_indices is not None:
        stats["sample_indices"] = list(indices)
    stats["target_failure_trace_state_signatures"] = list(target_failure_trace_state_signatures)
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
    stats["counterfactual_successor_summary"] = summarize_counterfactual_successor_sweeps(
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
    if not stats["target_failure_traces"]:
        stats.pop("target_failure_traces", None)
    if not stats["handoff_packets"]:
        stats.pop("handoff_packets", None)
    if not stats["shadow_candidates"]:
        stats.pop("shadow_candidates", None)
    if not stats["counterfactual_successor_sweeps"]:
        stats.pop("counterfactual_successor_sweeps", None)
        stats.pop("counterfactual_successor_summary", None)
    if profile_performance and perf_profile and total_start is not None:
        _profile_add_time(perf_profile, "total_wall_time", time.perf_counter() - total_start)
        stats["performance_profile"] = _finalize_perf_profile(perf_profile)
    return stats


def _merge_count_dict(target: dict, source: dict | None) -> None:
    if not isinstance(source, dict):
        return
    for key, value in source.items():
        if isinstance(value, dict):
            bucket = target.setdefault(key, {})
            if not isinstance(bucket, dict):
                bucket = {}
                target[key] = bucket
            _merge_count_dict(bucket, value)
        else:
            target[key] = int(target.get(key, 0) or 0) + int(value or 0)


def _merge_nested_count_dict(target: dict, source: dict | None) -> None:
    if not isinstance(source, dict):
        return
    for key, value in source.items():
        if isinstance(value, dict):
            bucket = target.setdefault(key, {})
            _merge_count_dict(bucket, value)
        else:
            target[key] = int(target.get(key, 0) or 0) + int(value or 0)


def _merge_profile_profiles(worker_stats: list[dict], *, wall_time: float) -> dict | None:
    profiles = [
        stats.get("performance_profile")
        for stats in worker_stats
        if isinstance(stats.get("performance_profile"), dict)
    ]
    if not profiles:
        return None
    timers = {key: 0.0 for key in PROFILE_TIMER_KEYS}
    counts = {key: 0 for key in PROFILE_COUNT_KEYS}
    cache: dict[str, dict[str, int]] = {}
    diagnostic_caches_enabled = False
    for profile in profiles:
        diagnostic_caches_enabled = diagnostic_caches_enabled or bool(
            profile.get("diagnostic_caches_enabled", False)
        )
        for key, value in (profile.get("timers_sec") or {}).items():
            timers[key] = float(timers.get(key, 0.0) or 0.0) + float(value or 0.0)
        for key, value in (profile.get("counts") or {}).items():
            counts[key] = int(counts.get(key, 0) or 0) + int(value or 0)
        for cache_name, cache_counts in (profile.get("cache") or {}).items():
            if not isinstance(cache_counts, dict):
                continue
            merged_counts = cache.setdefault(cache_name, {"hits": 0, "misses": 0})
            merged_counts["hits"] = int(merged_counts.get("hits", 0) or 0) + int(
                cache_counts.get("hits", 0) or 0
            )
            merged_counts["misses"] = int(merged_counts.get("misses", 0) or 0) + int(
                cache_counts.get("misses", 0) or 0
            )
    worker_total = float(timers.get("total_wall_time", 0.0) or 0.0)
    timers["parallel_wall_time"] = round(float(wall_time), 6)
    timers["worker_total_wall_time_sum"] = round(worker_total, 6)
    total_for_percent = float(wall_time) if wall_time > 0 else worker_total
    percentages = {
        key: round((float(value) / total_for_percent * 100.0), 3)
        if total_for_percent > 0
        else 0.0
        for key, value in timers.items()
    }
    return {
        "schema_version": "krk_performance_profile.v1",
        "timers_sec": {key: round(float(value), 6) for key, value in timers.items()},
        "timer_percentages_of_total": percentages,
        "counts": counts,
        "cache": cache,
        "diagnostic_caches_enabled": diagnostic_caches_enabled,
        "parallel_profile": True,
    }


def _merge_parallel_stats(
    worker_stats: list[dict],
    *,
    base_kwargs: dict,
    wall_time: float,
    parallel_workers: int,
    chunk_size: int,
    max_handoff_packets: int,
    max_shadow_candidates: int,
) -> dict:
    if not worker_stats:
        raise ValueError("no worker stats to merge")
    merged = copy.deepcopy(worker_stats[0])
    count_keys = (
        "total",
        "no_move",
        "improved",
        "flat",
        "worsened",
        "optimal",
        "conversion_failure_count",
        "one_ply_engine_decision_count",
        "one_ply_engine_ticks_total",
        "one_ply_engine_early_stop_count",
        "playout_engine_decision_count",
        "playout_engine_ticks_total",
        "playout_engine_early_stop_count",
        "handoff_packet_count",
        "shadow_candidate_count",
        "counterfactual_successor_sweep_count",
        "adapter_fire_count",
        "candidate_move_frame_count",
        "candidate_move_role_match_count",
        "candidate_move_role_supported_suggestion_count",
        "candidate_move_role_selected_supported_count",
        "stage7_post_box_frozen_model_candidate_supported_suggestion_count",
        "stage7_post_box_frozen_model_candidate_selected_supported_count",
        "plan_capsule_marker_count",
        "plan_capsule_entry_count",
        "plan_capsule_exit_count",
        "plan_capsule_abort_count",
        "plan_capsule_expired_count",
        "plan_capsule_progress_confirmed_count",
        "plan_capsule_active_decision_count",
        "plan_capsule_supported_suggestion_count",
        "plan_capsule_selected_supported_count",
        "plan_capsule_active_without_support_count",
        "plan_capsule_owned_arbitration_selected_count",
        "role_owned_score_normalization_selected_count",
    )
    max_keys = ("one_ply_engine_ticks_max", "playout_engine_ticks_max")
    dict_count_keys = (
        "playouts",
        "one_ply_status_counts",
        "conversion_status_counts",
        "semantic_alignment_status_counts",
        "semantic_alignment_confusion_counts",
        "handoff_packet_counts_by_phase",
        "shadow_candidate_counts_by_trigger",
        "adapter_supported_provider_by_outcome",
        "adapter_supported_move_by_outcome",
        "candidate_move_role_supported_role_by_outcome",
        "candidate_move_role_supported_move_by_outcome",
        "candidate_move_role_selected_by_outcome",
        "stage7_post_box_frozen_model_candidate_supported_move_by_outcome",
        "stage7_post_box_frozen_model_candidate_selected_by_outcome",
        "plan_capsule_marker_by_outcome",
        "plan_capsule_status_by_outcome",
        "plan_capsule_supported_provider_by_outcome",
        "plan_capsule_supported_move_by_outcome",
        "plan_capsule_selected_supported_by_outcome",
        "plan_capsule_owned_arbitration_provider_by_outcome",
        "role_owned_score_normalization_provider_by_outcome",
    )
    nested_count_keys = ("conversion_by_semantic_alignment_status",)
    list_keys = (
        "debug_failures",
        "debug_playouts",
        "target_failure_traces",
        "handoff_packets",
        "shadow_candidates",
        "counterfactual_successor_sweeps",
    )
    snapshot_keys = ("semantic_alignment_snapshots",)

    for key in count_keys:
        merged[key] = sum(int(stats.get(key, 0) or 0) for stats in worker_stats)
    for key in max_keys:
        merged[key] = max(int(stats.get(key, 0) or 0) for stats in worker_stats)
    for key in dict_count_keys:
        merged[key] = {}
        for stats in worker_stats:
            _merge_count_dict(merged[key], stats.get(key))
    for key in nested_count_keys:
        merged[key] = {}
        for stats in worker_stats:
            _merge_nested_count_dict(merged[key], stats.get(key))
    for key in list_keys:
        merged[key] = []
        for stats in worker_stats:
            merged[key].extend(list(stats.get(key, []) or []))
    for key in snapshot_keys:
        merged[key] = {}
        for stats in worker_stats:
            for bucket, items in (stats.get(key) or {}).items():
                merged[key].setdefault(bucket, []).extend(list(items or []))

    total = int(merged.get("total", 0) or 0)
    if total:
        merged["avg_reward"] = sum(
            float(stats.get("avg_reward", 0.0) or 0.0) * int(stats.get("total", 0) or 0)
            for stats in worker_stats
        ) / total
        merged["avg_oracle_reward"] = sum(
            float(stats.get("avg_oracle_reward", 0.0) or 0.0) * int(stats.get("total", 0) or 0)
            for stats in worker_stats
        ) / total

    evaluated = max(0, total - int(merged.get("no_move", 0) or 0))
    merged["one_ply_status"] = (
        "passed"
        if evaluated > 0
        and int(merged.get("no_move", 0) or 0) == 0
        and int(merged.get("worsened", 0) or 0) == 0
        and int(merged.get("optimal", 0) or 0) == total
        else "failed"
        if total > 0
        else "not_checked"
    )
    playout_total = sum(int(value) for value in (merged.get("playouts") or {}).values())
    mate_total = int((merged.get("playouts") or {}).get("mate", 0) or 0)
    if int(base_kwargs.get("playout_max_plies", 0) or 0) <= 0 or playout_total == 0:
        merged["conversion_status"] = "not_checked"
    elif mate_total == playout_total:
        merged["conversion_status"] = "passed"
    else:
        merged["conversion_status"] = "failed"
    merged["conversion_failure_count"] = max(0, playout_total - mate_total)

    merged["counterfactual_successor_summary"] = summarize_counterfactual_successor_sweeps(
        merged.get("counterfactual_successor_sweeps", [])
    )
    if not merged.get("counterfactual_successor_sweeps"):
        merged.pop("counterfactual_successor_sweeps", None)
        merged.pop("counterfactual_successor_summary", None)

    if max_handoff_packets > 0:
        merged["handoff_packets"] = merged.get("handoff_packets", [])[:max_handoff_packets]
        merged["handoff_packets_truncated"] = max(
            0,
            int(merged.get("handoff_packet_count", 0) or 0) - len(merged["handoff_packets"]),
        )
    if max_shadow_candidates > 0:
        merged["shadow_candidates"] = merged.get("shadow_candidates", [])[:max_shadow_candidates]
        merged["shadow_candidates_truncated"] = max(
            0,
            int(merged.get("shadow_candidate_count", 0) or 0) - len(merged["shadow_candidates"]),
        )
    for key in ("debug_failures", "debug_playouts", "target_failure_traces", "handoff_packets", "shadow_candidates"):
        if not merged.get(key):
            merged.pop(key, None)

    profile = _merge_profile_profiles(worker_stats, wall_time=wall_time)
    if profile is not None:
        merged["performance_profile"] = profile

    merged["parallel_validation"] = {
        "enabled": True,
        "workers": int(parallel_workers),
        "chunk_size": int(chunk_size),
        "chunks": len(worker_stats),
        "deterministic_sample_seeds": True,
        "sample_seed_formula": "base_seed * 1_000_000 + sample_index",
        "wall_time_sec": round(float(wall_time), 6),
    }
    merged["sample_indices"] = [
        index
        for stats in worker_stats
        for index in list(stats.get("sample_indices", []) or [])
    ]
    merged["deterministic_sample_seeds"] = True
    return merged


def _parallel_eval_worker(payload: dict) -> dict:
    kwargs = dict(payload["kwargs"])
    return evaluate_landmark_progress(**kwargs)


def evaluate_landmark_progress_parallel(
    *,
    parallel_workers: int,
    chunk_size: int,
    **kwargs,
) -> dict:
    samples = int(kwargs.get("samples", 0) or 0)
    if samples <= 0:
        return evaluate_landmark_progress(**kwargs)
    chunk_size = max(1, int(chunk_size or 1))
    chunks = [
        tuple(range(start, min(samples, start + chunk_size)))
        for start in range(0, samples, chunk_size)
    ]
    worker_count = max(1, min(int(parallel_workers), len(chunks)))
    base_kwargs = dict(kwargs)
    max_handoff_packets = int(base_kwargs.get("max_handoff_packets", 0) or 0)
    max_shadow_candidates = int(base_kwargs.get("max_shadow_candidates", 0) or 0)
    payloads = []
    for chunk in chunks:
        worker_kwargs = dict(base_kwargs)
        worker_kwargs.update({
            "samples": len(chunk),
            "sample_indices": chunk,
            "deterministic_sample_seeds": True,
            "verbose": False,
            "target_failure_traces_output": None,
            "shadow_candidates_output": None,
            "counterfactual_sweeps_output": None,
            "counterfactual_steps_output": None,
        })
        payloads.append({"kwargs": worker_kwargs})

    start = time.perf_counter()
    results: list[dict] = []
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(_parallel_eval_worker, payload) for payload in payloads]
        for index, future in enumerate(as_completed(futures), start=1):
            stats = future.result()
            results.append(stats)
            print(
                f"  parallel chunk {index}/{len(futures)}: "
                f"n={stats.get('total')} improved={stats.get('improved')} "
                f"optimal={stats.get('optimal')} playouts={stats.get('playouts', {})}",
                flush=True,
            )
    results.sort(key=lambda item: min(item.get("sample_indices", [0]) or [0]))
    wall_time = time.perf_counter() - start
    return _merge_parallel_stats(
        results,
        base_kwargs=base_kwargs,
        wall_time=wall_time,
        parallel_workers=worker_count,
        chunk_size=chunk_size,
        max_handoff_packets=max_handoff_packets,
        max_shadow_candidates=max_shadow_candidates,
    )


def print_landmark_results(
    stats: dict,
    *,
    black_policy: str = "adversarial",
    playout_max_plies: int = 0,
    print_json: bool = True,
) -> None:
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
        print(f"Counterfactual successor summary: {stats.get('counterfactual_successor_summary', {})}")
    if stats.get("semantic_alignment_status_counts"):
        print(f"Semantic alignment: {stats['semantic_alignment_status_counts']}")
    if stats.get("candidate_move_role_supported_suggestion_count"):
        print(f"Candidate move role suggestions: {stats['candidate_move_role_supported_suggestion_count']}")
    if stats.get("stage7_post_box_frozen_model_candidate_supported_suggestion_count"):
        print(
            "Stage7 frozen model candidate suggestions: "
            f"{stats['stage7_post_box_frozen_model_candidate_supported_suggestion_count']}"
        )
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
    if print_json:
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
    parser.add_argument("--no-json-stdout", action="store_true",
                        help="Print only the human summary; still writes full JSON when --json-output is set")
    parser.add_argument("--debug-failures", type=int, default=0,
                        help="Include this many non-oracle selected positions with board/move diagnostics")
    parser.add_argument("--debug-playouts", type=int, default=0,
                        help="Include this many non-mating playout traces with move-by-move diagnostics")
    parser.add_argument("--target-failure-trace-state-signatures", type=str, default="",
                        help="Comma-separated post-reply state signatures whose failed playouts should be traced")
    parser.add_argument("--max-target-failure-traces", type=int, default=0,
                        help="If >0, limit targeted failure traces to this count")
    parser.add_argument("--target-failure-traces-output", type=Path, default=None,
                        help="Optional JSONL path for targeted failure trace records")
    parser.add_argument("--max-ticks", type=int, default=200,
                        help="Max ReCoN ticks for the evaluated one-ply move")
    parser.add_argument("--playout-max-ticks", type=int, default=None,
                        help="Max ReCoN ticks for each White move inside playouts (default: --max-ticks)")
    parser.add_argument("--suggestion-limit", type=int, default=10,
                        help="Number of actuator suggestions retained per engine decision")
    parser.add_argument("--early-stop-stable-suggestions", type=int, default=0,
                        help="Diagnostic speedup: stop a ReCoN move loop after the top suggestion is stable for this many ticks (0 disables)")
    parser.add_argument("--lock-stage-filter-through-playout", action="store_true",
                        help="Guardrail diagnostic: keep --stage-filter active for every White playout move")
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
    parser.add_argument("--enable-successor-contract-gate", action="store_true",
                        help="Enable opt-in visible contract mismatch penalty for successor skill ownership")
    parser.add_argument("--enable-successor-role-licenses", action="store_true",
                        help="Enable additive visible role-license bonuses for successor provider skills")
    parser.add_argument("--enable-explicit-role-provider-support", action="store_true",
                        help="Enable sandbox explicit role-provider support adapters")
    parser.add_argument("--enable-role-owned-score-normalization", action="store_true",
                        help="Sandbox: let visible move-shape-gated adapter-supported suggestions own arbitration over raw cross-skill scores")
    parser.add_argument("--successor-role-veto-penalty", type=float, default=0.0,
                        help="Opt-in visible role-veto penalty applied only when another provider has a visible role license")
    parser.add_argument("--successor-stage0-drift-penalty", type=float, default=0.0,
                        help="Opt-in penalty for visibly unproductive stage0 king drift when edge-trap recovery is licensed")
    parser.add_argument("--enable-role-scoped-move-shapes", action="store_true",
                        help="Enable opt-in role-scoped visible move-shape bonuses")
    parser.add_argument("--role-scoped-move-shape-bonus", type=float, default=0.0,
                        help="Bonus weight for confirmed role-scoped visible move-shape licenses")
    parser.add_argument("--require-role-scoped-move-shape-worst-reply", action="store_true",
                        help="Require worst-reply survival terms for runtime role-scoped move-shape bonuses; slower, audit-oriented")
    parser.add_argument("--enable-stagnation-breaker", action="store_true",
                        help="Enable opt-in visible stagnation-breaker move license bonus")
    parser.add_argument("--stagnation-breaker-bonus", type=float, default=0.0,
                        help="Small bonus for candidate moves licensed by visible stagnation-breaker terms")
    parser.add_argument("--stagnation-breaker-king-support-bonus", type=float, default=0.0,
                        help="Extra opt-in bonus for loop-breaking king moves toward both enemy king and rook support")
    parser.add_argument("--enable-post-break-continuation", action="store_true",
                        help="Enable opt-in visible post-stagnation-break continuation move license bonus")
    parser.add_argument("--post-break-continuation-bonus", type=float, default=0.0,
                        help="Small bonus for candidate moves licensed by visible post-break continuation terms")
    parser.add_argument("--enable-stage7-king-tempo", action="store_true",
                        help="Enable opt-in Stage 7 visible king-tempo sandbox provider")
    parser.add_argument("--stage7-king-tempo-score", type=float, default=25.0,
                        help="Score for the opt-in Stage 7 visible king-tempo sandbox provider")
    parser.add_argument("--enable-stage7-drive-repair", action="store_true",
                        help="Enable opt-in Stage 7 visible drive-repair sandbox provider")
    parser.add_argument("--stage7-drive-repair-score", type=float, default=28.0,
                        help="Score for the opt-in Stage 7 visible drive-repair sandbox provider")
    parser.add_argument("--enable-stage7-post-king-tempo", action="store_true",
                        help="Enable opt-in Stage 7 visible post-king-tempo continuation provider")
    parser.add_argument("--stage7-post-king-tempo-score", type=float, default=30.0,
                        help="Score for the opt-in Stage 7 visible post-king-tempo continuation provider")
    parser.add_argument("--enable-stage7-post-box-continuation", action="store_true",
                        help="Enable opt-in Stage 7 visible post-box-shrink continuation provider")
    parser.add_argument("--stage7-post-box-continuation-score", type=float, default=32.0,
                        help="Score for the opt-in Stage 7 visible post-box-shrink continuation provider")
    parser.add_argument("--enable-stage7-learned-post-box-continuation", action="store_true",
                        help="Enable opt-in learned Stage 7 post-box-shrink continuation overlay providers")
    parser.add_argument("--stage7-learned-post-box-continuation-bonus", type=float, default=0.0,
                        help="Tiny opt-in visible owner support for learned Stage 7 post-box continuation providers")
    parser.add_argument("--enable-stage7-post-box-frozen-model-candidate", action="store_true",
                        help="Enable opt-in frozen visible-term CandidateMoveFrame sandbox suggestion for Stage 7 post-box states")
    parser.add_argument("--stage7-post-box-frozen-model-candidate-support", type=float, default=0.0,
                        help="Visible support amount for the opt-in frozen model candidate suggestion")
    parser.add_argument("--stage7-post-box-frozen-model", type=Path, default=None,
                        help="Path to non-promoted stage7_post_box_trajectory_provider_model JSON")
    parser.add_argument("--enable-plan-capsule-sandbox", action="store_true",
                        help="Enable non-causal Plan Capsule marker evidence recording; does not alter move scoring")
    parser.add_argument("--enable-stage7-plan-capsule", action="store_true",
                        help="Enable opt-in Stage 7 Plan Capsule v0 bounded support sandbox")
    parser.add_argument("--stage7-plan-capsule-ttl", type=int, default=3,
                        help="White-move TTL for the opt-in Stage 7 Plan Capsule v0 sandbox")
    parser.add_argument("--stage7-plan-capsule-support-bonus", type=float, default=0.0,
                        help="Small opt-in support amount for candidate moves licensed by the Stage 7 Plan Capsule")
    parser.add_argument("--enable-stage7-plan-capsule-owned-arbitration", action="store_true",
                        help="Sandbox: let active Plan Capsule licensed moves own arbitration within the bounded window")
    parser.add_argument("--enable-candidate-move-layer", action="store_true",
                        help="Enable ephemeral CandidateMoveFrame enumeration; default-off and non-requesting")
    parser.add_argument("--enable-stage7-king-support-fence-stabilizer", action="store_true",
                        help="Enable sandbox 0926 king-support fence-stabilizer MoveShapeRoleSpec matching")
    parser.add_argument("--candidate-move-role-support", type=float, default=0.0,
                        help="Visible support amount for sandbox role-scoped candidate-move suggestions")
    parser.add_argument("--composition-profile",
                        choices=[COMPOSITION_PROFILE_NONE, COMPOSITION_PROFILE_HANDOFF_V1],
                        default=COMPOSITION_PROFILE_NONE,
                        help="Named opt-in composition profile. Defaults to none.")
    parser.add_argument("--use-profile-validation-defaults", action="store_true",
                        help="Apply non-behavioral validation defaults recommended by the selected profile")
    parser.add_argument("--counterfactual-successors", type=str, default=None,
                        help="Comma-separated canonical successor skill IDs to force on failed post-reply states")
    parser.add_argument("--max-counterfactual-sweeps", type=int, default=0,
                        help="If >0, limit forced-successor sweeps to this many failed samples")
    parser.add_argument("--counterfactual-sweeps-output", type=Path, default=None,
                        help="Optional JSONL path for streaming forced-successor sweep records as they complete")
    parser.add_argument("--counterfactual-steps-output", type=Path, default=None,
                        help="Optional JSONL path for streaming each forced-successor playout result as it completes")
    parser.add_argument("--profile-performance", action="store_true",
                        help="Record diagnostic timing/count buckets without changing behavior")
    parser.add_argument("--enable-diagnostic-caches", action="store_true",
                        help="Enable opt-in pure memoization caches for diagnostic/profiling runs")
    parser.add_argument("--parallel-workers", type=int, default=1,
                        help="Run validation samples across this many worker processes")
    parser.add_argument("--chunk-size", type=int, default=25,
                        help="Samples per worker chunk when --parallel-workers > 1")
    args = parser.parse_args()

    source_names = (
        tuple(name.strip() for name in args.source_stage_names.split(",") if name.strip())
        if args.source_stage_names
        else None
    )
    frozen_model = None
    if args.stage7_post_box_frozen_model is not None:
        frozen_model = json.loads(args.stage7_post_box_frozen_model.read_text(encoding="utf-8"))
    eval_kwargs = dict(
        topology=args.topology,
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
        target_failure_trace_state_signatures=tuple(
            item.strip()
            for item in args.target_failure_trace_state_signatures.split(",")
            if item.strip()
        ),
        max_target_failure_traces=args.max_target_failure_traces,
        target_failure_traces_output=args.target_failure_traces_output,
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
        successor_contract_gate_enabled=args.enable_successor_contract_gate,
        successor_role_license_enabled=args.enable_successor_role_licenses,
        explicit_role_provider_support_enabled=args.enable_explicit_role_provider_support,
        role_owned_score_normalization_enabled=args.enable_role_owned_score_normalization,
        successor_role_veto_penalty=args.successor_role_veto_penalty,
        successor_stage0_drift_penalty=args.successor_stage0_drift_penalty,
        successor_role_scoped_move_shape_enabled=args.enable_role_scoped_move_shapes,
        successor_role_scoped_move_shape_bonus=args.role_scoped_move_shape_bonus,
        successor_role_scoped_move_shape_require_worst_reply=args.require_role_scoped_move_shape_worst_reply,
        stagnation_breaker_enabled=args.enable_stagnation_breaker,
        stagnation_breaker_bonus=args.stagnation_breaker_bonus,
        stagnation_breaker_king_support_bonus=args.stagnation_breaker_king_support_bonus,
        post_break_continuation_enabled=args.enable_post_break_continuation,
        post_break_continuation_bonus=args.post_break_continuation_bonus,
        stage7_king_tempo_enabled=args.enable_stage7_king_tempo,
        stage7_king_tempo_score=args.stage7_king_tempo_score,
        stage7_drive_repair_enabled=args.enable_stage7_drive_repair,
        stage7_drive_repair_score=args.stage7_drive_repair_score,
        stage7_post_king_tempo_enabled=args.enable_stage7_post_king_tempo,
        stage7_post_king_tempo_score=args.stage7_post_king_tempo_score,
        stage7_post_box_continuation_enabled=args.enable_stage7_post_box_continuation,
        stage7_post_box_continuation_score=args.stage7_post_box_continuation_score,
        stage7_learned_post_box_continuation_enabled=args.enable_stage7_learned_post_box_continuation,
        stage7_learned_post_box_continuation_bonus=args.stage7_learned_post_box_continuation_bonus,
        stage7_post_box_frozen_model_candidate_enabled=(
            args.enable_stage7_post_box_frozen_model_candidate
        ),
        stage7_post_box_frozen_model_candidate_support=(
            args.stage7_post_box_frozen_model_candidate_support
        ),
        stage7_post_box_frozen_model=frozen_model,
        plan_capsule_sandbox_enabled=args.enable_plan_capsule_sandbox,
        stage7_plan_capsule_enabled=args.enable_stage7_plan_capsule,
        stage7_plan_capsule_ttl=args.stage7_plan_capsule_ttl,
        stage7_plan_capsule_support_bonus=args.stage7_plan_capsule_support_bonus,
        stage7_plan_capsule_owned_arbitration_enabled=args.enable_stage7_plan_capsule_owned_arbitration,
        candidate_move_layer_enabled=args.enable_candidate_move_layer,
        stage7_king_support_fence_stabilizer_enabled=args.enable_stage7_king_support_fence_stabilizer,
        candidate_move_role_support=args.candidate_move_role_support,
        early_stop_stable_suggestions=args.early_stop_stable_suggestions,
        lock_stage_filter_through_playout=args.lock_stage_filter_through_playout,
        counterfactual_successors=tuple(
            item.strip()
            for item in (args.counterfactual_successors or "").split(",")
            if item.strip()
        ),
        max_counterfactual_sweeps=args.max_counterfactual_sweeps,
        counterfactual_sweeps_output=args.counterfactual_sweeps_output,
        counterfactual_steps_output=args.counterfactual_steps_output,
        profile_performance=args.profile_performance,
        enable_diagnostic_caches=args.enable_diagnostic_caches,
        verbose=True,
    )
    eval_kwargs, profile_runtime_overrides = _apply_composition_profile_to_eval_kwargs(
        eval_kwargs,
        args.composition_profile,
        use_validation_defaults=args.use_profile_validation_defaults,
    )
    if args.use_profile_validation_defaults and profile_runtime_overrides:
        if (
            args.parallel_workers == 1
            and "parallel_workers" in profile_runtime_overrides
            and not _cli_option_provided("--parallel-workers")
        ):
            args.parallel_workers = profile_runtime_overrides["parallel_workers"]
        if (
            args.chunk_size == 25
            and "chunk_size" in profile_runtime_overrides
            and not _cli_option_provided("--chunk-size")
        ):
            args.chunk_size = profile_runtime_overrides["chunk_size"]
    if args.parallel_workers > 1:
        stats = evaluate_landmark_progress_parallel(
            parallel_workers=args.parallel_workers,
            chunk_size=args.chunk_size,
            **eval_kwargs,
        )
    else:
        stats = evaluate_landmark_progress(**eval_kwargs)
    print_landmark_results(
        stats,
        black_policy=args.black_policy,
        playout_max_plies=args.playout_max_plies,
        print_json=not args.no_json_stdout,
    )
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        if args.profile_performance and stats.get("performance_profile"):
            start = time.perf_counter()
            _ = json.dumps(stats, indent=2)
            elapsed = time.perf_counter() - start
            profile = stats["performance_profile"]
            timers = profile.setdefault("timers_sec", {})
            timers["json_trace_serialization_time"] = round(
                float(timers.get("json_trace_serialization_time", 0.0) or 0.0) + elapsed,
                6,
            )
            timers["total_wall_time"] = round(
                float(timers.get("total_wall_time", 0.0) or 0.0) + elapsed,
                6,
            )
            total = float(timers.get("total_wall_time", 0.0) or 0.0)
            profile["timer_percentages_of_total"] = {
                key: round((float(value) / total * 100.0), 3) if total > 0 else 0.0
                for key, value in timers.items()
            }
        args.json_output.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
