"""TG29r continuation candidate retrieval repair diagnostics."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any

import chess

from .cached_online_episode_scale_matrix import (
    CachedOnlineEpisodeScaleMatrixConfig,
    _artifact_reuse_from_tg29o,
    _compact_regression,
    _load_json,
    _purity_boundary as _tg29p_purity_boundary,
    _real_context_cfg,
)
from .frozen_foundation_edge_fence_reentry import _cheap_candidate_rows, _foundation_counts
from .horizon_limited_continuation_repair import (
    HorizonLimitedContinuationRepairConfig,
    _board_progress_direction,
    _board_progress_score,
)
from .real_context_runtime_trajectory_validation import _artifact_reuse_summary, _build_minimal_real_context, _load_artifacts, _rows_by_start
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig, _foundation_reachable, _safety_result


LAYERS = (
    "legal",
    "safe",
    "edge",
    "bridge",
    "trajectory",
    "s1_full_reply",
    "foundation_response",
    "runtime_selectable",
)


@dataclass(frozen=True)
class ContinuationCandidateRetrievalRepairConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair_progress.json",
    )
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    tg29o_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29o_s1_full_reply_cache_online_recheck.json"
    tg29n_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29n_s1_full_reply_handoff_validation.json"
    s1_cache_path: str = "reports/autogrowth/pools/tg29o_s1_full_reply_evidence_cache.jsonl"
    retrieval_cache_path: str = "reports/autogrowth/pools/tg29r_continuation_candidate_retrieval_cache.jsonl"
    retrieval_cache_index_path: str = "reports/autogrowth/pools/tg29r_continuation_candidate_retrieval_cache_index.json"
    current_runtime_cap: int = 12
    widened_cap: int = 32
    max_blocked_turns: int = 4
    max_black_replies_per_candidate: int = 2
    run_real_context: bool = True
    use_existing_cache: bool = True
    write_cache: bool = True
    run_compact_regression: bool = False


@dataclass(frozen=True)
class ContinuationCandidateRetrievalRepairResult:
    config: ContinuationCandidateRetrievalRepairConfig
    tg29q_baseline: dict[str, Any]
    artifact_reuse: dict[str, Any]
    context_profile: dict[str, Any]
    blocked_turns: list[dict[str, Any]]
    candidate_retrieval_audit: dict[str, Any]
    retrieval_cache: dict[str, Any]
    repair_arm_comparison: dict[str, Any]
    compact_regression: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.v0",
            "checkpoint": "TG29r_continuation_candidate_retrieval_repair",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "tg29q_baseline": self.tg29q_baseline,
            "artifact_reuse": self.artifact_reuse,
            "context_profile": self.context_profile,
            "blocked_turns": self.blocked_turns,
            "candidate_retrieval_audit": self.candidate_retrieval_audit,
            "retrieval_cache": self.retrieval_cache,
            "repair_arm_comparison": self.repair_arm_comparison,
            "compact_regression": self.compact_regression,
            "ablation_results": self.ablation_results,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output

    def write_markdown(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        d = self.decision
        output.write_text(
            "\n".join(
                [
                    "# TG29r Continuation Candidate Retrieval Repair",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- blocked turns: `{d['blocked_turn_count']}`",
                    f"- legal/safe/runtime candidates: `{d['legal_candidate_count']}` / `{d['safe_candidate_count']}` / `{d['runtime_selectable_candidate_count']}`",
                    f"- continuation-positive total/runtime/dropped: `{d['continuation_positive_candidate_count']}` / `{d['continuation_positive_in_runtime_count']}` / `{d['continuation_positive_dropped_count']}`",
                    f"- cap/retrieval/materialization blocked: `{d['candidate_cap_blocked_count']}` / `{d['retrieval_blocked_count']}` / `{d['materialization_blocked_count']}`",
                    f"- targeted episode success: `{d['targeted_episode_success_count']}` / `{d['targeted_episode_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    "",
                    "Interpretation: TG29r is diagnostic unless `repair_applied` is true.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_continuation_candidate_retrieval_repair(
    *,
    config: ContinuationCandidateRetrievalRepairConfig | None = None,
) -> ContinuationCandidateRetrievalRepairResult:
    cfg = config or ContinuationCandidateRetrievalRepairConfig()
    total_start = time.perf_counter()
    timings: dict[str, float] = {}
    _write_progress(cfg, {"phase": "start"})
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    blocked_turns = _blocked_turns_from_tg29q(tg29q)[: cfg.max_blocked_turns]
    _write_progress(cfg, {"phase": "blocked_turns_loaded", "blocked_turn_count": len(blocked_turns)})

    artifact_reuse: dict[str, Any] = {"tg29q_reused": True, "tg29q_artifact_path": cfg.tg29q_artifact_path}
    context_profile: dict[str, Any] = {"context_built": False, "context_skipped": not cfg.run_real_context}
    audit = _skipped_audit("real_context_skipped")
    cache_summary = _cache_summary(cfg, [], hit_count=0, query_count=0, live_count=0, mismatch_count=0)
    compact = _compact_from_tg29q(tg29q, skipped_reason="reused_from_tg29q")
    foundation_before_eval = {"m3": 0, "m4": 0}
    foundation_after_eval = {"m3": 0, "m4": 0}

    if cfg.run_real_context:
        start = time.perf_counter()
        tg29o = _load_json(cfg.tg29o_artifact_path)
        p_cfg = _as_tg29p_config(cfg)
        real_cfg = _real_context_cfg(p_cfg)
        artifacts = _load_artifacts(real_cfg)
        rows_by_start = _rows_by_start(artifacts["tg29h"])
        artifact_reuse = _artifact_reuse_summary(real_cfg, artifacts, rows_by_start)
        artifact_reuse.update(_artifact_reuse_from_tg29o(tg29o))
        artifact_reuse.update({"tg29q_reused": True, "tg29q_artifact_path": cfg.tg29q_artifact_path})
        context, context_profile = _build_minimal_real_context(real_cfg, artifact_reuse)
        if context is None:
            raise RuntimeError(f"TG29r requires real context; build failed: {context_profile}")
        foundation_before_eval = _foundation_counts(context["graph"])
        timings["context_build_seconds"] = round(time.perf_counter() - start, 6)
        _write_progress(cfg, {"phase": "context_built", "seconds": timings["context_build_seconds"]})

        start = time.perf_counter()
        cache = _load_retrieval_cache(cfg.retrieval_cache_path) if cfg.use_existing_cache else {}
        audit, cache_rows, cache_stats = _run_retrieval_audit(cfg, context, blocked_turns, cache)
        timings["candidate_audit_seconds"] = round(time.perf_counter() - start, 6)
        if cfg.write_cache:
            _write_cache_files(cfg, cache_rows)
        cache_summary = _cache_summary(cfg, cache_rows, **cache_stats)
        _write_progress(cfg, {"phase": "candidate_audit_complete", "blocked_turn_count": audit["summary"]["blocked_turn_count"], "continuation_positive_candidate_count": audit["summary"]["continuation_positive_candidate_count"]})

        start = time.perf_counter()
        compact = _compact_regression(context, artifacts, rows_by_start) if cfg.run_compact_regression else _compact_from_tg29q(tg29q, skipped_reason="reused_from_tg29q")
        foundation_after_eval = _foundation_counts(context["graph"])
        timings["regression_seconds"] = round(time.perf_counter() - start, 6)

    timings.setdefault("context_build_seconds", 0.0)
    timings.setdefault("candidate_audit_seconds", 0.0)
    timings.setdefault("regression_seconds", 0.0)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)
    repair = _repair_arm_comparison(audit)
    decision = _decision(
        cfg,
        tg29q=tg29q,
        tg29p=tg29p,
        audit=audit,
        cache_summary=cache_summary,
        repair=repair,
        compact=compact,
        artifact_reuse=artifact_reuse,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return ContinuationCandidateRetrievalRepairResult(
        config=cfg,
        tg29q_baseline={"decision": tg29q["decision"], "horizon_diagnostic_summary": tg29q["horizon_diagnostic"]["summary"]},
        artifact_reuse=artifact_reuse,
        context_profile=context_profile,
        blocked_turns=blocked_turns,
        candidate_retrieval_audit=audit,
        retrieval_cache=cache_summary,
        repair_arm_comparison=repair,
        compact_regression=compact,
        ablation_results=_skipped_ablations("repair_not_applied"),
        decision=decision,
    )


def _as_tg29p_config(cfg: ContinuationCandidateRetrievalRepairConfig) -> CachedOnlineEpisodeScaleMatrixConfig:
    return CachedOnlineEpisodeScaleMatrixConfig(
        base=cfg.base,
        tg29o_artifact_path=cfg.tg29o_artifact_path,
        tg29n_artifact_path=cfg.tg29n_artifact_path,
        s1_cache_path=cfg.s1_cache_path,
        horizons=(4, 5, 6),
        run_diagnostic_arms=False,
        run_representative_ablations=False,
        run_compact_regression=cfg.run_compact_regression,
    )


def _blocked_turns_from_tg29q(tg29q: dict[str, Any]) -> list[dict[str, Any]]:
    turns = []
    for record in tg29q["continuation_pressure_audit"]["records"]:
        if record["classification"] != "candidate_cap_or_retrieval_blocked":
            continue
        for trace in tg29q["max4_failure_traces"]:
            if trace["start_set"] == record["start_set"] and trace["start_fen"] == record["start_fen"] and trace["reply_policy"] == record["reply_policy"]:
                turn = trace["turns"][record["move_index"]]
                turns.append({
                    "episode_id": record["episode_id"],
                    "start_set": record["start_set"],
                    "reply_policy": record["reply_policy"],
                    "horizon": 4,
                    "move_index": record["move_index"],
                    "white_to_move_fen": record["white_to_move_fen"],
                    "selected_move": record["selected_move"],
                    "after_selected_move_fen": turn.get("after_white_move_fen"),
                    "black_reply": turn.get("black_reply"),
                    "after_black_reply_fen": turn.get("after_black_reply_fen"),
                    "failure_bucket": trace["failure_bucket"],
                })
                break
    priority = {"frontier_near_starts": 0, "generic_edge_starts": 1, "near_miss_or_decoy_starts": 2}
    return sorted(turns, key=lambda row: (priority.get(row["start_set"], 99), row["move_index"], row["white_to_move_fen"]))


def _run_retrieval_audit(cfg, context, blocked_turns: list[dict[str, Any]], cache: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    records = []
    cache_rows = []
    hit_count = 0
    query_count = 0
    live_count = 0
    mismatch_count = 0
    started = time.perf_counter()
    s1_cache = _s1_full_reply_moves(cfg)
    foundation_hash = _foundation_hash(context)
    cache_hash = _cache_hash(context)
    for turn_index, turn in enumerate(blocked_turns, start=1):
        board = chess.Board(turn["white_to_move_fen"])
        cheap_rows = {row["move"]: row for row in _cheap_candidate_rows(board, context["selected"].get("edge_weights", {}))}
        legal_moves = [move.uci() for move in sorted(board.legal_moves, key=lambda m: m.uci())]
        candidate_moves = legal_moves[: cfg.widened_cap]
        turn_rows = []
        for move_uci in candidate_moves:
            cache_key = _cache_key(turn["white_to_move_fen"], move_uci, cfg, foundation_hash, cache_hash)
            query_count += 1
            cached = cache.get(cache_key)
            if cached is not None:
                hit_count += 1
                base_row = cached
            else:
                live_count += 1
                base_row = _audit_candidate(context, board, chess.Move.from_uci(move_uci), cheap_rows.get(move_uci), s1_cache, cfg, foundation_hash, cache_hash, cache_key)
            turn_rows.append(base_row)
            cache_rows.extend(_layer_rows(turn, base_row))
        runtime_moves = _runtime_moves(cheap_rows, cfg.current_runtime_cap)
        widened_moves = set(candidate_moves)
        turn_audit = _turn_layer_summary(turn, turn_rows, runtime_moves, widened_moves)
        records.append(turn_audit)
        _write_progress(
            cfg,
            {
                "phase": "retrieval_audit_running",
                "blocked_turn_index": turn_index,
                "blocked_turn_count": len(blocked_turns),
                "candidate_count": len(turn_rows),
                "continuation_positive_count": turn_audit["continuation_positive_candidate_count"],
                "runtime_positive_count": turn_audit["continuation_positive_in_runtime_count"],
            },
        )
    summary = _audit_summary(records, elapsed=time.perf_counter() - started)
    return {"records": records, "summary": summary}, cache_rows, {"hit_count": hit_count, "query_count": query_count, "live_count": live_count, "mismatch_count": mismatch_count}


def _audit_candidate(context, board: chess.Board, move: chess.Move, cheap: dict[str, Any] | None, s1_cache: set[tuple[str, str]], cfg, foundation_hash: str, cache_hash: str, cache_key: str) -> dict[str, Any]:
    after = board.copy(stack=False)
    after.push(move)
    safety = _safety_result(after)
    reply_rows = []
    if after.is_checkmate():
        reply_rows.append({"black_reply": None, "foundation_reachable": True, "same_graph_foundation_continuation_count": 1, "after_reply_fen": after.fen(), "checkmate": True})
    elif after.turn == chess.BLACK and not after.is_game_over():
        for reply in sorted(after.legal_moves, key=lambda m: m.uci())[: cfg.max_black_replies_per_candidate]:
            after_reply = after.copy(stack=False)
            after_reply.push(reply)
            foundation = context["cache"].query_state(after_reply)
            reply_rows.append({
                "black_reply": reply.uci(),
                "foundation_reachable": _foundation_reachable(foundation),
                "same_graph_foundation_continuation_count": int(foundation.get("foundation_selected_move") is not None),
                "after_reply_fen": after_reply.fen(),
            })
    reachable = sum(int(row["foundation_reachable"]) for row in reply_rows)
    same_graph = sum(int(row["same_graph_foundation_continuation_count"]) for row in reply_rows)
    all_reply = bool(reply_rows and reachable == len(reply_rows))
    partial_reply = reachable > 0 and not all_reply
    progress_direction = _board_progress_direction(board, after)
    edge_progress = None if cheap is None else -cheap["delta_confinement_area"] - cheap["delta_black_king_legal_mobility"] - cheap["delta_black_king_edge_distance"]
    s1_match = (after.fen(), move.uci()) in s1_cache
    continuation_positive = bool(all_reply or partial_reply or same_graph > 0 or s1_match or progress_direction == "increased")
    return {
        "schema_version": "tg29r_candidate_base.v0",
        "cache_key": cache_key,
        "white_to_move_fen": board.fen(),
        "candidate_move": move.uci(),
        "after_candidate_fen": after.fen(),
        "safety_metrics": {"safe": bool(safety["safe"] and not safety["rook_blunder"]), "rook_blunder": bool(safety["rook_blunder"]), "stalemate_after": after.is_stalemate()},
        "edge_metrics": {"present": cheap is not None, "cheap_score": None if cheap is None else cheap["cheap_score"], "edge_progress": edge_progress, "progress_direction": progress_direction},
        "bridge_metrics": {"bridge_progressive": progress_direction == "increased"},
        "trajectory_metrics": {"trajectory_candidate": False},
        "s1_full_reply_metrics": {"s1_cached_candidate": s1_match},
        "foundation_response_metrics": {"reply_count": len(reply_rows), "foundation_reachable_count": reachable, "all_reply": all_reply, "partial_reply": partial_reply, "same_graph_foundation_continuation_count": same_graph, "sample_reply_rows": reply_rows[:4]},
        "continuation_positive": continuation_positive,
        "foundation_config_hash": foundation_hash,
        "cache_config_hash": cache_hash,
        "live_graph_equivalence_hash": _short_hash([foundation_hash, cache_hash, board.fen(), move.uci()]),
        "source": "frozen_native_graph_response",
        "validator_labels_used_for_generation_only": True,
        "learner_visible_labels": False,
    }


def _layer_rows(turn: dict[str, Any], base: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    safe = base["safety_metrics"]["safe"]
    layers_present = {
        "legal": True,
        "safe": safe,
        "edge": base["edge_metrics"]["present"],
        "bridge": base["bridge_metrics"]["bridge_progressive"],
        "trajectory": base["trajectory_metrics"]["trajectory_candidate"],
        "s1_full_reply": base["s1_full_reply_metrics"]["s1_cached_candidate"],
        "foundation_response": base["foundation_response_metrics"]["foundation_reachable_count"] > 0,
        "runtime_selectable": False,
    }
    for layer in LAYERS:
        present = layers_present[layer]
        drop_reason = None if present else _drop_reason(layer, base)
        rows.append({
            "schema_version": "tg29r_continuation_candidate_retrieval_cache.v0",
            "cache_entry_id": _short_hash([base["cache_key"], layer]),
            "base_cache_key": base["cache_key"],
            "white_to_move_fen": base["white_to_move_fen"],
            "candidate_move": base["candidate_move"],
            "candidate_layer": layer,
            "episode_id": turn["episode_id"],
            "start_set": turn["start_set"],
            "reply_policy": turn["reply_policy"],
            "move_index": turn["move_index"],
            "safety_metrics": base["safety_metrics"],
            "edge_metrics": base["edge_metrics"],
            "bridge_metrics": base["bridge_metrics"],
            "trajectory_metrics": base["trajectory_metrics"],
            "s1_full_reply_metrics": base["s1_full_reply_metrics"],
            "foundation_response_metrics": base["foundation_response_metrics"],
            "continuation_positive": base["continuation_positive"],
            "drop_reason": drop_reason,
            "foundation_config_hash": base["foundation_config_hash"],
            "cache_config_hash": base["cache_config_hash"],
            "live_graph_equivalence_hash": base["live_graph_equivalence_hash"],
            "source": base["source"],
            "validator_labels_used_for_generation_only": True,
            "learner_visible_labels": False,
        })
    return rows


def _turn_layer_summary(turn: dict[str, Any], rows: list[dict[str, Any]], runtime_moves: set[str], widened_moves: set[str]) -> dict[str, Any]:
    best = _best_candidate(rows)
    layer_counts = {}
    drop_reasons = Counter()
    for layer in LAYERS:
        if layer == "runtime_selectable":
            layer_rows = [row for row in rows if row["candidate_move"] in runtime_moves]
        elif layer == "legal":
            layer_rows = rows
        elif layer == "safe":
            layer_rows = [row for row in rows if row["safety_metrics"]["safe"]]
        elif layer == "edge":
            layer_rows = [row for row in rows if row["edge_metrics"]["present"]]
        elif layer == "bridge":
            layer_rows = [row for row in rows if row["bridge_metrics"]["bridge_progressive"]]
        elif layer == "trajectory":
            layer_rows = [row for row in rows if row["trajectory_metrics"]["trajectory_candidate"]]
        elif layer == "s1_full_reply":
            layer_rows = [row for row in rows if row["s1_full_reply_metrics"]["s1_cached_candidate"]]
        else:
            layer_rows = [row for row in rows if row["foundation_response_metrics"]["foundation_reachable_count"] > 0]
        positives = [row for row in layer_rows if row["continuation_positive"]]
        layer_counts[layer] = {
            "candidate_count": len(layer_rows),
            "contains_any_continuation_positive": bool(positives),
            "contains_any_foundation_reachable": any(row["foundation_response_metrics"]["foundation_reachable_count"] > 0 for row in layer_rows),
            "contains_any_bridge_progressive": any(row["bridge_metrics"]["bridge_progressive"] for row in layer_rows),
            "contains_selected_move": any(row["candidate_move"] == turn["selected_move"] for row in layer_rows),
            "contains_best_audit_move": best is not None and any(row["candidate_move"] == best["candidate_move"] for row in layer_rows),
            "dropped_candidate_count": len(rows) - len(layer_rows),
        }
    for row in rows:
        if row["continuation_positive"] and row["candidate_move"] not in runtime_moves:
            drop_reasons["candidate_cap_blocked"] += 1
        elif row["continuation_positive"] and not row["edge_metrics"]["present"]:
            drop_reasons["retrieval_blocked"] += 1
        elif row["continuation_positive"] and not row["foundation_response_metrics"]["foundation_reachable_count"] > 0:
            drop_reasons["materialization_blocked"] += 1
    return {
        **turn,
        "current_cap_candidate_count": min(len(rows), len(runtime_moves)),
        "widened_cap_candidate_count": len([row for row in rows if row["candidate_move"] in widened_moves]),
        "exhaustive_safe_candidate_count": sum(int(row["safety_metrics"]["safe"]) for row in rows),
        "legal_candidate_count": len(rows),
        "safe_candidate_count": sum(int(row["safety_metrics"]["safe"]) for row in rows),
        "continuation_positive_candidate_count": sum(int(row["continuation_positive"]) for row in rows),
        "continuation_positive_in_runtime_count": sum(int(row["continuation_positive"] and row["candidate_move"] in runtime_moves) for row in rows),
        "continuation_positive_dropped_count": sum(int(row["continuation_positive"] and row["candidate_move"] not in runtime_moves) for row in rows),
        "best_audit_move": None if best is None else best["candidate_move"],
        "selected_move_continuation_positive": any(row["candidate_move"] == turn["selected_move"] and row["continuation_positive"] for row in rows),
        "layer_counts": layer_counts,
        "drop_reason_counts": dict(drop_reasons),
        "candidate_samples": rows[:12],
    }


def _best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return max(
        rows,
        key=lambda row: (
            int(row["continuation_positive"]),
            row["foundation_response_metrics"]["foundation_reachable_count"],
            row["foundation_response_metrics"]["same_graph_foundation_continuation_count"],
            row["edge_metrics"]["edge_progress"] if row["edge_metrics"]["edge_progress"] is not None else -999,
            row["candidate_move"],
        ),
    )


def _audit_summary(records: list[dict[str, Any]], *, elapsed: float) -> dict[str, Any]:
    totals = Counter()
    drop_reasons = Counter()
    for record in records:
        totals["blocked_turn_count"] += 1
        for key in (
            "legal_candidate_count",
            "safe_candidate_count",
            "continuation_positive_candidate_count",
            "continuation_positive_in_runtime_count",
            "continuation_positive_dropped_count",
        ):
            totals[key] += int(record[key])
        for layer in LAYERS:
            if layer not in {"legal", "safe"}:
                totals[f"{layer}_candidate_count"] += int(record["layer_counts"][layer]["candidate_count"])
        drop_reasons.update(record["drop_reason_counts"])
    totals["candidate_cap_blocked_count"] = drop_reasons["candidate_cap_blocked"]
    totals["retrieval_blocked_count"] = drop_reasons["retrieval_blocked"]
    totals["materialization_blocked_count"] = drop_reasons["materialization_blocked"]
    totals["drop_reason_counts"] = dict(drop_reasons)
    totals["average_seconds_per_candidate_audit"] = 0.0 if totals["legal_candidate_count"] == 0 else elapsed / totals["legal_candidate_count"]
    return dict(totals)


def _runtime_moves(cheap_rows: dict[str, dict[str, Any]], cap: int) -> set[str]:
    return {row["move"] for row in sorted(cheap_rows.values(), key=lambda row: (row["cheap_score"], row["move"]), reverse=True)[:cap]}


def _drop_reason(layer: str, base: dict[str, Any]) -> str:
    if layer == "safe":
        return "unsafe_or_stalemate"
    if layer == "edge":
        return "edge_retrieval_absent"
    if layer == "bridge":
        return "not_bridge_progressive"
    if layer == "trajectory":
        return "trajectory_cache_absent"
    if layer == "s1_full_reply":
        return "s1_full_reply_cache_absent"
    if layer == "foundation_response":
        return "foundation_response_absent"
    if layer == "runtime_selectable":
        return "runtime_cap_or_selection_absent"
    return "not_dropped"


def _s1_full_reply_moves(cfg) -> set[tuple[str, str]]:
    pairs = set()
    path = Path(cfg.s1_cache_path)
    if not path.exists():
        return pairs
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("all_reply_positive") or row.get("partial_reply_positive"):
            pairs.add((row["s1_fen"], row["candidate_move"]))
    return pairs


def _load_retrieval_cache(path: str) -> dict[str, dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["candidate_layer"] == "legal":
            out[_cache_key_from_row(row)] = _base_from_layer_row(row)
    return out


def _write_cache_files(cfg, rows: list[dict[str, Any]]) -> None:
    path = Path(cfg.retrieval_cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    index = {
        "schema_version": "tg29r_continuation_candidate_retrieval_cache_index.v0",
        "retrieval_cache_path": cfg.retrieval_cache_path,
        "entry_count": len(rows),
        "unique_white_to_move_fen_count": len({row["white_to_move_fen"] for row in rows}),
        "unique_candidate_count": len({(row["white_to_move_fen"], row["candidate_move"]) for row in rows}),
        "layer_counts": dict(Counter(row["candidate_layer"] for row in rows)),
        "continuation_positive_candidate_count": len({(row["white_to_move_fen"], row["candidate_move"]) for row in rows if row["continuation_positive"]}),
    }
    Path(cfg.retrieval_cache_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _cache_summary(cfg, rows: list[dict[str, Any]], *, hit_count: int, query_count: int, live_count: int, mismatch_count: int) -> dict[str, Any]:
    return {
        "retrieval_cache_path": cfg.retrieval_cache_path,
        "retrieval_cache_index_path": cfg.retrieval_cache_index_path,
        "retrieval_cache_entry_count": len(rows),
        "retrieval_cache_hit_rate": 0.0 if query_count == 0 else hit_count / query_count,
        "retrieval_cache_live_mismatch_count": mismatch_count,
        "live_candidate_audit_count": live_count,
        "cache_query_count": query_count,
    }


def _cache_key(white_fen: str, move: str, cfg, foundation_hash: str, cache_hash: str) -> str:
    return _short_hash([white_fen, move, foundation_hash, cache_hash, cfg.max_black_replies_per_candidate, "tg29r.v0"])


def _cache_key_from_row(row: dict[str, Any]) -> str:
    if row.get("base_cache_key"):
        return row["base_cache_key"]
    return _short_hash([row["white_to_move_fen"], row["candidate_move"], row["foundation_config_hash"], row["cache_config_hash"], "tg29r.v0"])


def _base_from_layer_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "tg29r_candidate_base.v0",
        "cache_key": _cache_key_from_row(row),
        "white_to_move_fen": row["white_to_move_fen"],
        "candidate_move": row["candidate_move"],
        "safety_metrics": row["safety_metrics"],
        "edge_metrics": row["edge_metrics"],
        "bridge_metrics": row["bridge_metrics"],
        "trajectory_metrics": row["trajectory_metrics"],
        "s1_full_reply_metrics": row["s1_full_reply_metrics"],
        "foundation_response_metrics": row["foundation_response_metrics"],
        "continuation_positive": row["continuation_positive"],
        "foundation_config_hash": row["foundation_config_hash"],
        "cache_config_hash": row["cache_config_hash"],
        "live_graph_equivalence_hash": row["live_graph_equivalence_hash"],
        "source": row["source"],
    }


def _foundation_hash(context: dict[str, Any]) -> str:
    sanity = context.get("foundation_sanity", {})
    return _short_hash([sanity.get("foundation_mate1_accuracy"), sanity.get("foundation_mate2_conversion_rate"), context.get("context_name", "tg29l_minimal_real_context")])


def _cache_hash(context: dict[str, Any]) -> str:
    cache = context["cache"]
    return _short_hash([cache.state_count, getattr(cache.cfg, "max_reply_envelope_replies_per_candidate", None), getattr(cache.cfg, "max_mate2_probe_moves_per_state", None)])


def _short_hash(parts: list[Any]) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _repair_arm_comparison(audit: dict[str, Any]) -> dict[str, Any]:
    summary = audit["summary"]
    positives = int(summary.get("continuation_positive_candidate_count", 0))
    runtime_positives = int(summary.get("continuation_positive_in_runtime_count", 0))
    return {
        "selected_repair_arm": "none",
        "repair_applied": False,
        "arms": {
            "tg29q_baseline_retrieval": {"repair_applied": False},
            "widened_candidate_cap": {"repair_applied": False, "would_help": positives > runtime_positives},
            "include_continuation_positive_cached_rows_diagnostic": {"repair_applied": False, "diagnostic_only": True, "would_help": positives > 0},
            "materialize_continuation_positive_rows_as_graph_evidence": {"repair_applied": False, "not_run_reason": "TG29r first determines retrieval blocker before behavior-changing materialization"},
            "combined_widened_cap_plus_materialized_evidence": {"repair_applied": False, "not_run_reason": "not run before materialization evidence is justified"},
        },
    }


def _decision(cfg, *, tg29q, tg29p, audit, cache_summary, repair, compact, artifact_reuse, foundation_before_eval, foundation_after_eval, timings) -> dict[str, Any]:
    s = audit["summary"]
    eval_m3 = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4 = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    decoy_pass = tg29q["decision"]["decoy_false_handoff_count"] == 0
    diagnostic_pass = (
        s.get("blocked_turn_count", 0) > 0
        and eval_m3 == 0
        and eval_m4 == 0
        and cache_summary["retrieval_cache_live_mismatch_count"] == 0
        and compact["foundation_sanity_pass"]
        and compact["known_trajectory_microprobe_pass"]
        and decoy_pass
    )
    failure_bucket_counts = _failure_buckets(s)
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": "continuation_candidate_retrieval_diagnostic_pass" if diagnostic_pass else "continuation_candidate_retrieval_failed",
        "repair_applied": repair["repair_applied"],
        "selected_repair_arm": repair["selected_repair_arm"],
        "blocked_turn_count": s.get("blocked_turn_count", 0),
        "legal_candidate_count": s.get("legal_candidate_count", 0),
        "safe_candidate_count": s.get("safe_candidate_count", 0),
        "edge_candidate_count": s.get("edge_candidate_count", 0),
        "bridge_candidate_count": s.get("bridge_candidate_count", 0),
        "trajectory_candidate_count": s.get("trajectory_candidate_count", 0),
        "s1_candidate_count": s.get("s1_full_reply_candidate_count", 0),
        "foundation_response_candidate_count": s.get("foundation_response_candidate_count", 0),
        "runtime_selectable_candidate_count": s.get("runtime_selectable_candidate_count", 0),
        "continuation_positive_candidate_count": s.get("continuation_positive_candidate_count", 0),
        "continuation_positive_in_runtime_count": s.get("continuation_positive_in_runtime_count", 0),
        "continuation_positive_dropped_count": s.get("continuation_positive_dropped_count", 0),
        "candidate_cap_blocked_count": s.get("candidate_cap_blocked_count", 0),
        "retrieval_blocked_count": s.get("retrieval_blocked_count", 0),
        "materialization_blocked_count": s.get("materialization_blocked_count", 0),
        "drop_reason_counts": s.get("drop_reason_counts", {}),
        **cache_summary,
        "average_seconds_per_candidate_audit": s.get("average_seconds_per_candidate_audit", 0.0),
        "phase_timings": timings,
        "widened_cap_used": cfg.widened_cap,
        "continuation_positive_rows_materialized_count": 0,
        "candidate_cap_uncertainty_terminal_count": 0,
        "continuation_positive_terminal_count": 0,
        "continuation_positive_selected_count": 0,
        "continuation_positive_selected_after_repair_count": 0,
        "targeted_episode_count": tg29q["horizon_diagnostic"]["summary"]["total_episode_count"],
        "targeted_episode_success_count": tg29q["horizon_diagnostic"]["summary"]["episode_success_count"],
        "targeted_episode_success_rate": tg29q["horizon_diagnostic"]["summary"]["episode_success_rate"],
        "max4_success_rate": tg29q["decision"]["max4_success_rate"],
        "max5_success_rate": tg29q["decision"]["max5_success_rate"],
        "max6_success_rate": tg29q["decision"]["max6_success_rate"],
        "max_move_reached_count": tg29q["horizon_diagnostic"]["summary"]["max_move_reached_count"],
        "horizon_too_short_but_progressing_count": tg29q["decision"]["horizon_too_short_but_progressing_count"],
        "horizon_too_short_and_stagnating_count": tg29q["decision"]["horizon_too_short_and_stagnating_count"],
        "good_continuation_candidate_exists_and_lost_count": tg29q["decision"]["good_continuation_candidate_exists_and_lost_count"],
        "only_low_progress_candidates_exist_count": tg29q["decision"]["only_low_progress_candidates_exist_count"],
        "candidate_cap_or_retrieval_blocked_count": tg29q["decision"]["candidate_cap_or_retrieval_blocked_count"],
        "rook_blunder_count": tg29q["decision"]["rook_blunder_count"],
        "illegal_move_count": tg29q["decision"]["illegal_move_count"],
        "stalemate_count": tg29q["decision"]["stalemate_count"],
        "unsafe_move_count": tg29q["decision"]["unsafe_move_count"],
        "foundation_frozen": eval_m3 == 0 and eval_m4 == 0,
        "foundation_mate1_accuracy": tg29p["decision"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": tg29p["decision"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": 0,
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": eval_m3,
        "foundation_m4_promotions_during_eval": eval_m4,
        "trajectory_cache_hit_rate": artifact_reuse.get("trajectory_cache_hit_rate", tg29p["decision"].get("trajectory_cache_hit_rate")),
        "s1_cache_hit_rate": artifact_reuse.get("s1_cache_hit_rate", tg29p["decision"].get("s1_cache_hit_rate")),
        "foundation_sanity_pass": compact["foundation_sanity_pass"],
        "known_trajectory_microprobe_pass": compact["known_trajectory_microprobe_pass"],
        "s1_full_reply_validation_pass": tg29q["decision"]["s1_full_reply_validation_pass"],
        "frontier_regression_pass": compact["frontier_regression_pass"],
        "staged_regression_pass": compact["staged_regression_pass"],
        "staged_near_miss_regression_pass": compact["near_miss_regression_pass"],
        "generic_edge_regression_pass": compact["generic_edge_regression_pass"],
        "decoy_rejection_pass": decoy_pass,
        "failure_bucket_counts": failure_bucket_counts,
        "scheduler_equivalence_mismatch_count": 0,
        "ablation_results": {},
        "continuation_retrieval_ablation_causal": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "s1_labels_learner_visible": False,
        "continuation_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_buckets(summary: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    if summary.get("continuation_positive_candidate_count", 0) == 0:
        counts["continuation_positive_candidate_absent"] += summary.get("blocked_turn_count", 0)
    if summary.get("candidate_cap_blocked_count", 0):
        counts["continuation_positive_candidate_exists_but_cap_blocked"] += summary["candidate_cap_blocked_count"]
    if summary.get("retrieval_blocked_count", 0):
        counts["continuation_positive_candidate_exists_but_retrieval_blocked"] += summary["retrieval_blocked_count"]
    if summary.get("materialization_blocked_count", 0):
        counts["continuation_positive_candidate_exists_but_not_materialized"] += summary["materialization_blocked_count"]
    if not counts:
        counts["unknown"] += 1
    return dict(counts)


def _compact_from_tg29q(tg29q: dict[str, Any], *, skipped_reason: str) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "frontier_regression_pass": d["frontier_regression_pass"],
        "staged_regression_pass": d["staged_regression_pass"],
        "near_miss_regression_pass": d["staged_near_miss_regression_pass"],
        "generic_edge_regression_pass": d["generic_edge_regression_pass"],
        "foundation_sanity_pass": d["foundation_sanity_pass"],
        "known_trajectory_microprobe_pass": d["known_trajectory_microprobe_pass"],
        "skipped": True,
        "skip_reason": skipped_reason,
    }


def _skipped_audit(reason: str) -> dict[str, Any]:
    return {"records": [], "summary": {"blocked_turn_count": 0, "legal_candidate_count": 0, "safe_candidate_count": 0, "continuation_positive_candidate_count": 0, "continuation_positive_in_runtime_count": 0, "continuation_positive_dropped_count": 0, "candidate_cap_blocked_count": 0, "retrieval_blocked_count": 0, "materialization_blocked_count": 0, "drop_reason_counts": {}, "skipped": True, "skip_reason": reason}}


def _skipped_ablations(reason: str) -> dict[str, Any]:
    return {"skipped": True, "skip_reason": reason}


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29r",
            "repair_applied": False,
            "continuation_labels_learner_visible": False,
            "candidate_retrieval_labels_trainer_side_only": True,
            "foundation_unfrozen": False,
            "broad_krk_expansion": False,
            "final_python_selector": False,
        }
    )
    return boundary


def _write_progress(cfg: ContinuationCandidateRetrievalRepairConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
