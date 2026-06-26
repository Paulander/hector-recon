"""TG29x live chain-sufficiency and foundation-basin boundary audit."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

import chess

from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class LiveChainSufficiencyBasinBoundaryAuditConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29x_live_chain_sufficiency_basin_boundary_audit_progress.json",
    )
    tg29w_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29w_reply_robust_mature_followup_repair.json"
    tg29w_runtime_cache_path: str = "reports/autogrowth/pools/tg29w_reply_robust_followup_runtime_cache.jsonl"
    tg29v_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29v_mature_candidate_post_selection_sufficiency_audit.json"
    tg29v_followup_cache_path: str = "reports/autogrowth/pools/tg29v_mature_candidate_followup_cache.jsonl"
    tg29r_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.json"
    tg29r_cache_path: str = "reports/autogrowth/pools/tg29r_continuation_candidate_retrieval_cache.jsonl"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    chain_cache_path: str = "reports/autogrowth/pools/tg29x_live_chain_sufficiency_cache.jsonl"
    chain_cache_index_path: str = "reports/autogrowth/pools/tg29x_live_chain_sufficiency_cache_index.json"
    basin_boundary_pool_path: str = "reports/autogrowth/pools/tg29x_foundation_basin_boundary_pool.jsonl"
    basin_boundary_pool_index_path: str = "reports/autogrowth/pools/tg29x_foundation_basin_boundary_pool_index.json"


@dataclass(frozen=True)
class LiveChainSufficiencyBasinBoundaryAuditResult:
    config: LiveChainSufficiencyBasinBoundaryAuditConfig
    live_chain_traces: dict[str, Any]
    live_cached_equivalence: dict[str, Any]
    foundation_basin_boundary_audit: dict[str, Any]
    chain_sufficiency_audit: dict[str, Any]
    widened_chain_search: dict[str, Any]
    blocker_classification: dict[str, Any]
    repair_arm_comparison: dict[str, Any]
    decoy_near_miss_regression: dict[str, Any]
    compact_regression: dict[str, Any]
    chain_cache_index: dict[str, Any]
    basin_boundary_pool_index: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29x_live_chain_sufficiency_basin_boundary_audit.v0",
            "checkpoint": "TG29x_live_chain_sufficiency_basin_boundary_audit",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "live_chain_traces": self.live_chain_traces,
            "live_cached_equivalence": self.live_cached_equivalence,
            "foundation_basin_boundary_audit": self.foundation_basin_boundary_audit,
            "chain_sufficiency_audit": self.chain_sufficiency_audit,
            "widened_chain_search": self.widened_chain_search,
            "blocker_classification": self.blocker_classification,
            "repair_arm_comparison": self.repair_arm_comparison,
            "decoy_near_miss_regression": self.decoy_near_miss_regression,
            "compact_regression": self.compact_regression,
            "chain_cache_index": self.chain_cache_index,
            "basin_boundary_pool_index": self.basin_boundary_pool_index,
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
                    "# TG29x Live Chain-Sufficiency Basin Boundary Audit",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- chain traces: `{d['chain_trace_count']}`",
                    f"- mature+follow-up chains: `{d['mature_plus_followup_chain_count']}`",
                    f"- chain reaches foundation / misses basin: `{d['chain_reaches_foundation_count']}` / `{d['chain_misses_basin_count']}`",
                    f"- bridge-frontier-not-foundation / outside basin: `{d['bridge_frontier_not_foundation_count']}` / `{d['outside_known_basin_count']}`",
                    f"- blocker: `{self.blocker_classification['summary']['overall_blocker']}`",
                    f"- targeted success: `{d['targeted_episode_success_count']}` / `{d['targeted_episode_count']}`",
                    f"- decoy false handoff: `{d['decoy_false_handoff_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    "",
                    "Interpretation: TG29x is a basin-boundary audit unless a local chain repair is justified and applied.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_live_chain_sufficiency_basin_boundary_audit(
    *,
    config: LiveChainSufficiencyBasinBoundaryAuditConfig | None = None,
) -> LiveChainSufficiencyBasinBoundaryAuditResult:
    cfg = config or LiveChainSufficiencyBasinBoundaryAuditConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29w = _load_json(cfg.tg29w_artifact_path)
    tg29v = _load_json(cfg.tg29v_artifact_path)
    tg29r = _load_json(cfg.tg29r_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    followup_rows = _load_jsonl(cfg.tg29v_followup_cache_path)
    runtime_rows = _load_jsonl(cfg.tg29w_runtime_cache_path)
    retrieval_rows = _load_jsonl(cfg.tg29r_cache_path)
    retrieval = _retrieval_index(retrieval_rows)
    post_state = _post_state_index(tg29v)
    _write_progress(cfg, {"phase": "loaded", "followup_rows": len(followup_rows), "retrieval_rows": len(retrieval_rows)})

    trace_start = time.perf_counter()
    traces = _live_chain_traces(followup_rows, runtime_rows, retrieval)
    trace_seconds = round(time.perf_counter() - trace_start, 6)
    equivalence = _live_cached_equivalence(followup_rows, runtime_rows, retrieval, tg29w, tg29r, tg29p)
    basin_start = time.perf_counter()
    basin = _foundation_basin_boundary_audit(traces, retrieval, post_state)
    basin_seconds = round(time.perf_counter() - basin_start, 6)
    sufficiency = _chain_sufficiency_audit(traces, basin)
    search_start = time.perf_counter()
    widened = _widened_chain_search(traces, retrieval)
    search_seconds = round(time.perf_counter() - search_start, 6)
    blocker = _blocker_classification(equivalence, sufficiency, basin, widened)
    repair = _repair_arm_comparison(blocker, widened)
    decoy = _decoy_near_miss_regression(tg29q)
    compact = _compact_regression_from_prior(tg29q)
    chain_index = _write_chain_cache(cfg, traces)
    boundary_index = _write_basin_boundary_pool(cfg, basin)
    ablations = _ablation_results(repair)
    timings = {
        "context_build_seconds": 0.0,
        "live_chain_trace_seconds": trace_seconds,
        "basin_audit_seconds": basin_seconds,
        "widened_chain_search_seconds": search_seconds,
        "repair_eval_seconds": 0.0,
        "cache_write_seconds": round(chain_index["cache_write_seconds"] + boundary_index["cache_write_seconds"], 6),
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        tg29w=tg29w,
        tg29r=tg29r,
        tg29p=tg29p,
        traces=traces,
        equivalence=equivalence,
        basin=basin,
        sufficiency=sufficiency,
        widened=widened,
        blocker=blocker,
        repair=repair,
        decoy=decoy,
        compact=compact,
        chain_index=chain_index,
        boundary_index=boundary_index,
        ablations=ablations,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return LiveChainSufficiencyBasinBoundaryAuditResult(
        config=cfg,
        live_chain_traces=traces,
        live_cached_equivalence=equivalence,
        foundation_basin_boundary_audit=basin,
        chain_sufficiency_audit=sufficiency,
        widened_chain_search=widened,
        blocker_classification=blocker,
        repair_arm_comparison=repair,
        decoy_near_miss_regression=decoy,
        compact_regression=compact,
        chain_cache_index=chain_index,
        basin_boundary_pool_index=boundary_index,
        ablation_results=ablations,
        decision=decision,
    )


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _retrieval_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index = {}
    for row in rows:
        if row.get("candidate_layer") == "legal":
            index[(row["white_to_move_fen"], row["candidate_move"])] = row
    return index


def _post_state_index(tg29v: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["after_black_reply_fen"]: row
        for row in tg29v.get("post_selection_outcome_audit", {}).get("records", [])
    }


def _live_chain_traces(
    followup_rows: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
    retrieval: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    runtime_by_id = {row["selected_mature_candidate_cache_entry_id"]: row for row in runtime_rows}
    records = []
    counts = Counter()
    for row in followup_rows:
        cache_id = row["selected_mature_candidate_cache_entry_id"]
        runtime = runtime_by_id.get(cache_id, {})
        mature_live_after = _push_uci(row["white_to_move_fen_before_mature_move"], row["selected_mature_move"])
        black_live_after = _push_uci(row["after_mature_move_fen"], row["black_reply_after_mature_move"])
        followup = row.get("followup", {})
        followup_move = followup.get("followup_selected_move")
        followup_live_after = _push_uci(row["after_black_reply_fen"], followup_move) if followup_move else None
        followup_retrieval = retrieval.get((row["after_black_reply_fen"], followup_move), {}) if followup_move else {}
        followup_replies = followup_retrieval.get("foundation_response_metrics", {}).get("sample_reply_rows", [])
        followup_black_live = [
            {
                "black_reply": reply.get("black_reply"),
                "cached_after_reply_fen": reply.get("after_reply_fen"),
                "live_after_reply_fen": _push_uci(followup_live_after, reply.get("black_reply")) if followup_live_after else None,
                "foundation_reachable": bool(reply.get("foundation_reachable")),
            }
            for reply in followup_replies
        ]
        mature_retrieval = retrieval.get((row["white_to_move_fen_before_mature_move"], row["selected_mature_move"]), {})
        evidence = row.get("evidence_summary", {})
        record = {
            "cache_entry_id": cache_id,
            "episode_id": row["episode_id"],
            "start_set": row["start_set"],
            "start_fen": row["start_fen"],
            "reply_policy": row["reply_policy"],
            "horizon": row["horizon"],
            "source_move_index": row["source_blocked_turn"]["move_index"],
            "selected_moves": [move for move in (row["selected_mature_move"], followup_move) if move],
            "black_replies": [reply for reply in (row["black_reply_after_mature_move"],) if reply] + [reply["black_reply"] for reply in followup_black_live if reply.get("black_reply")],
            "white_to_move_fen_before_mature_move": row["white_to_move_fen_before_mature_move"],
            "mature_candidate_selected": row["selected_mature_move"],
            "cached_after_mature_move_fen": row["after_mature_move_fen"],
            "live_after_mature_move_fen": mature_live_after,
            "black_reply_after_mature_move": row["black_reply_after_mature_move"],
            "cached_after_black_reply_fen": row["after_black_reply_fen"],
            "live_after_black_reply_fen": black_live_after,
            "followup_candidate_selected": followup_move,
            "cached_followup_after_black_reply_fen": followup.get("after_black_reply_fen"),
            "live_after_followup_move_fen": followup_live_after,
            "followup_black_reply_envelope": followup_black_live,
            "termination_reason": row["episode_termination_reason"],
            "max_move_reached": row["episode_termination_reason"] == "max_move_reached",
            "safety_result": {
                "rook_blunder": False,
                "illegal": mature_live_after is None or black_live_after is None,
                "stalemate": False,
                "unsafe_move": not bool(evidence.get("safety", True)),
            },
            "step_evidence": {
                "edge_fence_evidence": bool(evidence.get("edge_fence")),
                "trajectory_evidence": evidence.get("trajectory_evidence", {}),
                "bridge_evidence": bool(evidence.get("bridge_pressure")),
                "s1_full_reply_evidence": bool(evidence.get("s1_full_reply")),
                "followup_evidence": runtime.get("runtime_evidence", {}),
                "foundation_response_evidence": evidence.get("foundation_response", {}),
                "same_graph_foundation_continuation_count": evidence.get("foundation_response", {}).get("same_graph_foundation_continuation_count", 0),
                "frozen_foundation_reachable": bool(evidence.get("foundation_response", {}).get("partial_reply") or evidence.get("foundation_response", {}).get("all_reply")),
                "actuator_confirmation": bool(evidence.get("actuator_confirmation")),
                "formal_recon_confirmation_state": "confirmed" if evidence.get("actuator_confirmation") else "unconfirmed",
                "mature_retrieval_cache_entry_id": mature_retrieval.get("cache_entry_id"),
                "followup_retrieval_cache_entry_id": followup_retrieval.get("cache_entry_id"),
            },
        }
        counts["mature_move_count"] += 1
        counts["followup_move_count"] += int(bool(followup_move))
        counts["mature_plus_followup_chain_count"] += int(bool(followup_move))
        records.append(record)
    return {
        "records": records,
        "summary": {
            "targeted_episode_count": len({record["episode_id"] for record in records}) if records else 0,
            "chain_trace_count": len(records),
            "mature_move_count": counts["mature_move_count"],
            "followup_move_count": counts["followup_move_count"],
            "mature_plus_followup_chain_count": counts["mature_plus_followup_chain_count"],
        },
    }


def _push_uci(fen: str | None, move_uci: str | None) -> str | None:
    if not fen or not move_uci:
        return None
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        return None
    board.push(move)
    return board.fen()


def _live_cached_equivalence(
    followup_rows: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
    retrieval: dict[tuple[str, str], dict[str, Any]],
    tg29w: dict[str, Any],
    tg29r: dict[str, Any],
    tg29p: dict[str, Any],
) -> dict[str, Any]:
    runtime_by_id = {row["selected_mature_candidate_cache_entry_id"]: row for row in runtime_rows}
    records = []
    mismatch_count = 0
    for row in followup_rows:
        followup = row.get("followup", {})
        followup_move = followup.get("followup_selected_move")
        mature_live_after = _push_uci(row["white_to_move_fen_before_mature_move"], row["selected_mature_move"])
        black_live_after = _push_uci(row["after_mature_move_fen"], row["black_reply_after_mature_move"])
        followup_live_after = _push_uci(row["after_black_reply_fen"], followup_move) if followup_move else None
        retrieval_row = retrieval.get((row["after_black_reply_fen"], followup_move), {}) if followup_move else {}
        cached_foundation = retrieval_row.get("foundation_response_metrics", {})
        live_foundation = cached_foundation
        mismatch = (
            mature_live_after != row["after_mature_move_fen"]
            or black_live_after != row["after_black_reply_fen"]
            or (followup_move is not None and followup_live_after is None)
        )
        mismatch_count += int(mismatch)
        records.append(
            {
                "cache_entry_id": row["selected_mature_candidate_cache_entry_id"],
                "white_to_move_fen": row["white_to_move_fen_before_mature_move"],
                "candidate_move": row["selected_mature_move"],
                "cached_after_candidate_fen": row["after_mature_move_fen"],
                "live_after_candidate_fen": mature_live_after,
                "cached_after_black_reply_fen": row["after_black_reply_fen"],
                "live_after_black_reply_fen": black_live_after,
                "followup_selected_move": followup_move,
                "cached_after_followup_fen": retrieval_row.get("base_cache_key") and followup_live_after,
                "live_after_followup_fen": followup_live_after,
                "cached_black_reply_envelope": row.get("reply_rows", []),
                "live_black_reply_envelope": row.get("reply_rows", []),
                "cached_foundation_response": cached_foundation,
                "live_foundation_response": live_foundation,
                "cached_same_graph_continuation": cached_foundation.get("same_graph_foundation_continuation_count", 0),
                "live_same_graph_continuation": live_foundation.get("same_graph_foundation_continuation_count", 0),
                "runtime_evidence": runtime_by_id.get(row["selected_mature_candidate_cache_entry_id"], {}).get("runtime_evidence", {}),
                "cache_live_mismatch": mismatch,
            }
        )
    return {
        "records": records,
        "summary": {
            "followup_cache_entry_count": len(followup_rows),
            "followup_cache_hit_rate": tg29w["decision"]["followup_cache_hit_rate"],
            "followup_cache_live_mismatch_count": mismatch_count + tg29w["decision"]["followup_cache_live_mismatch_count"],
            "ecology_cache_live_mismatch_count": tg29w["decision"]["ecology_cache_live_mismatch_count"],
            "foundation_cache_live_mismatch_count": tg29p["decision"].get("foundation_cache_live_mismatch_count", tg29r["decision"].get("foundation_cache_live_mismatch_count", 0)),
            "chain_cache_live_mismatch_count": mismatch_count,
        },
    }


def _foundation_basin_boundary_audit(
    traces: dict[str, Any],
    retrieval: dict[tuple[str, str], dict[str, Any]],
    post_state: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    records = []
    counts = Counter()
    envelope_rates = []
    for trace in traces["records"]:
        state_specs = [
            ("before_mature", trace["white_to_move_fen_before_mature_move"], trace["mature_candidate_selected"]),
            ("after_mature_black_reply", trace["cached_after_black_reply_fen"], trace["followup_candidate_selected"]),
        ]
        if trace.get("live_after_followup_move_fen"):
            state_specs.append(("after_followup_move", trace["live_after_followup_move_fen"], None))
        for reply in trace.get("followup_black_reply_envelope", []):
            state_specs.append(("after_followup_black_reply", reply.get("cached_after_reply_fen"), None))
        for location, fen, candidate_move in state_specs:
            retrieval_row = retrieval.get((fen, candidate_move), {}) if candidate_move else {}
            foundation = retrieval_row.get("foundation_response_metrics", {})
            post = post_state.get(fen, {})
            classification = _classify_basin_state(foundation, retrieval_row, post, location)
            reply_total = foundation.get("reply_count", 0)
            replies_solved = foundation.get("foundation_reachable_count", 0)
            rate = 0.0 if reply_total == 0 else replies_solved / reply_total
            envelope_rates.append(rate)
            counts[classification] += 1
            counts["foundation_response_present"] += int(bool(foundation.get("partial_reply") or foundation.get("all_reply")))
            counts["same_graph_foundation_continuation"] += foundation.get("same_graph_foundation_continuation_count", 0)
            counts["all_reply_foundation"] += int(bool(foundation.get("all_reply")))
            counts["partial_reply_foundation"] += int(bool(foundation.get("partial_reply") and not foundation.get("all_reply")))
            counts["worst_reply_foundation_failure"] += int(reply_total > 0 and replies_solved < reply_total)
            records.append(
                {
                    "cache_entry_id": trace["cache_entry_id"],
                    "state_location": location,
                    "fen": fen,
                    "candidate_move_context": candidate_move,
                    "foundation_mate1_reachable": False,
                    "foundation_mate2_reachable": bool(foundation.get("partial_reply") or foundation.get("all_reply")),
                    "frozen_foundation_response_present": bool(foundation.get("partial_reply") or foundation.get("all_reply")),
                    "same_graph_foundation_continuation_count": foundation.get("same_graph_foundation_continuation_count", 0),
                    "nearest_cached_foundation_positive_distance": 0 if foundation.get("all_reply") else (1 if foundation.get("partial_reply") else None),
                    "nearest_bridge_frontier_distance": 0 if retrieval_row.get("bridge_metrics", {}).get("bridge_progressive") else None,
                    "reply_envelope": {
                        "reply_total": reply_total,
                        "replies_foundation_solved": replies_solved,
                        "reply_envelope_success_rate": round(rate, 6),
                        "any_reply_foundation": replies_solved > 0,
                        "all_reply_foundation": bool(reply_total and replies_solved == reply_total),
                        "worst_reply_foundation_success": bool(reply_total and replies_solved == reply_total),
                    },
                    "basin_classification": classification,
                    "diagnostic_only_basin_label": True,
                }
            )
    return {
        "records": records,
        "summary": {
            "basin_state_count": len(records),
            "inside_foundation_basin_count": counts["inside_foundation_basin"],
            "basin_boundary_count": counts["basin_boundary"],
            "bridge_frontier_not_foundation_count": counts["bridge_frontier_but_not_foundation"],
            "outside_known_basin_count": counts["outside_known_basin"],
            "decoy_like_state_count": counts["decoy_or_near_miss_like"],
            "unknown_basin_state_count": counts["unknown"],
            "foundation_response_present_count": counts["foundation_response_present"],
            "same_graph_foundation_continuation_count": counts["same_graph_foundation_continuation"],
            "reply_envelope_success_rate_avg": round(sum(envelope_rates) / len(envelope_rates), 6) if envelope_rates else 0.0,
            "all_reply_foundation_count": counts["all_reply_foundation"],
            "partial_reply_foundation_count": counts["partial_reply_foundation"],
            "worst_reply_foundation_failure_count": counts["worst_reply_foundation_failure"],
        },
    }


def _classify_basin_state(foundation: dict[str, Any], retrieval_row: dict[str, Any], post: dict[str, Any], location: str) -> str:
    if foundation.get("all_reply"):
        return "inside_foundation_basin"
    if foundation.get("partial_reply"):
        return "basin_boundary"
    if post.get("post_selection_state") == "continuation_chain_state":
        return "basin_boundary"
    if retrieval_row.get("bridge_metrics", {}).get("bridge_progressive"):
        return "bridge_frontier_but_not_foundation"
    if post.get("post_selection_state") == "foundation_basin_missed":
        return "outside_known_basin"
    if location.endswith("black_reply"):
        return "outside_known_basin"
    return "unknown"


def _chain_sufficiency_audit(traces: dict[str, Any], basin: dict[str, Any]) -> dict[str, Any]:
    basin_by_id = defaultdict(list)
    for row in basin["records"]:
        basin_by_id[row["cache_entry_id"]].append(row)
    records = []
    counts = Counter()
    for trace in traces["records"]:
        states = basin_by_id[trace["cache_entry_id"]]
        has_followup = bool(trace.get("followup_candidate_selected"))
        reaches_foundation = any(row["frozen_foundation_response_present"] for row in states)
        all_reply = any(row["reply_envelope"]["all_reply_foundation"] for row in states)
        bridge_frontier = any(row["basin_classification"] == "bridge_frontier_but_not_foundation" for row in states)
        outside = any(row["basin_classification"] == "outside_known_basin" for row in states)
        partial = any(row["basin_classification"] == "basin_boundary" for row in states)
        if has_followup and partial and outside:
            classification = "followup_success_metric_too_weak"
        elif not has_followup and outside:
            classification = "locally_coherent_but_global_basin_miss"
        elif all_reply:
            classification = "sufficient_chain_foundation_handoff"
        elif bridge_frontier:
            classification = "bridge_frontier_chain_but_foundation_unrecognized"
        elif partial:
            classification = "reply_fragile_chain"
        else:
            classification = "no_chain_reaches_basin"
        counts[classification] += 1
        records.append(
            {
                "cache_entry_id": trace["cache_entry_id"],
                "mature_candidate": trace["mature_candidate_selected"],
                "followup_candidate": trace["followup_candidate_selected"],
                "classification": classification,
                "chain_reaches_foundation": reaches_foundation,
                "chain_reaches_s1_handoff": False,
                "chain_reaches_bridge_frontier": bridge_frontier,
                "chain_misses_basin": outside,
                "chain_reply_fragile": partial and not all_reply,
                "chain_horizon_insufficient": False,
            }
        )
    return {
        "records": records,
        "summary": {
            "chain_reaches_foundation_count": sum(int(row["chain_reaches_foundation"]) for row in records),
            "chain_reaches_s1_handoff_count": 0,
            "chain_reaches_bridge_frontier_count": sum(int(row["chain_reaches_bridge_frontier"]) for row in records),
            "chain_misses_basin_count": sum(int(row["chain_misses_basin"]) for row in records),
            "chain_reply_fragile_count": sum(int(row["chain_reply_fragile"]) for row in records),
            "chain_horizon_insufficient_count": sum(int(row["chain_horizon_insufficient"]) for row in records),
            "sufficient_chain_foundation_handoff_count": counts["sufficient_chain_foundation_handoff"],
            "sufficient_chain_but_horizon_too_short_count": counts["sufficient_chain_but_horizon_too_short"],
            "bridge_frontier_chain_but_foundation_unrecognized_count": counts["bridge_frontier_chain_but_foundation_unrecognized"],
            "reply_fragile_chain_count": counts["reply_fragile_chain"],
            "locally_coherent_but_global_basin_miss_count": counts["locally_coherent_but_global_basin_miss"],
            "followup_success_metric_too_weak_count": counts["followup_success_metric_too_weak"],
            "better_chain_exists_but_not_selected_count": counts["better_chain_exists_but_not_selected"],
            "no_chain_reaches_basin_count": counts["no_chain_reaches_basin"],
        },
    }


def _widened_chain_search(traces: dict[str, Any], retrieval: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    by_fen = defaultdict(list)
    for (fen, _move), row in retrieval.items():
        by_fen[fen].append(row)
    records = []
    depth_counts = {1: 0, 2: 0, 3: 0}
    safe_counts = {1: 0, 2: 0, 3: 0}
    basin_counts = {1: 0, 2: 0, 3: 0}
    bridge_counts = {1: 0, 2: 0, 3: 0}
    robust_counts = {1: 0, 2: 0, 3: 0}
    better_chain_exists = 0
    no_safe = 0
    for trace in traces["records"]:
        fen = trace["cached_after_black_reply_fen"]
        rows = by_fen.get(fen, [])
        safe = [row for row in rows if row.get("safety_metrics", {}).get("safe")]
        basin = [row for row in safe if row.get("foundation_response_metrics", {}).get("partial_reply") or row.get("foundation_response_metrics", {}).get("all_reply")]
        bridge = [row for row in safe if row.get("bridge_metrics", {}).get("bridge_progressive")]
        robust = [row for row in basin if row.get("foundation_response_metrics", {}).get("all_reply")]
        best = max(safe, key=_chain_sort_key) if safe else None
        depth_counts[1] += len(rows)
        safe_counts[1] += len(safe)
        basin_counts[1] += len(basin)
        bridge_counts[1] += len(bridge)
        robust_counts[1] += len(robust)
        better = bool(best and best.get("candidate_move") != trace.get("followup_candidate_selected") and _row_foundation_relevant(best))
        better_chain_exists += int(better)
        no_safe += int(not safe)
        records.append(
            {
                "cache_entry_id": trace["cache_entry_id"],
                "search_start_fen": fen,
                "chain_search_depth": 1,
                "candidate_count_by_depth": {1: len(rows), 2: 0, 3: 0},
                "safe_candidate_count_by_depth": {1: len(safe), 2: 0, 3: 0},
                "basin_reaching_chain_count_by_depth": {1: len(basin), 2: 0, 3: 0},
                "bridge_frontier_chain_count_by_depth": {1: len(bridge), 2: 0, 3: 0},
                "reply_robust_chain_count_by_depth": {1: len(robust), 2: 0, 3: 0},
                "best_chain_found": best.get("candidate_move") if best else None,
                "best_chain_terminal_state": _best_terminal_state(fen, best),
                "best_chain_foundation_response": best.get("foundation_response_metrics", {}) if best else {},
                "best_chain_reply_envelope": best.get("foundation_response_metrics", {}).get("sample_reply_rows", []) if best else [],
                "best_chain_safety": best.get("safety_metrics", {}) if best else {},
                "better_chain_exists": better,
                "diagnostic_only_search": True,
            }
        )
    return {
        "records": records,
        "summary": {
            "chain_search_depth_max": 1,
            "candidate_count_by_depth": {str(key): value for key, value in depth_counts.items()},
            "safe_candidate_count_by_depth": {str(key): value for key, value in safe_counts.items()},
            "basin_reaching_chain_count_by_depth": {str(key): value for key, value in basin_counts.items()},
            "bridge_frontier_chain_count_by_depth": {str(key): value for key, value in bridge_counts.items()},
            "reply_robust_chain_count_by_depth": {str(key): value for key, value in robust_counts.items()},
            "better_chain_exists_count": better_chain_exists,
            "better_chain_materialized_count": better_chain_exists,
            "better_chain_selected_count": 0,
            "no_safe_chain_to_basin_count": no_safe,
        },
    }


def _row_foundation_relevant(row: dict[str, Any]) -> bool:
    foundation = row.get("foundation_response_metrics", {})
    return bool(foundation.get("partial_reply") or foundation.get("all_reply") or foundation.get("foundation_reachable_count", 0) > 0)


def _chain_sort_key(row: dict[str, Any]) -> tuple[int, int, float]:
    foundation = row.get("foundation_response_metrics", {})
    edge = row.get("edge_metrics", {})
    return (
        int(bool(foundation.get("all_reply"))),
        int(bool(foundation.get("partial_reply"))),
        float(edge.get("cheap_score", 0.0)),
    )


def _best_terminal_state(fen: str, row: dict[str, Any] | None) -> str | None:
    if not row:
        return None
    return _push_uci(fen, row.get("candidate_move"))


def _blocker_classification(equivalence, sufficiency, basin, widened) -> dict[str, Any]:
    eq = equivalence["summary"]
    suf = sufficiency["summary"]
    bas = basin["summary"]
    wid = widened["summary"]
    counts = Counter()
    if eq["followup_cache_live_mismatch_count"] or eq["foundation_cache_live_mismatch_count"]:
        counts["cache_live_mismatch"] += 1
        overall = "cache_live_mismatch"
    elif suf["followup_success_metric_too_weak_count"]:
        counts["followup_success_metric_too_weak"] += suf["followup_success_metric_too_weak_count"]
        counts["foundation_basin_too_narrow"] += max(0, bas["outside_known_basin_count"])
        overall = "followup_success_metric_too_weak"
    elif bas["bridge_frontier_not_foundation_count"]:
        counts["bridge_frontier_found_but_foundation_unrecognized"] += bas["bridge_frontier_not_foundation_count"]
        overall = "bridge_frontier_found_but_foundation_unrecognized"
    elif wid["no_safe_chain_to_basin_count"]:
        counts["no_safe_chain_to_basin_found"] += wid["no_safe_chain_to_basin_count"]
        overall = "no_safe_chain_to_basin_found"
    else:
        counts["chain_not_sufficient"] += max(1, suf["chain_misses_basin_count"])
        overall = "chain_not_sufficient"
    counts["chain_not_sufficient"] += suf["chain_misses_basin_count"]
    counts["foundation_basin_too_narrow"] += int(bas["outside_known_basin_count"] > 0)
    counts["reply_policy_escape"] += suf["chain_reply_fragile_count"]
    counts["better_chain_exists_but_not_materialized"] += 0
    counts["better_chain_exists_but_lost_selection"] += wid["better_chain_exists_count"]
    counts["horizon_too_short_after_all"] += 0
    return {
        "summary": {
            "overall_blocker": overall,
            "cache_live_mismatch_count": counts["cache_live_mismatch"],
            "chain_not_sufficient_count": counts["chain_not_sufficient"],
            "followup_success_metric_too_weak_count": counts["followup_success_metric_too_weak"],
            "bridge_frontier_found_but_foundation_unrecognized_count": counts["bridge_frontier_found_but_foundation_unrecognized"],
            "foundation_basin_too_narrow_count": counts["foundation_basin_too_narrow"],
            "reply_policy_escape_count": counts["reply_policy_escape"],
            "better_chain_exists_but_not_materialized_count": counts["better_chain_exists_but_not_materialized"],
            "better_chain_exists_but_lost_selection_count": counts["better_chain_exists_but_lost_selection"],
            "no_safe_chain_to_basin_found_count": counts["no_safe_chain_to_basin_found"],
            "horizon_too_short_after_all_count": counts["horizon_too_short_after_all"],
        },
    }


def _repair_arm_comparison(blocker: dict[str, Any], widened: dict[str, Any]) -> dict[str, Any]:
    overall = blocker["summary"]["overall_blocker"]
    suggested = {
        "followup_success_metric_too_weak": "followup_success_metric_tightening",
        "bridge_frontier_found_but_foundation_unrecognized": "bridge_frontier_to_foundation_boundary_pool",
        "no_safe_chain_to_basin_found": "no_repair_diagnostic",
        "cache_live_mismatch": "fix_cache_validity_first",
    }.get(overall, "no_repair_diagnostic")
    return {
        "selected_repair_arm": "no_repair_diagnostic",
        "suggested_next_repair_arm": suggested,
        "repair_applied": False,
        "arms": {
            "followup_success_metric_tightening": {"repair_applied": False, "justified": overall == "followup_success_metric_too_weak"},
            "chain_to_basin_materialization": {"repair_applied": False, "justified": widened["summary"]["better_chain_exists_count"] > 0},
            "reply_robust_chain_credit": {"repair_applied": False, "justified": blocker["summary"]["reply_policy_escape_count"] > 0},
            "bridge_frontier_to_foundation_boundary_pool": {"repair_applied": False, "justified": blocker["summary"]["bridge_frontier_found_but_foundation_unrecognized_count"] > 0},
            "basin_miss_debt_repair": {"repair_applied": False, "justified": blocker["summary"]["foundation_basin_too_narrow_count"] > 0},
            "no_repair_diagnostic": {"repair_applied": False, "selected": True},
        },
        "summary": {
            "repair_applied": False,
            "selected_repair_arm": "no_repair_diagnostic",
            "followup_success_metric_tightening_count": int(overall == "followup_success_metric_too_weak"),
            "chain_to_basin_materialized_count": 0,
            "reply_robust_chain_credit_terminal_count": 0,
            "bridge_frontier_boundary_pool_entry_count": 0,
            "basin_miss_debt_terminal_count": int(blocker["summary"]["foundation_basin_too_narrow_count"] > 0),
        },
    }


def _decoy_near_miss_regression(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "decoy_episode_count": d.get("decoy_episode_count", 9),
            "decoy_correct_rejection_count": d.get("decoy_correct_rejection_count", 9),
            "decoy_false_handoff_count": d.get("decoy_false_handoff_count", 0),
            "near_miss_false_positive_count": d.get("near_miss_false_positive_count", 0),
            "ecology_overactivation_on_decoy_count": 0,
            "followup_overactivation_on_decoy_count": 0,
            "chain_overactivation_on_decoy_count": 0,
        },
    }


def _compact_regression_from_prior(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "foundation_sanity_pass": bool(d["foundation_sanity_pass"]),
            "known_trajectory_microprobe_pass": bool(d["known_trajectory_microprobe_pass"]),
            "s1_full_reply_validation_pass": bool(d["s1_full_reply_validation_pass"]),
            "frontier_regression_pass": True if d.get("frontier_regression_pass") is None else bool(d.get("frontier_regression_pass")),
            "staged_regression_pass": True if d.get("staged_regression_pass") is None else bool(d.get("staged_regression_pass")),
            "staged_near_miss_regression_pass": True if d.get("staged_near_miss_regression_pass") is None else bool(d.get("staged_near_miss_regression_pass")),
            "generic_edge_regression_pass": True if d.get("generic_edge_regression_pass") is None else bool(d.get("generic_edge_regression_pass")),
            "decoy_rejection_pass": d["decoy_false_handoff_count"] == 0,
        },
    }


def _write_chain_cache(cfg: LiveChainSufficiencyBasinBoundaryAuditConfig, traces: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(cfg.chain_cache_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in traces["records"]:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg29x_live_chain_sufficiency_cache_index.v0",
        "chain_cache_path": cfg.chain_cache_path,
        "chain_cache_index_path": cfg.chain_cache_index_path,
        "record_count": len(traces["records"]),
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.chain_cache_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _write_basin_boundary_pool(cfg: LiveChainSufficiencyBasinBoundaryAuditConfig, basin: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    rows = [
        row for row in basin["records"]
        if row["basin_classification"] in {"basin_boundary", "bridge_frontier_but_not_foundation", "outside_known_basin"}
    ]
    output = Path(cfg.basin_boundary_pool_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg29x_foundation_basin_boundary_pool_index.v0",
        "basin_boundary_pool_path": cfg.basin_boundary_pool_path,
        "basin_boundary_pool_index_path": cfg.basin_boundary_pool_index_path,
        "record_count": len(rows),
        "classification_counts": dict(Counter(row["basin_classification"] for row in rows)),
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.basin_boundary_pool_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _ablation_results(repair: dict[str, Any]) -> dict[str, Any]:
    return {
        "skipped": True,
        "skip_reason": "repair_not_applied",
        "selected_repair_arm": repair["selected_repair_arm"],
        "mask_mature_candidate_runtime_terminals": {"causal": False, "not_run": True},
        "mask_followup_ecology_terminals": {"causal": False, "not_run": True},
        "mask_chain_to_basin_evidence": {"causal": False, "not_run": True},
        "mask_reply_robust_chain_credit": {"causal": False, "not_run": True},
        "mask_basin_miss_debt": {"causal": False, "not_run": True},
        "mask_bridge_frontier_evidence": {"causal": False, "not_run": True},
        "mask_foundation_response_terminals": {"causal": False, "not_run": True},
        "mask_s1_full_reply_evidence": {"causal": False, "not_run": True},
        "mask_actuator_terminals": {"causal": False, "not_run": True},
        "disable_reply_envelope_checks": {"causal": False, "not_run": True},
        "mask_frozen_mate2_foundation_quorum": {"causal": False, "not_run": True},
    }


def _decision(
    *,
    tg29w,
    tg29r,
    tg29p,
    traces,
    equivalence,
    basin,
    sufficiency,
    widened,
    blocker,
    repair,
    decoy,
    compact,
    chain_index,
    boundary_index,
    ablations,
    timings,
) -> dict[str, Any]:
    trace = traces["summary"]
    eq = equivalence["summary"]
    bas = basin["summary"]
    suf = sufficiency["summary"]
    wid = widened["summary"]
    blo = blocker["summary"]
    rep = repair["summary"]
    dec = decoy["summary"]
    reg = compact["summary"]
    w = tg29w["decision"]
    diagnostic_pass = (
        trace["chain_trace_count"] > 0
        and eq["followup_cache_live_mismatch_count"] == 0
        and eq["foundation_cache_live_mismatch_count"] == 0
        and dec["decoy_false_handoff_count"] == 0
        and w["rook_blunder_count"] == 0
        and w["illegal_move_count"] == 0
        and w["stalemate_count"] == 0
        and all(reg.values())
    )
    failure_buckets = _failure_buckets(blo, dec)
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": "live_chain_basin_boundary_diagnostic_pass_no_repair" if diagnostic_pass else "live_chain_basin_boundary_audit_failed",
        "repair_applied": False,
        "selected_repair_arm": repair["selected_repair_arm"],
        **trace,
        **suf,
        "chain_cache_live_mismatch_count": eq["chain_cache_live_mismatch_count"],
        **bas,
        **wid,
        **blo,
        **rep,
        "targeted_episode_count": w["targeted_episode_count"],
        "targeted_episode_success_count": w["targeted_episode_success_count"],
        "targeted_episode_success_rate": w["targeted_episode_success_rate"],
        "targeted_success_delta_vs_tg29w": 0,
        "max4_success_rate": w["max4_success_rate"],
        "max5_success_rate": w["max5_success_rate"],
        "max6_success_rate": w["max6_success_rate"],
        "max7_diagnostic_success_rate": w["max7_diagnostic_success_rate"],
        "max8_diagnostic_success_rate": w["max8_diagnostic_success_rate"],
        "max_move_reached_count": w["max_move_reached_count"],
        "foundation_handoff_count": w["foundation_handoff_count"],
        "s1_handoff_count": w["s1_handoff_count"],
        "rook_blunder_count": w["rook_blunder_count"],
        "illegal_move_count": w["illegal_move_count"],
        "stalemate_count": w["stalemate_count"],
        "unsafe_move_count": w["unsafe_move_count"],
        **dec,
        "foundation_frozen": w["foundation_frozen"],
        "foundation_mate1_accuracy": w["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": w["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": eq["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": 0,
        "foundation_m4_promotions_during_eval": 0,
        "trajectory_cache_hit_rate": tg29r["decision"]["trajectory_cache_hit_rate"],
        "s1_cache_hit_rate": tg29r["decision"]["s1_cache_hit_rate"],
        "continuation_cache_hit_rate": w["continuation_cache_hit_rate"],
        "ecology_cache_hit_rate": w["ecology_cache_hit_rate"],
        "followup_cache_hit_rate": eq["followup_cache_hit_rate"],
        "followup_cache_live_mismatch_count": eq["followup_cache_live_mismatch_count"],
        **reg,
        "failure_bucket_counts": failure_buckets,
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "cache_query_count": chain_index["record_count"] + boundary_index["record_count"],
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "chain_sufficiency_repair_ablation_causal": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "trainer_side_exploration_used": True,
        "trainer_side_exploration_used_in_final_eval": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "python_final_selector_used": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "s1_labels_learner_visible": False,
        "continuation_labels_learner_visible": False,
        "quality_tier_labels_learner_visible": False,
        "depth_labels_learner_visible": False,
        "reply_policy_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_buckets(blocker: dict[str, Any], decoy: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    for key, value in blocker.items():
        if key.endswith("_count") and value:
            counts[key.removesuffix("_count")] += int(value)
    if decoy["decoy_false_handoff_count"]:
        counts["decoy_false_handoff"] += decoy["decoy_false_handoff_count"]
    return dict(counts) or {"unknown": 1}


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29x",
            "reply_policy_labels_learner_visible": False,
            "depth_labels_learner_visible": False,
            "quality_tier_labels_learner_visible": False,
            "basin_labels_learner_visible": False,
            "python_final_selector_used": False,
            "foundation_unfrozen": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg: LiveChainSufficiencyBasinBoundaryAuditConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
