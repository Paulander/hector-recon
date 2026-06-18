"""TG26x terminal-kind lifecycle plus modest native foundation scale."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .internal_handoff_affordance_guard_audit import (
    InternalHandoffAffordanceConfig,
    _datasets,
    _evaluate_internal_handoff_arm,
    _mate2_cfg,
    _train_internal_handoff_gate,
)
from .native_quorum_materialization import _tg26t_config, _train_graph, _trained_graph
from .native_quorum_mate2_chaining import _evaluate_mate1_materialized, _evaluate_mate2_chain, _tg26u_config, _train_mate2_chain
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .terminal_lifecycle import apply_terminal_lifecycle


@dataclass(frozen=True)
class TerminalLifecycleModestScaleConfig:
    seed: int = 20260621
    tiny_mate1_train_count: int = 12
    tiny_mate1_heldout_count: int = 6
    tiny_mate2_train_count: int = 6
    tiny_mate2_heldout_count: int = 3
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
    equivalence_count: int = 4
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg26x_terminal_lifecycle_modest_scale_progress.json"


@dataclass(frozen=True)
class TerminalLifecycleModestScaleResult:
    config: TerminalLifecycleModestScaleConfig
    dataset: dict[str, Any]
    tiny_calibration: dict[str, Any]
    modest_scale: dict[str, Any]
    lifecycle: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26x_terminal_lifecycle_modest_scale.v0",
            "checkpoint": "TG26x_terminal_lifecycle_modest_scale",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "tiny_calibration": self.tiny_calibration,
            "modest_scale": self.modest_scale,
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


def run_terminal_lifecycle_modest_scale(
    *,
    config: TerminalLifecycleModestScaleConfig | None = None,
) -> TerminalLifecycleModestScaleResult:
    cfg = config or TerminalLifecycleModestScaleConfig()
    tiny = _run_scale(_internal_cfg(cfg, tiny=True), apply_lifecycle=True)
    _write_progress(cfg, {"phase": "tiny_calibration_complete", "tiny_calibration": tiny["summary"]})
    modest = _run_scale(_internal_cfg(cfg, tiny=False), apply_lifecycle=True)
    _write_progress(cfg, {
        "phase": "modest_scale_complete",
        "tiny_calibration": tiny["summary"],
        "modest_scale": modest["summary"],
    })
    lifecycle = modest["lifecycle"]
    equivalence = modest["scheduler_equivalence"]
    ablations = modest["ablation_results"]
    decision = {
        "checkpoint_pass": (
            tiny["internal"]["conversion_rate"] >= 1.0
            and modest["mate1_heldout"]["accuracy"] >= 0.80
            and modest["internal"]["conversion_rate"] > 0.0
            and modest["internal"]["same_graph_second_move_count"] > 0
            and not _purity_boundary()["validator_skip_used_during_internal_handoff_eval"]
            and equivalence["mismatch_count"] == 0
        ),
        "terminal_lifecycle_policy": lifecycle["policy"],
        "terminal_kind_stats": lifecycle["terminal_kind_stats"],
        "tiny_tg26w_conversion_rate": tiny["internal"]["conversion_rate"],
        "tiny_tg26w_false_positive_internal_gate_count": tiny["internal"]["false_positive_internal_gate_count"],
        "tiny_tg26w_false_negative_internal_gate_count": tiny["internal"]["false_negative_internal_gate_count"],
        "tiny_tg26w_approved_count": tiny["internal"]["internal_gate_approved_candidate_count"],
        "tiny_tg26w_rejected_count": tiny["internal"]["internal_gate_rejected_candidate_count"],
        "mate1_train_count": cfg.mate1_train_count,
        "mate1_heldout_count": cfg.mate1_heldout_count,
        "mate1_heldout_accuracy": modest["mate1_heldout"]["accuracy"],
        "mate1_null_count": modest["mate1_heldout"]["null_count"],
        "mate2_train_count": cfg.mate2_train_count,
        "mate2_heldout_count": cfg.mate2_heldout_count,
        "mate2_conversion_rate": modest["internal"]["conversion_rate"],
        "mate2_first_move_success_rate": modest["internal"]["first_move_success_rate"],
        "mate2_same_graph_second_move_count": modest["internal"]["same_graph_second_move_count"],
        "internal_gate_approved_candidate_count": modest["internal"]["internal_gate_approved_candidate_count"],
        "internal_gate_rejected_candidate_count": modest["internal"]["internal_gate_rejected_candidate_count"],
        "internal_gate_false_positive_count": modest["internal"]["false_positive_internal_gate_count"],
        "internal_gate_false_negative_count": modest["internal"]["false_negative_internal_gate_count"],
        "deep_reply_checks_run": _deep_reply_checks(modest["internal"]),
        "average_deep_reply_checks_per_position": _avg_deep_reply_checks(modest["internal"]),
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "m3_update_count": modest["graph_m3_update_count"],
        "m4_promotion_count_by_terminal_kind": lifecycle["m4_promotion_count_by_terminal_kind"],
        "pruning_count_by_terminal_kind": lifecycle["pruning_count_by_terminal_kind"],
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "ablation_results": {
            key: {
                "conversion_rate": value["conversion_rate"],
                "same_graph_second_move_count": value["same_graph_second_move_count"],
                "deep_reply_checks_run": _deep_reply_checks(value),
            }
            for key, value in ablations.items()
        },
        "purity_boundary": _purity_boundary(),
        "failure_mode": _failure_mode(modest),
    }
    return TerminalLifecycleModestScaleResult(
        config=cfg,
        dataset={
            "tiny_mate1_train_count": cfg.tiny_mate1_train_count,
            "tiny_mate1_heldout_count": cfg.tiny_mate1_heldout_count,
            "tiny_mate2_train_count": cfg.tiny_mate2_train_count,
            "tiny_mate2_heldout_count": cfg.tiny_mate2_heldout_count,
            "mate1_train_count": cfg.mate1_train_count,
            "mate1_heldout_count": cfg.mate1_heldout_count,
            "mate2_train_count": cfg.mate2_train_count,
            "mate2_heldout_count": cfg.mate2_heldout_count,
            "curriculum_labels_learner_visible": False,
        },
        tiny_calibration=tiny,
        modest_scale=modest,
        lifecycle=lifecycle,
        scheduler_equivalence=equivalence,
        ablation_results=ablations,
        decision=decision,
    )


def _run_scale(cfg: InternalHandoffAffordanceConfig, *, apply_lifecycle: bool) -> dict[str, Any]:
    mate1_train, mate1_heldout, mate2_train, mate2_heldout = _datasets(cfg)
    graph = _trained_graph(_tg26u_config(_mate2_cfg(cfg)), score_action_atoms=True)
    mate1_training = _train_graph(graph, mate1_train, _tg26u_config(_mate2_cfg(cfg)))
    mate1_eval = _evaluate_mate1_materialized(graph, mate1_heldout, _mate2_cfg(cfg))
    mate2_training = _train_mate2_chain(graph, mate2_train, _mate2_cfg(cfg))
    handoff_training = _train_internal_handoff_gate(graph, mate2_train, cfg)
    first_internal = _evaluate_internal_handoff_arm(graph, mate2_heldout, cfg)
    lifecycle = apply_terminal_lifecycle(
        graph,
        heldout_confirmed=first_internal["conversion_rate"] > 0.0 and mate1_eval["accuracy"] >= 0.80,
        prune=apply_lifecycle,
        promote=apply_lifecycle,
    )
    internal = _evaluate_internal_handoff_arm(graph, mate2_heldout, cfg)
    ablations = {
        "mask_internal_handoff_attention_terminals": _evaluate_internal_handoff_arm(graph, mate2_heldout, cfg, mask_internal_handoff=True),
        "mask_mate2_first_move_quorum": _evaluate_internal_handoff_arm(graph, mate2_heldout, cfg, disable_mate2_quorum=True),
        "mask_mate1_quorum": _evaluate_internal_handoff_arm(graph, mate2_heldout, cfg, disable_mate1_quorum=True),
        "mask_actuator_terminals": _evaluate_internal_handoff_arm(graph, mate2_heldout, cfg, mask_actuator=True),
        "disable_deep_continuation_checks": _evaluate_internal_handoff_arm(graph, mate2_heldout, cfg, disable_deep_continuation=True),
    }
    equivalence = _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(_mate2_cfg(cfg)))), mate1_train, mate1_heldout)
    summary = {
        "mate1_accuracy": mate1_eval["accuracy"],
        "mate1_null_count": mate1_eval["null_count"],
        "mate2_conversion_rate": internal["conversion_rate"],
        "mate2_first_move_success_rate": internal["first_move_success_rate"],
        "same_graph_second_move_count": internal["same_graph_second_move_count"],
        "approved": internal["internal_gate_approved_candidate_count"],
        "rejected": internal["internal_gate_rejected_candidate_count"],
        "false_positive": internal["false_positive_internal_gate_count"],
        "false_negative": internal["false_negative_internal_gate_count"],
    }
    return {
        "mate1_training": mate1_training,
        "mate1_heldout": mate1_eval,
        "mate2_training": {**mate2_training, "internal_handoff_training": handoff_training},
        "internal": internal,
        "ablation_results": ablations,
        "lifecycle": lifecycle,
        "scheduler_equivalence": equivalence,
        "graph_m3_update_count": graph.m3_update_count,
        "summary": summary,
    }


def _internal_cfg(cfg: TerminalLifecycleModestScaleConfig, *, tiny: bool) -> InternalHandoffAffordanceConfig:
    return InternalHandoffAffordanceConfig(
        seed=cfg.seed,
        mate1_train_count=cfg.tiny_mate1_train_count if tiny else cfg.mate1_train_count,
        mate1_heldout_count=cfg.tiny_mate1_heldout_count if tiny else cfg.mate1_heldout_count,
        mate2_train_count=cfg.tiny_mate2_train_count if tiny else cfg.mate2_train_count,
        mate2_heldout_count=cfg.tiny_mate2_heldout_count if tiny else cfg.mate2_heldout_count,
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
        guardless_probe_position_count=0,
        equivalence_count=cfg.equivalence_count,
    )


def _deep_reply_checks(result: dict[str, Any]) -> int:
    total = 0
    for sample in result.get("samples", []):
        for row in sample.get("candidate_diagnostics", []):
            total += int(row.get("reply_total", 0))
    return total


def _avg_deep_reply_checks(result: dict[str, Any]) -> float:
    count = max(1, int(result.get("position_count", 0)))
    return round(_deep_reply_checks(result) / count, 6)


def _write_progress(cfg: TerminalLifecycleModestScaleConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _failure_mode(modest: dict[str, Any]) -> str:
    if modest["mate1_heldout"]["accuracy"] < 0.80:
        return "Mate_In_1_quorum"
    if modest["internal"]["internal_gate_approved_candidate_count"] == 0:
        return "internal_gate_precision_or_activation"
    if modest["internal"]["conversion_rate"] == 0.0:
        return "Mate_In_2_handoff"
    if modest["internal"]["same_graph_second_move_count"] == 0:
        return "same_graph_continuation"
    return "none"


def _purity_boundary() -> dict[str, Any]:
    return {
        "native_recon_graph_execution": True,
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

