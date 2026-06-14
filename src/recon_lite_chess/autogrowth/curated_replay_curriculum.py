"""TG26k cumulative curated replay runway.

This checkpoint uses the repaired early KRK curriculum as a schedule while the
behavior-changing path remains terminal-local ReCoN substrate state. It trains
foundation buckets cumulatively instead of from scratch and records whether
terminal spawning/weights grow without forgetting earlier buckets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from .curated_terminal_curriculum import CuratedStageEntry, curated_stage_entries
from .features import validate_learner_record
from .foundation_curriculum import _mate_moves
from .terminal_substrate import (
    TerminalAffordanceLearner,
    _evaluate_terminal_mate_in_one,
    _evaluate_terminal_mate_in_two,
    _train_terminal_mate_in_one,
    _train_terminal_mate_in_two,
)


@dataclass(frozen=True)
class CuratedReplayCurriculumConfig:
    include_symmetries: bool = True
    train_repetitions: int = 5
    replay_repetitions: int = 2
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    mate1_regression_threshold: float = 0.98
    mate2_bucket_threshold: float = 0.90
    mate2_cumulative_threshold: float = 0.90
    max_samples: int = 32


@dataclass(frozen=True)
class CuratedReplayCurriculumResult:
    config: CuratedReplayCurriculumConfig
    dataset: dict[str, Any]
    mate1_foundation: dict[str, Any]
    mate2_bucket_sequence: tuple[dict[str, Any], ...]
    final_evaluation: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26k_curated_replay_curriculum.v0",
            "config": asdict(self.config),
            "purity_boundary": {
                "curriculum_labels_are_schedule_and_diagnostics_only": True,
                "stage_labels_learner_visible": False,
                "strategic_descriptions_learner_visible": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "direct_provider_override": False,
                "behavior_mediated_by_terminal_activations_and_weights": True,
            },
            "dataset": self.dataset,
            "mate1_foundation": self.mate1_foundation,
            "mate2_bucket_sequence": list(self.mate2_bucket_sequence),
            "final_evaluation": self.final_evaluation,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_curated_replay_curriculum(
    *,
    config: CuratedReplayCurriculumConfig | None = None,
) -> CuratedReplayCurriculumResult:
    cfg = config or CuratedReplayCurriculumConfig()
    entries = curated_stage_entries(include_symmetries=cfg.include_symmetries)
    mate1_fens = _unique(
        entry.fen
        for entry in entries
        if entry.stage_name == "Mate_In_1" and entry.mate_in_one_moves
    )
    mate2_buckets = _mate2_buckets(entries)
    mate2_all_fens = _unique(fen for bucket in mate2_buckets for fen in bucket["fens"])

    mate1_learner = TerminalAffordanceLearner.create(
        eta_m3=cfg.eta_m3,
        rich_feature_credit_scale=cfg.rich_feature_credit_scale,
    )
    mate2_learner = TerminalAffordanceLearner.create(
        eta_m3=cfg.eta_m3,
        rich_feature_credit_scale=cfg.rich_feature_credit_scale,
    )

    mate1_train = tuple(fen for fen in mate1_fens for _ in range(cfg.train_repetitions))
    mate1_training = _train_terminal_mate_in_one(mate1_train, learner=mate1_learner)
    mate1_eval = _evaluate_terminal_mate_in_one(
        mate1_fens,
        learner=mate1_learner,
        max_samples=cfg.max_samples,
    )

    sequence: list[dict[str, Any]] = []
    learned_fens: list[str] = []
    for bucket in mate2_buckets:
        before_m3 = mate2_learner.m3_update_count
        before_terminals = len(mate2_learner.terminals)
        prior_replay_position_count = len(learned_fens)
        train_fens = (
            tuple(fen for fen in learned_fens for _ in range(cfg.replay_repetitions))
            + tuple(fen for fen in bucket["fens"] for _ in range(cfg.train_repetitions))
        )
        training = _train_terminal_mate_in_two(
            train_fens,
            first_learner=mate2_learner,
            mate_learner=mate1_learner,
        )
        learned_fens = list(_unique([*learned_fens, *bucket["fens"]]))
        current_eval = _evaluate_terminal_mate_in_two(
            tuple(bucket["fens"]),
            first_learner=mate2_learner,
            mate_learner=mate1_learner,
            max_samples=cfg.max_samples,
        )
        cumulative_eval = _evaluate_terminal_mate_in_two(
            tuple(learned_fens),
            first_learner=mate2_learner,
            mate_learner=mate1_learner,
            max_samples=cfg.max_samples,
        )
        mate1_regression = _evaluate_terminal_mate_in_one(
            mate1_fens,
            learner=mate1_learner,
            max_samples=cfg.max_samples,
        )
        sequence.append({
            "bucket": {
                "bucket_id": bucket["bucket_id"],
                "stage_name": bucket["stage_name"],
                "position_index": bucket["position_index"],
                "position_count": len(bucket["fens"]),
                "description": bucket["description"],
                "fens": bucket["fens"],
                "forced_first_moves_by_fen": bucket["forced_first_moves_by_fen"],
            },
            "replay": {
                "current_train_records": len(bucket["fens"]) * cfg.train_repetitions,
                "prior_replay_records": prior_replay_position_count * cfg.replay_repetitions,
                "prior_replay_position_count": prior_replay_position_count,
                "replay_order": "prior_then_current",
            },
            "training": training,
            "current_bucket_evaluation": current_eval,
            "cumulative_mate2_evaluation": cumulative_eval,
            "mate1_regression": mate1_regression,
            "growth": {
                "m3_update_delta": mate2_learner.m3_update_count - before_m3,
                "terminal_count_before": before_terminals,
                "terminal_count_after": len(mate2_learner.terminals),
                "spawned_terminal_delta": len(mate2_learner.terminals) - before_terminals,
            },
            "pass": (
                current_eval["conversion_rate"] >= cfg.mate2_bucket_threshold
                and cumulative_eval["conversion_rate"] >= cfg.mate2_cumulative_threshold
                and mate1_regression["accuracy"] >= cfg.mate1_regression_threshold
                and mate2_learner.m3_update_count > before_m3
            ),
        })

    final_mate1 = _evaluate_terminal_mate_in_one(
        mate1_fens,
        learner=mate1_learner,
        max_samples=cfg.max_samples,
    )
    final_mate2 = _evaluate_terminal_mate_in_two(
        mate2_all_fens,
        first_learner=mate2_learner,
        mate_learner=mate1_learner,
        max_samples=cfg.max_samples,
    )
    final = {
        "mate1": final_mate1,
        "mate2": final_mate2,
        "terminal_substrate": {
            "mate1_terminal_count": len(mate1_learner.terminals),
            "mate2_first_terminal_count": len(mate2_learner.terminals),
            "mate1_m3_update_count": mate1_learner.m3_update_count,
            "mate2_first_m3_update_count": mate2_learner.m3_update_count,
            "mate1_top_positive_terminals": mate1_learner.to_dict(max_terminals=8)["top_positive_terminals"],
            "mate2_top_positive_terminals": mate2_learner.to_dict(max_terminals=8)["top_positive_terminals"],
        },
    }
    return CuratedReplayCurriculumResult(
        config=cfg,
        dataset={
            "source": "src/recon_lite_chess/training/krk_curriculum.py::KRK_STAGES",
            "include_symmetries": cfg.include_symmetries,
            "mate1_position_count": len(mate1_fens),
            "mate2_bucket_count": len(mate2_buckets),
            "mate2_position_count": len(mate2_all_fens),
            "mate2_bucket_ids": [bucket["bucket_id"] for bucket in mate2_buckets],
        },
        mate1_foundation={
            "training": mate1_training,
            "evaluation": mate1_eval,
            "m4_consolidation_event_count": int(
                mate1_eval["accuracy"] >= cfg.mate1_regression_threshold
                and mate1_learner.m3_update_count > 0
            ),
        },
        mate2_bucket_sequence=tuple(sequence),
        final_evaluation=final,
        decision=_decision(cfg=cfg, sequence=sequence, final=final),
    )


def _mate2_buckets(entries: tuple[CuratedStageEntry, ...]) -> tuple[dict[str, Any], ...]:
    buckets: dict[tuple[str, int], dict[str, Any]] = {}
    for entry in entries:
        if entry.stage_name != "Mate_In_2" or not entry.forced_mate_in_two_first_moves:
            continue
        key = (entry.stage_name, entry.position_index)
        bucket = buckets.setdefault(
            key,
            {
                "bucket_id": f"{entry.stage_name}:{entry.position_index}",
                "stage_name": entry.stage_name,
                "position_index": entry.position_index,
                "description": entry.description,
                "fens": [],
                "forced_first_moves_by_fen": {},
            },
        )
        if entry.fen not in bucket["forced_first_moves_by_fen"]:
            bucket["fens"].append(entry.fen)
            bucket["forced_first_moves_by_fen"][entry.fen] = entry.forced_mate_in_two_first_moves
    ordered = tuple(
        bucket
        for _key, bucket in sorted(buckets.items(), key=lambda item: item[0][1])
    )
    validate_learner_record([
        {
            "bucket_id": bucket["bucket_id"],
            "position_count": len(bucket["fens"]),
        }
        for bucket in ordered
    ])
    return ordered


def _decision(
    *,
    cfg: CuratedReplayCurriculumConfig,
    sequence: list[dict[str, Any]],
    final: dict[str, Any],
) -> dict[str, Any]:
    all_buckets_pass = bool(sequence) and all(item["pass"] for item in sequence)
    unstable_bucket_count = sum(int(not item["pass"]) for item in sequence)
    final_pass = (
        final["mate1"]["accuracy"] >= cfg.mate1_regression_threshold
        and final["mate2"]["conversion_rate"] >= cfg.mate2_cumulative_threshold
        and all_buckets_pass
        and final["terminal_substrate"]["mate2_first_m3_update_count"] > 0
    )
    return {
        "checkpoint_pass": final_pass,
        "all_buckets_pass": all_buckets_pass,
        "unstable_bucket_count": unstable_bucket_count,
        "final_replay_recovers_cumulative_mate2": (
            final["mate2"]["conversion_rate"] >= cfg.mate2_cumulative_threshold
        ),
        "bucket_interference_observed": unstable_bucket_count > 0,
        "mate1_regression_pass": final["mate1"]["accuracy"] >= cfg.mate1_regression_threshold,
        "mate2_cumulative_pass": final["mate2"]["conversion_rate"] >= cfg.mate2_cumulative_threshold,
        "m3_updates_nonzero": final["terminal_substrate"]["mate2_first_m3_update_count"] > 0,
        "m4_mate2_consolidation_event_count": int(final_pass),
        "self_growth_status": (
            "terminal spawning and M3 weighting are active, but flat shared terminal weights show "
            "bucket interference before stable M4 consolidation"
        ),
        "next_step": (
            "advance to curated edge/fence graded rollout with replay guards"
            if final_pass
            else "add local/context-gated candidate structure before edge/fence graded rollout"
        ),
    }


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
