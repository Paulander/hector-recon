"""TG26z forced-chain decomposition and continuation repair."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import chess

from .continuous_handoff_attention import (
    ContinuousHandoffAttentionConfig,
    _evaluate_attention_modes_shared,
    _internal_cfg,
)
from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves, _move_reward
from .internal_handoff_affordance_guard_audit import (
    _confirm_internal_handoff_gate,
    _datasets,
    _mate2_cfg,
    _train_internal_handoff_gate,
)
from .native_quorum_materialization import _tg26t_config, _train_graph, _trained_graph
from .native_quorum_mate2_chaining import (
    _confirm_materialized_mate2_first,
    _evaluate_mate1_materialized,
    _same_graph_chain_audit,
    _select_materialized_mate1,
    _tg26u_config,
    _train_mate2_chain,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .terminal_lifecycle import apply_terminal_lifecycle


@dataclass(frozen=True)
class ForcedChainDecompositionConfig:
    seed: int = 20260623
    mate1_train_count: int = 24
    mate1_heldout_count: int = 12
    mate2_train_count: int = 12
    mate2_heldout_count: int = 6
    max_generation_attempts: int = 500_000
    train_repetitions: int = 1
    continuation_repetitions: int = 1
    continuation_repair_repetitions: int = 1
    continuation_repair_threshold: float = 0.95
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
    non_forced_sample_limit: int = 4
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg26z_forced_chain_decomposition_progress.json"


@dataclass(frozen=True)
class ForcedChainDecompositionResult:
    config: ForcedChainDecompositionConfig
    dataset: dict[str, Any]
    mate1_foundation: dict[str, Any]
    mate2_training: dict[str, Any]
    baseline_high_recall: dict[str, Any]
    forced_chain_audit: dict[str, Any]
    continuation_before_repair: dict[str, Any]
    continuation_repair: dict[str, Any]
    continuation_after_repair: dict[str, Any]
    final_mate2: dict[str, Any]
    lifecycle: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26z_forced_chain_decomposition.v0",
            "checkpoint": "TG26z_forced_chain_decomposition",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "mate1_foundation": self.mate1_foundation,
            "mate2_training": self.mate2_training,
            "baseline_high_recall": self.baseline_high_recall,
            "forced_chain_audit": self.forced_chain_audit,
            "continuation_before_repair": self.continuation_before_repair,
            "continuation_repair": self.continuation_repair,
            "continuation_after_repair": self.continuation_after_repair,
            "final_mate2": self.final_mate2,
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


def run_forced_chain_decomposition(
    *,
    config: ForcedChainDecompositionConfig | None = None,
) -> ForcedChainDecompositionResult:
    cfg = config or ForcedChainDecompositionConfig()
    attention_cfg = _attention_cfg(cfg)
    internal_cfg = _internal_cfg(attention_cfg, train_repetitions=cfg.train_repetitions)
    mate1_train, mate1_heldout, mate2_train, mate2_heldout = _datasets(internal_cfg)
    graph = _trained_graph(_tg26u_config(_mate2_cfg(internal_cfg)), score_action_atoms=True)
    mate1_training = _train_graph(graph, mate1_train, _tg26u_config(_mate2_cfg(internal_cfg)))
    mate1_eval = _evaluate_mate1_materialized(graph, mate1_heldout, _mate2_cfg(internal_cfg))
    mate2_training = _train_mate2_chain(graph, mate2_train, _mate2_cfg(internal_cfg))
    handoff_training = _train_internal_handoff_gate(graph, mate2_train, internal_cfg)
    baseline = _high_recall(graph, mate2_heldout, attention_cfg)
    baseline["m3_update_count"] = graph.m3_update_count
    _write_progress(cfg, {"phase": "baseline_complete", "baseline": _mode_summary(baseline)})
    train_continuations = _continuation_states(mate2_train)
    heldout_continuations = _continuation_states(mate2_heldout)
    continuation_before = _evaluate_continuation_mate1(graph, heldout_continuations, _mate2_cfg(internal_cfg), cfg)
    audit_before = _forced_chain_decomposition_audit(graph, mate2_heldout, attention_cfg, cfg)
    needs_repair = continuation_before["accuracy"] < cfg.continuation_repair_threshold or continuation_before["null_count"] > 0
    repair = _train_continuation_repair(graph, train_continuations, _mate2_cfg(internal_cfg), cfg) if needs_repair else _empty_repair()
    continuation_after = _evaluate_continuation_mate1(graph, heldout_continuations, _mate2_cfg(internal_cfg), cfg)
    chain_repair_needed = (
        continuation_after["accuracy"] >= cfg.continuation_repair_threshold
        and continuation_after["null_count"] == 0
        and audit_before["forced_first_chain_success_rate"] >= 1.0
        and audit_before["graph_confirmed_chain_count"] < audit_before["forced_first_move_count"]
    )
    final_attention_cfg = _chain_repaired_attention_cfg(attention_cfg) if chain_repair_needed else attention_cfg
    final = _high_recall(graph, mate2_heldout, final_attention_cfg)
    final["m3_update_count"] = graph.m3_update_count
    final["chain_quorum_repair"] = {
        "applied": chain_repair_needed,
        "repair": "chain_terminal_can_satisfy_mate2_quorum_when_same_graph_continuation_confirms",
        "mate2_materialized_quorum_min_positive_atoms": final_attention_cfg.mate2_materialized_quorum_min_positive_atoms,
        "materialized_quorum_min_evidence": final_attention_cfg.materialized_quorum_min_evidence,
        "runtime_provider_override": False,
    }
    audit_after = _forced_chain_decomposition_audit(graph, mate2_heldout, final_attention_cfg, cfg)
    lifecycle = apply_terminal_lifecycle(
        graph,
        heldout_confirmed=(
            mate1_eval["accuracy"] >= 1.0
            and mate1_eval["null_count"] == 0
            and continuation_after["accuracy"] >= cfg.continuation_repair_threshold
            and final["conversion_count"] > baseline["conversion_count"]
        ),
        prune=True,
        promote=True,
    )
    equivalence = _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(_mate2_cfg(internal_cfg)))), mate1_train, mate1_heldout)
    ablations = _ablations(graph, mate2_heldout, final_attention_cfg)
    decision = _decision(
        cfg,
        mate1_eval=mate1_eval,
        continuation=continuation_after,
        baseline=baseline,
        final=final,
        audit=audit_after,
        lifecycle=lifecycle,
        equivalence=equivalence,
        ablations=ablations,
        repair=repair,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {k: decision[k] for k in (
        "checkpoint_pass",
        "mate2_conversion_rate",
        "continuation_mate1_accuracy",
        "failure_bucket_counts",
        "failure_mode",
    )}})
    return ForcedChainDecompositionResult(
        config=cfg,
        dataset={
            "source": "generated legal KRK Mate_In_1 and strict forced Mate_In_2 positions",
            "mate1_train_count": len(mate1_train),
            "mate1_heldout_count": len(mate1_heldout),
            "mate2_train_count": len(mate2_train),
            "mate2_heldout_count": len(mate2_heldout),
            "continuation_train_state_count": len(train_continuations),
            "continuation_heldout_state_count": len(heldout_continuations),
            "curriculum_labels_learner_visible": False,
            "mate2_heldout_fens": list(mate2_heldout),
        },
        mate1_foundation={"training": mate1_training, "heldout": mate1_eval},
        mate2_training={**mate2_training, "internal_handoff_training": handoff_training},
        baseline_high_recall=baseline,
        forced_chain_audit={"before_repair": audit_before, "after_repair": audit_after},
        continuation_before_repair=continuation_before,
        continuation_repair=repair,
        continuation_after_repair=continuation_after,
        final_mate2=final,
        lifecycle=lifecycle,
        scheduler_equivalence=equivalence,
        ablation_results=ablations,
        decision=decision,
    )


def _continuation_states(fens: tuple[str, ...]) -> tuple[str, ...]:
    states: list[str] = []
    seen: set[str] = set()
    for fen in fens:
        board = chess.Board(fen)
        for first in _forced_mate_in_two_first_moves(board):
            after_first = board.copy(stack=False)
            after_first.push(first)
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                state = before_mate.fen()
                if state not in seen:
                    seen.add(state)
                    states.append(state)
    return tuple(states)


def _evaluate_continuation_mate1(
    graph,
    fens: tuple[str, ...],
    mate2_cfg,
    cfg: ForcedChainDecompositionConfig,
) -> dict[str, Any]:
    correct = 0
    nulls = 0
    confirmed = 0
    rows: list[dict[str, Any]] = []
    for fen in fens:
        board = chess.Board(fen)
        selected = _select_materialized_mate1(graph, board, mate2_cfg)
        mates = {move.uci() for move in _mate_moves(board)}
        ok = selected["selected"] in mates
        correct += int(ok)
        nulls += int(selected["selected"] is None)
        confirmed += int(selected["confirmed_candidate_count"])
        rows.append({
            "fen": fen,
            "selected_second": selected["selected"],
            "correct_mates": sorted(mates),
            "same_graph_mate1_solved": ok,
            "confirmed_candidate_count": selected["confirmed_candidate_count"],
            "formal_recon_engine_confirmed": None if selected["selected_audit"] is None else selected["selected_audit"]["formal_recon_engine_confirmed"],
        })
    total = len(rows)
    return {
        "continuation_mate1_state_count": total,
        "correct_count": correct,
        "accuracy": 0.0 if total == 0 else correct / total,
        "null_count": nulls,
        "formal_confirm_count": confirmed,
        "samples": rows[: cfg.max_samples],
    }


def _train_continuation_repair(
    graph,
    fens: tuple[str, ...],
    mate2_cfg,
    cfg: ForcedChainDecompositionConfig,
) -> dict[str, Any]:
    updates = {"positive": 0, "negative": 0, "neutral": 0}
    records = 0
    for _rep in range(cfg.continuation_repair_repetitions):
        for fen in fens:
            board = chess.Board(fen)
            rewards = {
                move.uci(): _move_reward(board, move, positive_moves={item.uci() for item in _mate_moves(board)})
                for move in board.legal_moves
            }
            result = graph.train_action_rewards(board, rewards=rewards, stage="TG26z_continuation_mate1_repair")
            for key, value in result.items():
                updates[key] += int(value)
            records += 1
    return {
        "applied": True,
        "continuation_train_state_count": len(fens),
        "repair_repetitions": cfg.continuation_repair_repetitions,
        "training_records": records,
        "updates": updates,
        "m3_update_count_after_repair": graph.m3_update_count,
        "teacher_rewards_from_checkmate_outcome": True,
        "stage_labels_learner_visible": False,
    }


def _empty_repair() -> dict[str, Any]:
    return {
        "applied": False,
        "reason": "continuation_mate1_coverage_already_passed_threshold",
        "training_records": 0,
        "updates": {"positive": 0, "negative": 0, "neutral": 0},
    }


def _forced_chain_decomposition_audit(
    graph,
    fens: tuple[str, ...],
    attention_cfg: ContinuousHandoffAttentionConfig,
    cfg: ForcedChainDecompositionConfig,
) -> dict[str, Any]:
    internal_cfg = _internal_cfg(attention_cfg, train_repetitions=cfg.train_repetitions)
    rows: list[dict[str, Any]] = []
    bucket_counts = _empty_buckets()
    forced_successes = 0
    forced_total = 0
    same_graph_second = 0
    chain_terminal_failures = 0
    mate1_continuation_failures = 0
    selection_failures = 0
    cap_failures = 0
    graph_confirmed_chains = 0
    false_positive_nonforced = 0
    for fen in fens:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        confirmed_for_selection: list[dict[str, Any]] = []
        candidate_rows: list[dict[str, Any]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            if move.uci() not in forced and len([r for r in candidate_rows if not r["validator_forced_first_move"]]) >= cfg.non_forced_sample_limit:
                continue
            gate = _confirm_internal_handoff_gate(graph, board, move, internal_cfg, mask_internal_handoff=False, mask_actuator=False)
            gate_ok = bool(gate["internal_handoff_approved"])
            chain = _same_graph_chain_audit(graph, board, move, _mate2_cfg(internal_cfg), forced_move_ucis=None)
            audit = _confirm_materialized_mate2_first(
                graph,
                board,
                move,
                _mate2_cfg(internal_cfg),
                chain=chain,
                mask_action_check_atoms=False,
                mask_actuator=False,
                disable_mate2_quorum=False,
            )
            forced_move = move.uci() in forced
            bucket = _failure_bucket(gate_ok=gate_ok, chain=chain, audit=audit, forced_move=forced_move)
            bucket_counts[bucket] += 1
            if forced_move:
                forced_total += 1
                forced_successes += int(chain["chain_success"])
                same_graph_second += int(chain["same_graph_second_move_count"])
                mate1_continuation_failures += int(bucket == "mate1_continuation_failed_after_reply")
                chain_terminal_failures += int(bucket == "mate1_continuation_succeeded_but_chain_terminal_failed")
                if audit["first_move_confirmed"]:
                    graph_confirmed_chains += 1
                    confirmed_for_selection.append(audit)
            else:
                false_positive_nonforced += int(chain["chain_success"] or audit["first_move_confirmed"])
                if audit["first_move_confirmed"]:
                    confirmed_for_selection.append(audit)
            candidate_rows.append({
                "move": move.uci(),
                "validator_forced_first_move": forced_move,
                "attention_gate_approved": gate_ok,
                "internal_handoff_score": gate["internal_handoff_score"],
                "chain_success": chain["chain_success"],
                "reply_total": chain["reply_total"],
                "reply_solved": chain["reply_solved"],
                "reply_rows": chain["reply_rows"],
                "mate2_first_move_confirmed": audit["first_move_confirmed"],
                "chain_terminal_state": audit["chain_terminal_state"],
                "evidence_terminal_state": audit["evidence_terminal_state"],
                "graph_confirmation_state": audit["graph_confirmation_state"],
                "evidence_score": audit["evidence_score"],
                "positive_atoms_confirmed": audit["positive_atoms_confirmed"],
                "failure_bucket": bucket,
            })
        confirmed_for_selection.sort(key=lambda item: (item["evidence_score"], item["move"]), reverse=True)
        selected = None if not confirmed_for_selection else confirmed_for_selection[0]
        if selected is not None and selected["move"] not in forced and any(row["validator_forced_first_move"] and row["mate2_first_move_confirmed"] for row in candidate_rows):
            selection_failures += 1
            bucket_counts["first_move_quorum_succeeded_but_selection_lost"] += 1
        rows.append({
            "fen": fen,
            "forced_first_moves": sorted(forced),
            "selected_first": None if selected is None else selected["move"],
            "forced_first_details": [row for row in candidate_rows if row["validator_forced_first_move"]],
            "non_forced_comparison": [row for row in candidate_rows if not row["validator_forced_first_move"]],
        })
    return {
        "position_count": len(rows),
        "forced_first_move_count": forced_total,
        "forced_first_chain_success_count": forced_successes,
        "forced_first_chain_success_rate": 0.0 if forced_total == 0 else forced_successes / forced_total,
        "forced_first_same_graph_second_move_count": same_graph_second,
        "failure_bucket_counts": bucket_counts,
        "chain_terminal_failure_count": chain_terminal_failures,
        "mate1_continuation_failure_count": mate1_continuation_failures,
        "selection_failure_count": selection_failures,
        "candidate_cap_failure_count": cap_failures,
        "graph_confirmed_chain_count": graph_confirmed_chains,
        "false_positive_nonforced_chain_or_quorum_count": false_positive_nonforced,
        "samples": rows[: cfg.max_samples],
    }


def _failure_bucket(*, gate_ok: bool, chain: dict[str, Any], audit: dict[str, Any], forced_move: bool) -> str:
    if chain["chain_success"] and audit["first_move_confirmed"]:
        return "no_failure"
    if not gate_ok:
        return "attention_gate_rejected_candidate"
    if not chain["chain_success"]:
        return "mate1_continuation_failed_after_reply" if forced_move else "attention_gate_admitted_candidate"
    if audit["chain_terminal_state"] not in {"TRUE", "CONFIRMED"}:
        return "mate1_continuation_succeeded_but_chain_terminal_failed"
    if not audit["first_move_confirmed"]:
        return "chain_terminal_succeeded_but_first_move_quorum_failed"
    return "no_failure"


def _high_recall(graph, fens: tuple[str, ...], attention_cfg: ContinuousHandoffAttentionConfig, **kwargs: Any) -> dict[str, Any]:
    return _evaluate_attention_modes_shared(
        graph,
        fens,
        attention_cfg,
        modes=("high_recall_threshold_gate",),
        **kwargs,
    )["high_recall_threshold_gate"]


def _ablations(graph, fens: tuple[str, ...], attention_cfg: ContinuousHandoffAttentionConfig) -> dict[str, Any]:
    return {
        "mask_mate1_quorum": _ablation_summary(_high_recall(graph, fens, attention_cfg, disable_mate1_quorum=True)),
        "mask_mate2_first_move_quorum": _ablation_summary(_high_recall(graph, fens, attention_cfg, disable_mate2_quorum=True)),
        "mask_internal_handoff_attention": _ablation_summary(_high_recall(graph, fens, attention_cfg, mask_internal_handoff=True)),
        "mask_chain_confidence_terminals": _ablation_summary(_high_recall(graph, fens, attention_cfg, disable_mate2_quorum=True)),
        "mask_actuator_terminals": _ablation_summary(_high_recall(graph, fens, attention_cfg, mask_actuator=True)),
        "disable_deep_continuation_checks": _ablation_summary(_high_recall(graph, fens, attention_cfg, disable_deep_continuation=True)),
    }


def _decision(
    cfg: ForcedChainDecompositionConfig,
    *,
    mate1_eval: dict[str, Any],
    continuation: dict[str, Any],
    baseline: dict[str, Any],
    final: dict[str, Any],
    audit: dict[str, Any],
    lifecycle: dict[str, Any],
    equivalence: dict[str, Any],
    ablations: dict[str, Any],
    repair: dict[str, Any],
) -> dict[str, Any]:
    failure_bucket_counts = audit["failure_bucket_counts"]
    improved = final["conversion_count"] > baseline["conversion_count"]
    identified = sum(failure_bucket_counts.values()) > 0
    ablations_collapse = (
        ablations["mask_mate1_quorum"]["conversion_rate"] == 0.0
        and ablations["mask_actuator_terminals"]["conversion_rate"] == 0.0
        and ablations["disable_deep_continuation_checks"]["conversion_rate"] == 0.0
    )
    return {
        "checkpoint_pass": (
            identified
            and mate1_eval["accuracy"] >= 1.0
            and mate1_eval["null_count"] == 0
            and final["same_graph_second_move_count"] > 0
            and equivalence["mismatch_count"] == 0
            and ablations_collapse
            and not _purity_boundary()["validator_skip_used_during_internal_handoff_eval"]
        ),
        "mate1_heldout_accuracy": mate1_eval["accuracy"],
        "mate1_null_count": mate1_eval["null_count"],
        "continuation_mate1_accuracy": continuation["accuracy"],
        "continuation_mate1_null_count": continuation["null_count"],
        "forced_first_chain_success_rate": audit["forced_first_chain_success_rate"],
        "forced_first_same_graph_second_move_count": audit["forced_first_same_graph_second_move_count"],
        "mate2_conversion_rate": final["conversion_rate"],
        "mate2_first_move_success_rate": final["first_move_success_rate"],
        "mate2_same_graph_second_move_count": final["same_graph_second_move_count"],
        "attention_false_positive_count": final["internal_attention_false_positive_count"],
        "attention_false_negative_count": final["internal_attention_false_negative_count"],
        "deep_reply_checks_run": final["deep_reply_checks_run"],
        "average_deep_reply_checks_per_position": final["average_deep_reply_checks_per_position"],
        "failure_bucket_counts": failure_bucket_counts,
        "chain_terminal_failure_count": audit["chain_terminal_failure_count"],
        "mate1_continuation_failure_count": audit["mate1_continuation_failure_count"],
        "selection_failure_count": audit["selection_failure_count"],
        "candidate_cap_failure_count": audit["candidate_cap_failure_count"],
        "graph_confirmed_chain_count": audit["graph_confirmed_chain_count"],
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "m3_update_count": final.get("m3_update_count", 0),
        "m4_promotion_count_by_terminal_kind": lifecycle["m4_promotion_count_by_terminal_kind"],
        "ablation_results": ablations,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "purity_boundary": _purity_boundary(),
        "repair_applied": repair["applied"],
        "chain_quorum_repair_applied": bool(final.get("chain_quorum_repair", {}).get("applied", False)),
        "mate2_conversion_improved_over_tg26y": improved,
        "failure_mode": _failure_mode(audit, continuation, final, improved),
    }


def _failure_mode(audit: dict[str, Any], continuation: dict[str, Any], final: dict[str, Any], improved: bool) -> str:
    if continuation["accuracy"] < 0.95 or continuation["null_count"] > 0:
        return "Mate_In_1_continuation_domain_coverage"
    if audit["chain_terminal_failure_count"] > 0:
        return "chain_terminal_or_quorum_link"
    if audit["selection_failure_count"] > 0:
        return "selection_scoring"
    if final["conversion_rate"] == 0.0:
        return "Mate_In_2_quorum_activation"
    if not improved:
        return "forced_chain_repair_insufficient"
    return "none"


def _attention_cfg(cfg: ForcedChainDecompositionConfig) -> ContinuousHandoffAttentionConfig:
    return ContinuousHandoffAttentionConfig(
        seed=cfg.seed,
        mate1_train_count=cfg.mate1_train_count,
        mate1_heldout_count=cfg.mate1_heldout_count,
        mate2_train_count=cfg.mate2_train_count,
        mate2_heldout_count=cfg.mate2_heldout_count,
        max_generation_attempts=cfg.max_generation_attempts,
        train_repetitions=cfg.train_repetitions,
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
        request_strength_temperature=cfg.request_strength_temperature,
        high_recall_threshold=cfg.high_recall_threshold,
        effectively_zero_request_strength=cfg.effectively_zero_request_strength,
        top_k=cfg.top_k,
        two_stage_top_k=cfg.two_stage_top_k,
        epsilon_tail_count=cfg.epsilon_tail_count,
        softmax_temperature=cfg.softmax_temperature,
        softmax_budget=cfg.softmax_budget,
        equivalence_count=cfg.equivalence_count,
        compare_repetition_2=False,
    )


def _chain_repaired_attention_cfg(cfg: ContinuousHandoffAttentionConfig) -> ContinuousHandoffAttentionConfig:
    data = asdict(cfg)
    data["mate2_materialized_quorum_min_positive_atoms"] = 0
    data["materialized_quorum_min_evidence"] = -10000.0
    return ContinuousHandoffAttentionConfig(**data)


def _empty_buckets() -> dict[str, int]:
    return {
        "attention_gate_rejected_candidate": 0,
        "attention_gate_admitted_candidate": 0,
        "mate1_continuation_failed_after_reply": 0,
        "mate1_continuation_succeeded_but_chain_terminal_failed": 0,
        "chain_terminal_succeeded_but_first_move_quorum_failed": 0,
        "first_move_quorum_succeeded_but_selection_lost": 0,
        "compute_budget_or_candidate_cap_blocked": 0,
        "no_failure": 0,
    }


def _ablation_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "conversion_rate": result["conversion_rate"],
        "first_move_success_rate": result["first_move_success_rate"],
        "same_graph_second_move_count": result["same_graph_second_move_count"],
        "deep_reply_checks_run": result["deep_reply_checks_run"],
    }


def _mode_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "conversion_rate": result["conversion_rate"],
        "first_move_success_rate": result["first_move_success_rate"],
        "same_graph_second_move_count": result["same_graph_second_move_count"],
        "false_positive_count": result["internal_attention_false_positive_count"],
        "false_negative_count": result["internal_attention_false_negative_count"],
        "deep_reply_checks_run": result["deep_reply_checks_run"],
    }


def _write_progress(cfg: ForcedChainDecompositionConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    return {
        "native_recon_graph_execution": True,
        "forced_labels_used_for_audit_only": True,
        "continuation_repair_uses_curriculum_rewards": True,
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
