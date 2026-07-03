"""TG25 local precision gate for retry/fragment candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from recon_lite_chess.training.krk_curriculum import (
    box_min_side,
    compute_confinement_box,
    did_box_grow,
)

from .curriculum_reward_recovery import (
    CurriculumRewardRecoveryConfig,
    RetryRuntime,
    _build_retry_runtime,
    _build_yoked_random_runtime,
    _graded_paired_delta,
    _graded_playout,
    _safety_from_paired,
    _stage_slices,
    _summarize_rollouts,
    score_non_terminal_progress,
)
from .features import extract_diagnostic_features, validate_learner_record
from .positions import KRKPositionSet, generate_position_sets


@dataclass(frozen=True)
class PrecisionGateConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    min_support: int = 1
    max_candidates: int = 12
    horizons: tuple[int, ...] = (40, 80)
    min_sequence_credit: float = 0.10
    activation_max_distance: float = 0.5
    after_max_distance: float = 1.5
    chain_max_distance: float = 1.5
    max_chain_edges: int = 64
    chain_request_bonus: float = 0.75
    eta_m3: float = 0.08
    lag_negative_threshold: int = 1
    curriculum_probe_per_stage: int = 1
    max_rollout_samples: int = 8
    immediate_progress_threshold: float = 0.0


@dataclass(frozen=True)
class LocalPrecisionGate:
    immediate_progress_threshold: float
    suppress_confinement_worsening: bool
    suppress_rook_safety_regression: bool
    suppress_negative_immediate_progress: bool
    training_evidence: dict[str, Any]

    def evaluate(self, board: chess.Board, move: chess.Move | None, node: dict[str, Any] | None) -> dict[str, Any]:
        if move is None or move not in board.legal_moves:
            return {"suppress": False, "reason": "no_candidate_move"}
        before_features = extract_diagnostic_features(board)
        before_box = box_min_side(board)
        after = board.copy(stack=False)
        after.push(move)
        after_features = extract_diagnostic_features(after)
        after_box = box_min_side(after)
        confinement_would_worsen = did_box_grow(board, after)
        rook_safety_regression = (
            after_features["rook_present"] < before_features["rook_present"]
            or after_features["rook_attacked_by_black"] > before_features["rook_attacked_by_black"]
        )
        immediate_progress = score_non_terminal_progress(
            initial_features=before_features,
            final_features=after_features,
            initial_box=before_box,
            final_box=after_box,
            confinement_worsened_count=int(confinement_would_worsen),
            repetition_events=0,
            repeated_white_action_events=0,
            rook_attacked_count=int(after_features["rook_attacked_by_black"] > 0.0),
            rook_missing_count=int(after_features["rook_present"] <= 0.0),
        )
        if self.suppress_rook_safety_regression and rook_safety_regression:
            reason = "rook_safety_regression"
        elif self.suppress_confinement_worsening and confinement_would_worsen:
            reason = "confinement_would_worsen"
        elif self.suppress_negative_immediate_progress and immediate_progress < self.immediate_progress_threshold:
            reason = "negative_immediate_progress"
        else:
            reason = "passed"
        return {
            "suppress": reason != "passed",
            "reason": reason,
            "candidate_key": None if node is None else node.get("candidate_key"),
            "immediate_progress": immediate_progress,
            "box_min_side_before": before_box,
            "box_min_side_after": after_box,
            "box_min_side_delta": after_box - before_box,
            "confinement_would_worsen": confinement_would_worsen,
            "rook_safety_regression": bool(rook_safety_regression),
        }

    def to_dict(self) -> dict[str, Any]:
        learner_visible = {
            "node_type": "TERMINAL",
            "local_role": "candidate_precision_gate",
            "inputs": [
                "generic_board_features",
                "candidate_action_schema",
                "confinement_dimensions",
                "rook_safety_features",
                "immediate_progress_delta",
            ],
            "outputs": ["RET_inhibit_candidate_action"],
            "chooses_move_directly": False,
            "immediate_progress_threshold": self.immediate_progress_threshold,
        }
        validate_learner_record(learner_visible)
        return {
            "learner_visible": learner_visible,
            "suppress_confinement_worsening": self.suppress_confinement_worsening,
            "suppress_rook_safety_regression": self.suppress_rook_safety_regression,
            "suppress_negative_immediate_progress": self.suppress_negative_immediate_progress,
            "training_evidence": self.training_evidence,
        }


@dataclass(frozen=True)
class PrecisionGateResult:
    config: PrecisionGateConfig
    positions: KRKPositionSet
    retry_runtime: RetryRuntime
    yoked_random_runtime: RetryRuntime
    precision_gate: LocalPrecisionGate
    confirmation_metrics: dict[str, Any]
    confinement_sign_audit: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        primary = str(self.config.horizons[0])
        primary_metrics = self.confirmation_metrics[primary]
        return {
            "schema_version": "krk_autogrowth_tg25_local_precision_gate.v0",
            "checkpoint": "TG25_local_precision_gate",
            "config": {**asdict(self.config), "horizons": list(self.config.horizons)},
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "confinement_metric_sign_audit": self.confinement_sign_audit,
            "local_recon_structure": {
                "gate_node_type": "TERMINAL",
                "gate_relation": "RET",
                "gates_existing_retry_fragment_candidate": True,
                "gate_suppresses_only_candidate_action": True,
                "gate_chooses_replacement_move": False,
                "move_choice_mediated_by_local_script_nodes": True,
                "direct_move_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "curriculum_labels_learner_visible": False,
            },
            "credit_protocol": {
                "m3_train_select_split": "train",
                "m3_frozen_confirmation_split": "heldout",
                "confirmation_update_nodes": False,
                "m4_only_from_fresh_confirmation": True,
                "m4_consolidation_event_count": self.decision["m4_consolidation_event_count"],
            },
            "precision_gate": self.precision_gate.to_dict(),
            "arms": {
                "baseline": primary_metrics["baseline"],
                "ungated_candidate": primary_metrics["ungated_candidate"],
                "gated_candidate": primary_metrics["gated_candidate"],
                "yoked_random": primary_metrics["yoked_random"],
            },
            "paired_delta_metrics": primary_metrics["paired_deltas"],
            "safety_metrics": primary_metrics["safety_metrics"],
            "confirmation_metrics": self.confirmation_metrics,
            "decision": self.decision,
            "next_recommended_checkpoint": self.decision["next_recommended_checkpoint"],
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_precision_gate_experiment(
    *,
    config: PrecisionGateConfig,
    positions: KRKPositionSet | None = None,
) -> PrecisionGateResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    tg24_config = _as_tg24_config(config)
    retry_runtime = _build_retry_runtime(config=tg24_config, positions=positions)
    yoked_random_runtime = _build_yoked_random_runtime(config=tg24_config, positions=positions)
    precision_gate = derive_local_precision_gate(
        positions.train,
        config=config,
        retry_runtime=retry_runtime,
    )
    confirmation_metrics = _evaluate_confirmation(
        positions.heldout,
        config=config,
        retry_runtime=retry_runtime,
        yoked_random_runtime=yoked_random_runtime,
        precision_gate=precision_gate,
    )
    confinement_sign_audit = audit_confinement_sign_semantics()
    decision = _decision(
        config=config,
        metrics=confirmation_metrics,
        precision_gate=precision_gate,
    )
    return PrecisionGateResult(
        config=config,
        positions=positions,
        retry_runtime=retry_runtime,
        yoked_random_runtime=yoked_random_runtime,
        precision_gate=precision_gate,
        confirmation_metrics=confirmation_metrics,
        confinement_sign_audit=confinement_sign_audit,
        decision=decision,
    )


def derive_local_precision_gate(
    train_fens: Iterable[str],
    *,
    config: PrecisionGateConfig,
    retry_runtime: RetryRuntime,
) -> LocalPrecisionGate:
    horizon = max(config.horizons)
    tg24_config = _as_tg24_config(config)
    baseline = [
        _graded_playout(fen, arm="baseline", horizon=horizon, config=tg24_config, retry_runtime=None)
        for fen in train_fens
    ]
    ungated = [
        _graded_playout(
            fen,
            arm="continuation_retry_on",
            horizon=horizon,
            config=tg24_config,
            retry_runtime=retry_runtime,
        )
        for fen in train_fens
    ]
    negative_changed = 0
    positive_changed = 0
    neutral_changed = 0
    confinement_regression_changed = 0
    for base, candidate in zip(baseline, ungated):
        if not candidate["changed_from_baseline"]:
            continue
        graded_delta = candidate["graded_credit_total"] - base["graded_credit_total"]
        confinement_regressed = (
            candidate["confinement"]["box_grew_or_confinement_worsened_count"]
            > base["confinement"]["box_grew_or_confinement_worsened_count"]
        )
        if confinement_regressed:
            confinement_regression_changed += 1
        if graded_delta < 0.0 or confinement_regressed:
            negative_changed += 1
        elif graded_delta > 0.0:
            positive_changed += 1
        else:
            neutral_changed += 1
    evidence = {
        "source": "TG24-style paired train split evidence",
        "train_rollout_count": len(ungated),
        "changed_candidate_rollout_count": sum(1 for row in ungated if row["changed_from_baseline"]),
        "negative_or_confinement_regression_changed_count": negative_changed,
        "positive_changed_count": positive_changed,
        "neutral_changed_count": neutral_changed,
        "confinement_regression_changed_count": confinement_regression_changed,
        "m3_frozen_for_confirmation": True,
    }
    return LocalPrecisionGate(
        immediate_progress_threshold=config.immediate_progress_threshold,
        suppress_confinement_worsening=negative_changed > 0 or confinement_regression_changed > 0,
        suppress_rook_safety_regression=True,
        suppress_negative_immediate_progress=negative_changed > 0,
        training_evidence=evidence,
    )


def audit_confinement_sign_semantics() -> dict[str, Any]:
    examples = [
        chess.Board("8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"),
        chess.Board("8/8/8/8/2K5/6k1/4R3/8 w - - 0 1"),
    ]
    before, after = examples
    before_min = box_min_side(before)
    after_min = box_min_side(after)
    return {
        "source_function": "src/recon_lite_chess/training/krk_curriculum.py::did_box_grow",
        "definition": "confinement is considered worse when box_min_side_after > box_min_side_before",
        "box_min_side_delta_sign": "positive means looser/worse confinement; negative means tighter/better confinement",
        "compute_confinement_box_returns": "width,height proxy around black king using white rook line and board edges",
        "example_before_box": list(compute_confinement_box(before)),
        "example_after_box": list(compute_confinement_box(after)),
        "example_before_min_side": before_min,
        "example_after_min_side": after_min,
        "example_delta": after_min - before_min,
        "example_did_box_grow": did_box_grow(before, after),
        "used_by_gate": True,
    }


def _evaluate_confirmation(
    fens: Iterable[str],
    *,
    config: PrecisionGateConfig,
    retry_runtime: RetryRuntime,
    yoked_random_runtime: RetryRuntime,
    precision_gate: LocalPrecisionGate,
) -> dict[str, Any]:
    fens_tuple = tuple(fens)
    tg24_config = _as_tg24_config(config)
    by_horizon: dict[str, Any] = {}
    for horizon in config.horizons:
        baseline = [
            _graded_playout(fen, arm="baseline", horizon=horizon, config=tg24_config, retry_runtime=None)
            for fen in fens_tuple
        ]
        ungated = [
            _graded_playout(
                fen,
                arm="continuation_retry_on",
                horizon=horizon,
                config=tg24_config,
                retry_runtime=retry_runtime,
            )
            for fen in fens_tuple
        ]
        gated = [
            _graded_playout(
                fen,
                arm="continuation_retry_on",
                horizon=horizon,
                config=tg24_config,
                retry_runtime=retry_runtime,
                precision_gate=precision_gate,
            )
            for fen in fens_tuple
        ]
        yoked = [
            _graded_playout(
                fen,
                arm="yoked_random_control",
                horizon=horizon,
                config=tg24_config,
                retry_runtime=yoked_random_runtime,
            )
            for fen in fens_tuple
        ]
        by_horizon[str(horizon)] = {
            "baseline": _summarize_rollouts(baseline, arm="baseline", horizon=horizon, config=tg24_config),
            "ungated_candidate": _summarize_rollouts(
                ungated,
                arm="ungated_candidate",
                horizon=horizon,
                config=tg24_config,
            ),
            "gated_candidate": _summarize_rollouts(
                gated,
                arm="gated_candidate",
                horizon=horizon,
                config=tg24_config,
            ),
            "yoked_random": _summarize_rollouts(yoked, arm="yoked_random", horizon=horizon, config=tg24_config),
            "paired_deltas": {
                "baseline_vs_ungated": _graded_paired_delta(baseline, ungated),
                "baseline_vs_gated": _graded_paired_delta(baseline, gated),
                "ungated_vs_gated": _graded_paired_delta(ungated, gated),
                "baseline_vs_yoked_random": _graded_paired_delta(baseline, yoked),
            },
            "safety_metrics": {
                "ungated_candidate": _safety_from_paired(baseline, ungated),
                "gated_candidate": _safety_from_paired(baseline, gated),
                "yoked_random": _safety_from_paired(baseline, yoked),
            },
            "stage_slices": _stage_slices(baseline, gated, yoked),
            "samples": {
                "baseline": baseline[: config.max_rollout_samples],
                "ungated_candidate": ungated[: config.max_rollout_samples],
                "gated_candidate": gated[: config.max_rollout_samples],
                "yoked_random": yoked[: config.max_rollout_samples],
            },
        }
    return by_horizon


def _decision(
    *,
    config: PrecisionGateConfig,
    metrics: dict[str, Any],
    precision_gate: LocalPrecisionGate,
) -> dict[str, Any]:
    primary = str(config.horizons[0])
    primary_metrics = metrics[primary]
    ungated_vs_gated = primary_metrics["paired_deltas"]["ungated_vs_gated"]
    baseline_vs_gated = primary_metrics["paired_deltas"]["baseline_vs_gated"]
    safety = primary_metrics["safety_metrics"]["gated_candidate"]
    gate_suppressed = primary_metrics["gated_candidate"]["precision_gate_suppression_count"] > 0
    improves_vs_ungated = ungated_vs_gated["graded_credit_delta_sum"] > 0.0
    improves_vs_baseline = baseline_vs_gated["graded_credit_delta_sum"] > 0.0
    safety_clean = safety["protected_regression_count"] == 0
    m4_eligible = gate_suppressed and improves_vs_ungated and improves_vs_baseline and safety_clean
    return {
        "status": "tg25_gate_confirmation_pass" if m4_eligible else "tg25_gate_instrumented_no_m4",
        "primary_horizon": int(config.horizons[0]),
        "gate_suppression_count": primary_metrics["gated_candidate"]["precision_gate_suppression_count"],
        "gate_confinement_suppression_count": primary_metrics["gated_candidate"][
            "precision_gate_confinement_suppression_count"
        ],
        "graded_delta_gated_vs_ungated": ungated_vs_gated["graded_credit_delta_sum"],
        "graded_delta_gated_vs_baseline": baseline_vs_gated["graded_credit_delta_sum"],
        "gated_rook_loss_regressions": safety["rook_loss_regression_count"],
        "gated_stalemate_regressions": safety["stalemate_regression_count"],
        "gated_confinement_regressions": safety["confinement_regression_count"],
        "m3_training_selection_used": True,
        "m3_frozen_for_confirmation": True,
        "m4_eligible_from_fresh_confirmation": m4_eligible,
        "m4_consolidation_event_count": 1 if m4_eligible else 0,
        "behavior_mediated_by_local_recon_gate": True,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "curriculum_labels_learner_visible": False,
        "reasons": _decision_reasons(
            gate_suppressed=gate_suppressed,
            improves_vs_ungated=improves_vs_ungated,
            improves_vs_baseline=improves_vs_baseline,
            safety_clean=safety_clean,
            precision_gate=precision_gate,
        ),
        "next_recommended_checkpoint": (
            "Promote the local precision gate through M4 and test across seeds"
            if m4_eligible
            else "Inspect gate thresholds/context precision before M4; do not broaden candidate spawning yet"
        ),
    }


def _decision_reasons(
    *,
    gate_suppressed: bool,
    improves_vs_ungated: bool,
    improves_vs_baseline: bool,
    safety_clean: bool,
    precision_gate: LocalPrecisionGate,
) -> list[str]:
    reasons: list[str] = []
    if not gate_suppressed:
        reasons.append("gate_did_not_trigger_on_confirmation")
    if not improves_vs_ungated:
        reasons.append("gated_candidate_did_not_improve_vs_ungated")
    if not improves_vs_baseline:
        reasons.append("gated_candidate_did_not_improve_vs_baseline")
    if not safety_clean:
        reasons.append("gated_candidate_safety_regression")
    if not precision_gate.training_evidence["negative_or_confinement_regression_changed_count"]:
        reasons.append("weak_train_negative_evidence_for_gate")
    return reasons


def _as_tg24_config(config: PrecisionGateConfig) -> CurriculumRewardRecoveryConfig:
    return CurriculumRewardRecoveryConfig(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
        min_support=config.min_support,
        max_candidates=config.max_candidates,
        horizons=config.horizons,
        min_sequence_credit=config.min_sequence_credit,
        activation_max_distance=config.activation_max_distance,
        after_max_distance=config.after_max_distance,
        chain_max_distance=config.chain_max_distance,
        max_chain_edges=config.max_chain_edges,
        chain_request_bonus=config.chain_request_bonus,
        eta_m3=config.eta_m3,
        lag_negative_threshold=config.lag_negative_threshold,
        curriculum_probe_per_stage=config.curriculum_probe_per_stage,
        max_rollout_samples=config.max_rollout_samples,
    )
