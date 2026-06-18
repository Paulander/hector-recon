"""TG26y continuous handoff attention and Mate_In_2 replay."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import chess

from .foundation_curriculum import _forced_mate_in_two_first_moves
from .internal_handoff_affordance_guard_audit import (
    InternalHandoffAffordanceConfig,
    _confirm_internal_handoff_gate,
    _datasets,
    _empty_mate2_audit,
    _evaluate_internal_handoff_arm,
    _mate2_cfg,
    _train_internal_handoff_gate,
)
from .native_quorum_materialization import _tg26t_config, _train_graph, _trained_graph
from .native_quorum_mate2_chaining import (
    _confirm_materialized_mate2_first,
    _evaluate_mate1_materialized,
    _same_graph_chain_audit,
    _tg26u_config,
    _train_mate2_chain,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .terminal_lifecycle import apply_terminal_lifecycle


ATTENTION_MODES = (
    "binary_gate_baseline",
    "high_recall_threshold_gate",
    "top_k_request_strength",
    "top_k_epsilon_exploration",
    "softmax_temperature_sampling",
    "two_stage_attention",
)


@dataclass(frozen=True)
class ContinuousHandoffAttentionConfig:
    seed: int = 20260622
    mate1_train_count: int = 24
    mate1_heldout_count: int = 12
    mate2_train_count: int = 12
    mate2_heldout_count: int = 6
    max_generation_attempts: int = 500_000
    train_repetitions: int = 1
    continuation_repetitions: int = 1
    max_ticks: int = 30
    max_samples: int = 24
    eta_m3: float = 0.10
    handoff_eta_scale: float = 0.75
    max_abs_local_weight: float = 1.0
    max_candidates_per_move: int = 1
    max_shared_atom_candidates_per_choice: int = 3
    shared_atom_min_overlap: int = 6
    min_vote_score: float = -10000.0
    soft_quorum_min_positive_atoms: int = 3
    materialized_quorum_min_positive_atoms: int = 3
    mate2_materialized_quorum_min_positive_atoms: int = 2
    handoff_gate_min_positive_atoms: int = 2
    handoff_gate_min_score: float = -10000.0
    materialized_quorum_min_evidence: float = -10000.0
    veto_evidence_threshold: float = -0.25
    first_move_chain_min_reply_success_rate: float = 1.0
    request_strength_temperature: float = 5.0
    high_recall_threshold: float = 0.02
    effectively_zero_request_strength: float = 0.001
    top_k: int = 4
    two_stage_top_k: int = 6
    epsilon_tail_count: int = 2
    softmax_temperature: float = 0.35
    softmax_budget: int = 5
    equivalence_count: int = 4
    compare_repetition_2: bool = True
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg26y_continuous_handoff_attention_progress.json"


@dataclass(frozen=True)
class ContinuousHandoffAttentionResult:
    config: ContinuousHandoffAttentionConfig
    dataset: dict[str, Any]
    mate1_foundation: dict[str, Any]
    mate2_training: dict[str, Any]
    attention_modes: dict[str, Any]
    selected_mode_result: dict[str, Any]
    replay_comparison: dict[str, Any]
    lifecycle: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26y_continuous_handoff_attention.v0",
            "checkpoint": "TG26y_continuous_handoff_attention",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "mate1_foundation": self.mate1_foundation,
            "mate2_training": self.mate2_training,
            "attention_modes": self.attention_modes,
            "selected_mode_result": self.selected_mode_result,
            "replay_comparison": self.replay_comparison,
            "lifecycle": self.lifecycle,
            "scheduler_equivalence": self.scheduler_equivalence,
            "ablation_results": self.ablation_results,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_continuous_handoff_attention(
    *,
    config: ContinuousHandoffAttentionConfig | None = None,
) -> ContinuousHandoffAttentionResult:
    cfg = config or ContinuousHandoffAttentionConfig()
    run = _run_replay(cfg, train_repetitions=cfg.train_repetitions)
    _write_progress(cfg, {"phase": "primary_replay_complete", "summary": run["summary"]})
    selected_mode = _select_attention_mode(run["attention_modes"])
    selected = run["attention_modes"][selected_mode]
    promotion_threshold = max(1, math.ceil(run["dataset"]["mate2_heldout_count"] * (4 / 6)))
    lifecycle = apply_terminal_lifecycle(
        run["graph"],
        heldout_confirmed=(
            run["mate1_heldout"]["accuracy"] >= 1.0
            and run["mate1_heldout"]["null_count"] == 0
            and selected["conversion_count"] >= promotion_threshold
            and selected["internal_attention_false_negative_count"] <= 1
        ),
        prune=True,
        promote=True,
    )
    replay_comparison: dict[str, Any] = {
        "train_repetition_1": {
            "selected_attention_mode": selected_mode,
            "mate2_conversion_rate": selected["conversion_rate"],
            "false_negative_count": selected["internal_attention_false_negative_count"],
            "deep_reply_checks_run": selected["deep_reply_checks_run"],
        }
    }
    if cfg.compare_repetition_2:
        rep2_cfg = ContinuousHandoffAttentionConfig(**{**asdict(cfg), "train_repetitions": 2, "compare_repetition_2": False})
        rep2 = _run_replay(rep2_cfg, train_repetitions=2, modes=(selected_mode,))
        rep2_selected = rep2["attention_modes"][selected_mode]
        replay_comparison["train_repetition_2"] = {
            "selected_attention_mode": selected_mode,
            "mate2_conversion_rate": rep2_selected["conversion_rate"],
            "false_negative_count": rep2_selected["internal_attention_false_negative_count"],
            "deep_reply_checks_run": rep2_selected["deep_reply_checks_run"],
            "m3_update_count": rep2["graph"].m3_update_count,
        }
        _write_progress(cfg, {
            "phase": "repetition_2_comparison_complete",
            "primary": replay_comparison["train_repetition_1"],
            "repetition_2": replay_comparison["train_repetition_2"],
        })
    equivalence = run["scheduler_equivalence"]
    ablations = _run_ablations(run["graph"], run["mate2_heldout"], cfg, selected_mode)
    decision = _decision(cfg, run, selected_mode, selected, lifecycle, equivalence, ablations)
    return ContinuousHandoffAttentionResult(
        config=cfg,
        dataset=run["dataset"],
        mate1_foundation={"training": run["mate1_training"], "heldout": run["mate1_heldout"]},
        mate2_training=run["mate2_training"],
        attention_modes=run["attention_modes"],
        selected_mode_result=selected,
        replay_comparison=replay_comparison,
        lifecycle=lifecycle,
        scheduler_equivalence=equivalence,
        ablation_results=ablations,
        decision=decision,
    )


def _run_replay(
    cfg: ContinuousHandoffAttentionConfig,
    *,
    train_repetitions: int,
    modes: tuple[str, ...] = ATTENTION_MODES,
) -> dict[str, Any]:
    internal_cfg = _internal_cfg(cfg, train_repetitions=train_repetitions)
    mate1_train, mate1_heldout, mate2_train, mate2_heldout = _datasets(internal_cfg)
    graph = _trained_graph(_tg26u_config(_mate2_cfg(internal_cfg)), score_action_atoms=True)
    mate1_training = _train_graph(graph, mate1_train, _tg26u_config(_mate2_cfg(internal_cfg)))
    mate1_eval = _evaluate_mate1_materialized(graph, mate1_heldout, _mate2_cfg(internal_cfg))
    mate2_training = _train_mate2_chain(graph, mate2_train, _mate2_cfg(internal_cfg))
    handoff_training = _train_internal_handoff_gate(graph, mate2_train, internal_cfg)
    attention_modes = _evaluate_attention_modes_shared(graph, mate2_heldout, cfg, modes=modes)
    selected_for_lifecycle = _select_attention_mode(attention_modes)
    _apply_lifecycle_events(graph, attention_modes[selected_for_lifecycle].get("lifecycle_events", []))
    equivalence = _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(_mate2_cfg(internal_cfg)))), mate1_train, mate1_heldout)
    return {
        "graph": graph,
        "dataset": {
            "source": "generated legal KRK Mate_In_1 and strict forced Mate_In_2 positions",
            "mate1_train_count": len(mate1_train),
            "mate1_heldout_count": len(mate1_heldout),
            "mate2_train_count": len(mate2_train),
            "mate2_heldout_count": len(mate2_heldout),
            "train_repetitions": train_repetitions,
            "curriculum_labels_learner_visible": False,
            "mate2_heldout_fens": list(mate2_heldout),
        },
        "mate1_training": mate1_training,
        "mate1_heldout": mate1_eval,
        "mate2_training": {**mate2_training, "internal_handoff_training": handoff_training},
        "mate2_heldout": mate2_heldout,
        "attention_modes": attention_modes,
        "scheduler_equivalence": equivalence,
        "summary": {
            "mate1_accuracy": mate1_eval["accuracy"],
            "mate1_null_count": mate1_eval["null_count"],
            "best_attention_mode": _select_attention_mode(attention_modes),
            "best_conversion_rate": max((item["conversion_rate"] for item in attention_modes.values()), default=0.0),
            "m3_update_count": graph.m3_update_count,
        },
    }


def _evaluate_attention_mode(
    graph,
    fens: tuple[str, ...],
    cfg: ContinuousHandoffAttentionConfig,
    *,
    mode: str,
    mask_internal_handoff: bool = False,
    disable_mate2_quorum: bool = False,
    disable_mate1_quorum: bool = False,
    mask_actuator: bool = False,
    disable_deep_continuation: bool = False,
) -> dict[str, Any]:
    internal_cfg = _internal_cfg(cfg, train_repetitions=cfg.train_repetitions)
    rows: list[dict[str, Any]] = []
    all_strengths: list[float] = []
    all_scores: list[float] = []
    first_success = 0
    converted = 0
    same_graph_second = 0
    false_positive = 0
    false_negative = 0
    deep_reply_checks = 0
    top_k_count = 0
    tail_count = 0
    hard_rejected = 0
    exploration_rescue = 0
    materialized_mate2 = 0
    candidate_budget_used = 0
    fn_diag: list[dict[str, Any]] = []
    fp_diag: list[dict[str, Any]] = []
    for fen in fens:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        candidates: list[dict[str, Any]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            gate = _confirm_internal_handoff_gate(
                graph,
                board,
                move,
                internal_cfg,
                mask_internal_handoff=mask_internal_handoff,
                mask_actuator=mask_actuator,
            )
            gate["mask_internal_handoff"] = mask_internal_handoff
            gate["mask_actuator"] = mask_actuator
            attention = _attention_record(cfg, fen, move.uci(), gate)
            candidates.append({
                "move": move,
                "move_uci": move.uci(),
                "gate": gate,
                "attention": attention,
                "forced": move.uci() in forced,
            })
            all_strengths.append(attention["request_strength"])
            all_scores.append(attention["internal_handoff_score"])
        selected_moves = _select_for_attention_mode(cfg, mode, fen, candidates)
        selected_ucis = {item["move_uci"] for item in selected_moves}
        top_k_count += sum(1 for item in selected_moves if item["attention"]["selection_reason"].startswith("top"))
        tail_count += sum(1 for item in selected_moves if item["attention"]["selection_reason"] in {"epsilon_tail", "softmax_tail"})
        hard_rejected += sum(
            1
            for item in candidates
            if item["move_uci"] not in selected_ucis
            and item["attention"]["request_strength"] <= cfg.effectively_zero_request_strength
        )
        false_negative += sum(1 for item in candidates if item["forced"] and item["move_uci"] not in selected_ucis)
        false_positive += sum(1 for item in selected_moves if not item["forced"])
        candidate_budget_used += len(selected_moves)
        confirmed: list[dict[str, Any]] = []
        candidate_rows: list[dict[str, Any]] = []
        for item in candidates:
            selected_for_deep = item["move_uci"] in selected_ucis
            if selected_for_deep and not disable_deep_continuation:
                chain = _same_graph_chain_audit(
                    graph,
                    board,
                    item["move"],
                    _mate2_cfg(internal_cfg),
                    forced_move_ucis=None,
                    disable_mate1_quorum=disable_mate1_quorum,
                    mask_actuator=mask_actuator,
                )
            else:
                chain = {
                    "chain_success": False,
                    "reply_success_rate": 0.0,
                    "reply_total": 0,
                    "reply_solved": 0,
                    "same_graph_second_move_count": 0,
                    "reply_rows": [],
                    "disabled": disable_deep_continuation,
                    "deep_reply_check_skipped": not selected_for_deep,
                    "skip_reason": "low_request_strength_dormant" if not selected_for_deep else "deep_continuation_disabled",
                }
            deep_reply_checks += int(chain.get("reply_total", 0))
            if selected_for_deep:
                mate2 = _confirm_materialized_mate2_first(
                    graph,
                    board,
                    item["move"],
                    _mate2_cfg(internal_cfg),
                    chain=chain,
                    mask_action_check_atoms=False,
                    mask_actuator=mask_actuator,
                    disable_mate2_quorum=disable_mate2_quorum,
                )
            else:
                mate2 = _empty_mate2_audit(item["move_uci"], chain)
            if mate2["first_move_confirmed"]:
                confirmed.append(mate2)
                materialized_mate2 += 1
            _update_attention_lifecycle(graph, item, selected_for_deep=selected_for_deep)
            if item["forced"] and not selected_for_deep and len(fn_diag) < cfg.max_samples:
                fn_diag.append(_attention_diagnostic(item, chain=chain, audit=mate2, forced=forced))
            if selected_for_deep and not item["forced"] and len(fp_diag) < cfg.max_samples:
                fp_diag.append(_attention_diagnostic(item, chain=chain, audit=mate2, forced=forced))
            candidate_rows.append(_attention_diagnostic(item, chain=chain, audit=mate2, forced=forced))
        confirmed.sort(key=lambda item: (item["evidence_score"], item["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]
        selected_move = None if selected is None else selected["move"]
        ok_first = selected_move in forced
        ok_chain = bool(selected and selected["chain"]["chain_success"])
        first_success += int(ok_first)
        converted += int(ok_first and ok_chain)
        same_graph_second += 0 if selected is None else int(selected["chain"]["same_graph_second_move_count"])
        exploration_rescue += int(
            ok_first
            and any(item["move_uci"] == selected_move and item["attention"]["selection_reason"] in {"epsilon_tail", "softmax_tail"} for item in selected_moves)
        )
        rows.append({
            "fen": fen,
            "attention_mode": mode,
            "selected_first": selected_move,
            "forced_first_moves": sorted(forced),
            "first_move_success": ok_first,
            "converted": ok_first and ok_chain,
            "candidate_count": len(candidates),
            "selected_for_deep_count": len(selected_moves),
            "candidate_diagnostics": candidate_rows[: cfg.max_samples],
        })
    total = len(rows)
    return {
        "attention_mode": mode,
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "same_graph_second_move_count": same_graph_second,
        "request_strength_distribution": _distribution(all_strengths),
        "score_distribution": _distribution(all_scores),
        "top_k_candidate_count": top_k_count,
        "tail_sampled_candidate_count": tail_count,
        "hard_rejected_count": hard_rejected,
        "internal_attention_false_positive_count": false_positive,
        "internal_attention_false_negative_count": false_negative,
        "deep_reply_checks_run": deep_reply_checks,
        "average_deep_reply_checks_per_position": round(deep_reply_checks / max(1, total), 6),
        "exploration_rescue_count": exploration_rescue,
        "candidate_budget_used": candidate_budget_used,
        "materialized_mate2_quorum_confirmed_count": materialized_mate2,
        "false_negative_diagnostics": fn_diag,
        "false_positive_diagnostics": fp_diag,
        "validator_skip_used_during_eval": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "samples": rows[: cfg.max_samples],
    }


def _evaluate_attention_modes_shared(
    graph,
    fens: tuple[str, ...],
    cfg: ContinuousHandoffAttentionConfig,
    *,
    modes: tuple[str, ...],
    mask_internal_handoff: bool = False,
    disable_mate2_quorum: bool = False,
    disable_mate1_quorum: bool = False,
    mask_actuator: bool = False,
    disable_deep_continuation: bool = False,
) -> dict[str, Any]:
    internal_cfg = _internal_cfg(cfg, train_repetitions=cfg.train_repetitions)
    accum = {mode: _empty_mode_accumulator(mode) for mode in modes}
    all_strengths_by_mode = {mode: [] for mode in modes}
    all_scores_by_mode = {mode: [] for mode in modes}
    samples_by_mode = {mode: [] for mode in modes}
    fn_by_mode = {mode: [] for mode in modes}
    fp_by_mode = {mode: [] for mode in modes}
    lifecycle_by_mode = {mode: [] for mode in modes}
    for fen in fens:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        candidates: list[dict[str, Any]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            gate = _confirm_internal_handoff_gate(
                graph,
                board,
                move,
                internal_cfg,
                mask_internal_handoff=mask_internal_handoff,
                mask_actuator=mask_actuator,
            )
            gate["mask_internal_handoff"] = mask_internal_handoff
            gate["mask_actuator"] = mask_actuator
            attention = _attention_record(cfg, fen, move.uci(), gate)
            candidates.append({
                "move": move,
                "move_uci": move.uci(),
                "gate": gate,
                "attention": attention,
                "forced": move.uci() in forced,
            })
        selected_by_mode: dict[str, dict[str, str]] = {}
        union_selected: dict[str, dict[str, Any]] = {}
        for mode in modes:
            mode_candidates = _candidate_clones(candidates)
            selected = _select_for_attention_mode(cfg, mode, fen, mode_candidates)
            selected_by_mode[mode] = {item["move_uci"]: item["attention"]["selection_reason"] for item in selected}
            for item in selected:
                original = next(candidate for candidate in candidates if candidate["move_uci"] == item["move_uci"])
                union_selected[item["move_uci"]] = original
        chain_by_move: dict[str, dict[str, Any]] = {}
        audit_by_move: dict[str, dict[str, Any]] = {}
        for item in candidates:
            selected_for_any = item["move_uci"] in union_selected
            if selected_for_any and not disable_deep_continuation:
                chain = _same_graph_chain_audit(
                    graph,
                    board,
                    item["move"],
                    _mate2_cfg(internal_cfg),
                    forced_move_ucis=None,
                    disable_mate1_quorum=disable_mate1_quorum,
                    mask_actuator=mask_actuator,
                )
            else:
                chain = {
                    "chain_success": False,
                    "reply_success_rate": 0.0,
                    "reply_total": 0,
                    "reply_solved": 0,
                    "same_graph_second_move_count": 0,
                    "reply_rows": [],
                    "disabled": disable_deep_continuation,
                    "deep_reply_check_skipped": not selected_for_any,
                    "skip_reason": "low_request_strength_dormant" if not selected_for_any else "deep_continuation_disabled",
                }
            if selected_for_any:
                audit = _confirm_materialized_mate2_first(
                    graph,
                    board,
                    item["move"],
                    _mate2_cfg(internal_cfg),
                    chain=chain,
                    mask_action_check_atoms=False,
                    mask_actuator=mask_actuator,
                    disable_mate2_quorum=disable_mate2_quorum,
                )
            else:
                audit = _empty_mate2_audit(item["move_uci"], chain)
            chain_by_move[item["move_uci"]] = chain
            audit_by_move[item["move_uci"]] = audit
        for mode in modes:
            selected_reasons = selected_by_mode[mode]
            selected_ucis = set(selected_reasons)
            confirmed: list[dict[str, Any]] = []
            candidate_rows: list[dict[str, Any]] = []
            for item in candidates:
                all_strengths_by_mode[mode].append(item["attention"]["request_strength"])
                all_scores_by_mode[mode].append(item["attention"]["internal_handoff_score"])
                selected_for_deep = item["move_uci"] in selected_ucis
                clone = _candidate_with_reason(item, selected_reasons.get(item["move_uci"], "not_selected"))
                chain = chain_by_move[item["move_uci"]] if selected_for_deep else _empty_chain(selected_for_deep=False)
                audit = audit_by_move[item["move_uci"]] if selected_for_deep else _empty_mate2_audit(item["move_uci"], chain)
                if selected_for_deep and audit["first_move_confirmed"]:
                    confirmed.append(audit)
                    accum[mode]["materialized_mate2"] += 1
                if item["forced"] and not selected_for_deep and len(fn_by_mode[mode]) < cfg.max_samples:
                    fn_by_mode[mode].append(_attention_diagnostic(clone, chain=chain, audit=audit, forced=forced))
                if selected_for_deep and not item["forced"] and len(fp_by_mode[mode]) < cfg.max_samples:
                    fp_by_mode[mode].append(_attention_diagnostic(clone, chain=chain, audit=audit, forced=forced))
                candidate_rows.append(_attention_diagnostic(clone, chain=chain, audit=audit, forced=forced))
                lifecycle_by_mode[mode].append({
                    "handoff_quorum_script_id": item["gate"]["handoff_quorum_script_id"],
                    "selected_for_deep": selected_for_deep,
                    "forced": item["forced"],
                })
            confirmed.sort(key=lambda item: (item["evidence_score"], item["move"]), reverse=True)
            selected = None if not confirmed else confirmed[0]
            selected_move = None if selected is None else selected["move"]
            ok_first = selected_move in forced
            ok_chain = bool(selected and selected["chain"]["chain_success"])
            top_count = sum(1 for reason in selected_reasons.values() if reason.startswith("top"))
            tail_count = sum(1 for reason in selected_reasons.values() if reason in {"epsilon_tail", "softmax_tail"})
            hard_rejected = sum(
                1
                for item in candidates
                if item["move_uci"] not in selected_ucis
                and item["attention"]["request_strength"] <= cfg.effectively_zero_request_strength
            )
            false_negative = sum(1 for item in candidates if item["forced"] and item["move_uci"] not in selected_ucis)
            false_positive = sum(1 for item in candidates if (not item["forced"]) and item["move_uci"] in selected_ucis)
            checks = sum(int(chain_by_move[uci].get("reply_total", 0)) for uci in selected_ucis)
            accum[mode]["first_success"] += int(ok_first)
            accum[mode]["converted"] += int(ok_first and ok_chain)
            accum[mode]["same_graph_second"] += 0 if selected is None else int(selected["chain"]["same_graph_second_move_count"])
            accum[mode]["top_k_count"] += top_count
            accum[mode]["tail_count"] += tail_count
            accum[mode]["hard_rejected"] += hard_rejected
            accum[mode]["false_negative"] += false_negative
            accum[mode]["false_positive"] += false_positive
            accum[mode]["deep_reply_checks"] += checks
            accum[mode]["candidate_budget_used"] += len(selected_ucis)
            accum[mode]["exploration_rescue"] += int(
                ok_first
                and selected_move in selected_reasons
                and selected_reasons[selected_move] in {"epsilon_tail", "softmax_tail"}
            )
            samples_by_mode[mode].append({
                "fen": fen,
                "attention_mode": mode,
                "selected_first": selected_move,
                "forced_first_moves": sorted(forced),
                "first_move_success": ok_first,
                "converted": ok_first and ok_chain,
                "candidate_count": len(candidates),
                "selected_for_deep_count": len(selected_ucis),
                "candidate_diagnostics": candidate_rows[: cfg.max_samples],
            })
    results: dict[str, Any] = {}
    for mode in modes:
        results[mode] = _finalize_mode_result(
            cfg,
            accum[mode],
            position_count=len(fens),
            strengths=all_strengths_by_mode[mode],
            scores=all_scores_by_mode[mode],
            false_negative_diagnostics=fn_by_mode[mode],
            false_positive_diagnostics=fp_by_mode[mode],
            lifecycle_events=lifecycle_by_mode[mode],
            samples=samples_by_mode[mode],
        )
    return results


def _select_for_attention_mode(
    cfg: ContinuousHandoffAttentionConfig,
    mode: str,
    fen: str,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    eligible = [item for item in candidates if item["attention"]["request_strength"] > cfg.effectively_zero_request_strength]
    if mode == "binary_gate_baseline":
        selected = [item for item in candidates if item["gate"]["internal_handoff_approved"]]
        for item in selected:
            item["attention"]["selection_reason"] = "binary_approved"
        return selected
    if mode == "high_recall_threshold_gate":
        selected = [item for item in eligible if item["attention"]["request_strength"] >= cfg.high_recall_threshold]
        for item in selected:
            item["attention"]["selection_reason"] = "threshold"
        return selected
    ranked = sorted(eligible, key=lambda item: (item["attention"]["request_strength"], item["attention"]["internal_handoff_score"], item["move_uci"]), reverse=True)
    if mode == "top_k_request_strength":
        selected = ranked[: cfg.top_k]
        for item in selected:
            item["attention"]["selection_reason"] = "top_k"
        return selected
    if mode == "top_k_epsilon_exploration":
        top = ranked[: cfg.top_k]
        rest = ranked[cfg.top_k :]
        tail = _stable_tail_sample(fen, rest, cfg.epsilon_tail_count)
        for item in top:
            item["attention"]["selection_reason"] = "top_k"
        for item in tail:
            item["attention"]["selection_reason"] = "epsilon_tail"
        return _dedupe_candidates([*top, *tail])
    if mode == "softmax_temperature_sampling":
        softmaxed = _softmax_ranked(ranked, cfg.softmax_temperature)
        selected = [item for item, _prob in softmaxed[: cfg.softmax_budget]]
        if len(softmaxed) > cfg.softmax_budget:
            tail = _stable_tail_sample(f"softmax|{fen}", [item for item, _prob in softmaxed[cfg.softmax_budget :]], 1)
            for item in tail:
                item["attention"]["selection_reason"] = "softmax_tail"
            selected.extend(tail)
        for item in selected:
            item["attention"].setdefault("selection_reason", "softmax_top")
        return _dedupe_candidates(selected)
    if mode == "two_stage_attention":
        selected = ranked[: cfg.two_stage_top_k]
        for item in selected:
            item["attention"]["selection_reason"] = "top_broad_attention"
        return selected
    raise ValueError(f"unknown attention mode: {mode}")


def _empty_mode_accumulator(mode: str) -> dict[str, Any]:
    return {
        "attention_mode": mode,
        "first_success": 0,
        "converted": 0,
        "same_graph_second": 0,
        "top_k_count": 0,
        "tail_count": 0,
        "hard_rejected": 0,
        "false_positive": 0,
        "false_negative": 0,
        "deep_reply_checks": 0,
        "exploration_rescue": 0,
        "candidate_budget_used": 0,
        "materialized_mate2": 0,
    }


def _finalize_mode_result(
    cfg: ContinuousHandoffAttentionConfig,
    accum: dict[str, Any],
    *,
    position_count: int,
    strengths: list[float],
    scores: list[float],
    false_negative_diagnostics: list[dict[str, Any]],
    false_positive_diagnostics: list[dict[str, Any]],
    lifecycle_events: list[dict[str, Any]],
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "attention_mode": accum["attention_mode"],
        "position_count": position_count,
        "first_move_success_count": accum["first_success"],
        "first_move_success_rate": 0.0 if position_count == 0 else accum["first_success"] / position_count,
        "conversion_count": accum["converted"],
        "conversion_rate": 0.0 if position_count == 0 else accum["converted"] / position_count,
        "same_graph_second_move_count": accum["same_graph_second"],
        "request_strength_distribution": _distribution(strengths),
        "score_distribution": _distribution(scores),
        "top_k_candidate_count": accum["top_k_count"],
        "tail_sampled_candidate_count": accum["tail_count"],
        "hard_rejected_count": accum["hard_rejected"],
        "internal_attention_false_positive_count": accum["false_positive"],
        "internal_attention_false_negative_count": accum["false_negative"],
        "deep_reply_checks_run": accum["deep_reply_checks"],
        "average_deep_reply_checks_per_position": round(accum["deep_reply_checks"] / max(1, position_count), 6),
        "exploration_rescue_count": accum["exploration_rescue"],
        "candidate_budget_used": accum["candidate_budget_used"],
        "materialized_mate2_quorum_confirmed_count": accum["materialized_mate2"],
        "false_negative_diagnostics": false_negative_diagnostics[: cfg.max_samples],
        "false_positive_diagnostics": false_positive_diagnostics[: cfg.max_samples],
        "lifecycle_events": lifecycle_events,
        "validator_skip_used_during_eval": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "samples": samples[: cfg.max_samples],
    }


def _candidate_clones(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **item,
            "attention": dict(item["attention"]),
        }
        for item in candidates
    ]


def _candidate_with_reason(item: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        **item,
        "attention": {
            **item["attention"],
            "selection_reason": reason,
        },
    }


def _empty_chain(*, selected_for_deep: bool) -> dict[str, Any]:
    return {
        "chain_success": False,
        "reply_success_rate": 0.0,
        "reply_total": 0,
        "reply_solved": 0,
        "same_graph_second_move_count": 0,
        "reply_rows": [],
        "disabled": False,
        "deep_reply_check_skipped": not selected_for_deep,
        "skip_reason": "low_request_strength_dormant" if not selected_for_deep else "not_evaluated",
    }


def _attention_record(
    cfg: ContinuousHandoffAttentionConfig,
    fen: str,
    move_uci: str,
    gate: dict[str, Any],
) -> dict[str, Any]:
    score = float(gate["internal_handoff_score"])
    positive_count = int(gate["confirmed_positive_handoff_atom_count"])
    negative_count = len(gate["negative_handoff_atoms"])
    masked = bool(gate.get("mask_internal_handoff")) or bool(gate.get("mask_actuator"))
    raw = score + 0.20 * positive_count - 0.03 * negative_count
    uncertainty = 0.0 if masked else min(0.12, 1.0 / (1.0 + abs(raw)) * 0.25)
    request_strength = 0.0 if masked else _sigmoid(raw / max(0.001, cfg.request_strength_temperature))
    request_strength = min(1.0, max(0.0, request_strength + uncertainty))
    return {
        "move": move_uci,
        "internal_handoff_score": round(score, 6),
        "request_strength": round(request_strength, 6),
        "positive_attention_atoms": gate["positive_handoff_atoms"],
        "negative_veto_atoms": gate["negative_handoff_atoms"],
        "confirmed_positive_attention_atom_count": positive_count,
        "uncertainty_exploration_bonus": round(uncertainty, 6),
        "hard_rejected": request_strength <= cfg.effectively_zero_request_strength,
        "selection_reason": "not_selected",
        "handoff_quorum_script_id": gate["handoff_quorum_script_id"],
        "fen_digest": hashlib.sha1(fen.encode("utf-8")).hexdigest()[:12],
    }


def _apply_lifecycle_events(graph, events: list[dict[str, Any]]) -> None:
    for event in events:
        terminal_id = f"{event['handoff_quorum_script_id']}_evidence_terminal"
        if terminal_id not in graph.graph.nodes:
            continue
        node = graph.graph.nodes[terminal_id]
        node.meta["request_exposures"] = int(node.meta.get("request_exposures", 0)) + 1
        node.meta["activation_count"] = int(node.meta.get("activation_count", 0)) + int(event["selected_for_deep"])
        if event["selected_for_deep"] and event["forced"]:
            node.meta["confirm_count"] = int(node.meta.get("confirm_count", 0)) + 1
            node.meta["handoff_positive_count"] = int(node.meta.get("handoff_positive_count", 0)) + 1
        elif event["selected_for_deep"]:
            node.meta["false_positive_count"] = int(node.meta.get("false_positive_count", 0)) + 1
            node.meta["handoff_negative_count"] = int(node.meta.get("handoff_negative_count", 0)) + 1
        elif event["forced"]:
            node.meta["false_negative_count"] = int(node.meta.get("false_negative_count", 0)) + 1
            node.meta["handoff_false_negative_count"] = int(node.meta.get("handoff_false_negative_count", 0)) + 1


def _binary_mode_result(binary: dict[str, Any], cfg: ContinuousHandoffAttentionConfig) -> dict[str, Any]:
    strengths: list[float] = []
    scores: list[float] = []
    for sample in binary.get("samples", []):
        for row in sample.get("candidate_diagnostics", []):
            score = row.get("internal_handoff_score")
            if score is not None:
                scores.append(float(score))
                strengths.append(_sigmoid(float(score) / max(0.001, cfg.request_strength_temperature)))
    checks = _deep_reply_checks(binary)
    return {
        "attention_mode": "binary_gate_baseline",
        "position_count": binary["position_count"],
        "first_move_success_count": binary["first_move_success_count"],
        "first_move_success_rate": binary["first_move_success_rate"],
        "conversion_count": binary["conversion_count"],
        "conversion_rate": binary["conversion_rate"],
        "same_graph_second_move_count": binary["same_graph_second_move_count"],
        "request_strength_distribution": _distribution(strengths),
        "score_distribution": _distribution(scores),
        "top_k_candidate_count": binary["internal_gate_approved_candidate_count"],
        "tail_sampled_candidate_count": 0,
        "hard_rejected_count": binary["internal_gate_rejected_candidate_count"],
        "internal_attention_false_positive_count": binary["false_positive_internal_gate_count"],
        "internal_attention_false_negative_count": binary["false_negative_internal_gate_count"],
        "deep_reply_checks_run": checks,
        "average_deep_reply_checks_per_position": round(checks / max(1, binary["position_count"]), 6),
        "exploration_rescue_count": 0,
        "candidate_budget_used": binary["internal_gate_approved_candidate_count"],
        "materialized_mate2_quorum_confirmed_count": binary["materialized_mate2_quorum_confirmed_count"],
        "false_negative_diagnostics": _filter_diagnostics(binary, forced=True, selected=False, max_count=cfg.max_samples),
        "false_positive_diagnostics": _filter_diagnostics(binary, forced=False, selected=True, max_count=cfg.max_samples),
        "validator_skip_used_during_eval": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "samples": binary.get("samples", [])[: cfg.max_samples],
    }


def _run_ablations(graph, fens: tuple[str, ...], cfg: ContinuousHandoffAttentionConfig, mode: str) -> dict[str, Any]:
    return {
        "mask_internal_handoff_attention": _ablation_summary(_evaluate_attention_modes_shared(
            graph, fens, cfg, modes=(mode,), mask_internal_handoff=True
        )[mode]),
        "mask_mate2_first_move_quorum": _ablation_summary(_evaluate_attention_modes_shared(
            graph, fens, cfg, modes=(mode,), disable_mate2_quorum=True
        )[mode]),
        "mask_mate1_quorum": _ablation_summary(_evaluate_attention_modes_shared(
            graph, fens, cfg, modes=(mode,), disable_mate1_quorum=True
        )[mode]),
        "mask_actuator_terminals": _ablation_summary(_evaluate_attention_modes_shared(
            graph, fens, cfg, modes=(mode,), mask_actuator=True
        )[mode]),
        "disable_deep_continuation_checks": _ablation_summary(_evaluate_attention_modes_shared(
            graph, fens, cfg, modes=(mode,), disable_deep_continuation=True
        )[mode]),
    }


def _decision(
    cfg: ContinuousHandoffAttentionConfig,
    run: dict[str, Any],
    selected_mode: str,
    selected: dict[str, Any],
    lifecycle: dict[str, Any],
    equivalence: dict[str, Any],
    ablations: dict[str, Any],
) -> dict[str, Any]:
    checks_ok = selected["deep_reply_checks_run"] <= max(1, selected["position_count"]) * 250
    ablations_collapse = (
        ablations["mask_internal_handoff_attention"]["conversion_rate"] < selected["conversion_rate"]
        and ablations["mask_mate1_quorum"]["conversion_rate"] == 0.0
        and ablations["mask_actuator_terminals"]["conversion_rate"] == 0.0
    )
    pass_threshold = max(1, math.ceil(run["dataset"]["mate2_heldout_count"] * (4 / 6)))
    return {
        "checkpoint_pass": (
            run["mate1_heldout"]["accuracy"] >= 1.0
            and run["mate1_heldout"]["null_count"] == 0
            and selected["conversion_count"] >= pass_threshold
            and selected["internal_attention_false_negative_count"] <= 1
            and selected["same_graph_second_move_count"] > 0
            and checks_ok
            and ablations_collapse
            and equivalence["mismatch_count"] == 0
            and not _purity_boundary()["validator_skip_used_during_internal_handoff_eval"]
        ),
        "selected_attention_mode": selected_mode,
        "mate1_heldout_accuracy": run["mate1_heldout"]["accuracy"],
        "mate1_null_count": run["mate1_heldout"]["null_count"],
        "mate2_conversion_rate": selected["conversion_rate"],
        "mate2_first_move_success_rate": selected["first_move_success_rate"],
        "mate2_same_graph_second_move_count": selected["same_graph_second_move_count"],
        "request_strength_distribution": selected["request_strength_distribution"],
        "top_k_candidate_count": selected["top_k_candidate_count"],
        "tail_sampled_candidate_count": selected["tail_sampled_candidate_count"],
        "internal_attention_false_positive_count": selected["internal_attention_false_positive_count"],
        "internal_attention_false_negative_count": selected["internal_attention_false_negative_count"],
        "deep_reply_checks_run": selected["deep_reply_checks_run"],
        "average_deep_reply_checks_per_position": selected["average_deep_reply_checks_per_position"],
        "conversion_per_attention_mode": {
            mode: {
                "conversion_rate": value["conversion_rate"],
                "first_move_success_rate": value["first_move_success_rate"],
                "false_negative_count": value["internal_attention_false_negative_count"],
                "false_positive_count": value["internal_attention_false_positive_count"],
                "deep_reply_checks_run": value["deep_reply_checks_run"],
            }
            for mode, value in run["attention_modes"].items()
        },
        "false_negative_diagnostics": selected["false_negative_diagnostics"],
        "false_positive_diagnostics": selected["false_positive_diagnostics"],
        "exploration_rescue_count": selected["exploration_rescue_count"],
        "candidate_budget_used": selected["candidate_budget_used"],
        "terminal_kind_lifecycle_active": True,
        "pruning_count_by_terminal_kind": lifecycle["pruning_count_by_terminal_kind"],
        "m4_promotion_count_by_terminal_kind": lifecycle["m4_promotion_count_by_terminal_kind"],
        "m3_update_count": run["graph"].m3_update_count,
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "ablation_results": ablations,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "purity_boundary": _purity_boundary(),
        "failure_mode": _failure_mode(run, selected, checks_ok),
    }


def _select_attention_mode(attention_modes: dict[str, Any]) -> str:
    if not attention_modes:
        return "none"
    return max(
        attention_modes,
        key=lambda mode: (
            attention_modes[mode]["conversion_count"],
            -attention_modes[mode]["internal_attention_false_negative_count"],
            -attention_modes[mode]["deep_reply_checks_run"],
            attention_modes[mode]["first_move_success_count"],
        ),
    )


def _update_attention_lifecycle(graph, item: dict[str, Any], *, selected_for_deep: bool) -> None:
    terminal_id = f"{item['gate']['handoff_quorum_script_id']}_evidence_terminal"
    if terminal_id not in graph.graph.nodes:
        return
    node = graph.graph.nodes[terminal_id]
    node.meta["request_exposures"] = int(node.meta.get("request_exposures", 0)) + 1
    node.meta["activation_count"] = int(node.meta.get("activation_count", 0)) + int(selected_for_deep)
    if selected_for_deep and item["forced"]:
        node.meta["confirm_count"] = int(node.meta.get("confirm_count", 0)) + 1
        node.meta["handoff_positive_count"] = int(node.meta.get("handoff_positive_count", 0)) + 1
    elif selected_for_deep:
        node.meta["false_positive_count"] = int(node.meta.get("false_positive_count", 0)) + 1
        node.meta["handoff_negative_count"] = int(node.meta.get("handoff_negative_count", 0)) + 1
    elif item["forced"]:
        node.meta["false_negative_count"] = int(node.meta.get("false_negative_count", 0)) + 1
        node.meta["handoff_false_negative_count"] = int(node.meta.get("handoff_false_negative_count", 0)) + 1


def _attention_diagnostic(item: dict[str, Any], *, chain: dict[str, Any], audit: dict[str, Any], forced: set[str]) -> dict[str, Any]:
    attention = item["attention"]
    return {
        "move": item["move_uci"],
        "validator_forced_first_move": item["move_uci"] in forced,
        "internal_handoff_score": attention["internal_handoff_score"],
        "request_strength": attention["request_strength"],
        "selection_reason": attention["selection_reason"],
        "positive_attention_atoms": attention["positive_attention_atoms"],
        "negative_veto_atoms": attention["negative_veto_atoms"],
        "uncertainty_exploration_bonus": attention["uncertainty_exploration_bonus"],
        "deep_reply_checks_run": int(chain.get("reply_total", 0)) > 0,
        "reply_total": int(chain.get("reply_total", 0)),
        "reply_solved": int(chain.get("reply_solved", 0)),
        "same_graph_second_move_count": int(chain.get("same_graph_second_move_count", 0)),
        "chain_success": bool(chain.get("chain_success", False)),
        "materialized_quorum_script_id": audit.get("quorum_script_id"),
        "actuator_terminal_state": audit.get("actuator_terminal_state"),
        "FormalReConEngine_confirmation_state": audit.get("graph_confirmation_state"),
    }


def _distribution(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None, "mean": None}
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min": round(ordered[0], 6),
        "p25": round(_percentile(ordered, 0.25), 6),
        "median": round(_percentile(ordered, 0.50), 6),
        "p75": round(_percentile(ordered, 0.75), 6),
        "max": round(ordered[-1], 6),
        "mean": round(sum(ordered) / len(ordered), 6),
    }


def _percentile(ordered: list[float], q: float) -> float:
    if len(ordered) == 1:
        return ordered[0]
    idx = (len(ordered) - 1) * q
    low = math.floor(idx)
    high = math.ceil(idx)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - idx) + ordered[high] * (idx - low)


def _sigmoid(value: float) -> float:
    if value >= 50:
        return 1.0
    if value <= -50:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def _softmax_ranked(candidates: list[dict[str, Any]], temperature: float) -> list[tuple[dict[str, Any], float]]:
    if not candidates:
        return []
    logits = [item["attention"]["request_strength"] / max(0.001, temperature) for item in candidates]
    max_logit = max(logits)
    weights = [math.exp(logit - max_logit) for logit in logits]
    total = sum(weights)
    return sorted(zip(candidates, [weight / total for weight in weights]), key=lambda item: (item[1], item[0]["move_uci"]), reverse=True)


def _stable_tail_sample(seed: str, candidates: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    ordered = sorted(
        candidates,
        key=lambda item: hashlib.sha1(f"{seed}|{item['move_uci']}".encode("utf-8")).hexdigest(),
    )
    return ordered[: max(0, count)]


def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in candidates:
        if item["move_uci"] in seen:
            continue
        seen.add(item["move_uci"])
        result.append(item)
    return result


def _filter_diagnostics(binary: dict[str, Any], *, forced: bool, selected: bool, max_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample in binary.get("samples", []):
        for row in sample.get("candidate_diagnostics", []):
            was_forced = bool(row.get("validator_forced_first_move"))
            was_selected = bool(row.get("deep_reply_checks_run"))
            if was_forced == forced and was_selected == selected:
                rows.append(row)
            if len(rows) >= max_count:
                return rows
    return rows


def _deep_reply_checks(result: dict[str, Any]) -> int:
    total = 0
    for sample in result.get("samples", []):
        for row in sample.get("candidate_diagnostics", []):
            total += int(row.get("reply_total", 0))
    return total


def _ablation_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "conversion_rate": result["conversion_rate"],
        "first_move_success_rate": result["first_move_success_rate"],
        "same_graph_second_move_count": result["same_graph_second_move_count"],
        "internal_attention_false_negative_count": result["internal_attention_false_negative_count"],
        "deep_reply_checks_run": result["deep_reply_checks_run"],
    }


def _write_progress(cfg: ContinuousHandoffAttentionConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _internal_cfg(cfg: ContinuousHandoffAttentionConfig, *, train_repetitions: int) -> InternalHandoffAffordanceConfig:
    return InternalHandoffAffordanceConfig(
        seed=cfg.seed,
        mate1_train_count=cfg.mate1_train_count,
        mate1_heldout_count=cfg.mate1_heldout_count,
        mate2_train_count=cfg.mate2_train_count,
        mate2_heldout_count=cfg.mate2_heldout_count,
        max_generation_attempts=cfg.max_generation_attempts,
        train_repetitions=train_repetitions,
        continuation_repetitions=cfg.continuation_repetitions,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        eta_m3=cfg.eta_m3,
        handoff_eta_scale=cfg.handoff_eta_scale,
        max_abs_local_weight=cfg.max_abs_local_weight,
        max_candidates_per_move=cfg.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=cfg.max_shared_atom_candidates_per_choice,
        shared_atom_min_overlap=cfg.shared_atom_min_overlap,
        min_vote_score=cfg.min_vote_score,
        soft_quorum_min_positive_atoms=cfg.soft_quorum_min_positive_atoms,
        materialized_quorum_min_positive_atoms=cfg.materialized_quorum_min_positive_atoms,
        mate2_materialized_quorum_min_positive_atoms=cfg.mate2_materialized_quorum_min_positive_atoms,
        handoff_gate_min_positive_atoms=cfg.handoff_gate_min_positive_atoms,
        handoff_gate_min_score=cfg.handoff_gate_min_score,
        materialized_quorum_min_evidence=cfg.materialized_quorum_min_evidence,
        veto_evidence_threshold=cfg.veto_evidence_threshold,
        first_move_chain_min_reply_success_rate=cfg.first_move_chain_min_reply_success_rate,
        guardless_probe_position_count=0,
        equivalence_count=cfg.equivalence_count,
    )


def _failure_mode(run: dict[str, Any], selected: dict[str, Any], checks_ok: bool) -> str:
    if run["mate1_heldout"]["accuracy"] < 1.0 or run["mate1_heldout"]["null_count"] > 0:
        return "Mate_In_1_continuation_weakness"
    if selected["internal_attention_false_negative_count"] > 1:
        return "request_strength_scoring_false_negatives"
    if not checks_ok:
        return "false_positives_causing_compute_explosion"
    if selected["conversion_rate"] == 0.0:
        return "Mate_In_2_quorum_or_handoff_weakness"
    if selected["same_graph_second_move_count"] == 0:
        return "same_graph_continuation_weakness"
    if selected["conversion_count"] < math.ceil(run["dataset"]["mate2_heldout_count"] * (4 / 6)):
        return "exploration_or_attention_insufficient"
    return "none"


def _purity_boundary() -> dict[str, Any]:
    return {
        "native_recon_graph_execution": True,
        "continuous_handoff_attention": True,
        "terminal_kind_lifecycle_active": True,
        "same_native_graph_for_mate1_and_mate2": True,
        "materialized_mate1_quorum": True,
        "materialized_mate2_quorum": True,
        "internal_handoff_affordance_materialized": True,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_touched": False,
    }
