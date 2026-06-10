#!/usr/bin/env python3
"""Build a replay-free Stage 7 evidence merge and decision gate.

This script reads existing non-causal Stage 7 artifacts and emits a compact
diagnostic table. It does not run gameplay, label new moves, use DTM at runtime,
mutate topology, train a provider, or add a repair path.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ARTIFACT_NAMES = {
    "neutral_matrix": "stage7_neutral_diagnostic_matrix.json",
    "family_diagnosis": "stage7_post_box_family_diagnosis.json",
    "remaining_dtm": "stage7_remaining_dtm_candidate_summary.json",
    "candidate_move_0926": "stage7_0926_move_shape_role_candidate_audit.json",
    "candidate_move_2cc": "stage7_2cc_candidate_move_dtm_alignment.json",
    "m3_trainability": "stage7_post_box_m3_trainability_assessment.json",
    "capsule_fidelity": "stage7_capsule_trajectory_fidelity_audit.json",
    "expanded_capsule_fidelity": "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json",
    "expanded_capsule_replay": "stage7_expanded_ranked_capsule_phase1_replay_h40.json",
    "strategy_arbitration_dataset": "stage7_unified_strategy_arbitration_dataset.json",
    "strategy_arbitration_probe": "stage7_unified_strategy_arbitration_probe.json",
    "plan_capsule_owned_failure_analysis": "stage7_plan_capsule_owned_failure_analysis_50_h40.json",
}


DECISION_STATUSES = {
    "proceed_to_training_objective_benchmark",
    "proceed_to_curriculum_boundary_audit",
    "proceed_to_missing_feature_audit",
    "proceed_to_continuation_capacity_overlay_design",
    "stop_stage7_and_freeze_as_known_residual",
}


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _state_key(fen: str | None, fallback: str) -> str:
    if fen:
        return fen
    return fallback


def _new_row(fen: str | None, state_id: str | None = None) -> dict[str, Any]:
    return {
        "state_identity": {
            "family_id": None,
            "state_signature": state_id,
            "post_reply_fen": fen,
            "source_artifacts": [],
            "sample_support_count": None,
        },
        "terminal_space_context": {
            "black_king_edge_distance": None,
            "black_king_edge_bucket": None,
            "box_area": None,
            "box_area_relevance": None,
            "rook_safe": None,
            "fence_cut_status": None,
            "king_support_status": None,
            "mate_in_one_available": None,
            "mate_basin_or_edge_net_proxy": None,
            "semantic_alignment_bucket": None,
            "active_terminal_terms": [],
        },
        "strategy_provider_evidence": {
            "raw_selected_provider": None,
            "raw_selected_move": None,
            "raw_global_top_provider": None,
            "raw_global_top_move": None,
            "provider_local_rank_info": [],
            "role_owned_arbitration_candidate": None,
            "forced_provider_results": {},
            "best_forced_provider": None,
            "candidate_move_result": None,
            "legal_first_or_dtm_label": None,
        },
        "continuation_evidence": {
            "current_graph_result_h40": None,
            "forced_provider_result_h40": None,
            "legal_first_result_h40_h50": None,
            "dtm_result": None,
            "closed_loop_capsule_result": None,
            "teacher_fidelity_topk": None,
        },
        "hypothesis_labels": [],
        "missing_evidence": [],
    }


def _add_source(row: dict[str, Any], source: str) -> None:
    sources = row["state_identity"]["source_artifacts"]
    if source not in sources:
        sources.append(source)


def _add_label(row: dict[str, Any], label: str) -> None:
    labels = row["hypothesis_labels"]
    if label not in labels:
        labels.append(label)


def _add_missing(row: dict[str, Any], cell: str, replay_free: bool, smallest_label: str | None = None) -> None:
    entry = {
        "missing_cell": cell,
        "can_be_filled_replay_free": replay_free,
        "smallest_bounded_h40_label_needed": smallest_label,
    }
    if entry not in row["missing_evidence"]:
        row["missing_evidence"].append(entry)


def _edge_bucket(value: Any) -> str | None:
    if value is None:
        return None
    try:
        distance = int(value)
    except (TypeError, ValueError):
        return None
    if distance <= 0:
        return "at_edge"
    if distance == 1:
        return "near_edge"
    return "central_or_midboard"


def _fence_cut_status(terms: dict[str, Any]) -> str | None:
    if terms.get("fence_exists") and terms.get("fence_stable"):
        return "stable_fence"
    if terms.get("fence_exists"):
        return "fence_exists_unstable"
    if terms.get("cut_stable"):
        return "cut_stable"
    if terms.get("fence_or_cut_not_preserved"):
        return "fence_or_cut_not_preserved"
    return None


def _king_support_status(terms: dict[str, Any]) -> str | None:
    if terms.get("white_king_support_available"):
        return "support_available"
    if terms.get("white_king_can_improve_support") or terms.get("king_support_improvement_move_exists"):
        return "support_can_improve"
    return None


def _edge_net_proxy(terms: dict[str, Any]) -> str | None:
    proxies = [
        "mate_basin_available",
        "edge_trap_shape_available",
        "edge_rook_transfer_recovery_available",
        "corner_net_pressure_available",
        "enemy_king_near_edge",
    ]
    active = [term for term in proxies if terms.get(term)]
    return ",".join(active) if active else None


def _context_from_board_features(board_features: dict[str, Any]) -> dict[str, Any]:
    terms = board_features.get("terminal_terms") or {}
    metrics = board_features.get("metrics") or {}
    return {
        "black_king_edge_distance": metrics.get("enemy_edge_distance")
        if metrics.get("enemy_edge_distance") is not None
        else board_features.get("black_king_edge_distance"),
        "black_king_edge_bucket": _edge_bucket(
            metrics.get("enemy_edge_distance")
            if metrics.get("enemy_edge_distance") is not None
            else board_features.get("black_king_edge_distance")
        ),
        "box_area": metrics.get("box_area") if metrics.get("box_area") is not None else board_features.get("box_area"),
        "box_area_relevance": board_features.get("box_area_relevance"),
        "rook_safe": bool(terms.get("rook_safe")) if "rook_safe" in terms else board_features.get("rook_safe"),
        "fence_cut_status": _fence_cut_status(terms),
        "king_support_status": _king_support_status(terms),
        "mate_in_one_available": bool(terms.get("mate_in_one_available")) if terms else None,
        "mate_basin_or_edge_net_proxy": _edge_net_proxy(terms),
        "active_terminal_terms": board_features.get("active_terminal_terms") or sorted(
            key for key, value in terms.items() if value
        ),
    }


def _context_from_visible_terms(visible_terms: dict[str, Any]) -> dict[str, Any]:
    terms = {term: True for term in visible_terms.get("current_terms") or []}
    return {
        "black_king_edge_distance": None,
        "black_king_edge_bucket": "near_edge" if terms.get("enemy_king_near_edge") else None,
        "box_area": None,
        "box_area_relevance": "high" if terms.get("box_area_large") else None,
        "rook_safe": True if terms.get("rook_safe") else None,
        "fence_cut_status": _fence_cut_status(terms),
        "king_support_status": _king_support_status(terms),
        "mate_in_one_available": True if terms.get("mate_in_one_available") else None,
        "mate_basin_or_edge_net_proxy": _edge_net_proxy(terms),
        "active_terminal_terms": sorted(terms),
    }


def _context_from_fen(fen: str | None) -> dict[str, Any]:
    if not fen:
        return {}
    try:
        import contextlib
        import io

        import chess

        with contextlib.redirect_stdout(io.StringIO()):
            from recon_lite_chess.krk_baseline_nodes import _compute_krk_context_terms, _krk_geometry_metrics

        board = chess.Board(fen)
        terms = _compute_krk_context_terms(board)
        metrics = _krk_geometry_metrics(board) or {}
    except Exception:
        return {}
    return {
        "black_king_edge_distance": metrics.get("enemy_edge_distance"),
        "black_king_edge_bucket": _edge_bucket(metrics.get("enemy_edge_distance")),
        "box_area": metrics.get("box_area"),
        "box_area_relevance": _box_area_relevance_from_metrics(metrics),
        "rook_safe": bool(terms.get("rook_safe")) if terms else None,
        "fence_cut_status": _fence_cut_status(terms),
        "king_support_status": _king_support_status(terms),
        "mate_in_one_available": bool(terms.get("mate_in_one_available")) if terms else None,
        "mate_basin_or_edge_net_proxy": _edge_net_proxy(terms),
        "active_terminal_terms": sorted(key for key, value in terms.items() if value),
    }


def _box_area_relevance_from_metrics(metrics: dict[str, Any]) -> str | None:
    edge_value = metrics.get("enemy_edge_distance")
    box_value = metrics.get("box_area")
    if edge_value is None or box_value is None:
        return None
    try:
        edge = int(edge_value)
        box = int(box_value)
    except (TypeError, ValueError):
        return None
    if edge <= 0:
        return "low"
    if edge == 1:
        return "medium" if box >= 8 else "low"
    return "high" if box >= 12 else "medium"


def _merge_context(row: dict[str, Any], context: dict[str, Any]) -> None:
    target = row["terminal_space_context"]
    for key, value in context.items():
        if key == "active_terminal_terms":
            existing = set(target.get(key) or [])
            existing.update(value or [])
            target[key] = sorted(existing)
        elif value is not None and target.get(key) is None:
            target[key] = value


def _best_forced_provider(results: dict[str, Any]) -> dict[str, Any] | None:
    mates: list[tuple[str, dict[str, Any]]] = []
    for provider, result in results.items():
        if isinstance(result, dict) and result.get("result") == "mate":
            mates.append((provider, result))
    if not mates:
        return None
    mates.sort(key=lambda item: int(item[1].get("plies") or 9999))
    provider, result = mates[0]
    return {
        "provider": provider,
        "result": result.get("result"),
        "plies": result.get("plies"),
        "first_move": result.get("first_move"),
        "horizon": result.get("horizon"),
    }


def _summarize_forced_results(results: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for provider, result in results.items():
        if not isinstance(result, dict):
            continue
        summary[provider] = {
            "result": result.get("result"),
            "plies": result.get("plies"),
            "first_move": result.get("first_move"),
            "horizon": result.get("horizon"),
            "h80_result": result.get("h80_result"),
        }
    return summary


def _update_from_family(rows: dict[str, dict[str, Any]], family_payload: dict[str, Any]) -> None:
    source = "stage7_post_box_family_diagnosis.json"
    for family in family_payload.get("families") or []:
        if not isinstance(family, dict):
            continue
        fen = family.get("post_reply_fen")
        key = _state_key(fen, str(family.get("state_id") or family.get("family_id")))
        row = rows.setdefault(key, _new_row(fen, family.get("state_id")))
        _add_source(row, source)
        row["state_identity"]["family_id"] = family.get("family_id")
        row["state_identity"]["state_signature"] = family.get("state_id")
        row["state_identity"]["post_reply_fen"] = fen
        row["state_identity"]["sample_support_count"] = 1

        context = _context_from_visible_terms(family.get("visible_terms") or {})
        source_record = family.get("source_record") or {}
        if not source_record and isinstance(family.get("candidate"), dict):
            source_record = family["candidate"].get("source_record") or {}
        if source_record.get("semantic_alignment_status"):
            context["semantic_alignment_bucket"] = source_record["semantic_alignment_status"]
        _merge_context(row, context)

        strategy = row["strategy_provider_evidence"]
        strategy["raw_selected_provider"] = family.get("selected_successor")
        strategy["raw_selected_move"] = family.get("selected_move")
        forced = family.get("forced_provider_results") or {}
        strategy["forced_provider_results"] = _summarize_forced_results(forced)
        strategy["best_forced_provider"] = family.get("best_forced_provider") or _best_forced_provider(forced)
        if family.get("legal_first_summary"):
            strategy["legal_first_or_dtm_label"] = family["legal_first_summary"]

        continuation = row["continuation_evidence"]
        continuation["current_graph_result_h40"] = family.get("conversion_result")
        if strategy["best_forced_provider"]:
            continuation["forced_provider_result_h40"] = strategy["best_forced_provider"]
        elif forced:
            continuation["forced_provider_result_h40"] = {
                "result": "no_forced_provider_mate",
                "tested_provider_count": len(forced),
            }
        if family.get("legal_first_summary"):
            continuation["legal_first_result_h40_h50"] = family["legal_first_summary"]

        diagnosis = family.get("diagnosis")
        if diagnosis == "existing_provider_can_convert_if_family_role_selects_it":
            _add_label(row, "already_solved_by_existing_provider_if_arbitrated")
            _add_label(row, "strategy_arbitration_candidate")
        if diagnosis == "unresolved_by_existing_forced_providers_at_h80":
            _add_label(row, "continuation_capacity_candidate")
            _add_label(row, "unresolved_without_new_continuation_policy")
        if family.get("failure_classes"):
            _add_label(row, "phase_boundary_candidate")
            _add_label(row, "bad_curriculum_boundary_candidate")
        if not row["terminal_space_context"].get("box_area"):
            _add_missing(row, "exact_box_area_and_edge_distance", True, None)
        if not family.get("legal_first_summary"):
            _add_missing(row, "legal_first_h40_label", False, "one bounded h40 legal-first/provider-best label if this family remains decision-critical")


def _update_from_remaining_dtm(rows: dict[str, dict[str, Any]], payload: dict[str, Any]) -> None:
    source = "stage7_remaining_dtm_candidate_summary.json"
    for candidate in payload.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        fen = candidate.get("post_reply_fen")
        key = _state_key(fen, str(candidate.get("state_id") or candidate.get("candidate_id")))
        row = rows.setdefault(key, _new_row(fen, candidate.get("state_id")))
        _add_source(row, source)
        row["state_identity"]["family_id"] = row["state_identity"]["family_id"] or candidate.get("candidate_id")
        row["state_identity"]["state_signature"] = row["state_identity"]["state_signature"] or candidate.get("state_id")
        row["state_identity"]["post_reply_fen"] = row["state_identity"]["post_reply_fen"] or fen
        dtm = candidate.get("dtm") or {}
        row["continuation_evidence"]["dtm_result"] = {
            "diagnosis": candidate.get("diagnosis"),
            "state_dtm": dtm.get("state_dtm"),
            "best_dtm_plies": dtm.get("best_dtm_plies"),
            "winning_move_count": dtm.get("winning_move_count"),
            "legal_move_count": dtm.get("legal_move_count"),
            "best_moves": [move.get("move") for move in (dtm.get("best_moves") or [])[:8] if isinstance(move, dict)],
        }
        row["strategy_provider_evidence"]["legal_first_or_dtm_label"] = row["strategy_provider_evidence"].get(
            "legal_first_or_dtm_label"
        ) or {
            "source_terms": candidate.get("source_terms"),
            "trigger_failure_classes": candidate.get("trigger_failure_classes"),
        }
        _add_label(row, "continuation_capacity_candidate")
        _add_label(row, "training_objective_model_expression_candidate")
        _add_label(row, "unresolved_without_new_continuation_policy")
        _add_label(row, "bad_curriculum_boundary_candidate")
        _add_missing(row, "provider_internal_trainability_for_this_state", True, None)


def _update_from_candidate_move_0926(rows: dict[str, dict[str, Any]], payload: dict[str, Any]) -> None:
    source = "stage7_0926_move_shape_role_candidate_audit.json"
    for record in payload.get("records") or []:
        if not isinstance(record, dict):
            continue
        fen = record.get("fen")
        key = _state_key(fen, str(record.get("state_signature") or "candidate_move"))
        row = rows.setdefault(key, _new_row(fen, record.get("state_signature")))
        _add_source(row, source)
        row["state_identity"]["state_signature"] = row["state_identity"]["state_signature"] or record.get("state_signature")
        row["strategy_provider_evidence"]["candidate_move_result"] = {
            "role_id": payload.get("role_id"),
            "matching_move_count": record.get("matching_move_count"),
            "matching_moves": [move.get("move") for move in record.get("matching_moves") or [] if isinstance(move, dict)],
            "legal_move_count": record.get("legal_move_count"),
        }
        if record.get("matching_move_count"):
            _add_label(row, "missing_feature_candidate")
        else:
            _add_missing(row, "candidate_move_role_for_this_family", True, None)


def _update_from_candidate_move_2cc(rows: dict[str, dict[str, Any]], payload: dict[str, Any]) -> None:
    if not payload:
        return
    source = "stage7_2cc_candidate_move_dtm_alignment.json"
    fen = payload.get("target_fen")
    key = _state_key(fen, "stage7_2cc_candidate_move_dtm_alignment")
    row = rows.setdefault(key, _new_row(fen, "state.2cc0b3e1033a"))
    _add_source(row, source)
    dtm = payload.get("dtm") or {}
    graph = payload.get("legal_first_current_graph") or {}
    trajectory = payload.get("trajectory_summary") or {}
    row["strategy_provider_evidence"]["candidate_move_result"] = {
        "dtm_best_moves": dtm.get("best_moves"),
        "optimal_move_count": dtm.get("optimal_move_count"),
        "legal_first_current_graph": graph,
        "first_reference_steps": trajectory.get("first_white_steps"),
    }
    row["continuation_evidence"]["dtm_result"] = {
        "state_dtm": dtm.get("state_dtm"),
        "winning_move_count": dtm.get("winning_move_count"),
        "legal_move_count": dtm.get("legal_move_count"),
        "all_legal_moves_win": dtm.get("all_legal_moves_win"),
        "best_child_dtm": dtm.get("best_child_dtm"),
        "best_moves": dtm.get("best_moves"),
    }
    row["continuation_evidence"]["legal_first_result_h40_h50"] = graph
    _add_label(row, "continuation_capacity_candidate")
    _add_label(row, "missing_feature_candidate")
    _add_label(row, "training_objective_model_expression_candidate")
    _add_label(row, "bad_curriculum_boundary_candidate")


def _update_from_arbitration_dataset(rows: dict[str, dict[str, Any]], payload: dict[str, Any]) -> None:
    source = "stage7_unified_strategy_arbitration_dataset.json"
    for record in payload.get("records") or []:
        if not isinstance(record, dict):
            continue
        fen = record.get("fen")
        key = _state_key(fen, str(record.get("state_id") or "arbitration"))
        row = rows.setdefault(key, _new_row(fen, record.get("state_id")))
        _add_source(row, source)
        row["state_identity"]["state_signature"] = row["state_identity"]["state_signature"] or record.get("state_id")
        _merge_context(row, _context_from_board_features(record.get("board_features") or {}))
        suggestions = record.get("suggestions") or []
        if suggestions:
            top = max(suggestions, key=lambda item: float(item.get("raw_score") or 0.0))
            row["strategy_provider_evidence"]["raw_global_top_provider"] = top.get("provider_id")
            row["strategy_provider_evidence"]["raw_global_top_move"] = top.get("move")
            rank1 = [
                {
                    "provider_id": item.get("provider_id"),
                    "move": item.get("move"),
                    "raw_score": item.get("raw_score"),
                    "provider_local_rank": item.get("provider_local_rank"),
                    "provider_local_normalized_score": item.get("provider_local_normalized_score"),
                    "playout_label": item.get("playout_label"),
                }
                for item in suggestions
                if item.get("provider_local_rank") == 1
            ]
            row["strategy_provider_evidence"]["provider_local_rank_info"] = rank1[:12]
            if any((item.get("playout_label") or {}).get("result") == "mate" for item in rank1):
                _add_label(row, "strategy_arbitration_candidate")
            else:
                _add_missing(row, "provider_best_h40_mating_label", False, "one bounded h40 label for provider-best shortlist")


def _update_from_fidelity(rows: dict[str, dict[str, Any]], payload: dict[str, Any], source: str) -> None:
    acc = payload.get("teacher_forced_accuracy") or {}
    topk = {
        "teacher_move_top1_rate": acc.get("teacher_move_top1_rate"),
        "dtm_positive_top1_rate": acc.get("dtm_positive_top1_rate"),
        "dtm_positive_top3_rate": acc.get("dtm_positive_top3_rate"),
        "top_level_diagnosis": payload.get("top_level_diagnosis"),
    }
    for record in payload.get("closed_loop_records") or []:
        if not isinstance(record, dict):
            continue
        fen = record.get("start_fen")
        key = _state_key(fen, str(record.get("source") or source))
        row = rows.setdefault(key, _new_row(fen))
        _add_source(row, source)
        row["continuation_evidence"]["closed_loop_capsule_result"] = {
            "result": record.get("result"),
            "plies": record.get("plies"),
            "selected_skill": record.get("selected_skill"),
            "selected_move": record.get("selected_move"),
            "selected_target_class": record.get("selected_target_class"),
            "selected_is_dtm_positive": record.get("selected_is_dtm_positive"),
            "teacher_move": record.get("teacher_move"),
            "positive_moves": record.get("positive_moves"),
            "first_divergence": record.get("first_divergence"),
        }
        row["continuation_evidence"]["teacher_fidelity_topk"] = topk
        if record.get("result") != "mate":
            _add_label(row, "training_objective_model_expression_candidate")
            _add_label(row, "unresolved_without_new_continuation_policy")
        if record.get("first_divergence"):
            _add_label(row, "bad_curriculum_boundary_candidate")


def _update_from_m3(rows: dict[str, dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe_result": payload.get("probe_result"),
        "counts": payload.get("counts") or {},
        "diagnostic_labels": payload.get("diagnostic_labels") or [],
        "trainable_internal_edge_count": payload.get("trainable_internal_edge_count"),
        "causal_status": payload.get("causal_status"),
    }


def build_evidence_merge(artifact_root: Path) -> dict[str, Any]:
    paths = {key: artifact_root / name for key, name in ARTIFACT_NAMES.items()}
    artifacts = {key: _load_optional_json(path) for key, path in paths.items()}
    rows: dict[str, dict[str, Any]] = {}

    _update_from_family(rows, artifacts["family_diagnosis"])
    _update_from_remaining_dtm(rows, artifacts["remaining_dtm"])
    _update_from_candidate_move_0926(rows, artifacts["candidate_move_0926"])
    _update_from_candidate_move_2cc(rows, artifacts["candidate_move_2cc"])
    _update_from_arbitration_dataset(rows, artifacts["strategy_arbitration_dataset"])
    _update_from_fidelity(rows, artifacts["capsule_fidelity"], "stage7_capsule_trajectory_fidelity_audit.json")
    _update_from_fidelity(
        rows,
        artifacts["expanded_capsule_fidelity"],
        "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json",
    )

    for row in rows.values():
        _merge_context(row, _context_from_fen(row["state_identity"].get("post_reply_fen")))
        if row["terminal_space_context"].get("box_area") is not None and row["terminal_space_context"].get(
            "black_king_edge_distance"
        ) is not None:
            row["missing_evidence"] = [
                item
                for item in row["missing_evidence"]
                if item.get("missing_cell") != "exact_box_area_and_edge_distance"
            ]
        if not row["hypothesis_labels"]:
            _add_label(row, "missing_feature_candidate")
            _add_missing(row, "hypothesis_specific_evidence", True, None)
        if row["continuation_evidence"].get("dtm_result") and not row["continuation_evidence"].get(
            "closed_loop_capsule_result"
        ):
            _add_missing(row, "closed_loop_capsule_replay_for_dtm_state", True, None)

    row_list = sorted(
        rows.values(),
        key=lambda row: (
            row["state_identity"].get("family_id") or "",
            row["state_identity"].get("state_signature") or "",
            row["state_identity"].get("post_reply_fen") or "",
        ),
    )
    label_counts = Counter(label for row in row_list for label in row["hypothesis_labels"])
    missing_counts = Counter(item["missing_cell"] for row in row_list for item in row["missing_evidence"])

    merge = {
        "schema_version": "stage7_evidence_merge_table.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage8_training_allowed": False,
        "stage7_promotion_allowed": False,
        "artifact_root": str(artifact_root),
        "source_artifacts": {
            key: {"path": str(path), "exists": path.exists()} for key, path in paths.items()
        },
        "rows": row_list,
        "summary": {
            "row_count": len(row_list),
            "hypothesis_label_counts": dict(sorted(label_counts.items())),
            "missing_evidence_counts": dict(sorted(missing_counts.items())),
            "m3_trainability_summary": _update_from_m3(rows, artifacts["m3_trainability"]),
            "arbitration_probe_answers": (artifacts["strategy_arbitration_probe"].get("answers") or {}),
            "arbitration_probe_state_count": artifacts["strategy_arbitration_probe"].get("dataset_state_count"),
            "arbitration_probe_labeled_state_count": artifacts["strategy_arbitration_probe"].get("labeled_state_count"),
        },
    }
    validate_evidence_merge(merge)
    return merge


def build_decision_gate(merge: dict[str, Any]) -> dict[str, Any]:
    labels = Counter(merge["summary"].get("hypothesis_label_counts") or {})
    m3 = merge["summary"].get("m3_trainability_summary") or {}
    arbitration_answers = merge["summary"].get("arbitration_probe_answers") or {}

    rows = merge.get("rows") or []
    closed_loop_failed = any(
        ((row.get("continuation_evidence") or {}).get("closed_loop_capsule_result") or {}).get("result")
        not in {None, "mate"}
        for row in rows
    )
    weak_teacher_fidelity = any(
        (
            ((row.get("continuation_evidence") or {}).get("teacher_fidelity_topk") or {}).get(
                "dtm_positive_top1_rate"
            )
            or 1.0
        )
        < 0.5
        for row in rows
    )
    m3_non_trainable = "not_trainable" in str(m3.get("probe_result") or "")
    arbitration_no_help = arbitration_answers and not any(bool(value) for value in arbitration_answers.values())

    model_expression_score = labels.get("training_objective_model_expression_candidate", 0)
    model_expression_score += 3 if closed_loop_failed else 0
    model_expression_score += 2 if weak_teacher_fidelity else 0
    model_expression_score += 1 if m3_non_trainable else 0

    continuation_score = labels.get("continuation_capacity_candidate", 0)
    continuation_score += labels.get("unresolved_without_new_continuation_policy", 0) // 2

    missing_feature_score = labels.get("missing_feature_candidate", 0)
    curriculum_score = labels.get("bad_curriculum_boundary_candidate", 0)
    arbitration_score = labels.get("strategy_arbitration_candidate", 0)
    arbitration_score -= 1 if arbitration_no_help else 0

    selected_status = "proceed_to_training_objective_benchmark"
    confidence = "medium_high"
    rationale = [
        "The learnable post-box provider is selected in residual closed-loop replays but still max-plies.",
        "Trajectory fidelity remains weak after expanded DTM-margin supervision, while top-3 signal shows partial representation rather than complete absence.",
        "M3 trainability evidence indicates the previous scripted provider path lacked useful trainable internal move-policy edges.",
        "The first unified arbitration probe did not identify a better provider owner and did not support low box-area relevance as the main residual explanation.",
    ]
    if continuation_score > model_expression_score and not model_expression_score:
        selected_status = "proceed_to_continuation_capacity_overlay_design"
        confidence = "medium"
        rationale = [
            "Evidence is dominated by unresolved forced-provider and DTM-won/current-graph-failed cases.",
            "No current training-objective evidence dominates the residuals.",
        ]
    elif missing_feature_score > model_expression_score + continuation_score:
        selected_status = "proceed_to_missing_feature_audit"
        confidence = "medium"
        rationale = [
            "Visible term separability evidence dominates the current rows.",
            "Proceed with non-causal term contrast before any runtime term change.",
        ]
    elif curriculum_score >= model_expression_score + continuation_score + missing_feature_score:
        selected_status = "proceed_to_curriculum_boundary_audit"
        confidence = "medium"
        rationale = [
            "Most rows point to box_shrink as an unstable owner rather than a local policy failure.",
        ]
    elif merge["summary"].get("row_count", 0) < 3:
        selected_status = "stop_stage7_and_freeze_as_known_residual"
        confidence = "low"
        rationale = [
            "Evidence remains too sparse to choose the next diagnostic class without overfitting.",
        ]

    gate = {
        "schema_version": "stage7_decision_gate.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selected_status": selected_status,
        "selected_status_confidence": confidence,
        "supported_hypothesis": {
            "primary": "training_objective_model_expression"
            if selected_status == "proceed_to_training_objective_benchmark"
            else selected_status.replace("proceed_to_", "").replace("_audit", ""),
            "weighted_evidence_scores": {
                "strategy_arbitration_phase_boundary": arbitration_score,
                "continuation_capacity": continuation_score,
                "missing_feature_ontology": missing_feature_score,
                "training_objective_model_expression": model_expression_score,
                "bad_standalone_curriculum_boundary": curriculum_score,
            },
            "raw_label_counts": dict(labels),
        },
        "rationale": rationale,
        "minimum_next_step": (
            "Run an offline-only training-objective/model-expression benchmark on existing DTM trajectory states: "
            "compare current learned scoring against a ranked/pairwise preference objective and a visible-term baseline; "
            "report top-k fidelity and closed-loop drift diagnostics. Do not compile a runtime repair."
        )
        if selected_status == "proceed_to_training_objective_benchmark"
        else "Run the named next diagnostic class only, preserving all current non-causal constraints.",
        "secondary_hypotheses": [
            {
                "hypothesis": "continuation_capacity",
                "status": "plausible_secondary",
                "reason": "Some states remain DTM-won/current-graph-failed and forced-provider unresolved.",
            },
            {
                "hypothesis": "missing_feature_ontology",
                "status": "plausible_secondary",
                "reason": "Candidate-move terms separate 0926 but do not yet explain all residual families.",
            },
            {
                "hypothesis": "strategy_arbitration_phase_boundary",
                "status": "not_currently_dominant",
                "reason": "First arbitration probe found no provider-local/rank1 advantage in sampled residuals.",
            },
            {
                "hypothesis": "bad_standalone_curriculum_boundary",
                "status": "plausible_secondary",
                "reason": "Stage 7 remains local-valid but composition-quarantined after multiple diagnostic paths.",
            },
        ],
        "blocked_next_steps": [
            "train_stage8",
            "promote_stage7",
            "add_runtime_repair_or_causal_sandbox",
            "add_provider_bonus_or_penalty",
            "add_support_adapter",
            "use_runtime_dtm_or_tablebase",
            "mutate_topology_during_gameplay",
        ],
        "arbitration_probe_answers": arbitration_answers,
        "m3_trainability_summary": m3,
        "source_merge_schema": merge.get("schema_version"),
    }
    validate_decision_gate(gate)
    return gate


def validate_evidence_merge(merge: dict[str, Any]) -> None:
    if merge.get("schema_version") != "stage7_evidence_merge_table.v1":
        raise ValueError("unexpected merge schema")
    if merge.get("causal_status") != "non_causal":
        raise ValueError("evidence merge must be non-causal")
    if merge.get("runtime_behavior_changed") is not False:
        raise ValueError("evidence merge must not change runtime behavior")
    if merge.get("stage8_training_allowed") is not False or merge.get("stage7_promotion_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")
    for row in merge.get("rows") or []:
        for key in [
            "state_identity",
            "terminal_space_context",
            "strategy_provider_evidence",
            "continuation_evidence",
            "hypothesis_labels",
            "missing_evidence",
        ]:
            if key not in row:
                raise ValueError(f"row missing {key}")


def validate_decision_gate(gate: dict[str, Any]) -> None:
    if gate.get("schema_version") != "stage7_decision_gate.v1":
        raise ValueError("unexpected decision gate schema")
    if gate.get("causal_status") != "non_causal":
        raise ValueError("decision gate must be non-causal")
    if gate.get("runtime_behavior_changed") is not False:
        raise ValueError("decision gate must not change runtime behavior")
    if gate.get("selected_status") not in DECISION_STATUSES:
        raise ValueError(f"unknown selected_status: {gate.get('selected_status')}")
    if gate.get("stage8_training_allowed") is not False or gate.get("stage7_promotion_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")


def render_merge_markdown(merge: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Evidence Merge Table",
        "",
        "This report is replay-free and non-causal. It merges existing Stage 7 artifacts without changing runtime behavior.",
        "",
        "## Summary",
        "",
        f"- Rows: {merge['summary']['row_count']}",
        f"- Hypothesis labels: `{merge['summary']['hypothesis_label_counts']}`",
        f"- Missing evidence: `{merge['summary']['missing_evidence_counts']}`",
        f"- M3 trainability: `{merge['summary']['m3_trainability_summary'].get('probe_result')}`",
        f"- Arbitration answers: `{merge['summary']['arbitration_probe_answers']}`",
        "",
        "## Rows",
        "",
    ]
    for idx, row in enumerate(merge["rows"], start=1):
        ident = row["state_identity"]
        context = row["terminal_space_context"]
        strategy = row["strategy_provider_evidence"]
        continuation = row["continuation_evidence"]
        lines.extend(
            [
                f"### {idx}. {ident.get('state_signature') or ident.get('family_id') or 'unknown_state'}",
                "",
                f"- Family: `{ident.get('family_id')}`",
                f"- FEN: `{ident.get('post_reply_fen')}`",
                f"- Sources: `{ident.get('source_artifacts')}`",
                f"- Context: edge={context.get('black_king_edge_distance')} ({context.get('black_king_edge_bucket')}), "
                f"box={context.get('box_area')}, relevance={context.get('box_area_relevance')}, "
                f"rook_safe={context.get('rook_safe')}, fence/cut={context.get('fence_cut_status')}, "
                f"king_support={context.get('king_support_status')}",
                f"- Selected provider/move: `{strategy.get('raw_selected_provider')}` / `{strategy.get('raw_selected_move')}`",
                f"- Raw top provider/move: `{strategy.get('raw_global_top_provider')}` / `{strategy.get('raw_global_top_move')}`",
                f"- Best forced provider: `{strategy.get('best_forced_provider')}`",
                f"- Current graph h40: `{continuation.get('current_graph_result_h40')}`",
                f"- Legal/DTM label: `{strategy.get('legal_first_or_dtm_label')}`",
                f"- Capsule result: `{continuation.get('closed_loop_capsule_result')}`",
                f"- Teacher fidelity: `{continuation.get('teacher_fidelity_topk')}`",
                f"- Labels: `{row.get('hypothesis_labels')}`",
                f"- Missing evidence: `{row.get('missing_evidence')}`",
                "",
            ]
        )
    return "\n".join(lines)


def render_gate_markdown(gate: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Decision Gate",
        "",
        "This decision gate recommends the next diagnostic/training class only. It does not implement a repair.",
        "",
        f"- Selected status: `{gate['selected_status']}`",
        f"- Confidence: `{gate['selected_status_confidence']}`",
        f"- Primary hypothesis: `{gate['supported_hypothesis']['primary']}`",
        f"- Stage 7 promotion allowed: `{gate['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{gate['stage8_training_allowed']}`",
        "",
        "## Rationale",
        "",
    ]
    lines.extend(f"- {item}" for item in gate["rationale"])
    lines.extend(
        [
            "",
            "## Minimum Next Step",
            "",
            gate["minimum_next_step"],
            "",
            "## Secondary Hypotheses",
            "",
        ]
    )
    for item in gate["secondary_hypotheses"]:
        lines.append(f"- {item['hypothesis']}: {item['status']} - {item['reason']}")
    lines.extend(
        [
            "",
            "## Blocked Next Steps",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in gate["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path("reports/structural_candidates"))
    parser.add_argument("--merge-json-output", type=Path, required=True)
    parser.add_argument("--merge-markdown-output", type=Path, required=True)
    parser.add_argument("--gate-json-output", type=Path, required=True)
    parser.add_argument("--gate-markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    merge = build_evidence_merge(args.artifact_root)
    gate = build_decision_gate(merge)

    args.merge_json_output.parent.mkdir(parents=True, exist_ok=True)
    args.gate_json_output.parent.mkdir(parents=True, exist_ok=True)
    args.merge_json_output.write_text(json.dumps(merge, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.merge_markdown_output.write_text(render_merge_markdown(merge), encoding="utf-8")
    args.gate_json_output.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.gate_markdown_output.write_text(render_gate_markdown(gate), encoding="utf-8")

    if not args.no_json_stdout:
        print(json.dumps({"merge": merge, "decision_gate": gate}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
