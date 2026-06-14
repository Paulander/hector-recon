"""TG26l context-gated local terminal subgraphs for repaired Mate_In_2 buckets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from .curated_replay_curriculum import _mate2_buckets
from .curated_terminal_curriculum import curated_stage_entries
from .features import validate_learner_record
from .foundation_curriculum import _mate_moves
from .terminal_substrate import (
    TerminalAffordanceLearner,
    _bucket,
    _train_terminal_mate_in_one,
    _train_terminal_mate_in_two,
    extract_terminal_feature_vector,
)


@dataclass(frozen=True)
class ContextGatedCurriculumConfig:
    include_symmetries: bool = True
    train_repetitions: int = 5
    gate_min_overlap: float = 0.72
    gate_granularity: str = "position"
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    mate1_threshold: float = 0.98
    mate2_threshold: float = 0.95
    max_samples: int = 32


@dataclass(frozen=True)
class ContextGate:
    gate_id: str
    parent_locality: str
    prototypes: tuple[tuple[str, ...], ...]
    min_overlap: float

    def activation(self, board: chess.Board) -> dict[str, Any]:
        keys = set(context_terminal_keys(board))
        best_overlap = 0.0
        best_hits = 0
        best_total = 0
        for prototype in self.prototypes:
            prototype_set = set(prototype)
            hits = len(keys & prototype_set)
            total = max(1, len(prototype_set))
            overlap = hits / total
            if overlap > best_overlap:
                best_overlap = overlap
                best_hits = hits
                best_total = total
        return {
            "gate_id": self.gate_id,
            "parent_locality": self.parent_locality,
            "confirmed": best_overlap >= self.min_overlap,
            "overlap": round(best_overlap, 6),
            "hits": best_hits,
            "prototype_size": best_total,
            "chooses_move_directly": False,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "gate_id": self.gate_id,
            "parent_locality": self.parent_locality,
            "prototype_count": len(self.prototypes),
            "prototype_sizes": [len(item) for item in self.prototypes],
            "min_overlap": self.min_overlap,
            "node_type": "TERMINAL/SCRIPT context gate scaffold",
            "learner_visible_features": "generic before-position terminal buckets",
            "chooses_move_directly": False,
        }
        validate_learner_record(payload)
        return payload


@dataclass
class ContextGatedMate2Learner:
    gates: tuple[ContextGate, ...]
    first_learners: dict[str, TerminalAffordanceLearner]
    mate_learner: TerminalAffordanceLearner

    def choose_first(self, board: chess.Board) -> tuple[chess.Move | None, dict[str, Any]]:
        activations = [gate.activation(board) for gate in self.gates]
        confirmed = [item for item in activations if item["confirmed"]]
        had_confirmed_gate = bool(confirmed)
        if not confirmed:
            confirmed = sorted(activations, key=lambda item: item["overlap"], reverse=True)[:1]
        best_overlap = max(item["overlap"] for item in confirmed) if confirmed else 0.0
        active = [item for item in confirmed if item["overlap"] >= best_overlap]
        options: list[tuple[float, str, chess.Move]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            score = 0.0
            for activation in active:
                learner = self.first_learners[activation["gate_id"]]
                score += activation["overlap"] * learner.weight_for_move(board, move)
            options.append((score, move.uci(), move))
        if not options:
            return None, {"activations": activations, "active_gates": active, "had_confirmed_gate": had_confirmed_gate}
        options.sort(reverse=True)
        return options[0][-1], {
            "activations": activations,
            "active_gates": active,
            "had_confirmed_gate": had_confirmed_gate,
            "selected_score": round(options[0][0], 6),
        }


@dataclass(frozen=True)
class ContextGatedCurriculumResult:
    config: ContextGatedCurriculumConfig
    dataset: dict[str, Any]
    gates: tuple[dict[str, Any], ...]
    training: dict[str, Any]
    evaluation: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26l_context_gated_curriculum.v0",
            "config": asdict(self.config),
            "purity_boundary": {
                "curriculum_labels_are_schedule_and_diagnostics_only": True,
                "stage_labels_learner_visible": False,
                "strategic_descriptions_learner_visible": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "direct_provider_override": False,
                "behavior_mediated_by_context_gate_and_terminal_subgraph_weights": True,
            },
            "dataset": self.dataset,
            "gates": list(self.gates),
            "training": self.training,
            "evaluation": self.evaluation,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_context_gated_curriculum(
    *,
    config: ContextGatedCurriculumConfig | None = None,
) -> ContextGatedCurriculumResult:
    cfg = config or ContextGatedCurriculumConfig()
    entries = curated_stage_entries(include_symmetries=cfg.include_symmetries)
    mate1_fens = _unique(
        entry.fen
        for entry in entries
        if entry.stage_name == "Mate_In_1" and entry.mate_in_one_moves
    )
    buckets = _mate2_buckets(entries)
    contexts = _gate_contexts(buckets, granularity=cfg.gate_granularity)
    mate2_fens = _unique(fen for bucket in buckets for fen in bucket["fens"])
    mate_learner = TerminalAffordanceLearner.create(
        eta_m3=cfg.eta_m3,
        rich_feature_credit_scale=cfg.rich_feature_credit_scale,
    )
    mate1_train = tuple(fen for fen in mate1_fens for _ in range(cfg.train_repetitions))
    mate1_training = _train_terminal_mate_in_one(mate1_train, learner=mate_learner)

    gates: list[ContextGate] = []
    first_learners: dict[str, TerminalAffordanceLearner] = {}
    bucket_training: list[dict[str, Any]] = []
    for context in contexts:
        gate = ContextGate(
            gate_id=context["gate_id"],
            parent_locality="curated_mate2_local_parent",
            prototypes=tuple(tuple(context_terminal_keys(chess.Board(fen))) for fen in context["fens"]),
            min_overlap=cfg.gate_min_overlap,
        )
        learner = TerminalAffordanceLearner.create(
            eta_m3=cfg.eta_m3,
            rich_feature_credit_scale=cfg.rich_feature_credit_scale,
        )
        train_fens = tuple(fen for fen in context["fens"] for _ in range(cfg.train_repetitions))
        training = _train_terminal_mate_in_two(
            train_fens,
            first_learner=learner,
            mate_learner=mate_learner,
        )
        gates.append(gate)
        first_learners[gate.gate_id] = learner
        bucket_training.append({
            "bucket_id": gate.gate_id,
            "source_bucket_id": context["source_bucket_id"],
            "position_count": len(context["fens"]),
            "train_records": len(train_fens),
            "training": training,
            "gate": gate.to_dict(),
        })

    gated = ContextGatedMate2Learner(
        gates=tuple(gates),
        first_learners=first_learners,
        mate_learner=mate_learner,
    )
    evaluation = _evaluate_context_gated(
        mate2_fens,
        gated=gated,
        max_samples=cfg.max_samples,
    )
    gate_activation_summary = _gate_activation_summary(evaluation["samples"], total=evaluation["position_count"])
    decision = {
        "checkpoint_pass": (
            evaluation["conversion_rate"] >= cfg.mate2_threshold
            and gate_activation_summary["no_confirmed_gate_count"] == 0
        ),
        "m4_mate2_consolidation_event_count": int(
            evaluation["conversion_rate"] >= cfg.mate2_threshold
            and gate_activation_summary["no_confirmed_gate_count"] == 0
        ),
        "mate2_threshold": cfg.mate2_threshold,
        "context_gate_stabilized_bucket_admission": evaluation["conversion_rate"] >= cfg.mate2_threshold,
        "next_step": (
            "use context-gated local candidates as the repaired Mate_In_2 substrate before edge/fence"
            if evaluation["conversion_rate"] >= cfg.mate2_threshold
            else "tighten context gates before edge/fence"
        ),
    }
    return ContextGatedCurriculumResult(
        config=cfg,
        dataset={
            "source": "src/recon_lite_chess/training/krk_curriculum.py::KRK_STAGES",
            "include_symmetries": cfg.include_symmetries,
            "gate_granularity": cfg.gate_granularity,
            "mate1_position_count": len(mate1_fens),
            "mate2_bucket_count": len(buckets),
            "mate2_gate_context_count": len(contexts),
            "mate2_position_count": len(mate2_fens),
            "mate2_bucket_ids": [bucket["bucket_id"] for bucket in buckets],
        },
        gates=tuple(gate.to_dict() for gate in gates),
        training={
            "mate1": mate1_training,
            "mate2_buckets": bucket_training,
            "mate1_terminal_count": len(mate_learner.terminals),
            "mate1_m3_update_count": mate_learner.m3_update_count,
            "mate2_first_terminal_count_by_bucket": {
                gate_id: len(learner.terminals)
                for gate_id, learner in first_learners.items()
            },
            "mate2_first_m3_update_count_by_bucket": {
                gate_id: learner.m3_update_count
                for gate_id, learner in first_learners.items()
            },
        },
        evaluation={
            **evaluation,
            "gate_activation_summary": gate_activation_summary,
        },
        decision=decision,
    )


def context_terminal_keys(board: chess.Board) -> tuple[str, ...]:
    features = extract_terminal_feature_vector(board)
    keys = tuple(
        f"before_terminal:{key}={_bucket(value)}"
        for key, value in sorted(features.items())
    )
    validate_learner_record(keys)
    return keys


def _gate_contexts(buckets: tuple[dict[str, Any], ...], *, granularity: str) -> tuple[dict[str, Any], ...]:
    contexts: list[dict[str, Any]] = []
    for bucket in buckets:
        if granularity == "bucket":
            contexts.append({
                "gate_id": bucket["bucket_id"],
                "source_bucket_id": bucket["bucket_id"],
                "fens": tuple(bucket["fens"]),
            })
            continue
        if granularity != "position":
            raise ValueError(f"unsupported gate granularity: {granularity}")
        for index, fen in enumerate(bucket["fens"]):
            contexts.append({
                "gate_id": f"{bucket['bucket_id']}:context:{index}",
                "source_bucket_id": bucket["bucket_id"],
                "fens": (fen,),
            })
    return tuple(contexts)


def _evaluate_context_gated(
    fens: Iterable[str],
    *,
    gated: ContextGatedMate2Learner,
    max_samples: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_success = 0
    converted = 0
    replied_total = 0
    replied_mated = 0
    for fen in tuple(fens):
        board = chess.Board(fen)
        forced = _forced_mate_in_two_first_moves(board)
        forced_uci = {move.uci() for move in forced}
        first, gate_info = gated.choose_first(board)
        first_ok = first is not None and first.uci() in forced_uci
        first_success += int(first_ok)
        all_replies_mated = False
        reply_rows: list[dict[str, Any]] = []
        if first is not None:
            after_first = board.copy(stack=False)
            after_first.push(first)
            all_replies_mated = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                mate_move = gated.mate_learner.choose(before_mate)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                ok = mate_move is not None and mate_move.uci() in mates
                replied_total += 1
                replied_mated += int(ok)
                all_replies_mated = all_replies_mated and ok
                reply_rows.append({
                    "black_reply": reply.uci(),
                    "selected_mate": None if mate_move is None else mate_move.uci(),
                    "correct_mates": sorted(mates),
                    "mated": ok,
                })
        converted += int(first_ok and all_replies_mated)
        rows.append({
            "fen": fen,
            "selected_first": None if first is None else first.uci(),
            "forced_first_moves": sorted(forced_uci),
            "first_move_success": first_ok,
            "all_replies_mated": all_replies_mated,
            "gate_info": gate_info,
            "reply_checks": reply_rows[:8],
        })
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "forced_mate_reply_coverage": 0.0 if replied_total == 0 else replied_mated / replied_total,
        "wrong_first_move_count": total - first_success,
        "samples": rows[:max_samples],
    }


def _gate_activation_summary(samples: list[dict[str, Any]], *, total: int) -> dict[str, Any]:
    active_counts: dict[str, int] = {}
    no_confirmed = 0
    for row in samples:
        active = row["gate_info"]["active_gates"]
        no_confirmed += int(not row["gate_info"].get("had_confirmed_gate", False))
        for gate in active:
            active_counts[gate["gate_id"]] = active_counts.get(gate["gate_id"], 0) + 1
    return {
        "sampled_position_count": len(samples),
        "total_position_count": total,
        "active_gate_counts_in_samples": dict(sorted(active_counts.items())),
        "no_confirmed_gate_count": no_confirmed,
    }


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _forced_mate_in_two_first_moves(board: chess.Board) -> tuple[chess.Move, ...]:
    from .foundation_curriculum import _forced_mate_in_two_first_moves as forced

    return tuple(forced(board))
