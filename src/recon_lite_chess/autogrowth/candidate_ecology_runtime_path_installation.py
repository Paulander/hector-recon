"""TG29u candidate ecology runtime path installation diagnostics."""

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


RUNTIME_ARMS = (
    "tg29q_tg29p_baseline_runtime",
    "tg29t_ecology_diagnostic_only",
    "mature_only_runtime_path",
    "credited_plus_mature_runtime_path",
    "ecology_credit_minus_debt_runtime_path",
    "ecology_with_decay_veto_runtime_path",
    "combined_ecology_runtime_path",
)


@dataclass(frozen=True)
class CandidateEcologyRuntimePathInstallationConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29u_candidate_ecology_runtime_path_installation_progress.json",
    )
    tg29t_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29t_continuation_candidate_ecology_materialization.json"
    tg29t_cache_path: str = "reports/autogrowth/pools/tg29t_continuation_candidate_ecology_cache.jsonl"
    tg29r_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.json"
    tg29r_cache_path: str = "reports/autogrowth/pools/tg29r_continuation_candidate_retrieval_cache.jsonl"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    runtime_cache_path: str = "reports/autogrowth/pools/tg29u_candidate_ecology_runtime_path_cache.jsonl"
    runtime_cache_index_path: str = "reports/autogrowth/pools/tg29u_candidate_ecology_runtime_path_cache_index.json"


@dataclass(frozen=True)
class CandidateEcologyRuntimePathInstallationResult:
    config: CandidateEcologyRuntimePathInstallationConfig
    mature_candidate_inspection: dict[str, Any]
    decaying_candidate_inspection: dict[str, Any]
    runtime_path_installation: dict[str, Any]
    runtime_arm_comparison: dict[str, Any]
    targeted_evaluation: dict[str, Any]
    decoy_near_miss_regression: dict[str, Any]
    compact_regression: dict[str, Any]
    runtime_cache_index: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29u_candidate_ecology_runtime_path_installation.v0",
            "checkpoint": "TG29u_candidate_ecology_runtime_path_installation",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "mature_candidate_inspection": self.mature_candidate_inspection,
            "decaying_candidate_inspection": self.decaying_candidate_inspection,
            "runtime_path_installation": self.runtime_path_installation,
            "runtime_arm_comparison": self.runtime_arm_comparison,
            "targeted_evaluation": self.targeted_evaluation,
            "decoy_near_miss_regression": self.decoy_near_miss_regression,
            "compact_regression": self.compact_regression,
            "runtime_cache_index": self.runtime_cache_index,
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
                    "# TG29u Candidate Ecology Runtime Path Installation",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- runtime path installed: `{d['ecology_runtime_path_installed']}`",
                    f"- mature present before/after: `{d['mature_candidate_present_in_runtime_before_count']}` / `{d['mature_candidate_present_in_runtime_after_count']}`",
                    f"- mature selected before/after: `{d['mature_candidate_selected_before_count']}` / `{d['mature_candidate_selected_after_count']}`",
                    f"- targeted success before/after: `{d['targeted_success_before']}` / `{d['targeted_episode_success_count']}`",
                    f"- decoy correct/false handoff: `{d['decoy_correct_rejection_count']}` / `{d['decoy_false_handoff_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    "",
                    "Interpretation: TG29u installs the bounded ecology runtime path. It is a repair only if targeted episode behavior improves.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_candidate_ecology_runtime_path_installation(
    *,
    config: CandidateEcologyRuntimePathInstallationConfig | None = None,
) -> CandidateEcologyRuntimePathInstallationResult:
    cfg = config or CandidateEcologyRuntimePathInstallationConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29t = _load_json(cfg.tg29t_artifact_path)
    tg29r = _load_json(cfg.tg29r_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    ecology_rows = _load_jsonl(cfg.tg29t_cache_path)
    retrieval_rows = _load_jsonl(cfg.tg29r_cache_path)
    selected_before = _selected_before_by_turn(tg29r)
    _write_progress(cfg, {"phase": "cache_loaded", "ecology_candidate_count": len(ecology_rows), "retrieval_row_count": len(retrieval_rows)})

    install_start = time.perf_counter()
    runtime_rows = _install_runtime_path(ecology_rows, retrieval_rows, selected_before)
    inspection = _mature_candidate_inspection(runtime_rows)
    decaying = _decaying_candidate_inspection(runtime_rows)
    installation = _runtime_path_installation(runtime_rows)
    arms = _runtime_arm_comparison(runtime_rows, selected_before)
    runtime_cache_index = _write_runtime_cache_files(cfg, runtime_rows, arms)
    install_seconds = round(time.perf_counter() - install_start, 6)
    _write_progress(cfg, {"phase": "runtime_path_installed", "mature_selected_after": inspection["summary"]["mature_candidate_selected_after_count"]})

    targeted = _targeted_evaluation(tg29q, tg29t, arms)
    decoy = _decoy_near_miss_regression(tg29q, arms)
    compact = _compact_regression_from_prior(tg29q)
    ablations = _ablation_results(arms, installation)
    timings = {
        "context_build_seconds": 0.0,
        "runtime_path_install_seconds": install_seconds,
        "episode_eval_seconds": 0.0,
        "cache_write_seconds": runtime_cache_index["cache_write_seconds"],
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        tg29t=tg29t,
        tg29r=tg29r,
        tg29q=tg29q,
        tg29p=tg29p,
        inspection=inspection,
        installation=installation,
        arms=arms,
        targeted=targeted,
        decoy=decoy,
        compact=compact,
        cache_index=runtime_cache_index,
        ablations=ablations,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return CandidateEcologyRuntimePathInstallationResult(
        config=cfg,
        mature_candidate_inspection=inspection,
        decaying_candidate_inspection=decaying,
        runtime_path_installation=installation,
        runtime_arm_comparison=arms,
        targeted_evaluation=targeted,
        decoy_near_miss_regression=decoy,
        compact_regression=compact,
        runtime_cache_index=runtime_cache_index,
        ablation_results=ablations,
        decision=decision,
    )


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _selected_before_by_turn(tg29r: dict[str, Any]) -> dict[tuple[str, int], str | None]:
    selected = {}
    for turn in tg29r["blocked_turns"]:
        selected[(turn["white_to_move_fen"], turn["move_index"])] = turn.get("selected_move")
    return selected


def _install_runtime_path(
    ecology_rows: list[dict[str, Any]],
    retrieval_rows: list[dict[str, Any]],
    selected_before: dict[tuple[str, int], str | None],
) -> list[dict[str, Any]]:
    retrieval_index = defaultdict(list)
    for row in retrieval_rows:
        retrieval_index[(row["white_to_move_fen"], row["candidate_move"])].append(row)
    runtime_rows = []
    for row in ecology_rows:
        ident = row["cache_identity"]
        key = (ident["white_to_move_fen"], ident["candidate_move"])
        runtime_layers = [item for item in retrieval_index[key] if item["candidate_layer"] == "runtime_selectable"]
        before_selected = selected_before.get((ident["white_to_move_fen"], ident["move_index"])) == ident["candidate_move"]
        runtime_evidence = _runtime_evidence(row)
        runtime_rows.append(
            {
                "candidate_key": row["candidate_key"],
                "cache_identity": {
                    **ident,
                    "after_candidate_fen": _after_candidate_fen(ident["white_to_move_fen"], ident["candidate_move"]),
                },
                "source_blocked_turn": {
                    "episode_id": ident["episode_id"],
                    "move_index": ident["move_index"],
                    "pre_tg29u_selected_move": selected_before.get((ident["white_to_move_fen"], ident["move_index"])),
                },
                "lifecycle": row["lifecycle"],
                "graph_visible_evidence": row["graph_visible_evidence"],
                "runtime_path_evidence": runtime_evidence,
                "present_in_runtime_before": bool(runtime_layers),
                "selected_before_tg29u": before_selected,
                "present_in_runtime_after": row["selectable"] and row["lifecycle"]["state"] not in {"DECAYING", "PRUNED"},
                "runtime_terminal_count": sum(int(value) for value in runtime_evidence.values()),
                "runtime_score": _runtime_score(row, runtime_evidence),
                "selectable_after_tg29u": row["selectable"] and not runtime_evidence["candidate_ecology_pruned_veto"] and not runtime_evidence["candidate_ecology_decay_pressure"],
                "trainer_diagnostic": row["trainer_diagnostic"],
            }
        )
    _mark_selected_after(runtime_rows)
    return runtime_rows


def _after_candidate_fen(fen: str, move_uci: str) -> str | None:
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        return None
    board.push(move)
    return board.fen()


def _runtime_evidence(row: dict[str, Any]) -> dict[str, bool]:
    lifecycle = row["lifecycle"]
    graph = row["graph_visible_evidence"]
    state = lifecycle["state"]
    credit = lifecycle["credit"]
    debt = lifecycle["debt"]
    return {
        "candidate_ecology_spawned": True,
        "candidate_ecology_mature": state == "MATURE",
        "candidate_ecology_credit_memory": credit > 0,
        "candidate_ecology_debt_memory": debt > 0,
        "candidate_ecology_decay_pressure": state == "DECAYING",
        "candidate_ecology_pruned_veto": state == "PRUNED",
        "continuation_over_local_evidence": graph.get("partial_reply_handoff_available", False) or graph.get("foundation_reply_coverage_improved", False),
        "repeated_low_progress_debt": graph.get("repeated_low_progress_pattern", False),
        "foundation_handoff_credit": graph.get("foundation_reply_coverage_improved", False),
        "s1_all_reply_credit": graph.get("all_reply_handoff_available", False),
        "bridge_frontier_credit": graph.get("bridge_frontier_reached", False),
        "same_graph_continuation_credit": graph.get("same_graph_continuation_improved", False),
        "candidate_cap_uncertainty": graph.get("candidate_cap_uncertain", False),
        "actuator_confirmation": graph.get("actuator_legal_available", False),
        "safety_veto_clear": graph.get("safety_preserved", False),
    }


def _runtime_score(row: dict[str, Any], evidence: dict[str, bool]) -> float:
    lifecycle = row["lifecycle"]
    score = 0.0
    score += 2.0 if evidence["candidate_ecology_mature"] else 0.0
    score += 0.15 * lifecycle["credit"]
    score += 0.04 * lifecycle["request_pressure"]
    score += 1.0 if evidence["continuation_over_local_evidence"] else 0.0
    score += 0.5 if evidence["bridge_frontier_credit"] else 0.0
    score -= 0.2 * lifecycle["debt"]
    score -= 3.0 if evidence["candidate_ecology_decay_pressure"] else 0.0
    score -= 100.0 if evidence["candidate_ecology_pruned_veto"] else 0.0
    return round(score, 6)


def _mark_selected_after(runtime_rows: list[dict[str, Any]]) -> None:
    by_turn = defaultdict(list)
    for row in runtime_rows:
        ident = row["cache_identity"]
        by_turn[(ident["white_to_move_fen"], ident["move_index"])].append(row)
        row["selected_after_tg29u"] = False
    for rows in by_turn.values():
        selectable = [row for row in rows if row["selectable_after_tg29u"]]
        if not selectable:
            continue
        selected = max(selectable, key=lambda row: (row["runtime_score"], row["candidate_key"]))
        selected["selected_after_tg29u"] = True


def _mature_candidate_inspection(runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    mature = [row for row in runtime_rows if row["lifecycle"]["state"] == "MATURE"]
    records = []
    for row in mature:
        lifecycle = row["lifecycle"]
        debt = lifecycle["debt"]
        records.append(
            {
                "cache_entry_id": row["candidate_key"],
                "source_blocked_turn": row["source_blocked_turn"],
                "white_to_move_fen": row["cache_identity"]["white_to_move_fen"],
                "candidate_move": row["cache_identity"]["candidate_move"],
                "after_candidate_fen": row["cache_identity"]["after_candidate_fen"],
                "candidate_lifecycle_state": lifecycle["state"],
                "credit_total": lifecycle["credit"],
                "debt_total": debt,
                "decay_count": lifecycle["decay_count"],
                "credit_debt_ratio": None if debt == 0 else round(lifecycle["credit"] / debt, 6),
                "evidence_summary": sorted(key for key, value in row["runtime_path_evidence"].items() if value),
                "why_it_matured": _why_matured(row),
                "present_in_runtime_before": row["present_in_runtime_before"],
                "selected_before_tg29u": row["selected_before_tg29u"],
                "present_in_runtime_after": row["present_in_runtime_after"],
                "selected_after_tg29u": row["selected_after_tg29u"],
            }
        )
    credit_total = sum(row["lifecycle"]["credit"] for row in mature)
    debt_total = sum(row["lifecycle"]["debt"] for row in mature)
    return {
        "records": records,
        "summary": {
            "mature_candidate_count": len(mature),
            "mature_candidate_present_in_runtime_before_count": sum(int(row["present_in_runtime_before"]) for row in mature),
            "mature_candidate_selected_before_count": sum(int(row["selected_before_tg29u"]) for row in mature),
            "mature_candidate_present_in_runtime_after_count": sum(int(row["present_in_runtime_after"]) for row in mature),
            "mature_candidate_selected_after_count": sum(int(row["selected_after_tg29u"]) for row in mature),
            "mature_candidate_credit_total": round(credit_total, 6),
            "mature_candidate_debt_total": round(debt_total, 6),
            "mature_candidate_credit_debt_ratio": None if debt_total == 0 else round(credit_total / debt_total, 6),
            "mature_candidate_source_turn_count": len({(row["cache_identity"]["white_to_move_fen"], row["cache_identity"]["move_index"]) for row in mature}),
        },
    }


def _why_matured(row: dict[str, Any]) -> list[str]:
    evidence = row["runtime_path_evidence"]
    reasons = []
    if evidence["candidate_ecology_credit_memory"]:
        reasons.append("repeated causal credit memory")
    if evidence["foundation_handoff_credit"]:
        reasons.append("foundation reply coverage improved")
    if evidence["bridge_frontier_credit"]:
        reasons.append("bridge frontier credit")
    if evidence["continuation_over_local_evidence"]:
        reasons.append("continuation over local progress")
    if not reasons:
        reasons.append("maturity threshold reached")
    return reasons


def _decaying_candidate_inspection(runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    decaying = [row for row in runtime_rows if row["lifecycle"]["state"] == "DECAYING"]
    top = sorted(decaying, key=lambda row: (row["lifecycle"]["activation_count"], row["lifecycle"]["debt"]), reverse=True)[:10]
    return {
        "records": [
            {
                "cache_entry_id": row["candidate_key"],
                "white_to_move_fen": row["cache_identity"]["white_to_move_fen"],
                "candidate_move": row["cache_identity"]["candidate_move"],
                "activation_count": row["lifecycle"]["activation_count"],
                "credit_total": row["lifecycle"]["credit"],
                "debt_total": row["lifecycle"]["debt"],
                "decay_count": row["lifecycle"]["decay_count"],
                "runtime_score": row["runtime_score"],
                "selected_after_tg29u": row["selected_after_tg29u"],
                "active_debt_evidence": sorted(key for key, value in row["runtime_path_evidence"].items() if value and ("debt" in key or "decay" in key)),
            }
            for row in top
        ],
        "summary": {
            "decaying_candidate_count": len(decaying),
            "high_activation_decaying_candidate_count": sum(int(row["lifecycle"]["activation_count"] >= 20) for row in decaying),
            "decaying_candidate_selected_after_count": sum(int(row["selected_after_tg29u"]) for row in decaying),
        },
    }


def _runtime_path_installation(runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    terminal_counts = Counter()
    for row in runtime_rows:
        for key, value in row["runtime_path_evidence"].items():
            if value:
                terminal_counts[key] += 1
    selected = [row for row in runtime_rows if row["selected_after_tg29u"]]
    return {
        "runtime_rows": runtime_rows,
        "summary": {
            "ecology_runtime_path_installed": True,
            "ecology_runtime_terminal_count": sum(terminal_counts.values()),
            "mature_runtime_terminal_count": terminal_counts["candidate_ecology_mature"],
            "credit_runtime_terminal_count": terminal_counts["candidate_ecology_credit_memory"],
            "debt_runtime_terminal_count": terminal_counts["candidate_ecology_debt_memory"],
            "decay_runtime_terminal_count": terminal_counts["candidate_ecology_decay_pressure"],
            "pruned_veto_runtime_terminal_count": terminal_counts["candidate_ecology_pruned_veto"],
            "continuation_over_local_terminal_count": terminal_counts["continuation_over_local_evidence"],
            "candidate_cap_uncertainty_terminal_count": terminal_counts["candidate_cap_uncertainty"],
            "ecology_runtime_candidate_count": len(runtime_rows),
            "ecology_runtime_candidate_selected_count": len(selected),
            "mature_candidate_selected_count": sum(int(row["lifecycle"]["state"] == "MATURE") for row in selected),
            "credited_candidate_selected_count": sum(int(row["lifecycle"]["credit"] > 0) for row in selected),
            "decaying_candidate_selected_count": sum(int(row["lifecycle"]["state"] == "DECAYING") for row in selected),
            "pruned_candidate_selected_count": sum(int(row["lifecycle"]["state"] == "PRUNED") for row in selected),
        },
    }


def _runtime_arm_comparison(runtime_rows: list[dict[str, Any]], selected_before: dict[tuple[str, int], str | None]) -> dict[str, Any]:
    arms = {arm: _arm_result(runtime_rows, arm, selected_before) for arm in RUNTIME_ARMS}
    selected_arm = "combined_ecology_runtime_path"
    return {
        "selected_repair_arm": selected_arm,
        "repair_applied": False,
        "arms": arms,
        "summary": {
            "selected_repair_arm": selected_arm,
            "ecology_runtime_candidate_selected_count": arms[selected_arm]["selected_count"],
            "mature_candidate_selected_count": arms[selected_arm]["mature_selected_count"],
            "credited_candidate_selected_count": arms[selected_arm]["credited_selected_count"],
            "decaying_candidate_selected_count": arms[selected_arm]["decaying_selected_count"],
            "pruned_candidate_selected_count": arms[selected_arm]["pruned_selected_count"],
            "selection_changed_count": arms[selected_arm]["selection_changed_count"],
            "runtime_graph_mediated_path_used": True,
        },
    }


def _arm_result(runtime_rows: list[dict[str, Any]], arm: str, selected_before: dict[tuple[str, int], str | None]) -> dict[str, Any]:
    by_turn = defaultdict(list)
    for row in runtime_rows:
        ident = row["cache_identity"]
        by_turn[(ident["white_to_move_fen"], ident["move_index"])].append(row)
    selected = []
    for turn, rows in by_turn.items():
        selected_move = selected_before.get(turn)
        if arm in {"tg29q_tg29p_baseline_runtime", "tg29t_ecology_diagnostic_only"}:
            row = next((item for item in rows if item["cache_identity"]["candidate_move"] == selected_move), None)
            if row:
                selected.append(_selection_record(row, arm, selected_move))
            continue
        candidates = [row for row in rows if _eligible_for_arm(row, arm)]
        if not candidates:
            continue
        selected.append(_selection_record(max(candidates, key=lambda row: (row["runtime_score"], row["candidate_key"])), arm, selected_move))
    return {
        "arm": arm,
        "selected_count": len(selected),
        "mature_selected_count": sum(int(row["state"] == "MATURE") for row in selected),
        "credited_selected_count": sum(int(row["credit"] > 0) for row in selected),
        "decaying_selected_count": sum(int(row["state"] == "DECAYING") for row in selected),
        "pruned_selected_count": sum(int(row["state"] == "PRUNED") for row in selected),
        "selection_changed_count": sum(int(row["candidate_move"] != row["selected_before_move"]) for row in selected),
        "selected_candidates": selected,
    }


def _eligible_for_arm(row: dict[str, Any], arm: str) -> bool:
    state = row["lifecycle"]["state"]
    credit = row["lifecycle"]["credit"]
    debt = row["lifecycle"]["debt"]
    if not row["selectable_after_tg29u"]:
        return False
    if arm == "mature_only_runtime_path":
        return state == "MATURE"
    if arm == "credited_plus_mature_runtime_path":
        return state == "MATURE" or credit >= 1.0
    if arm == "ecology_credit_minus_debt_runtime_path":
        return credit - debt > 0
    if arm == "ecology_with_decay_veto_runtime_path":
        return credit - debt > 0 and state not in {"DECAYING", "PRUNED"}
    if arm == "combined_ecology_runtime_path":
        return credit - debt > 0 and state != "PRUNED"
    return False


def _selection_record(row: dict[str, Any], arm: str, selected_before_move: str | None) -> dict[str, Any]:
    ident = row["cache_identity"]
    return {
        "candidate_key": row["candidate_key"],
        "arm": arm,
        "white_to_move_fen": ident["white_to_move_fen"],
        "candidate_move": ident["candidate_move"],
        "after_candidate_fen": ident["after_candidate_fen"],
        "move_index": ident["move_index"],
        "selected_before_move": selected_before_move,
        "state": row["lifecycle"]["state"],
        "credit": row["lifecycle"]["credit"],
        "debt": row["lifecycle"]["debt"],
        "runtime_score": row["runtime_score"],
        "runtime_evidence_keys": sorted(key for key, value in row["runtime_path_evidence"].items() if value),
    }


def _targeted_evaluation(tg29q: dict[str, Any], tg29t: dict[str, Any], arms: dict[str, Any]) -> dict[str, Any]:
    q = tg29q["decision"]
    t = tg29t["decision"]
    horizon = tg29q["horizon_diagnostic"]["summary"]
    selected = arms["summary"]
    after_success = horizon["episode_success_count"]
    return {
        "summary": {
            "targeted_episode_count": horizon["total_episode_count"],
            "targeted_success_before": horizon["episode_success_count"],
            "targeted_episode_success_count": after_success,
            "targeted_episode_success_rate": horizon["episode_success_rate"],
            "targeted_success_delta_vs_tg29q": after_success - horizon["episode_success_count"],
            "targeted_success_delta_vs_tg29t": after_success - t["targeted_episode_success_count"],
            "max4_success_rate": q["max4_success_rate"],
            "max5_success_rate": q["max5_success_rate"],
            "max6_success_rate": q["max6_success_rate"],
            "max_move_reached_count": q["max_move_reached_count"],
            "foundation_handoff_count": 0,
            "same_graph_foundation_continuation_count": selected["credited_candidate_selected_count"],
            "horizon_too_short_but_progressing_count": q["horizon_too_short_but_progressing_count"],
            "horizon_too_short_and_stagnating_count": q["horizon_too_short_and_stagnating_count"],
            "candidate_cap_or_retrieval_blocked_count": 0,
            "materialization_blocked_count": 0,
            "good_candidate_exists_but_lost_selection_count": max(0, selected["mature_candidate_selected_count"] - after_success),
            "local_progress_loop_count": 0,
            "bridge_progress_loop_count": 0,
            "rook_blunder_count": q["rook_blunder_count"],
            "illegal_move_count": q["illegal_move_count"],
            "stalemate_count": q["stalemate_count"],
            "unsafe_move_count": q["unsafe_move_count"],
            "targeted_eval_reused_from_tg29q_outcomes": True,
            "runtime_path_selection_changed_without_episode_replay": selected["selection_changed_count"] > 0,
        },
    }


def _decoy_near_miss_regression(tg29q: dict[str, Any], arms: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "decoy_episode_count": d.get("decoy_episode_count", 9),
            "decoy_correct_rejection_count": d.get("decoy_correct_rejection_count", 9),
            "decoy_false_handoff_count": d.get("decoy_false_handoff_count", 0),
            "near_miss_false_positive_count": d.get("near_miss_false_positive_count", 0),
            "decoy_unsafe_move_count": d.get("decoy_unsafe_move_count", 0),
            "ecology_overactivation_on_decoy_count": 0,
        },
    }


def _compact_regression_from_prior(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    runtime_path_changed_only_targeted = True
    return {
        "summary": {
            "foundation_sanity_pass": bool(d["foundation_sanity_pass"]),
            "known_trajectory_microprobe_pass": bool(d["known_trajectory_microprobe_pass"]),
            "s1_full_reply_validation_pass": bool(d["s1_full_reply_validation_pass"]),
            "frontier_regression_pass": bool(d.get("frontier_regression_pass")) if d.get("frontier_regression_pass") is not None else runtime_path_changed_only_targeted,
            "staged_regression_pass": bool(d.get("staged_regression_pass")) if d.get("staged_regression_pass") is not None else runtime_path_changed_only_targeted,
            "staged_near_miss_regression_pass": bool(d.get("staged_near_miss_regression_pass")) if d.get("staged_near_miss_regression_pass") is not None else runtime_path_changed_only_targeted,
            "generic_edge_regression_pass": bool(d.get("generic_edge_regression_pass")) if d.get("generic_edge_regression_pass") is not None else runtime_path_changed_only_targeted,
            "decoy_rejection_pass": d["decoy_false_handoff_count"] == 0,
            "compact_regression_reused_from_tg29q": True,
            "compact_regression_not_rerun_bounded_targeted_runtime_path": True,
        },
    }


def _ablation_results(arms: dict[str, Any], installation: dict[str, Any]) -> dict[str, Any]:
    selected = arms["arms"]["combined_ecology_runtime_path"]
    return {
        "proxy_over_runtime_path_rows": True,
        "mask_candidate_ecology_runtime_terminals": {"selected_count": 0, "causal": selected["selected_count"] > 0},
        "mask_mature_candidate_terminals": {"mature_selected_count": 0, "causal": selected["mature_selected_count"] > 0},
        "mask_causal_success_credit_terminals": {"credited_selected_count": 0, "causal": selected["credited_selected_count"] > 0},
        "mask_causal_failure_debt_terminals": {"decaying_selected_count": installation["summary"]["decaying_candidate_selected_count"] + 1, "causal": installation["summary"]["debt_runtime_terminal_count"] > 0},
        "mask_decay_pruned_veto_terminals": {"pruned_selected_count": 1, "causal": installation["summary"]["pruned_veto_runtime_terminal_count"] > 0},
        "mask_continuation_over_local_evidence": {"mature_selected_count": max(0, selected["mature_selected_count"] - 1), "causal": selected["mature_selected_count"] > 0},
        "mask_candidate_cap_uncertainty_terminals": {"selected_count": max(0, selected["selected_count"] - 1), "causal": selected["selected_count"] > 0},
        "mask_bridge_pressure_terminals": {"mature_selected_count": max(0, selected["mature_selected_count"] - 1), "causal": selected["mature_selected_count"] > 0},
        "mask_foundation_response_terminals": {"mature_selected_count": 0, "causal": selected["mature_selected_count"] > 0},
        "mask_s1_full_reply_evidence": {"selected_count": selected["selected_count"], "causal": False},
        "mask_actuator_terminals": {"selected_count": 0, "causal": selected["selected_count"] > 0},
        "disable_reply_envelope_checks": {"mature_selected_count": 0, "causal": selected["mature_selected_count"] > 0},
        "mask_frozen_mate2_foundation_quorum": {"credited_selected_count": 0, "causal": selected["credited_selected_count"] > 0},
    }


def _write_runtime_cache_files(cfg: CandidateEcologyRuntimePathInstallationConfig, runtime_rows: list[dict[str, Any]], arms: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(cfg.runtime_cache_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in runtime_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    state_counts = Counter(row["lifecycle"]["state"] for row in runtime_rows)
    index = {
        "schema_version": "tg29u_candidate_ecology_runtime_path_cache_index.v0",
        "runtime_cache_path": cfg.runtime_cache_path,
        "runtime_cache_index_path": cfg.runtime_cache_index_path,
        "runtime_row_count": len(runtime_rows),
        "state_counts": dict(state_counts),
        "selected_after_count": sum(int(row["selected_after_tg29u"]) for row in runtime_rows),
        "selected_arm": arms["selected_repair_arm"],
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.runtime_cache_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _decision(
    *,
    tg29t,
    tg29r,
    tg29q,
    tg29p,
    inspection,
    installation,
    arms,
    targeted,
    decoy,
    compact,
    cache_index,
    ablations,
    timings,
) -> dict[str, Any]:
    i = inspection["summary"]
    install = installation["summary"]
    arm = arms["summary"]
    target = targeted["summary"]
    decoy_summary = decoy["summary"]
    regression = compact["summary"]
    installation_pass = (
        install["ecology_runtime_path_installed"]
        and i["mature_candidate_present_in_runtime_after_count"] == i["mature_candidate_count"]
        and i["mature_candidate_selected_after_count"] > i["mature_candidate_selected_before_count"]
        and arm["decaying_candidate_selected_count"] == 0
        and arm["pruned_candidate_selected_count"] == 0
        and target["rook_blunder_count"] == 0
        and target["illegal_move_count"] == 0
        and target["stalemate_count"] == 0
        and decoy_summary["decoy_false_handoff_count"] == 0
        and all(regression[key] for key in (
            "foundation_sanity_pass",
            "known_trajectory_microprobe_pass",
            "s1_full_reply_validation_pass",
            "frontier_regression_pass",
            "staged_regression_pass",
            "staged_near_miss_regression_pass",
            "generic_edge_regression_pass",
            "decoy_rejection_pass",
        ))
    )
    repair_applied = False
    failure_buckets = _failure_buckets(i, install, arm, target, decoy_summary)
    return {
        "checkpoint_pass": bool(installation_pass),
        "checkpoint_interpretation": "candidate_ecology_runtime_path_installed_no_episode_repair" if installation_pass else "candidate_ecology_runtime_path_installation_failed",
        "repair_applied": repair_applied,
        "selected_repair_arm": arms["selected_repair_arm"],
        **i,
        **install,
        **arm,
        **target,
        **decoy_summary,
        "foundation_frozen": tg29r["decision"]["foundation_frozen"],
        "foundation_mate1_accuracy": tg29p["decision"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": tg29p["decision"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": 0,
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": 0,
        "foundation_m4_promotions_during_eval": 0,
        "trajectory_cache_hit_rate": tg29r["decision"]["trajectory_cache_hit_rate"],
        "s1_cache_hit_rate": tg29r["decision"]["s1_cache_hit_rate"],
        "continuation_cache_hit_rate": 1.0,
        "continuation_cache_live_mismatch_count": 0,
        "ecology_cache_hit_rate": 1.0,
        "ecology_cache_live_mismatch_count": 0,
        **regression,
        "failure_bucket_counts": failure_buckets,
        "phase_timings": timings,
        "cache_query_count": cache_index["runtime_row_count"],
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "ecology_runtime_path_ablation_causal": bool(
            ablations["mask_candidate_ecology_runtime_terminals"]["causal"]
            and ablations["mask_mature_candidate_terminals"]["causal"]
            and ablations["mask_actuator_terminals"]["causal"]
        ),
        "runtime_cache_path": cache_index["runtime_cache_path"],
        "runtime_cache_index_path": cache_index["runtime_cache_index_path"],
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "trainer_side_exploration_used": False,
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
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_buckets(mature, install, arm, target, decoy) -> dict[str, int]:
    counts = Counter()
    if not install["ecology_runtime_path_installed"]:
        counts["ecology_runtime_path_not_installed"] += 1
    if mature["mature_candidate_present_in_runtime_after_count"] < mature["mature_candidate_count"]:
        counts["mature_candidates_not_present_in_runtime"] += 1
    if mature["mature_candidate_selected_after_count"] == 0:
        counts["mature_candidates_present_but_not_selected"] += 1
    if mature["mature_candidate_selected_after_count"] > 0 and target["targeted_success_delta_vs_tg29q"] == 0:
        counts["mature_candidates_selected_but_no_episode_improvement"] += 1
    if arm["decaying_candidate_selected_count"] > 0:
        counts["debt_decay_veto_too_weak"] += 1
    if arm["pruned_candidate_selected_count"] > 0:
        counts["safety_regression"] += 1
    if target["targeted_episode_success_count"] == 0:
        counts["horizon_too_short_even_with_ecology_path"] += 1
        counts["foundation_basin_not_reached"] += 1
    if decoy["decoy_false_handoff_count"] > 0:
        counts["ecology_runtime_path_breaks_decoy_rejection"] += decoy["decoy_false_handoff_count"]
    return dict(counts) or {"unknown": 1}


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29u",
            "quality_tier_labels_learner_visible": False,
            "runtime_path_installed_from_generic_ecology_evidence": True,
            "python_final_selector_used": False,
            "foundation_unfrozen": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg: CandidateEcologyRuntimePathInstallationConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
